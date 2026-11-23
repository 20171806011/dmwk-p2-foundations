"""Check budget-driven layout selection against a direct four-entry cost table."""
import argparse
import copy
import json
from pathlib import Path
import time

from compile_ir import compile_request, compiler

ROOT = Path(__file__).resolve().parent


def run_checks():
    start = time.perf_counter()
    source = json.loads((ROOT / "example_request.json").read_text())["source"]
    # Separately tabulated (dense words, rows, columns, full response capacity, max rank).
    table = [(12, 1, 1, 1, 1), (15, 1, 2, 2, 1), (16, 2, 1, 2, 1), (20, 2, 2, 4, 2)]
    checks = accepted = refused = 0
    samples = []
    for fmt in ("BF16", "FP32"):
        for cap in (11, 12, 15, 16, 20):
            for response in (1, 2, 3, 4, 5):
                for rank in (1, 2):
                    limits = dict(d_row_budget=2, d_col_budget=3, parameter_budget=cap,
                                  call_budget=7, min_A_response_dimension=response, required_update_rank=rank)
                    request = dict(source=source, fmt=fmt, layout_limits=limits)
                    fits = [r for r in table if r[0] <= cap and r[3] >= response and r[4] >= rank]
                    try:
                        artifact = compile_request(request)
                    except compiler.CompileRefused:
                        if fits:
                            raise AssertionError("Rejected a feasible shape")
                        refused += 1
                    else:
                        observed = artifact["layout"]["a_rows"], artifact["layout"]["a_cols"]
                        if not fits or observed != fits[0][1:3]:
                            raise AssertionError("Selected shape differs from the minimum in the cost table")
                        accepted += 1
                    checks += 1
        # A two-output anchor can require a more expensive shape with identical algebraic capacity.
        limits = dict(d_row_budget=2, d_col_budget=3, parameter_budget=20, call_budget=7,
                      min_A_response_dimension=2, required_update_rank=1)
        req = dict(source=source, fmt=fmt, layout_limits=limits,
                   response_request={"inputs":[[1]], "outputs":[[[1,1],[-1,1]]]})
        chosen = compile_request(req)
        if chosen["layout"]["full_shape"] != [4,4]:
            raise AssertionError("Anchor shape was omitted in planning")
        checks += 1
        accepted += 1
        denied = copy.deepcopy(req)
        denied["layout_limits"]["parameter_budget"] = 15
        try:
            compile_request(denied)
        except compiler.CompileRefused:
            refused += 1
            checks += 1
        else:
            raise AssertionError("Accepted anchor requiring 16 cells under 15-word budget")
        samples.append({"fmt":fmt,"two_output_anchor_shape":chosen["layout"]["full_shape"],
                        "physical_word_cost":chosen["cost"]["dense_matrix_word_slots"]})
    return {"schema":"dmwk-p2-c1-layout-search-v1", "status":"passed", "seed":20261114,
            "checks":checks, "compile_requests_accepted":accepted,"expected_refusals":refused,
            "unexpected_failures":0,"samples":samples,"elapsed_seconds":time.perf_counter()-start,
            "scope":"Complete named budget grid and anchor probes on the parity source; four supported shapes"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"layout_results.json")
    args = parser.parse_args()
    value = run_checks()
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")
    print(value["checks"], value["compile_requests_accepted"], value["expected_refusals"])

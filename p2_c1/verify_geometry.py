"""Read-only paired D graph diagnostics for stored gate-block edits."""
import argparse
import json
import time
from fractions import Fraction
from pathlib import Path

import c1_compiler as cc
from c1_runtime import get_fp

ROOT = Path(__file__).resolve().parent
SEED = 20261114


def select_wire(wire, state, inputs, selected, one):
    kind, index = wire
    if kind == "const":
        return (0, one)[index]
    return {"state": state, "input": inputs, "gate": selected}[kind][index]


def replay_graph(graph, bank, state, inputs, fmt):
    """Evaluate the bound graph on this bank's own wires under the C1 policy."""
    fp = get_fp()
    one = fp.encode_constant(1, fmt)
    selected = []
    traces = []
    audit = fp.Audit()
    for site in graph["D_calls"]:
        left, right = [select_wire(w, state, inputs, selected, one) for w in site["args"]]
        h = (left, right, one)
        pre, activated = [], []
        for i in site["rows"]:
            acc = site["bias_words"][i]
            for j in site["columns"]:
                term = fp.mul_words(bank[i][j], h[j], fmt, audit)
                acc = fp.add_words(acc, term, fmt, audit)
            pre.append(acc)
            activated.append(0 if fp.decode_word(acc, fmt) <= 0 else acc)
        if any(w not in (0, one) for w in activated):
            raise ValueError("Modified call leaves the certified Boolean invariant")
        selected.append(activated[site["selected_row"]])
        physical = h + (0,) * (len(bank[0])-3)
        traces.append((site["id"], physical, tuple(pre), tuple(activated), selected[-1]))

    def read_ports(key):
        return tuple(select_wire(w, state, inputs, selected, one) for w in graph[key])

    return traces, read_ports("next_state_wires"), read_ports("output_wires")


def compare(source, budget, artifact, candidate, fmt):
    cc.check_artifact(artifact, source, budget, fmt)
    old = cc.initial_weights(artifact)
    new = tuple(tuple(row) for row in candidate)
    if len(new) != len(old) or any(len(row) != len(old[0]) for row in new):
        raise ValueError("Shape of candidate differs from the artifact")
    delta = cc.xp.sub(cc.decode_matrix(new, fmt), cc.decode_matrix(old, fmt))
    if any(v for i, row in enumerate(delta.rows) for j, v in enumerate(row)
           if i >= 2 or j >= 3):
        raise ValueError("Comparison requires identical A and cross-block words")
    legal_states = cc.legal_states(artifact)
    legal_inputs = cc.legal_inputs(artifact)
    generators, failures = set(), []
    observed_sites = {site["id"]: set() for site in artifact["graph"]["D_calls"]}
    table = []
    count = 0
    for state in legal_states:
        for inputs in legal_inputs:
            initial = cc.execute_d(artifact, old, state, inputs)
            original = [(s["id"], s["physical_activation_words"], s["preactivation_words"],
                         s["D_output_words"], s["result_word"]) for s in initial["site_traces"]]
            alternative, next_state, output = replay_graph(artifact["graph"], new, state, inputs, fmt)
            for entry in original:
                h = tuple(get_fp().decode_word(x, fmt) for x in entry[1])
                observed_sites[entry[0]].add(h)
                generators.add(h)
            count += len(original)
            same = original == alternative and next_state == initial["next_state_words"] and output == initial["output_words"]
            table.append([state, inputs, original, alternative, initial["next_state_words"], next_state,
                          initial["output_words"], output])
            if not same:
                failures.append({"state": state, "input": inputs, "old_outputs": initial["output_words"],
                                 "new_outputs": output, "old_next": initial["next_state_words"],
                                 "new_next": next_state})
    def generator_rank(vectors):
        return cc.xp.rank(cc.xp.matrix(sorted(vectors), ncols=len(old[0])))
    coverage = artifact["proof"]["coverage"]
    per_site = {site["id"]: {tuple(x) for x in site["activation_bits"]} for site in coverage["per_site"]}
    if observed_sites != per_site or generators != {tuple(h) for h in coverage["all_state_activation_bits"]}:
        raise ValueError("Complete reference table disagrees with compiled activation proof")
    alg = all(sum(v*x for v, x in zip(row, h)) == 0 for row in delta.rows for h in generators)
    return {"source_sha256": artifact["source_sha256"], "artifact_sha256": cc.digest(artifact),
            "graph_sha256": artifact["graph_sha256"], "policy":artifact["numerical_policy"],
            "schedule": artifact["schedule"], "old_words":old,"candidate_words":new,
            "domain":artifact["domain"],"format": fmt, "state_input_contexts":len(table),
            "original_call_observations":count, "envelope_rank":generator_rank(generators),
            "per_site_rank":{site:generator_rank(hs) for site,hs in observed_sites.items()},
            "envelope_generators":[[int(x) for x in h] for h in sorted(generators)],
            "decoded_effective_delta":[[str(x) for x in row] for row in delta.rows],
            "actual_update_rank":cc.xp.rank(delta), "exact_annihilation_on_original_envelope":alg,
            "complete_observations_bitwise_equal":not failures, "counterexamples":failures,
            "paired_trace_sha256":cc.digest(table),"authorizes_commit":False}


def run_checks():
    import compiled_owner as owner
    start = time.perf_counter()
    if not __debug__:
        raise RuntimeError("Run geometry checks without optimization")
    checks = 0
    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    gate = ["and", ["const", 1], ["const", 1]]
    source = {"schema":cc.SCHEMA, "state_ports":["s"], "input_ports":["u"], "output_ports":["o"],
              "initial_states":[[0],[1]], "next_state":[gate], "outputs":[gate]}
    budget = cc.default_budget(1, 1)
    records, refusals = [], []
    for fmt, precision in (("BF16", 8), ("FP32", 24)):
        artifact = cc.compile_program(source, budget, fmt)
        live = owner.CompiledOwner(source, budget, fmt, owner.cu.OptimizerConfig("sgd", Fraction(1,4)))
        for name, coeffs, same in (("coupled_integer", (2,0,-1),True),
                                   ("midpoint_cancellation",(2**precision,1,-2**precision),False)):
            words = [list(row) for row in cc.initial_weights(artifact)]
            words[0][:3] = [get_fp().encode_constant(v,fmt) for v in coeffs]
            report = compare(source, budget, artifact, words, fmt)
            report["case"] = name
            check(report["exact_annihilation_on_original_envelope"] is True,"Exact annihilation")
            check(report["complete_observations_bitwise_equal"] is same,"Word equality classification")
            check(report["envelope_rank"] == report["actual_update_rank"] == 1,"Envelope/update rank")
            check(report["original_call_observations"] == 8 and report["state_input_contexts"] == 4,"Coverage")
            check(list(report["per_site_rank"].values()) == [1,1],"Per-site generator ranks")
            check(len(report["counterexamples"]) == (0 if same else 4),"Differing contexts")
            before = live.snapshot()
            try:
                live.prepare(owner.endpoint_request(words))
            except owner.UpdateRejected as exc:
                refusals.append({"format":fmt,"case":name,"reason":str(exc)})
            else:
                raise AssertionError("Immutable-cell edit unexpectedly prepared")
            check(live.snapshot() == before,"Refused edit changed live snapshot")
            records.append(report)
    return {"status":"passed", "schema":"c1-geometric-comparison-v1","seed":SEED,
            "checks":checks,"expected_refusals":len(refusals),"unexpected_failures":0,
            "cases":records,"refusals":refusals,"elapsed_seconds":time.perf_counter()-start,
            "scope":"Complete two-call constant-AND fixture, fixed graphs and own-wire replay. Read-only."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"geometric_results.json")
    result_path = parser.parse_args().output
    result = run_checks()
    result_path.parent.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:result[k] for k in ("status","checks","expected_refusals","elapsed_seconds")}))

"""New B4 capacity evidence only; prior verification suites are not imported."""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import time

from b4_runtime import environment_metadata, get_fp
import capacity_history as ch

xp = ch.xp
ROOT = Path(__file__).resolve().parent
SEED = 20261114


def _words(rows, fmt):
    return tuple(tuple(get_fp().encode_constant(v, fmt) for v in row) for row in rows)


def _row_zero(matrix):
    return all(v == 0 for row in matrix.rows for v in row)


def _small_consistent(equations):
    """Direct two-unknown equations, independently of producer RREF."""
    active = []
    for a, b, y in equations:
        if a == b == 0:
            if y != 0: return False
        else: active.append((a, b, y))
    if not active: return True
    a, b, y = active[0]
    solution = (y/a, Q(0)) if a != 0 else (Q(0), y/b)
    for c, d, z in active[1:]:
        det = a*d-b*c
        if det:
            solution = ((y*d-b*z)/det, (a*z-y*c)/det)
            break
    return all(a*solution[0]+b*solution[1] == y for a, b, y in equations)


def exact_cases():
    checks, cases = 0, 0
    digest = hashlib.sha256()
    H = xp.matrix(((1,), (0,)))
    pairs = tuple(product((-1, 0, 1), repeat=2))
    for fmt in ("BF16", "FP32"):
        for endpoints in product(pairs, repeat=3):
            hist = tuple(_words((row,), fmt) for row in endpoints)
            report = ch.analyze_history(hist, fmt, (H,), rank_cap=1)
            first, middle, last = endpoints
            current = middle[0] == first[0] and last[0] == middle[0]
            final = last[0] == first[0]
            assert report["all_current_space_checks_pass"] == current
            assert report["final_preserves_initial_space"] == final
            assert report["every_prefix_preserves_initial_space"] == (current and final)
            direct = tuple(Q(last[j]-first[j]) for j in range(2))
            assert report["final_difference"].rows == (direct,)
            assert report["telescope_sum"].rows == (direct,)
            assert all(s["budget"]["unrestricted_update_space_dimension"] == 1 for s in report["steps"])
            assert report["global_provenance_verified"] is False
            digest.update(repr((fmt, endpoints, current, final, direct)).encode())
            cases += 1; checks += 7
    rng = random.Random(SEED)
    seeded = []
    for case in range(72):
        n, d = rng.randrange(1, 4), rng.randrange(1, 5)
        r = rng.randrange(d+1)
        H = xp.eye(d) if r == d else xp.Matrix(tuple(tuple(Q(int(i == j or i == d-1)) for j in range(r)) for i in range(d)), r)
        N = xp.nullspace(xp.transpose(H)); c = d-r
        W = xp.matrix(tuple(tuple(rng.randrange(-2, 3) for _ in range(d)) for _ in range(n)))
        exact_history = [W]
        for _ in range(4):
            left = [rng.randrange(-1, 2) for _ in range(n)]
            right = [rng.randrange(-1, 2) for _ in range(c)]
            Z = xp.Matrix(tuple(tuple(Q(a*b) for b in right) for a in left), c)
            W = xp.add(W, xp.matmul(Z, xp.transpose(N)))
            exact_history.append(W)
        fmt = ("BF16", "FP32")[case % 2]
        stored = tuple(_words(W.rows, fmt) for W in exact_history)
        report = ch.analyze_history(stored, fmt, (H,), rank_cap=1, targets=xp.eye(d))
        assert report["decoded_endpoints"] == tuple(exact_history)
        assert report["all_current_space_checks_pass"] and report["all_arrival_anchors_preserved"]
        assert all(s["budget"]["unrestricted_update_space_dimension"] == n*c for s in report["steps"])
        assert all(s["update_rank"] <= 1 for s in report["steps"])
        assert report["final_rank"] <= min(n, c, 4)
        assert report["final_difference"] == xp.sub(exact_history[-1], exact_history[0])
        seeded.append({"case": case, "format": fmt, "H": H, "history": report})
        checks += 6
    return {"checks": checks, "exhaustive_stored_history_cases": cases,
            "exhaustive_family": "all triples of one-row two-coordinate endpoints in {-1,0,1}, both formats",
            "family_digest": digest.hexdigest(), "seeded_fixed_space_cases": 72,
            "seed": SEED, "seeded_cases": seeded}


def response_cases():
    checks, queries, budgets, feasible = 0, 0, 0, 0
    digest = hashlib.sha256()
    for h in product((Q(0), Q(1)), repeat=2):
        H = xp.matrix(tuple((v,) for v in h))
        for entries in product((Q(0), Q(1)), repeat=4):
            X = xp.matrix((entries[:2], entries[2:]))
            budget = ch.algebra_budget(H, 1, X)
            vectors = [h, (entries[0], entries[2]), (entries[1], entries[3])]
            active = [v for v in vectors if any(v)]
            combined_rank = 0 if not active else (2 if any(a[0]*b[1]-a[1]*b[0] != 0 for a in active for b in active) else 1)
            s = combined_rank-int(any(h))
            assert budget["unrestricted_response_image_dimension"] == s
            assert budget["target_silent_update_space_dimension"] == 2-int(any(h))-s
            assert budget["global_provenance_verified"] is False
            checks += 3; budgets += 1
            for row in product((Q(-1), Q(0), Q(1)), repeat=2):
                R = xp.matrix((row,))
                expected = _small_consistent(((h[0], h[1], Q(0)),
                                             (entries[0], entries[2], row[0]),
                                             (entries[1], entries[3], row[1])))
                for cap in (None, 0, 1):
                    report = ch.response_feasibility(H, X, R, cap)
                    wanted = expected and (cap != 0 or not any(row))
                    assert report["feasible"] == wanted
                    if wanted:
                        a, b = report["solution"].rows[0]
                        assert a*h[0]+b*h[1] == 0
                        assert tuple(a*entries[j]+b*entries[2+j] for j in range(2)) == row
                        assert xp.rank(report["solution"]) == int(any(row))
                        checks += 3; feasible += 1
                    digest.update(repr((h, entries, row, cap, wanted)).encode())
                    queries += 1; checks += 1
    e1, e2, both = (xp.matrix(v) for v in (((1,), (0,)), ((0,), (1,)), ((1,), (1,))))
    anchor_records = []
    compatible = 0
    for y1, y2, y3 in product((-1, 0, 1), repeat=3):
        tasks = tuple((H, xp.matrix(((y,),))) for H, y in zip((e1, e2, both), (y1, y2, y3)))
        report = ch.joint_task_feasibility(tasks)
        assert report["compatible"] == (y3 == y1+y2)
        for i, j in ((0, 1), (0, 2), (1, 2)):
            assert ch.joint_task_feasibility((tasks[i], tasks[j]))["compatible"]
            checks += 1
        if report["compatible"]:
            assert report["particular_solution"].rows == ((Q(y1), Q(y2)),)
            assert report["solution_affine_dimension"] == 0
            checks += 2; compatible += 1
        else:
            witness = report["impossibility_witness"]
            assert _row_zero(witness["H_alpha"]) and not _row_zero(witness["Y_alpha"])
            checks += 1
        anchor_records.append({"labels": (y1, y2, y3), "report": report})
        checks += 1
    rankcap = ch.response_feasibility(xp.zeros(2, 0), xp.eye(2), xp.eye(2), 1)
    assert not rankcap["feasible"]
    checks += 1
    return {"checks": checks, "response_budget_cases": budgets, "prescribed_response_cap_queries": queries,
            "feasible_queries": feasible, "family_digest": digest.hexdigest(),
            "three_task_assignments": 27, "jointly_compatible_assignments": compatible,
            "pairwise_compatibility_checks": 81, "task_records": anchor_records,
            "rank_cap_impossibility": rankcap}


def named_histories():
    checks, records = 0, []
    e1, e2 = xp.matrix(((1,), (0,))), xp.matrix(((0,), (1,)))
    for fmt in ("BF16", "FP32"):
        hist = lambda rows: tuple(_words((row,), fmt) for row in rows)
        fixed = ch.analyze_history(hist(((0, 0), (0, 1), (0, 2), (0, -1))), fmt, (e1,), targets=e2)
        assert fixed["all_arrival_anchors_preserved"]
        assert [s["budget"]["unrestricted_update_space_dimension"] for s in fixed["steps"]] == [1, 1, 1]
        cancel = ch.analyze_history(hist(((0, 0), (1, 0), (0, 0))), fmt, (e1,))
        assert cancel["final_preserves_initial_space"] and not cancel["every_prefix_preserves_initial_space"]
        cumulative = ch.analyze_history(hist(((0, 0), (0, 1), (0, 1))), fmt, (e1, e2), mode="cumulative", targets=e2)
        assert [s["budget"]["unrestricted_update_space_dimension"] for s in cumulative["steps"]] == [1, 0]
        assert cumulative["all_arrival_anchors_preserved"]
        assert not cumulative["steps"][1]["prefix_preserves_seen_union_relative_W0"]
        admission = ch.task_anchor_check(hist(((0, 1),))[0], fmt, e2, xp.zeros(1, 1))
        assert not admission["anchor_satisfied"]
        moving = ch.analyze_history(hist(((0, 0), (0, 1), (1, 1))), fmt, (e1, e2), mode="moving")
        assert moving["all_current_space_checks_pass"] and not moving["all_arrival_anchors_preserved"]
        recovered = ch.analyze_history(hist(((0, 0), (0, 1), (0, 1), (1, 1))), fmt,
                                      (e1, xp.eye(2), e2), mode="moving")
        assert [s["budget"]["unrestricted_update_space_dimension"] for s in recovered["steps"]] == [1, 0, 1]
        assert recovered["all_current_space_checks_pass"]
        H3 = xp.matrix(((1,), (0,), (0,)))
        rank_history = tuple(_words(m, fmt) for m in (
            ((0, 0, 0),)*3, ((0, 0, 0), (0, 1, 0), (0, 0, 0)), ((0, 0, 0), (0, 1, 0), (0, 0, 1))))
        ranks = ch.analyze_history(rank_history, fmt, (H3,), rank_cap=1)
        assert [s["update_rank"] for s in ranks["steps"]] == [1, 1]
        assert ranks["final_rank"] == 2 and ranks["fixed_space_cap_bound"] == 2
        sample = ch.algebra_budget(e1, 2)
        registered = ch.registered_budget("shared_axis_v1", fmt)
        assert sample["unrestricted_update_space_dimension"] == 2 and not sample["global_provenance_verified"]
        assert registered["unrestricted_update_space_dimension"] == 0 and registered["global_provenance_verified"]
        records.append({"format": fmt, "fixed_reuse": fixed, "final_cancellation_not_prefix_safety": cancel,
                        "cumulative_exhaustion": cumulative, "new_anchor_admission_mismatch": admission,
                        "moving_history_damage": moving, "moving_capacity_recovery": recovered,
                        "rank_one_steps_sum_rank_two": ranks, "sample_budget": sample, "registered_global_budget": registered})
        checks += 14
    return {"checks": checks, "records": records}


def _members(family, key):
    return {tuple(tuple(row) for row in r["endpoint_words"]) for r in family["records"] if r[key]}


def finite_cases():
    checks, families, boundaries = 0, [], []
    for fmt in ("BF16", "FP32"):
        fp = get_fp(); enc = lambda v: fp.encode_constant(v, fmt)
        old = ((enc(1), 0), (0, enc(1)))
        strong = ((0, enc(1)), (enc(2), enc(-1)))
        integers = tuple(enc(v) for v in (-1, 0, 1, 2))
        tiny = (0, 1, enc(1))
        before = ch.enumerate_endpoint_family("duplicate_feedback_v1", fmt, old, integers)
        after = ch.enumerate_endpoint_family("duplicate_feedback_v1", fmt, strong, integers)
        assert before["absolute_family_sha256"] == after["absolute_family_sha256"]
        assert _members(before, "ALG") == _members(after, "ALG")
        assert _members(before, "BIT") == _members(after, "BIT")
        assert before["groups"]["ALG"]["endpoints"] == after["groups"]["BIT"]["endpoints"] == 16
        images = lambda f, key: {json.dumps(r["A_new_output_words"]) for r in f["records"] if r[key]}
        assert images(before, "ALG") == images(after, "ALG") and images(before, "BIT") == images(after, "BIT")
        duplicate = ch.enumerate_endpoint_family("duplicate_feedback_v1", fmt, old, tiny)
        split = ch.enumerate_endpoint_family("split_feedback_v1", fmt, old, tiny)
        raw_zero = ch.enumerate_endpoint_family("duplicate_feedback_v1", fmt, ((0, 0), (0, 0)), (0, enc(1)))
        axes = ch.enumerate_endpoint_family("shared_axis_v1", fmt, old, integers)
        assert duplicate["groups"]["ALG"]["endpoints"] == 4 and duplicate["groups"]["BIT"]["endpoints"] == 16
        assert duplicate["groups"]["BIT"]["effective_rank_histogram"]["2"] == 8
        assert split["groups"]["ALG"]["endpoints"] == 1 and split["groups"]["BIT"]["endpoints"] == 2
        assert raw_zero["groups"]["BIT"]["endpoints"] == 1 and raw_zero["groups"]["E_CERT"]["endpoints"] == 0
        assert axes["groups"]["ALG"]["endpoints"] == axes["groups"]["BIT"]["endpoints"] == 1
        named = (("fixed_class_before", before), ("fixed_class_after", after), ("tiny_duplicate", duplicate),
                 ("tiny_split", split), ("raw_BIT_not_E_CERT", raw_zero), ("global_shared_axes", axes))
        for name, family in named:
            for group in family["groups"].values():
                assert group["raw_A_response_image_count"] <= group["A_total_endpoints"] <= group["endpoints"]
                assert group["exact_A_response_image_count"] <= group["endpoints"]
                checks += 2
            family["case"] = name; families.append(family)
        checks += 10
        spec = fp.get_format(fmt)
        maxword = ((spec.exponent_mask-1) << spec.fraction_bits) | ((1 << spec.fraction_bits)-1)
        M = fp.decode_word(maxword, fmt)
        saturated = ((maxword, maxword), (maxword, maxword))
        H = xp.matrix(((1,), (1,)))
        budget = ch.algebra_budget(H, 2)
        probe = ch.cd.dense_words(saturated, (enc(Q(1, 2)), enc(Q(1, 2))), fmt)
        assert probe == (maxword, maxword)
        neighbor = ((maxword-1, maxword), (maxword, maxword))
        residual = xp.matmul(xp.sub(ch.decode_matrix(neighbor, fmt), ch.decode_matrix(saturated, fmt)), H)
        assert not _row_zero(residual) and budget["unrestricted_update_space_dimension"] == 2
        N = 2*(spec.exponent_mask)*((1 << spec.fraction_bits))-1
        eta = fp.decode_word(1, fmt)
        stall = ch.quantize_proposal(((enc(1),),), xp.matrix(((eta,),)), fmt)
        assert stall["quantization_stall"] and stall["new_words"] == ((enc(1),),)
        alternative = ch.quantize_proposal(((enc(1),),), xp.matrix(((1,),)), fmt)
        assert not alternative["stored_noop"] and alternative["new_words"] == ((enc(2),),)
        commit = ch.quantize_proposal(((enc(1 << spec.p), 0),), xp.matrix(((1, -1),)), fmt)
        assert commit["effective_delta"].rows == ((Q(0), Q(-1)),)
        thirds = fp.encode_constant(Q(1, 3), fmt)
        s = fp.decode_word(thirds, fmt)
        Qwords = _words(tuple(tuple(2*s if i == j else -s for j in range(3)) for i in range(3)), fmt)
        zero3 = ((0, 0, 0),)*3
        witness = ch.cd.classify_endpoint("thirds_two_inputs_v1", fmt, zero3, Qwords, ((enc(1), 0, 0),))
        assert witness["ALG"] and not witness["BIT"]
        assert ch._protected_signature("thirds_two_inputs_v1", fmt, zero3) != ch._protected_signature("thirds_two_inputs_v1", fmt, Qwords)
        boundaries.append({"format": fmt, "same_absolute_class": {"family_sha256": before["absolute_family_sha256"],
                           "ALG_members_unchanged": True, "BIT_members_unchanged": True, "absolute_A_images_unchanged": True},
                           "saturation": {"old_words": saturated, "finite_old_probe_words": probe, "M": M,
                           "budget": budget, "neighbor_residual": residual, "whole_format_N": N,
                           "saturated_ALG_count_proved": 1, "zero_anchor_ALG_count_proved": N*N,
                           "scope": "Different anchors, not reachable endpoints of one fixed-ALG safe chain; counts proved, not enumerated"},
                           "quantization_stall": stall, "available_large_storable_step": alternative,
                           "quantization_breaks_ideal_constraint": commit, "thirds_ALG_not_BIT": witness})
        checks += 7
    return {"checks": checks, "family_count": len(families),
            "enumerated_candidates": sum(f["enumerated_candidates"] for f in families),
            "families": families, "boundaries": boundaries,
            "scope": "Complete explicit palettes; whole-format extremal counts remain handwritten proofs"}


def refusal_cases():
    H = xp.matrix(((1,), (0,)))
    W = ((0, 0),)
    actions = [
        ("empty_history", lambda: ch.analyze_history((), "BF16", (H,))),
        ("unknown_mode", lambda: ch.analyze_history((W,), "BF16", (H,), mode="samples_are_global")),
        ("schedule_length", lambda: ch.analyze_history((W, W), "BF16", (), mode="moving")),
        ("negative_cap", lambda: ch.algebra_budget(H, 1, rank_cap=-1)),
        ("sample_registry", lambda: ch.registered_budget("sample_only", "BF16")),
        ("duplicate_palette", lambda: ch.enumerate_endpoint_family("duplicate_feedback_v1", "BF16", ((16256, 0), (0, 16256)), (0, 0))),
        ("negative_zero", lambda: ch.quantize_proposal(((32768,),), xp.zeros(1, 1), "BF16")),
        ("nonfinite_word", lambda: ch.quantize_proposal(((32640,),), xp.zeros(1, 1), "BF16")),
        ("inexact_increment", lambda: ch.quantize_proposal(((0,),), [[0.5]], "BF16")),
        ("oversized_family", lambda: ch.enumerate_endpoint_family("duplicate_feedback_v1", "BF16", ((16256, 0), (0, 16256)), (0, 16256), max_candidates=1)),
    ]
    records = []
    for name, action in actions:
        try: action()
        except ValueError as exc: records.append({"case": name, "type": type(exc).__name__, "reason": str(exc)})
        else: raise AssertionError("Expected refusal absent: "+name)
    return {"checks": len(records), "expected_refusals": len(records), "records": records}


def run_checks():
    start = time.perf_counter()
    sections = {"stored_histories": exact_cases(), "responses_and_anchors": response_cases(),
                "named_evolution": named_histories(), "finite_endpoint_capacity": finite_cases(),
                "refusals": refusal_cases()}
    return {"schema": "dmwk-p2-b4-capacity-v1", "status": "passed", "seed": SEED,
            "checks": sum(s["checks"] for s in sections.values()), "unexpected_failures": 0,
            "expected_refusals": sections["refusals"]["expected_refusals"], "sections": ch.record(sections),
            "environment": environment_metadata(), "elapsed_seconds": time.perf_counter()-start,
            "SMT_queries": 0, "proof_assistant_checked": False, "prior_stage_suites_rerun": False,
            "new_optimizer_training_runs": 0,
            "scope": "Exact/fixed finite capacity histories, not global application provenance or live authorization"}


def main():
    if not __debug__: raise SystemExit("Run verification without -O/-OO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"capacity_results.json")
    args = parser.parse_args()
    result = run_checks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("sections", "environment")}))


if __name__ == "__main__": main()

"""Finite B3 guard, branch, ReLU and rounding-boundary checks.

The uniform guard result is the separate handwritten box/margin proof.
Finite complete families and seeded trials are recorded as such here.
"""
from __future__ import annotations

from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json
import random
import sys
import time

sys.dont_write_bytecode = True
import control_flow as cf

SEED = 20261114
ROOT = Path(__file__).resolve().parent


def run_checks():
    started = time.perf_counter()
    checks = 0
    refusals = []
    fp, cb = cf.get_fp(), cf.cb

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            raise AssertionError(label)

    def refuse(label, fn):
        try:
            fn()
        except cf.MarginRefused as exc:
            refusals.append({"label": label, "reason": str(exc)})
            check(True, label)
        else:
            check(False, "Expected refusal did not occur: " + label)

    rng = random.Random(SEED)
    seeded = []
    for index in range(24):
        d = rng.randint(1, 3)
        a = tuple(Q(rng.randint(-2, 2), 8) for _ in range(d))
        ap = tuple(v+Q(rng.randint(-1, 1), 16) for v in a)
        b = Q(rng.choice((-4, 4)))
        bp = b+Q(rng.randint(-1, 1), 16)
        pairs = []
        for _ in range(5):
            x = tuple(rng.choice((Q(-1, 2), Q(0), Q(1, 2))) for _ in range(d))
            xp = tuple(v+rng.choice((Q(-1, 4), Q(0), Q(1, 4))) for v in x)
            pairs.append((x, xp))
        seeded.append((index, a, ap, b, bp, tuple(pairs)))

    formats = []
    for fmt in ("BF16", "FP32"):
        t0 = time.perf_counter()
        constants = cb.format_constants(fmt)
        eta, p = constants["eta"], constants["precision"]

        def enc(value):
            return fp.encode_constant(Q(value), fmt)

        def vec(values):
            return tuple(enc(x) for x in values)

        complete = []
        for sign in (1, -1):
            a, ap = vec((Q(1, 4), Q(-1, 4))), vec((Q(1, 4), Q(-1, 8)))
            b, bp = enc(2*sign), enc(Q(2*sign)+Q(1, 16))
            B, Bp, radius = (Q(1), Q(1)), (Q(5, 4), Q(5, 4)), Q(1, 4)
            cert = cf.certify_guard_margin(a, ap, b, bp, fmt, B, Bp, radius)
            pairs = tuple((vec(x), vec(tuple(v+e for v, e in zip(x, shift))))
                          for x in product((-1, 0, 1), repeat=2)
                          for shift in product((Q(-1, 4), Q(0), Q(1, 4)), repeat=2))
            diag = cf.diagnose_finite_pairs(a, ap, b, bp, pairs, fmt,
                                           old_box=B, new_box=Bp, input_radius=radius)
            check(diag["pair_count"] == 81, "Complete two-dimensional grid count")
            check(diag["all_declared_branches_equal"], "Complete family branch equality")
            check(cert["same_branch"] == (sign == 1), "Expected signed margin branch")
            check(not cert["authorizes_live_commit"] and not cert["global_trajectory_containment_verified"],
                  "Margin report cannot grant publication/global provenance")
            for pair in diag["pairs"]:
                check(abs(pair["actual_guard_change"]) <= cert["guard_change_bound"], "Uniform bound contains actual guard change")
                check(abs(pair["old_executed_guard"]) >= cert["margin"], "Certified old margin lower bound")
                check(pair["old_branch"] == pair["new_branch"] == cert["same_branch"], "Complete pair branch agrees with certificate")
            complete.append({"sign": sign, "family": "all 3^2 old grid points times all 3^2 offset grid points",
                             "certificate": cert, "diagnostics": diag})

        properties = []
        for index, aq, apq, bq, bpq, rational_pairs in seeded:
            a, ap, b, bp = vec(aq), vec(apq), enc(bq), enc(bpq)
            d = len(a)
            B, Bp, radius = (Q(1, 2),)*d, (Q(3, 4),)*d, Q(1, 4)
            cert = cf.certify_guard_margin(a, ap, b, bp, fmt, B, Bp, radius)
            pairs = tuple((vec(x), vec(xp)) for x, xp in rational_pairs)
            diag = cf.diagnose_finite_pairs(a, ap, b, bp, pairs, fmt,
                                           old_box=B, new_box=Bp, input_radius=radius)
            check(diag["pair_count"] == 5 and diag["all_declared_branches_equal"], "Seeded pair count/equality")
            for pair in diag["pairs"]:
                check(abs(pair["actual_guard_change"]) <= cert["guard_change_bound"], "Seeded two-domain bound")
                check(pair["old_branch"] == pair["new_branch"] == cert["same_branch"], "Seeded branch margin")
            properties.append({"case": index, "dimension": d, "certificate": cert, "diagnostics": diag})

        # Strict guard: zero is false. Both stored input and bias changes
        # of exactly eta can produce a unit branch-output jump.
        input_jump = cf.diagnose_finite_pairs((enc(1),), (enc(1),), 0, 0,
                                               (((0,), (1,)),), fmt)
        bias_jump = cf.diagnose_finite_pairs((0,), (0,), 0, 1,
                                              (((0,), (0,)),), fmt)
        equality_jump = cf.diagnose_finite_pairs((0,), (0,), 1, 0,
                                                  (((0,), (0,)),), fmt)
        for name, diag in (("tiny_input", input_jump), ("tiny_bias", bias_jump)):
            row = diag["pairs"][0]
            check(row["old_executed_guard"] == 0 and row["new_executed_guard"] == eta, name + " eta guard")
            check(row["old_branch_output"] == 0 and row["new_branch_output"] == 1, name + " unit output jump")
            check(row["rho_old"] == row["rho_new"] == 0, name + " jump is not a guard-rounding error")
        eq = equality_jump["pairs"][0]
        check(eq["old_executed_guard"] == eta and eq["new_executed_guard"] == 0 and
              eq["old_branch"] and not eq["new_branch"], "Strict-guard equality boundary flips")
        refuse(fmt + ": equality-to-change margin", lambda: cf.strict_margin(eta, eta))
        refuse(fmt + ": zero margin", lambda: cf.strict_margin(0, 0))
        refuse(fmt + ": old interval contains threshold", lambda: cf.certify_guard_margin(
            (enc(1),), (enc(1),), 0, 0, fmt, (eta,), (eta,), eta))

        # An omitted new-domain/radius premise is not allowed to pass a
        # finite diagnostic as if it had checked both actual inputs.
        refuse(fmt + ": new input outside new domain", lambda: cf.diagnose_finite_pairs(
            (enc(1),), (enc(1),), enc(4), enc(4), (((0,), (enc(2),)),), fmt,
            old_box=(Q(1),), new_box=(Q(1),), input_radius=Q(2)))
        refuse(fmt + ": old input outside old domain", lambda: cf.diagnose_finite_pairs(
            (enc(1),), (enc(1),), enc(4), enc(4), (((enc(2),), (0,)),), fmt,
            old_box=(Q(1),), new_box=(Q(2),), input_radius=Q(2)))
        refuse(fmt + ": input radius omitted by underestimate", lambda: cf.diagnose_finite_pairs(
            (enc(1),), (enc(1),), enc(4), enc(4), (((0,), (enc(1),)),), fmt,
            old_box=(Q(1),), new_box=(Q(1),), input_radius=Q(1, 2)))
        refuse(fmt + ": only old domain supplied", lambda: cf.diagnose_finite_pairs(
            (enc(1),), (enc(1),), enc(4), enc(4), (((0,), (0,)),), fmt,
            old_box=(Q(1),)))
        for changed in ("pairwise", "fma", "fused_guard"):
            refuse(fmt + ": uncertified " + changed, lambda changed=changed: cf.certify_guard_margin(
                (enc(1),), (enc(1),), enc(4), enc(4), fmt,
                (Q(1),), (Q(1),), Q(0), policy=changed))
        refuse(fmt + ": negative radius", lambda: cf.certify_guard_margin(
            (enc(1),), (enc(1),), enc(4), enc(4), fmt,
            (Q(1),), (Q(1),), Q(-1)))
        refuse(fmt + ": approximate host bound", lambda: cf.certify_guard_margin(
            (enc(1),), (enc(1),), enc(4), enc(4), fmt,
            (1.0,), (Q(1),), Q(0)))
        nonfinite = fp.get_format(fmt).exponent_mask << fp.get_format(fmt).fraction_bits
        refuse(fmt + ": nonfinite endpoint", lambda: cf.certify_guard_margin(
            (enc(1),), (nonfinite,), enc(4), enc(4), fmt,
            (Q(1),), (Q(1),), Q(0)))
        refuse(fmt + ": unproved overflow envelope", lambda: cf.certify_guard_margin(
            (constants["maximum_word"],), (constants["maximum_word"],), 0, 0, fmt,
            (Q(2),), (Q(2),), Q(0)))

        # Exact ReLU is coordinatewise, not equivariant under R90.
        R = (vec((0, -1)), vec((1, 0)))
        x = vec((1, -1))
        rx = cb.trace_affine(R, x, fmt)
        relu_rx = cf.relu_words(rx["output_words"], fmt)
        relu_x = cf.relu_words(x, fmt)
        r_relu_x = cb.trace_affine(R, relu_x, fmt)
        left, right = cb.decode_vector(relu_rx, fmt), r_relu_x["decoded_output"]
        check(left == (Q(1), Q(1)) and right == (Q(0), Q(1)), "ReLU/R90 concrete values")
        check(left != right and max(abs(a-b) for a, b in zip(left, right)) == 1,
              "ReLU/R90 discrepancy")
        rotation = {"R_words": R, "input_words": x, "relu_Rx_words": relu_rx,
                    "R_relu_x_words": r_relu_x["output_words"],
                    "relu_Rx": left, "R_relu_x": right, "difference_linf": Q(1),
                    "arithmetic_counts": {key: rx["arithmetic_counts"][key]+r_relu_x["arithmetic_counts"][key]
                                          for key in rx["arithmetic_counts"]},
                    "scope": "one exact R90 counterexample; no general rotation equivariance"}

        half = cf.diagnose_finite_pairs((enc(Q(1, 2)),), (enc(Q(1, 2)),), 0, 0,
                                          (((1,), (enc(2*eta),)),), fmt)
        half_pair = half["pairs"][0]
        half_distance = half_pair["input_distance_linf"]
        half_jump = abs(half_pair["actual_guard_change"])
        check(half_pair["old_output_word"] == 0 and half_pair["new_output_word"] == 1,
              "Half eta tie/one eta output")
        check(half_distance == eta and half_jump == eta, "Half-map pair sizes")
        check(half_jump/half_distance == 1 and half_jump > Q(1, 2)*half_distance,
              "Rounded half-map violates exact Lipschitz constant")

        small = Q(1, 1 << p)
        epsilon = Q(1, 1 << (2*p-1))
        affine = cf.diagnose_finite_pairs((enc(1),), (enc(1),), enc(1), enc(1),
                                            (((enc(small),), (enc(small+epsilon),)),), fmt)
        pair = affine["pairs"][0]
        jump = pair["actual_guard_change"]
        check(pair["old_executed_guard"] == 1 and pair["new_executed_guard"] == 1+2*small,
              "One-plus near-tie outputs")
        check(pair["old_signed_error"] == -small and pair["new_signed_error"] == small-epsilon,
              "Both exact signed execution errors")
        full = epsilon+pair["rho_old"]+pair["rho_new"]
        without_old, without_new = epsilon+pair["rho_new"], epsilon+pair["rho_old"]
        check(full == jump == 2*small, "Both-error bound is tight in example")
        check(without_old < jump and without_new < jump, "Omitting either execution error fails")
        check(jump/epsilon == 1 << p, "Rounded one-plus ratio")

        formats.append({"format": fmt, "precision": p, "eta": eta,
                        "complete_margin_families": complete,
                        "complete_margin_pair_executions": 162,
                        "seeded_guard_cases": properties, "seeded_guard_case_count": len(properties),
                        "seeded_guard_pair_executions": 5*len(properties),
                        "branch_jumps": {"tiny_input": input_jump, "tiny_bias": bias_jump,
                                         "equality_boundary": equality_jump},
                        "relu_rotation": rotation,
                        "rounded_half_map": {"exact_L": Q(1, 2), "observed_pair_ratio": Q(1), "diagnostics": half},
                        "both_rounding_errors": {"exact_L": Q(1), "observed_pair_ratio": Q(1 << p),
                                                 "full_bound": full, "bound_without_old_error": without_old,
                                                 "bound_without_new_error": without_new, "diagnostics": affine},
                        "elapsed_seconds": time.perf_counter()-t0})

    return cf.record({"status": "passed", "seed": SEED, "checks": checks,
                      "check_unit": "Explicit finite diagnostic and refusal assertions; not universal proof count",
                      "unexpected_failures": 0, "expected_refusals": len(refusals),
                      "refusals": refusals, "formats": formats,
                      "elapsed_seconds": time.perf_counter()-started,
                      "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                                        for name in ("control_flow.py", "verify_control.py")},
                      "backend": fp.backend_metadata(),
                      "scope": "Complete declared small pair families, seeded affine guards, and named boundary examples; analytic uniform guard proof is separate",
                      "global_reachability_or_program_proof": False,
                      "authorizes_live_commit": False, "prior_stage_suites_rerun": False,
                      "SMT_queries": 0, "proof_assistant_checked": False})


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run verification without -O/-OO")
    result = run_checks()
    output = ROOT / "control_results.json"
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"],
                      "expected_refusals": result["expected_refusals"], "output": str(output)}))

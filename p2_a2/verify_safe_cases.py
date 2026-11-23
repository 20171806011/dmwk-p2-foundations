"""Finite structural-update evidence, separate from the all-time T4 proof."""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
import itertools
import random
import time

from p1_runtime import get_fp
from safe_update import StructuralKernel, UpdateRejected, POLICY

SEED = 20261114


class Checks:
    def __init__(self):
        self.total = 0
        self.refusals = 0

    def __call__(self, condition, message):
        self.total += 1
        if not condition:
            raise AssertionError(message)

    def refuses(self, kernel, function, message):
        before = kernel.snapshot()
        self.total += 1
        try:
            function()
        except (UpdateRejected, ValueError, TypeError):
            self.refusals += 1
        else:
            raise AssertionError("Expected refusal: " + message)
        self(kernel.snapshot() == before, "Refusal changed live bank: " + message)


def _boundary_words(fmt_name):
    fp = get_fp(); fmt = fp.get_format(fmt_name)
    values = [0, fp.encode_constant(1, fmt_name), fp.encode_constant(2, fmt_name),
              fp.encode_constant(-2, fmt_name), 1, fmt.sign_mask | 1,
              fmt.fraction_mask, 1 << fmt.fraction_bits,
              fmt.max_finite_word, fmt.sign_mask | fmt.max_finite_word]
    return tuple(dict.fromkeys(values))


def _replace_theta(kernel, theta):
    old = kernel.weights
    return kernel.commit_words((old[0], (old[1][0], theta)),
                               expected_version=kernel.version,
                               format_name=kernel.format_name)


def run_checks():
    start = time.perf_counter(); fp = get_fp(); check = Checks()
    formats = []
    for fmt_name in ("BF16", "FP32"):
        fmt = fp.get_format(fmt_name); one = fp.encode_constant(1, fmt_name)
        words = _boundary_words(fmt_name); arithmetic = fp.Audit()
        local_cases = 0
        # Every local D state/input pair, at each listed theta boundary word.
        for theta, q, u in itertools.product(words, (0, 1), (0, 1)):
            kernel = StructuralKernel(fmt_name, q, theta)
            actual = kernel.d_tick(one if u else 0, audit=arithmetic)
            check(actual == (one if q ^ u else 0), "D local transition changed with theta")
            check(kernel.a_output(one, audit=arithmetic) == theta, "A unit response is stored theta")
            check(kernel.a_output(0, audit=arithmetic) == 0, "A zero response is canonical zero")
            local_cases += 1

        trace_cases = trace_ticks = trace_updates = 0
        # Exhaust every length-five Boolean input sequence and both initial states.
        for q0 in (0, 1):
            for inputs in itertools.product((0, 1), repeat=5):
                control = StructuralKernel(fmt_name, q0)
                treated = StructuralKernel(fmt_name, q0)
                expected = q0
                for t, u in enumerate(inputs):
                    prior_state = treated.state_word
                    theta = words[(t + sum(inputs) + q0) % len(words)]
                    receipt = _replace_theta(treated, theta)
                    check(treated.state_word == prior_state, "Weight transaction changed D state")
                    check(receipt[1] != receipt[2] or receipt[1][1][1] == theta,
                          "Receipt records the actual stored candidate")
                    expected ^= u
                    a = control.d_tick(one if u else 0, audit=arithmetic)
                    b = treated.d_tick(one if u else 0, audit=arithmetic)
                    check(a == b == (one if expected else 0), "Feedback trace mismatch")
                    check(treated.a_output(one, audit=arithmetic) == theta, "Committed A response")
                    trace_ticks += 1; trace_updates += 1
                trace_cases += 1

        # One longer feedback/commit schedule, with an independent integer oracle.
        rng = random.Random(SEED)
        control = StructuralKernel(fmt_name, 1); treated = StructuralKernel(fmt_name, 1)
        expected = 1; long_updates = 0
        for tick in range(256):
            if tick % 3 == 0:
                theta = words[rng.randrange(len(words))]
                _replace_theta(treated, theta); long_updates += 1
                check(treated.a_output(one, audit=arithmetic) == theta, "Long-run A observation")
            u = rng.randrange(2); expected ^= u
            a = control.d_tick(one if u else 0, audit=arithmetic)
            b = treated.d_tick(one if u else 0, audit=arithmetic)
            check(a == b == (one if expected else 0), "Long protected feedback mismatch")

        # A nonzero, exactly stored update has a concrete changed learning output.
        learner = StructuralKernel(fmt_name, 0)
        old_snapshot = learner.snapshot(); old_output = learner.a_output(one)
        receipt = learner.commit_theta_ideal(2, expected_version=0)
        new_output = learner.a_output(one)
        check(old_output == one and new_output == fp.encode_constant(2, fmt_name), "Nontrivial learning witness")
        check(receipt[3] == (1, 1), "Effective stored update is exactly one")
        check(old_snapshot[5] == learner.state_word, "Learning changed protected state")
        zero_before = learner.a_output(0)
        learner.commit_theta_ideal(-2, expected_version=learner.version)
        check(learner.a_output(0) == zero_before == 0, "Safe update may be useless on target a=0")
        # A nonzero ideal change can quantize away even in the safe mask.
        quantized = StructuralKernel(fmt_name)
        ideal = Fraction(1) + Fraction(1, 1 << (fmt.p + 2))
        rounded_receipt = quantized.commit_theta_ideal(ideal, expected_version=0)
        check(rounded_receipt[3] == (0, 1) and quantized.a_output(one) == one,
              "Ideal movement can have zero effective stored movement")

        # Refusals are transactional, including callback-bearing instrumentation.
        victim = StructuralKernel(fmt_name, 1); initial = victim.weights
        infinity = fmt.exponent_mask << fmt.fraction_bits
        requests = [
            ("protected00", ((0, 0), initial[1])),
            ("protected01", ((initial[0][0], one), initial[1])),
            ("protected10", (initial[0], (one, one))),
            ("negative_zero", (initial[0], (0, fmt.sign_mask))),
            ("infinity", (initial[0], (0, infinity))),
            ("nan", (initial[0], (0, infinity | 1))),
            ("out_of_range", (initial[0], (0, 1 << fmt.total_bits))),
            ("negative_raw", (initial[0], (0, -1))),
            ("float_word", (initial[0], (0, 1.0))),
            ("bool_word", (initial[0], (0, True))),
            ("outer_list", list(initial)),
            ("row_list", (list(initial[0]), initial[1])),
            ("wrong_shape", (initial[0],)),
        ]
        format_refusals_start = check.refusals
        for label, candidate in requests:
            check.refuses(victim, lambda c=candidate: victim.commit_words(c,
                expected_version=victim.version, format_name=fmt_name), label)
        for label, kwargs in [
            ("stale", {"expected_version": victim.version + 1}),
            ("bool_version", {"expected_version": True}),
            ("other_format", {"format_name": "FP32" if fmt_name == "BF16" else "BF16"}),
            ("FMA", {"policy": "fma"}),
            ("reduction_tree", {"policy": "pairwise"}),
            ("algebra_only_claim", {"route": "exact_projection"}),
            ("sample_only_claim", {"route": "sample_checked"}),
            ("SVD_only_claim", {"route": "svd"}),
        ]:
            args = {"expected_version": victim.version, "format_name": fmt_name}; args.update(kwargs)
            check.refuses(victim, lambda a=args: victim.commit_words(initial, **a), label)
        check.refuses(victim, lambda: victim.__init__(fmt_name, 0), "public reinitialization")
        check.refuses(victim, lambda: victim.commit_theta_ideal(float("nan"), expected_version=victim.version),
                      "host floating candidate")
        check.refuses(victim, lambda: victim.commit_theta_ideal(1 << 1024, expected_version=victim.version),
                      "quantized overflow")
        for invalid in (fmt.sign_mask, 2, True, 0.0):
            check.refuses(victim, lambda x=invalid: victim.d_tick(x), "illegal D input")
            check.refuses(victim, lambda x=invalid: victim.a_output(x), "illegal A input")
        check.refuses(victim, lambda: victim.d_tick(one, policy="fused"), "D changed execution graph")
        check.refuses(victim, lambda: victim.a_output(one, policy="reassociated"), "A changed execution graph")
        callbacks = []
        class ReentrantList(list):
            def append(self, item):
                callbacks.append("append"); victim.d_tick(one)
        class ReentrantInt(int):
            def __add__(self, other):
                callbacks.append("counter"); victim.d_tick(one)
                return int(self) + other
        bad_audit = fp.Audit(); bad_audit.events = ReentrantList()
        check.refuses(victim, lambda: victim.d_tick(one, audit=bad_audit), "list callback audit")
        bad_counter = fp.Audit(); bad_counter.native_multiply = ReentrantInt(0)
        check.refuses(victim, lambda: victim.a_output(one, audit=bad_counter), "counter callback audit")
        check.refuses(victim, lambda: victim.d_tick(one, audit=object()), "foreign audit object")
        check(callbacks == [], "Rejected instrumentation executed a callback")
        held_snapshot = victim.snapshot()
        try:
            held_snapshot[3][1][1] = 0
        except TypeError:
            pass
        else:
            raise AssertionError("Snapshot unexpectedly mutable")
        check(victim.snapshot() == held_snapshot, "Snapshot alias mutation")

        # Complete BF16 storage-domain check; bounded seeded FP32 word selection.
        word_start = time.perf_counter()
        validator = StructuralKernel(fmt_name)
        selected = range(1 << 16) if fmt_name == "BF16" else tuple(
            dict.fromkeys(words + (fmt.sign_mask, infinity, infinity | 1,
                                  fmt.sign_mask | infinity) +
                          tuple(random.Random(SEED + i).getrandbits(32) for i in range(512))))
        accepted = rejected = 0
        for raw in selected:
            expected_accept = (((raw >> fmt.fraction_bits) & fmt.exponent_mask) != fmt.exponent_mask
                               and raw != fmt.sign_mask)
            before = validator.snapshot()
            try:
                _replace_theta(validator, raw)
            except UpdateRejected:
                check(not expected_accept, "Admitted finite theta was rejected")
                check(validator.snapshot() == before, "Refused storage word changed state")
                rejected += 1
            else:
                check(expected_accept, "Special value or negative zero was accepted")
                check(validator.state_word == before[5] and validator.ticks == before[6],
                      "Storage-domain check changed protected fields")
                accepted += 1
        if fmt_name == "BF16":
            check(accepted == 65279 and rejected == 257, "Complete BF16 domain count")
        if fmt_name == "FP32":
            check(arithmetic.native_oracle_checks == arithmetic.native_add + arithmetic.native_multiply,
                  "Every native operation is checked against rational RNE")
            check(all(e["result_dtype"] == "float32" for e in arithmetic.events), "Native dtype promotion")
        formats.append({
            "format": fmt_name,
            "mask": ((0, 0), (0, 1)),
            "policy": POLICY,
            "local_state_input_theta_cases": local_cases,
            "theta_boundary_words": [hex(x) for x in words],
            "exhaustive_length_five_input_traces": trace_cases,
            "trace_ticks": trace_ticks,
            "trace_updates": trace_updates,
            "seeded_long_feedback_ticks": 256,
            "seeded_long_updates": long_updates,
            "nonzero_learning_witness": {"old_theta": "1", "new_theta": "2",
                "effective_change": "1", "A_input": "1", "old_output": "1", "new_output": "2"},
            "safe_but_unresponsive_target": {"A_input": "0", "output_before_after": "0"},
            "nonzero_ideal_change_quantized_away": {"ideal_theta": str(ideal), "stored_theta": "1",
                "effective_change": "0"},
            "explicit_refusals_with_unchanged_snapshot": check.refusals - format_refusals_start,
            "storage_word_validation": {"scope": "all 65536 BF16 words" if fmt_name == "BF16"
                else "boundary words plus 512 seeded FP32 word draws (deduplicated)",
                "words_checked": accepted + rejected, "accepted": accepted, "rejected": rejected,
                "seconds": time.perf_counter() - word_start},
            "arithmetic_counts": {k: v for k, v in asdict(arithmetic).items() if k != "events"},
            "native_event_count": len(arithmetic.events),
            "arithmetic_scope": "software BF16 RNE" if fmt_name == "BF16"
                else "local native NumPy float32 scalar operations with exact-rational bit audit",
            "structural_free_coordinates": 1,
            "unrestricted_algebraic_update_dimension_for_V_span_e1": 2,
        })
    return {"status": "passed", "checks": check.total, "seed": SEED,
            "explicit_transaction_refusals": check.refusals,
            "seconds": time.perf_counter() - start, "formats": formats,
            "theorem_scope": "The all-finite-time conclusion is the separate T4 induction under the fixed sparse graph/trusted API contract, not an inference from these finite runs.",
            "limitations": ["No arbitrary dense GEMM/FMA/reassociation substitution",
                            "No arbitrary private-memory/module mutation or concurrent API calls",
                            "No GPU/native BF16/full proof-assistant certification",
                            "Only a strict one-dimensional structural subset of the two-dimensional algebraic update space"]}


if __name__ == "__main__":
    import json
    from pathlib import Path
    result = run_checks()
    target = Path(__file__).with_name("safe_verification_results.json")
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks": result["checks"],
                      "seconds": result["seconds"], "output": str(target)}))

"""Finite production checks for the A3 registered-domain certificate route."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import time

from a3_runtime import get_fp
from certificate_kernel import (CertificateKernel, CertificateRejected, POLICY,
    SCHEDULE, initial_weights, model_descriptor, make_certificate, check_certificate)

SEED = 20261114


class Checks:
    def __init__(self):
        self.count = 0
        self.refusals = 0

    def check(self, condition, description):
        self.count += 1
        if not condition:
            raise AssertionError(description)

    def rejected(self, fn, kernel=None):
        before = None if kernel is None else kernel.snapshot()
        try:
            fn()
        except CertificateRejected:
            self.refusals += 1
            self.check(kernel is None or kernel.snapshot() == before,
                       "A refused operation changed the live snapshot")
            return
        raise AssertionError("Expected a certificate refusal")


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def rehashed(data):
    value = deepcopy(data)
    value["payload_sha256"] = hashlib.sha256(canonical(value["payload"]).encode("ascii")).hexdigest()
    return canonical(value)


def run_checks():
    started = time.perf_counter()
    tracker = Checks()
    fp = get_fp()
    rng = random.Random(SEED)
    formats = []
    for fmt in ("BF16", "FP32"):
        section_start = time.perf_counter()
        enc = lambda x: fp.encode_constant(x, fmt)
        one = enc(1)
        identity = initial_weights("duplicate_feedback_v1", fmt)
        strong = ((0, one), (enc(2), enc(-1)))
        k = CertificateKernel(fmt)
        before_prepare = k.snapshot()
        text = k.prepare(strong)
        tracker.check(k.snapshot() == before_prepare, "Preparation mutated live state")
        evidence = check_certificate(text, k.model_id, fmt, k.weights, k.version)
        tracker.check(evidence["payload"]["proof"]["exact_effective_delta_annihilates_registered_span"],
                      "Main dense witness must satisfy exact annihilation too")
        before_a = k.a_output((one, 0))
        receipt = k.commit(text)
        after_a = k.a_output((one, 0))
        tracker.check(before_a == (one, 0) and after_a == (0, enc(2)), "Nonzero A response missing")
        tracker.check(receipt[1] != receipt[2] and k.state_word == 0 and k.ticks == 0,
                      "Valid commit must change endpoint but preserve protected state")
        tracker.rejected(lambda: k.commit(text), k)

        # Exhaust every bounded integer endpoint, not just projected samples.
        exhaustive = []
        for model in ("duplicate_feedback_v1", "split_feedback_v1"):
            accepted = rejected = 0
            for values in product(range(-2, 3), repeat=4):
                matrix = ((enc(values[0]), enc(values[1])), (enc(values[2]), enc(values[3])))
                # Exact small-integer criterion is a separate finite oracle.
                expected = values[0]+values[1] == 1 and values[2]+values[3] == 1
                if model == "split_feedback_v1":
                    expected = expected and values[0] == 1 and values[2] == 0
                try:
                    cert = make_certificate(model, fmt, identity, matrix)
                    accepted += 1
                    tracker.check(expected, "Accepted endpoint violates finite integer oracle")
                    tracker.check(json.loads(cert)["payload"]["proof"]["exact_effective_delta_annihilates_registered_span"],
                                  "Small-integer accepted endpoint had an unexpected algebraic residual")
                except CertificateRejected:
                    rejected += 1
                    tracker.check(not expected, "Refused a complete-domain equal small-integer endpoint")
            exhaustive.append({"model": model, "alphabet": [-2,-1,0,1,2], "matrices": 625,
                               "accepted": accepted, "refused": rejected,
                               "oracle": "Integer row-sum and (for split) first-column identities"})

        # Every q0 and all 32 length-five histories; two nontrivial banks alternate.
        traces = ticks = commits = 0
        for initial in (0, 1):
            for inputs in product((0, 1), repeat=5):
                base = CertificateKernel(fmt, initial_bit=initial)
                changed = CertificateKernel(fmt, initial_bit=initial)
                previous = initial
                for index, u in enumerate(inputs):
                    candidate = strong if index % 2 == 0 else identity
                    old_snapshot = changed.snapshot()
                    cert = changed.prepare(candidate)
                    changed.commit(cert)
                    tracker.check(changed.state_word == old_snapshot[6] and changed.ticks == old_snapshot[7],
                                  "Commit changed state or tick metadata")
                    observed = changed.d_tick(one if u else 0)
                    reference = base.d_tick(one if u else 0)
                    expected_q = previous ^ u
                    tracker.check(observed == reference, "Protected full call outputs/next state differ")
                    tracker.check(changed.state_word == (one if expected_q else 0), "Boolean recurrence mismatch")
                    previous = expected_q
                    ticks += 1
                    commits += 1
                traces += 1

        # Seeded varied safe endpoints in an actual feedback trajectory.
        property_cases = 48
        seeded = CertificateKernel(fmt, initial_bit=1)
        expected_state = 1
        for _ in range(property_cases):
            a, b = rng.randrange(-16,17), rng.randrange(-16,17)
            candidate = ((enc(a), enc(1-a)), (enc(b), enc(1-b)))
            seeded.commit(seeded.prepare(candidate))
            u = rng.randrange(2)
            observation = seeded.d_tick(one if u else 0)
            expected_state ^= u
            tracker.check(observation[2] == (one if expected_state else 0), "Seeded feedback mismatch")

        # A full-domain certificate remains valid across ticks if the weight
        # version is unchanged; it is not a certificate for only the old q.
        moving = CertificateKernel(fmt)
        pending = moving.prepare(strong)
        moving.d_tick(one)
        live_state = moving.state_word
        moving.commit(pending)
        tracker.check(moving.state_word == live_state and moving.ticks == 1,
                      "Global-domain certificate mishandled an intervening legal tick")

        # Finite bit equality need not imply exact annihilation of the span.
        eta_candidate = ((one, 1), (0, one))
        eta_kernel = CertificateKernel(fmt)
        eta_text = eta_kernel.prepare(eta_candidate)
        eta_data = json.loads(eta_text)
        tracker.check(not eta_data["payload"]["proof"]["exact_effective_delta_annihilates_registered_span"],
                      "Subnormal observational example incorrectly called algebraically null")
        eta_kernel.commit(eta_text)
        tracker.check(eta_kernel.a_output((0, one)) == (1, one), "Subnormal A response missing")

        # Rehashed attacks test truth checking, not just checksum mismatch.
        victim = CertificateKernel(fmt)
        pristine = json.loads(victim.prepare(strong))
        attacks = []
        def mutate(name, operation):
            changed = deepcopy(pristine)
            operation(changed["payload"])
            attacks.append((name, rehashed(changed)))
        mutate("algebra_only_claim", lambda p: p.__setitem__("claim", "exact_algebra"))
        mutate("pointwise_claim", lambda p: p.__setitem__("claim", "pointwise_bound"))
        mutate("stale_version", lambda p: p.__setitem__("expected_weight_version", 2))
        mutate("bool_version", lambda p: p.__setitem__("expected_weight_version", False))
        mutate("float_version", lambda p: p.__setitem__("expected_weight_version", 0.0))
        mutate("old_endpoint", lambda p: p["old_weights"][0].__setitem__(0, 0))
        mutate("new_unsafe_endpoint", lambda p: p["new_weights"][0].__setitem__(1, 0))
        mutate("false_effective_delta", lambda p: p["effective_delta"][0].__setitem__(0, [0,1]))
        mutate("wrong_model", lambda p: p.__setitem__("model_id", "split_feedback_v1"))
        mutate("wrong_format", lambda p: p.__setitem__("format", "FP32" if fmt=="BF16" else "BF16"))
        mutate("sample_label", lambda p: p["descriptor"].__setitem__("coverage", "samples_only"))
        mutate("missing_site", lambda p: p["descriptor"]["sites"].pop())
        mutate("missing_legal_activation", lambda p: p["descriptor"]["sites"][0]["activations"].pop())
        mutate("missing_initial_state", lambda p: p["descriptor"]["legal_initial_state_words"].pop())
        mutate("missing_input", lambda p: p["descriptor"]["legal_external_input_words"].pop())
        mutate("forged_invariant", lambda p: p["descriptor"].__setitem__("invariant_id", "caller_claim"))
        mutate("FMA_policy", lambda p: p["descriptor"].__setitem__("numerical_policy", "fma"))
        mutate("FTZ_policy", lambda p: p["descriptor"].__setitem__("numerical_policy", "flush-to-zero"))
        mutate("reordered_graph", lambda p: p["descriptor"]["graph"].__setitem__("matrix_evaluation", "descending columns"))
        mutate("fused_graph", lambda p: p["descriptor"]["graph"].__setitem__("arithmetic", "fused GEMM"))
        mutate("changed_schedule", lambda p: p["descriptor"].__setitem__("schedule", "in-place sequential state writes"))
        mutate("A_feedback", lambda p: p["descriptor"].__setitem__("A_to_D_feedback", True))
        mutate("fake_source", lambda p: p["implementation_sha256"].__setitem__("certificate_kernel.py", "0"*64))
        mutate("missing_case_evidence", lambda p: p["proof"]["call_cases"].pop())
        mutate("missing_transition_evidence", lambda p: p["proof"]["state_transition_cases"].pop())
        mutate("fake_result", lambda p: p["proof"]["call_cases"][0]["new_output_words"].__setitem__(0, one))
        mutate("extra_field", lambda p: p.__setitem__("trusted", True))
        for _, bad in attacks:
            tracker.rejected(lambda bad=bad: victim.commit(bad), victim)
        good_text = canonical(pristine)
        malformed = ["[]", "null", "{", good_text+" ", good_text.replace('"payload":', '"payload":{},"payload":',1),
                     good_text.replace('"expected_weight_version":0', '"expected_weight_version":NaN',1)]
        for bad in malformed:
            tracker.rejected(lambda bad=bad: victim.commit(bad), victim)
        wrong_hash = deepcopy(pristine); wrong_hash["payload_sha256"] = "0"*64
        tracker.rejected(lambda: victim.commit(canonical(wrong_hash)), victim)
        tracker.rejected(lambda: victim.commit({"pointwise_bound":0}), victim)

        callbacks = []
        class BadString(str):
            def __len__(self):
                callbacks.append("length")
                return super().__len__()
        class BadInt(int):
            def __int__(self):
                callbacks.append("int")
                return super().__int__()
        tracker.rejected(lambda: victim.commit(BadString(good_text)), victim)
        tracker.rejected(lambda: victim.prepare(((BadInt(one),0),(0,one))), victim)
        tracker.check(callbacks == [], "Caller callback was invoked")
        spec = fp.get_format(fmt)
        for word in (True, -1, 1 << spec.total_bits, spec.sign_mask,
                     spec.exponent_mask << spec.fraction_bits,
                     (spec.exponent_mask << spec.fraction_bits)|1):
            tracker.rejected(lambda word=word: victim.prepare(((word,0),(0,one))), victim)
        tracker.rejected(lambda: victim.prepare([[one,0],[0,one]]), victim)
        tracker.rejected(lambda: victim.d_tick(enc(2)), victim)
        tracker.rejected(lambda: victim.d_tick(one, policy="FMA"), victim)
        tracker.rejected(lambda: victim.d_tick(one, schedule="different"), victim)
        tracker.rejected(lambda: victim.a_output((one,one)), victim)
        tracker.rejected(lambda: victim.__init__(fmt), victim)
        tracker.rejected(lambda: CertificateKernel(fmt, initial_bit=2))
        tracker.rejected(lambda: make_certificate("sample_domain",fmt,identity,strong))
        tracker.rejected(lambda: check_certificate(good_text,"split_feedback_v1",fmt,identity))
        # Invalid original endpoint cannot assert state-invariant provenance.
        tracker.rejected(lambda: make_certificate("duplicate_feedback_v1",fmt,((0,0),(0,0)),((0,0),(0,0))))
        saved = victim.snapshot()
        victim.commit(good_text)
        tracker.check(saved[4] == 0 and saved[5] == identity and saved[6] == 0,
                      "Previously returned immutable snapshot changed")

        formats.append({"format":fmt,"exhaustive_endpoint_families":exhaustive,
            "stateful_trace_count":traces,"stateful_ticks":ticks,"stateful_commits":commits,
            "seeded_feedback_cases":property_cases,"rehashed_tampering_cases":len(attacks),
            "malformed_serialization_cases":len(malformed),"callback_invocations":callbacks,
            "nonzero_learning_witness":{"old_weights":identity,"new_weights":strong,
                "A_input":(one,0),"old_output":before_a,"new_output":after_a,
                "protected_exact_annihilation":True},
            "bitwise_without_algebra_witness":{"candidate":eta_candidate,
                "exact_annihilation":False,"A_input":(0,one),"A_output":(1,one),
                "scope":"Complete finite registered bit domain, not every real combination"},
            "certificate_proof_arithmetic_counts":evidence["payload"]["proof"]["arithmetic_counts"],
            "certificate_proof_count_scope":"One complete strong-witness issuance only; not total suite operations",
            "seconds":time.perf_counter()-section_start})
    return {"status":"passed","seed":SEED,"checks":tracker.count,
            "check_unit":"Explicit production assertions; exhaustive endpoint refusals counted separately",
            "explicit_refusals":tracker.refusals,"unexpected_failures":0,
            "formats":formats,"seconds":time.perf_counter()-started,
            "scope":"Finite executable checker tests. All-finite-time program theorem is a separate handwritten induction.",
            "SMT_queries":0,"prior_stage_suites_rerun":False}


if __name__ == "__main__":
    result = run_checks()
    path = Path(__file__).with_name("certificate_results.json")
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"checks":result["checks"],
                      "seconds":result["seconds"],"output":str(path)}))

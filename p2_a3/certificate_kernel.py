"""A3 complete registered-domain certificates and a stateful dense reference.

The trusted registry, not the caller, defines coverage. A certificate is a
reproducible data record; its checksum is not authority. Checkers recompute
every declared finite call and the state invariant before a commit.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from a3_runtime import get_fp


POLICY = "p2-a3-dense-bias-first-separate-rne-canonical-zero-v1"
SCHEDULE = "p2-a3-serialized-snapshot-state-then-input-synchronous-commit-v1"
CLAIM = "bitwise_complete_registered_domain_v1"


class CertificateRejected(ValueError):
    """The stated complete-domain executable contract could not be verified."""


def require(test, message):
    if not test:
        raise CertificateRejected(message)


def _policy():
    return "p2-a3-dense-bias-first-separate-rne-canonical-zero-v1"


def _schedule():
    return "p2-a3-serialized-snapshot-state-then-input-synchronous-commit-v1"


def _format(fmt):
    require(type(fmt) is str and fmt in ("BF16", "FP32"), "Unsupported format")
    return get_fp().get_format(fmt)


def _word(raw, fmt):
    spec = _format(fmt)
    require(type(raw) is int and 0 <= raw < (1 << spec.total_bits),
            "Raw words must be in-range built-in integers")
    require(((raw >> spec.fraction_bits) & spec.exponent_mask) != spec.exponent_mask,
            "Nonfinite words are not admitted")
    require(raw != spec.sign_mask, "Zero words must be canonical +0")
    get_fp().decode_word(raw, fmt)
    return raw


def _matrix(value, fmt, shape):
    rows, cols = shape
    require(type(value) is tuple and len(value) == rows, "Matrix row shape/type mismatch")
    require(all(type(row) is tuple and len(row) == cols for row in value),
            "Matrix column shape/type mismatch")
    return tuple(tuple(_word(x, fmt) for x in row) for row in value)


def _version(value):
    require(type(value) is int and 0 <= value < (1 << 63),
            "Version must be a nonnegative bounded built-in integer")
    return value


def _encoded(value, fmt):
    return get_fp().encode_constant(value, fmt)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode("ascii")).hexdigest()


def _pair(value):
    return [value.numerator, value.denominator]


def _implementation_hashes():
    fp = get_fp()
    try:
        return {"certificate_kernel.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "p1_execution.py": hashlib.sha256(Path(fp.__file__).read_bytes()).hexdigest()}
    except OSError as exc:
        raise CertificateRejected("Required implementation identity is unavailable: " + str(exc)) from None


def model_descriptor(model_id, fmt):
    """Fresh primitive descriptor from a fixed trusted registry.

    These are declared complete finite domains, not discovered sample sets.
    No caller-provided descriptor can extend or replace this registry.
    """
    _format(fmt)
    require(type(model_id) is str and model_id in (
        "duplicate_feedback_v1", "split_feedback_v1", "thirds_two_inputs_v1",
        "commit_rounding_v1", "shared_axis_v1"), "Unknown or uncertified model/domain")
    one = _encoded(1, fmt)
    stateful = model_id in ("duplicate_feedback_v1", "split_feedback_v1")
    if stateful:
        shape = [2, 2]
        sites = [{"id": "state", "activations": [[0, 0], [one, one]]},
                 {"id": "input", "activations": [[0, 0],
                    [one, one] if model_id == "duplicate_feedback_v1" else [one, 0]]}]
    elif model_id == "thirds_two_inputs_v1":
        shape = [3, 3]
        sites = [{"id": "all_declared_inputs", "activations": [[one]*3, [1]*3]}]
    elif model_id == "commit_rounding_v1":
        shape = [2, 2]
        sites = [{"id": "unit_pair", "activations": [[one, one]]}]
    else:
        shape = [2, 2]
        sites = [{"id": "axis_0", "activations": [[one, 0]]},
                 {"id": "axis_1", "activations": [[0, one]]}]
    return {
        "registry_schema": "dmwk-p2-a3-fixed-registry-v1",
        "model_id": model_id, "physical_matrix_id": "shared_W_0", "format": fmt,
        "shape": shape, "fixed_bias_words": [0]*shape[0], "sites": sites,
        "coverage": "all_declared_inputs_not_samples",
        "domain_id": model_id + ":complete-domain-v1",
        "invariant_id": model_id + (":canonical-bit-closed-v1" if stateful else ":explicit-finite-domain-v1"),
        "legal_initial_state_words": [0, one] if stateful else [],
        "legal_external_input_words": [0, one] if stateful else [],
        "input_history": "every finite Boolean input word sequence" if stateful else "stateless declared calls only",
        "graph": {"matrix_evaluation": "all rows, all columns, bias first, ascending columns",
                  "arithmetic": "separate multiply then add; no skipped zero terms",
                  "site_order": [s["id"] for s in sites],
                  "transition": "xor_first_outputs_same_old_snapshot" if stateful else "none",
                  "protected_observation": "full output words of every protected site and next D state"},
        "numerical_policy": _policy(), "schedule": _schedule(),
        "stateful": stateful,
        "A_domain": [[one, 0], [0, one], [0, 0]] if stateful else [],
        "A_to_D_feedback": False,
    }


def initial_weights(model_id, fmt):
    descriptor = model_descriptor(model_id, fmt)
    one = _encoded(1, fmt)
    if model_id == "thirds_two_inputs_v1":
        return ((0, 0, 0),)*3
    if model_id == "commit_rounding_v1":
        return ((_encoded(1 << _format(fmt).p, fmt), 0), (0, 0))
    require(descriptor["shape"] == [2, 2], "Unexpected registry shape")
    return ((one, 0), (0, one))


def _dense(weights, activation, fmt, audit):
    fp = get_fp()
    outputs = []
    for row in weights:
        accumulator = 0
        for weight, value in zip(row, activation):
            product = fp.mul_words(weight, value, fmt, audit)
            accumulator = fp.add_words(accumulator, product, fmt, audit)
        outputs.append(accumulator)
    return tuple(outputs)


def _xor(left, right, fmt, audit):
    fp = get_fp()
    product = fp.mul_words(left, right, fmt, audit)
    twice = fp.mul_words(_encoded(2, fmt), product, fmt, audit)
    negative = fp.mul_words(_encoded(-1, fmt), twice, fmt, audit)
    summed = fp.add_words(left, right, fmt, audit)
    return fp.add_words(summed, negative, fmt, audit)


def _audit_record(audit):
    return {name: getattr(audit, name) for name in (
        "native_multiply", "native_add", "software_multiply", "software_add",
        "exact_sums", "native_oracle_checks")}


def _delta(old, new, fmt):
    fp = get_fp()
    return tuple(tuple(fp.decode_word(b, fmt)-fp.decode_word(a, fmt)
                       for a, b in zip(ro, rn)) for ro, rn in zip(old, new))


def _proof(model_id, fmt, old, new, descriptor):
    """Recompute complete finite call equality and closure from trusted data."""
    fp = get_fp()
    audit = fp.Audit()  # Never accept caller instrumentation or callbacks.
    delta = _delta(old, new, fmt)
    records = []
    all_algebra_zero = True
    try:
        for site in descriptor["sites"]:
            for activation in site["activations"]:
                old_result = _dense(old, activation, fmt, audit)
                new_result = _dense(new, activation, fmt, audit)
                require(old_result == new_result,
                        "Complete-domain bitwise comparison failed at site " + site["id"])
                if descriptor["stateful"]:
                    # Every admitted bank in this concrete invariant must
                    # match the baseline full output, not just next q.
                    expected = tuple(activation)
                    require(old_result == expected and new_result == expected,
                            "Endpoint does not satisfy registered full-output invariant")
                decoded = tuple(fp.decode_word(x, fmt) for x in activation)
                residual = tuple(sum((a*b for a, b in zip(row, decoded)), Fraction(0))
                                 for row in delta)
                all_algebra_zero = all_algebra_zero and all(x == 0 for x in residual)
                records.append({"site": site["id"], "activation_words": list(activation),
                                "old_output_words": list(old_result), "new_output_words": list(new_result),
                                "exact_effective_delta_output": [_pair(x) for x in residual]})
        transitions = []
        if descriptor["stateful"]:
            one = _encoded(1, fmt)
            for q in (0, one):
                for u in (0, one):
                    hs = (q, q)
                    hi = (u, u) if model_id == "duplicate_feedback_v1" else (u, 0)
                    old_s = _dense(old, hs, fmt, audit)
                    old_i = _dense(old, hi, fmt, audit)
                    new_s = _dense(new, hs, fmt, audit)
                    new_i = _dense(new, hi, fmt, audit)
                    old_next = _xor(old_s[0], old_i[0], fmt, audit)
                    new_next = _xor(new_s[0], new_i[0], fmt, audit)
                    expected = one if (q == one) != (u == one) else 0
                    require(old_next == new_next == expected,
                            "Complete registered state/input closure check failed")
                    transitions.append({"old_state_word": q, "input_word": u,
                                        "old_next_word": old_next, "new_next_word": new_next})
    except fp.ExecutionError as exc:
        raise CertificateRejected("Declared arithmetic could not be verified: " + str(exc)) from None
    return {"method": "exhaustive_registered_raw_word_domain",
            "call_cases": records, "call_case_count": len(records),
            "state_transition_cases": transitions, "transition_case_count": len(transitions),
            "exact_effective_delta_annihilates_registered_span": all_algebra_zero,
            "algebraic_condition_required_for_this_bitwise_claim": False,
            "arithmetic_counts": _audit_record(audit)}


def make_certificate(model_id, fmt, old_words, new_words, version=0):
    """Issue reproducible finite-domain evidence; do not mutate a live kernel."""
    descriptor = model_descriptor(model_id, fmt)
    version = _version(version)
    old = _matrix(old_words, fmt, descriptor["shape"])
    new = _matrix(new_words, fmt, descriptor["shape"])
    proof = _proof(model_id, fmt, old, new, descriptor)
    payload = {"schema": "dmwk-p2-a3-certificate-v1", "claim": CLAIM,
               "model_id": model_id, "format": fmt, "expected_weight_version": version,
               "old_weights": [list(row) for row in old],
               "new_weights": [list(row) for row in new],
               "effective_delta": [[_pair(x) for x in row] for row in _delta(old, new, fmt)],
               "descriptor": descriptor, "descriptor_sha256": _hash(descriptor),
               "implementation_sha256": _implementation_hashes(), "proof": proof}
    return _json({"payload": payload, "payload_sha256": _hash(payload)})


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CertificateRejected("Duplicate JSON object key")
        result[key] = value
    return result


def _parse(text):
    require(type(text) is str and len(text) <= 100000,
            "Certificate must be a bounded built-in string")
    try:
        value = json.loads(text, object_pairs_hook=_strict_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(
                               CertificateRejected("Nonfinite JSON token")))
    except (ValueError, TypeError, RecursionError) as exc:
        raise CertificateRejected("Invalid certificate JSON: " + str(exc)) from None
    require(type(value) is dict and set(value) == {"payload", "payload_sha256"},
            "Certificate envelope schema mismatch")
    require(type(value["payload"]) is dict, "Certificate payload must be an object")
    require(type(value["payload_sha256"]) is str, "Certificate hash must be a string")
    return value


def check_certificate(text, model_id, fmt, old_words, version=0):
    """Recompute the authoritative record; hashes alone never authorize."""
    descriptor = model_descriptor(model_id, fmt)
    old = _matrix(old_words, fmt, descriptor["shape"])
    version = _version(version)
    supplied = _parse(text)
    payload = supplied["payload"]
    require(payload.get("claim") == "bitwise_complete_registered_domain_v1",
            "Algebraic, numerical or unknown evidence cannot authorize this commit")
    require(type(payload.get("expected_weight_version")) is int and
            payload["expected_weight_version"] == version, "Stale or invalid certificate version")
    candidate_list = payload.get("new_weights")
    require(type(candidate_list) is list and
            all(type(row) is list for row in candidate_list), "Candidate JSON matrix type mismatch")
    candidate = _matrix(tuple(tuple(row) for row in candidate_list), fmt, descriptor["shape"])
    expected_text = make_certificate(model_id, fmt, old, candidate, version)
    # Canonical byte identity also distinguishes bool from int, 1.0 from 1,
    # signed textual zeros, extra fields, omissions, and recomputed forgeries.
    require(text == expected_text, "Certificate does not match independently recomputed complete evidence")
    return json.loads(expected_text)


class CertificateKernel:
    """Trusted single-threaded stateful reference with transactional commits.

    Arbitrary private-memory/module mutation, asynchronous races and host
    failures are outside this API contract. Returned snapshots are primitive
    immutable tuples. Certificate text is checked afresh at each commit.
    """
    __slots__ = ("_initialized", "_format", "_model", "_one", "_bank")

    def __init__(self, format_name, model_id="duplicate_feedback_v1", initial_bit=0):
        require(not getattr(self, "_initialized", False), "A live kernel cannot be reinitialized")
        descriptor = model_descriptor(model_id, format_name)
        require(descriptor["stateful"], "Only registered stateful models have a live kernel")
        require(type(initial_bit) is int and initial_bit in (0, 1), "Initial state must be a Boolean bit")
        self._format = format_name
        self._model = model_id
        self._one = _encoded(1, format_name)
        self._bank = (0, initial_weights(model_id, format_name), self._one if initial_bit else 0, 0)
        self._initialized = True

    @property
    def format_name(self):
        return self._format

    @property
    def model_id(self):
        return self._model

    @property
    def weights(self):
        return self._bank[1]

    @property
    def version(self):
        return self._bank[0]

    @property
    def state_word(self):
        return self._bank[2]

    @property
    def ticks(self):
        return self._bank[3]

    def snapshot(self):
        return (self._model, self._format, _policy(), _schedule(), *self._bank)

    def prepare(self, candidate_words):
        version, old, _, _ = self._bank
        return make_certificate(self._model, self._format, old, candidate_words, version)

    def commit(self, text):
        version, old, state, ticks = self._bank
        checked = check_certificate(text, self._model, self._format, old, version)
        require(version < (1 << 63)-1, "Version exhausted; no unbounded machine counter is assumed")
        candidate = tuple(tuple(row) for row in checked["payload"]["new_weights"])
        new_bank = (version+1, candidate, state, ticks)
        receipt = (version+1, old, candidate, checked["payload_sha256"])
        self._bank = new_bank
        return receipt

    def _contract(self, policy, schedule):
        require(type(policy) is str and policy == _policy(), "Uncertified numerical graph/policy")
        require(type(schedule) is str and schedule == _schedule(), "Uncertified schedule")

    def _bit(self, raw):
        require(type(raw) is int and raw in (0, self._one), "Canonical Boolean word required")
        return raw

    def d_tick(self, input_word, *, policy=POLICY, schedule=SCHEDULE):
        self._contract(policy, schedule)
        u = self._bit(input_word)
        version, weights, q, ticks = self._bank
        # Both full matrix calls read this old-state and weight snapshot.
        hs = (q, q)
        hi = (u, u) if self._model == "duplicate_feedback_v1" else (u, 0)
        fp = get_fp()
        audit = fp.Audit()
        try:
            ys = _dense(weights, hs, self._format, audit)
            yi = _dense(weights, hi, self._format, audit)
            self._bit(ys[0]); self._bit(ys[1]); self._bit(yi[0]); self._bit(yi[1])
            candidate = self._bit(_xor(ys[0], yi[0], self._format, audit))
        except fp.ExecutionError as exc:
            raise CertificateRejected("Tick arithmetic refused: " + str(exc)) from None
        new_bank = (version, weights, candidate, ticks+1)
        observation = (ys, yi, candidate)
        self._bank = new_bank
        return observation

    def a_output(self, activation_words, *, policy=POLICY, schedule=SCHEDULE):
        self._contract(policy, schedule)
        require(type(activation_words) is tuple and len(activation_words) == 2,
                "A input must be a two-word tuple")
        point = tuple(self._bit(x) for x in activation_words)
        require(point in ((self._one, 0), (0, self._one), (0, 0)),
                "A input is outside the fixed legal domain")
        return _dense(self.weights, point, self._format, get_fp().Audit())

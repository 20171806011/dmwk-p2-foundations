"""B1 trusted serialized candidate acceptance and one combined publication.

Certificates are semantic evidence, not signatures of caller intent. A coherent
new request with fully valid recomputed evidence is another authorized request.
No secret, private-memory protection, crash consistency or concurrency is claimed.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from b1_runtime import get_fp, load_a3
import constrained_updates as cu

xp = cu.xp
ck = load_a3("certificate_kernel")
SCHEDULE = "p2-b1-trusted-serial-full-snapshot-combined-publication-v1"
STRUCTURAL_POLICY = "p2-b1-sparse-D-columns-0-1-separate-rne-canonical-zero-v1"


class UpdateRejected(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise UpdateRejected(message)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode("ascii")).hexdigest()


def _strict_object(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "Duplicate JSON key")
        out[key] = value
    return out


def _parse(text):
    require(type(text) is str and len(text) <= 1000000, "Candidate must be a bounded built-in string")
    try:
        parsed = json.loads(text, object_pairs_hook=_strict_object,
                            parse_constant=lambda _: (_ for _ in ()).throw(UpdateRejected("Nonfinite JSON token")))
    except (ValueError, TypeError, RecursionError) as exc:
        raise UpdateRejected("Invalid candidate JSON: " + str(exc)) from None
    require(type(parsed) is dict and set(parsed) == {"payload", "payload_sha256"}, "Candidate envelope mismatch")
    require(type(parsed["payload"]) is dict and type(parsed["payload_sha256"]) is str, "Candidate payload mismatch")
    return parsed


def _word(raw, fmt):
    try:
        return ck._word(raw, fmt)
    except ValueError as exc:
        raise UpdateRejected(str(exc)) from None


def _bank(words, fmt, shape):
    require(type(words) is tuple and len(words) == shape[0], "Immutable endpoint row tuple required")
    require(all(type(row) is tuple and len(row) == shape[1] for row in words), "Immutable endpoint column tuple required")
    return tuple(tuple(_word(v, fmt) for v in row) for row in words)


def _one(fmt):
    return get_fp().encode_constant(1, fmt)


def model_descriptor(model_id, fmt):
    require(type(model_id) is str and model_id in (
        "duplicate_feedback_v1", "split_feedback_v1", "structural_duplicate_v1"), "Unknown/unproved B1 model")
    ck._format(fmt)
    if model_id != "structural_duplicate_v1":
        return {"B1_registry": "dmwk-p2-b1-model-v1", "route": "dense_A3",
                "registered_model": ck.model_descriptor(model_id, fmt),
                "combined_schedule": SCHEDULE}
    one = _one(fmt)
    return {"B1_registry": "dmwk-p2-b1-model-v1", "route": "structural_reserve",
            "model_id": model_id, "format": fmt, "shape": [2, 3],
            "fixed_bias_words": [0, 0], "fixed_columns": [[one, 0], [0, one]],
            "sites": [{"id": "state", "activations": [[0, 0, 0], [one, one, 0]]},
                      {"id": "input", "activations": [[0, 0, 0], [one, one, 0]]}],
            "domain_id": "structural_duplicate_v1:all_boolean_state_input_pairs",
            "coverage": "all_reachable_states_and_all_finite_boolean_input_sequences",
            "legal_initial_state_words": [0, one], "legal_external_input_words": [0, one],
            "invariant_id": "canonical_bit_with_immutable_identity_columns",
            "graph": {"D": "all rows, only columns 0 then 1, separate multiply/add, zero bias first",
                      "A": "all rows, columns 0 then 1 then 2, separate multiply/add, zero bias first",
                      "site_order": ["state", "input"],
                      "transition": "xor_first_outputs_same_old_snapshot",
                      "observation": "full D site outputs and next q"},
            "A_domain": [[0, 0, one], [one, 0, 0], [0, 0, 0]],
            "A_to_D_feedback": False, "numerical_policy": STRUCTURAL_POLICY,
            "combined_schedule": SCHEDULE}


def _shape(model_id, fmt):
    d = model_descriptor(model_id, fmt)
    return tuple(d["registered_model"]["shape"] if d["route"] == "dense_A3" else d["shape"])


def _sites(model_id, fmt):
    d = model_descriptor(model_id, fmt)
    return d["registered_model"]["sites"] if d["route"] == "dense_A3" else d["sites"]


def global_generators(model_id, fmt):
    vectors = [tuple(get_fp().decode_word(v, fmt) for v in a)
               for site in _sites(model_id, fmt) for a in site["activations"]]
    d = _shape(model_id, fmt)[1]
    return xp.Matrix(tuple(tuple(v[j] for v in vectors) for j in range(d)), len(vectors))


def initial_weights(model_id, fmt):
    model_descriptor(model_id, fmt)
    if model_id == "structural_duplicate_v1":
        one = _one(fmt)
        return ((one, 0, one), (0, one, 0))
    return ck.initial_weights(model_id, fmt)


def decode_matrix(words, fmt):
    require(type(words) in (tuple, list) and len(words) > 0, "Nonempty word matrix required")
    width = len(words[0])
    require(all(type(row) in (tuple, list) and len(row) == width for row in words), "Ragged words")
    return xp.matrix(tuple(tuple(get_fp().decode_word(_word(v, fmt), fmt) for v in row) for row in words), ncols=width)


def quantize_endpoint(old_words, increment, fmt):
    old = decode_matrix(old_words, fmt)
    require(type(increment) is xp.Matrix and old.shape == increment.shape, "Increment shape mismatch")
    candidate = xp.add(old, increment)
    try:
        words = tuple(tuple(get_fp().round_fraction(v, fmt) for v in row) for row in candidate.rows)
        return _bank(words, fmt, old.shape)
    except (ValueError, get_fp().ExecutionError) as exc:
        raise UpdateRejected("Endpoint quantization rejected: " + str(exc)) from None


def _structural_admit(words, fmt):
    bank = _bank(words, fmt, (2, 3))
    one = _one(fmt)
    require(tuple(row[:2] for row in bank) == ((one, 0), (0, one)), "Structural immutable columns changed")
    return bank


def _evaluate(words, activation, fmt, columns, audit):
    fp = get_fp()
    values = []
    for row in words:
        acc = 0
        for j in columns:
            acc = fp.add_words(acc, fp.mul_words(row[j], activation[j], fmt, audit), fmt, audit)
        values.append(acc)
    return tuple(values)


def evaluate_a(weights, activation, fmt, model_id):
    descriptor = model_descriptor(model_id, fmt)
    words = _bank(weights, fmt, _shape(model_id, fmt))
    require(type(activation) in (tuple, list), "A activation must be a word sequence")
    admitted = descriptor["registered_model"]["A_domain"] if descriptor["route"] == "dense_A3" else descriptor["A_domain"]
    require(list(activation) in admitted and all(type(v) is int for v in activation), "Outside declared A domain")
    audit = get_fp().Audit()
    out = _evaluate(words, tuple(activation), fmt, range(len(activation)), audit)
    return {"output_words": list(out), "arithmetic_counts": ck._audit_record(audit)}


def evaluate_d(weights, q, u, fmt, model_id):
    descriptor = model_descriptor(model_id, fmt)
    words = _bank(weights, fmt, _shape(model_id, fmt))
    require(type(q) is int and type(u) is int and q in (0, _one(fmt)) and u in (0, _one(fmt)), "Canonical Boolean q/u required")
    audit = get_fp().Audit()
    if model_id == "structural_duplicate_v1":
        # Admission is pure; arithmetic read exclusion starts after this check.
        _structural_admit(words, fmt)
        hs, hi, columns = (q, q, 0), (u, u, 0), range(2)
    else:
        hs = (q, q)
        hi = (u, u) if model_id == "duplicate_feedback_v1" else (u, 0)
        columns = range(2)
    os = _evaluate(words, hs, fmt, columns, audit)
    oi = _evaluate(words, hi, fmt, columns, audit)
    next_q = ck._xor(os[0], oi[0], fmt, audit)
    return {"state_activation_words": list(hs), "input_activation_words": list(hi),
            "state_output_words": list(os), "input_output_words": list(oi),
            "next_state_word": next_q, "arithmetic_counts": ck._audit_record(audit)}


def _structural_certificate(old, new, fmt):
    _structural_admit(old, fmt); _structural_admit(new, fmt)
    records = []
    for q in (0, _one(fmt)):
        for u in (0, _one(fmt)):
            a, b = evaluate_d(old, q, u, fmt, "structural_duplicate_v1"), evaluate_d(new, q, u, fmt, "structural_duplicate_v1")
            require(a == b, "Structural complete transition equality failed")
            require(a["state_output_words"] == [q, q] and a["input_output_words"] == [u, u], "Structural full output invariant failed")
            expected = _one(fmt) if bool(q) != bool(u) else 0
            require(a["next_state_word"] == expected, "Structural XOR closure failed")
            records.append({"q": q, "u": u, "trace": a})
    return {"method": "exhaustive_all_four_registered_boolean_state_input_pairs",
            "state_transition_cases": records, "state_transition_case_count": 4,
            "arithmetic_read_scope": "D excludes reserve after pure admitted-bank validation"}


def ai_request(direction, restriction="projected"):
    require(type(restriction) is str and restriction in ("none", "projected", "structural"), "Unknown AI restriction")
    return {"source": "ai", "restriction": restriction, "direction": cu.matrix_record(direction)}


def optimizer_request(gradient, restriction="projected"):
    require(type(restriction) is str and restriction in ("projected", "structural"), "Unsafe baseline mode is offline only")
    return {"source": "optimizer", "restriction": restriction, "gradient": cu.matrix_record(gradient)}


def _clone_config(config):
    record = cu.config_record(config)
    scalars = {k: (None if v is None else Fraction(*v)) for k, v in record.items()
               if k not in ("kind", "clip_mode")}
    return cu.OptimizerConfig(kind=record["kind"], clip_mode=record["clip_mode"], **scalars)


def _source_hashes():
    paths = [Path(__file__), Path(cu.__file__), Path(__file__).with_name("b1_runtime.py"),
             Path(ck.__file__), Path(get_fp().__file__)]
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


@dataclass(frozen=True)
class CombinedBank:
    weights: tuple
    q_word: int
    ticks: int
    weight_version: int
    optimizer_state: cu.OptimizerState


class OptimizerKernel:
    __slots__ = ("_initialized", "_model", "_fmt", "_config", "_claim", "_bank")

    def __init__(self, model_id, fmt, config, claim="ALG_AND_BIT", initial_words=None, initial_state_word=0):
        require(not getattr(self, "_initialized", False), "A live kernel cannot be reinitialized")
        model_descriptor(model_id, fmt)
        require(type(claim) is str and claim in ("BIT", "ALG_AND_BIT"), "Unknown acceptance claim")
        require(type(initial_state_word) is int and initial_state_word in (0, _one(fmt)), "Initial state is not a canonical Boolean word")
        owned_config = _clone_config(config)
        baseline = initial_weights(model_id, fmt)
        words = baseline if initial_words is None else _bank(initial_words, fmt, _shape(model_id, fmt))
        if model_id == "structural_duplicate_v1":
            _structural_certificate(baseline, words, fmt)
        else:
            ck.make_certificate(model_id, fmt, baseline, words, 0)
        self._model, self._fmt, self._config, self._claim = model_id, fmt, owned_config, claim
        self._bank = CombinedBank(words, initial_state_word, 0, 0, cu.initial_optimizer_state(*_shape(model_id, fmt)))
        self._initialized = True

    @property
    def weights(self): return self._bank.weights

    @property
    def state_word(self): return self._bank.q_word

    @property
    def version(self): return self._bank.weight_version

    @property
    def ticks(self): return self._bank.ticks

    @property
    def model_id(self): return self._model

    @property
    def format_name(self): return self._fmt

    def snapshot(self):
        bank = self._bank
        return {"model_id": self._model, "format": self._fmt, "claim": self._claim,
                "config": cu.config_record(self._config), "weights": [list(row) for row in bank.weights],
                "q_word": bank.q_word, "ticks": bank.ticks, "weight_version": bank.weight_version,
                "optimizer_state": cu.state_record(bank.optimizer_state), "schedule": SCHEDULE}

    def _stage(self, request):
        require(type(request) is dict, "Request must be a primitive object")
        source = request.get("source")
        require(type(source) is str and source in ("ai", "optimizer"), "Unknown candidate source")
        key = "direction" if source == "ai" else "gradient"
        require(set(request) == {"source", "restriction", key}, "Request schema mismatch")
        direction = cu.matrix_from_record(request[key])
        restriction = request["restriction"]
        canonical = ai_request(direction, restriction) if source == "ai" else optimizer_request(direction, restriction)
        require(_json(request) == _json(canonical), "Request must be canonical")
        require(direction.shape == _shape(self._model, self._fmt), "Request matrix shape mismatch")
        require(restriction != "structural" or self._model == "structural_duplicate_v1", "Structural mask not registered for this model")
        old = decode_matrix(self._bank.weights, self._fmt)
        H = global_generators(self._model, self._fmt)
        if source == "optimizer":
            stage = cu.stage_optimizer(old, direction, self._bank.optimizer_state, self._config,
                                       mode=restriction, H=H, free_columns=(2,) if self._model == "structural_duplicate_v1" else ())
        else:
            increment = direction
            if restriction == "projected": increment = cu.project_direction(direction, H)
            if restriction == "structural": increment = cu.mask_direction(direction, (2,))
            stage = cu.Stage(direction, increment, self._bank.optimizer_state,
                             {"source": "ai", "restriction": restriction, "arithmetic": "exact rational proposal",
                              "optimizer_state": "unchanged", "authorizes_endpoint": False})
        candidate = quantize_endpoint(self._bank.weights, stage.increment, self._fmt)
        effective = xp.sub(decode_matrix(candidate, self._fmt), old)
        preview = {"request": canonical, "old_snapshot": self.snapshot(),
                   "raw_increment": cu.matrix_record(stage.raw_increment), "increment": cu.matrix_record(stage.increment),
                   "candidate_words": [list(row) for row in candidate], "candidate_exact": cu.matrix_record(decode_matrix(candidate, self._fmt)),
                   "effective_delta": cu.matrix_record(effective), "effective_delta_rank": xp.rank(effective),
                   "proposal_rank": xp.rank(stage.increment), "next_optimizer_state": cu.state_record(stage.next_state),
                   "audit": stage.audit, "certified": False}
        return preview, candidate, stage.next_state

    def preview(self, request):
        try:
            preview, _, _ = self._stage(request)
            return json.loads(_json(preview))
        except (ValueError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Proposal preview rejected: " + str(exc)) from None

    def _prepared(self, request):
        require(self._bank.weight_version < cu.LIMIT, "Weight version exhausted")
        preview, candidate, next_state = self._stage(request)
        if self._model == "structural_duplicate_v1":
            certificate = _structural_certificate(self._bank.weights, candidate, self._fmt)
        else:
            text = ck.make_certificate(self._model, self._fmt, self._bank.weights, candidate, self._bank.weight_version)
            certificate = ck.check_certificate(text, self._model, self._fmt, self._bank.weights, self._bank.weight_version)
        delta = xp.sub(decode_matrix(candidate, self._fmt), decode_matrix(self._bank.weights, self._fmt))
        residual = xp.matmul(delta, global_generators(self._model, self._fmt))
        algebra_zero = residual == xp.zeros(residual.nrows, residual.ncols)
        require(self._claim == "BIT" or algebra_zero, "Submitted endpoint violates the selected exact ALG condition")
        payload = {"schema": "dmwk-p2-b1-candidate-v1", "claim": self._claim,
                   "descriptor": model_descriptor(self._model, self._fmt), "source_sha256": _source_hashes(),
                   "optimizer_config": cu.config_record(self._config), "optimizer_config_sha256": _hash(cu.config_record(self._config)),
                   "old_snapshot_sha256": _hash(self.snapshot()), "staged": preview,
                   "complete_domain_certificate": certificate,
                   "exact_effective_residual": cu.matrix_record(residual), "ALG": algebra_zero,
                   "BIT": True, "origin_authenticity": "trusted-caller semantic candidate; no cryptographic intent authentication"}
        text = _json({"payload": payload, "payload_sha256": _hash(payload)})
        next_bank = CombinedBank(candidate, self._bank.q_word, self._bank.ticks,
                                 self._bank.weight_version+1, next_state)
        return text, next_bank

    def prepare(self, request):
        try:
            text, _ = self._prepared(request)
            return text
        except (ValueError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Candidate preparation rejected: " + str(exc)) from None

    def commit(self, prepared_text):
        try:
            supplied = _parse(prepared_text)
            payload = supplied["payload"]
            require(type(payload.get("staged")) is dict, "Missing staged candidate")
            require(payload.get("old_snapshot_sha256") == _hash(self.snapshot()), "Stale or mismatched combined snapshot")
            expected, next_bank = self._prepared(payload["staged"].get("request"))
            require(prepared_text == expected, "Candidate differs from complete semantic recomputation")
            receipt = {"accepted": True, "weight_version": next_bank.weight_version,
                       "candidate_sha256": hashlib.sha256(expected.encode("ascii")).hexdigest(),
                       "claim": self._claim, "optimizer_step": next_bank.optimizer_state.step}
        except (ValueError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Candidate commit rejected: " + str(exc)) from None
        # The sole publication point: state and endpoint are owned together.
        self._bank = next_bank
        return receipt

    def tick(self, u_word):
        try:
            bank = self._bank
            require(bank.ticks < cu.LIMIT, "Tick counter exhausted")
            trace = evaluate_d(bank.weights, bank.q_word, u_word, self._fmt, self._model)
            one = _one(self._fmt)
            expected_s = [bank.q_word, bank.q_word]
            expected_i = [u_word, 0] if self._model == "split_feedback_v1" else [u_word, u_word]
            require(trace["state_output_words"] == expected_s and trace["input_output_words"] == expected_i,
                    "Protected full output invariant violated")
            require(trace["next_state_word"] == (one if bool(bank.q_word) != bool(u_word) else 0), "Protected next-state invariant violated")
            next_bank = CombinedBank(bank.weights, trace["next_state_word"], bank.ticks+1,
                                     bank.weight_version, bank.optimizer_state)
        except (ValueError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Protected tick rejected: " + str(exc)) from None
        self._bank = next_bank
        return trace

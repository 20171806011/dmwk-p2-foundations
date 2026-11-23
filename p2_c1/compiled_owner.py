"""C1 trusted serial owner for a completely reconstructed compiled program.

Only the reserved A block may change. Numerical diagnostics are not authority.
All protocol work creates unpublished values; one final pointer assignment
publishes weights, optimizer and ledgers together. No concurrency/crash claim.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import c1_compiler as cc
from c1_runtime import get_fp, load_b1

cu = load_b1("constrained_updates")
xp = cu.xp
SCHEMA = "dmwk-p2-c1-compiled-owner-v1"
CANDIDATE = "dmwk-p2-c1-exact-compiled-update-v1"
SCHEDULE = "c1-trusted-serial-one-snapshot-one-publication-v1"
LIMIT = (1 << 63) - 1


class UpdateRejected(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise UpdateRejected(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def pair(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def _rat(value):
    require(type(value) in (int, Fraction), "Expected an exact integer or Fraction")
    return Fraction(value)


def _bounded(value, maximum, name):
    require(type(value) is int and 0 <= value <= maximum, name + " outside its declared bound")
    return value


def _sources():
    paths = (Path(__file__), Path(cc.__file__), Path(__file__).with_name("c1_runtime.py"),
             Path(cu.__file__), Path(xp.__file__), Path(get_fp().__file__))
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _decode(words, fmt):
    return xp.matrix(tuple(tuple(get_fp().decode_word(x, fmt) for x in row) for row in words))


def _matrix(raw, shape):
    value = cu.matrix_from_record(raw)
    require(value.shape == shape, "Candidate matrix differs from the compiled bank shape")
    require(all(max(abs(v.numerator).bit_length(), v.denominator.bit_length()) <= 4096
                for row in value.rows for v in row), "Candidate rational exceeds reference bit-size limit")
    return value


def structural_mask(matrix):
    """Final row-and-column restriction, after the complete optimizer proposal."""
    require(type(matrix) is xp.Matrix and matrix.nrows >= 3 and matrix.ncols >= 4,
            "Expected a full compiled matrix")
    return xp.matrix(tuple(tuple(v if i >= 2 and j >= 3 else Fraction(0)
                                 for j, v in enumerate(row)) for i, row in enumerate(matrix.rows)))


def ai_request(direction, restriction="structural"):
    require(type(direction) is xp.Matrix, "Exact full-bank direction required")
    require(restriction in ("structural", "none"), "Unknown AI restriction")
    return {"kind": "ai_increment", "restriction": restriction,
            "direction": cu.matrix_record(direction)}


def optimizer_request(gradient):
    require(type(gradient) is xp.Matrix, "Exact full-bank gradient required")
    return {"kind": "optimizer", "gradient": cu.matrix_record(gradient)}


def endpoint_request(words):
    require(type(words) in (tuple, list) and all(type(row) in (tuple, list) for row in words),
            "Endpoint must be a sequence of word rows")
    return {"kind": "stored_endpoint", "weight_words": [list(row) for row in words]}


def _request(request, shape):
    require(type(request) is dict and type(request.get("kind")) is str, "Candidate request schema mismatch")
    kind = request["kind"]
    if kind == "ai_increment":
        require(set(request) == {"kind", "restriction", "direction"} and
                type(request["restriction"]) is str and request["restriction"] in ("structural", "none"),
                "AI request fields or restriction invalid")
        matrix = _matrix(request["direction"], shape)
        normalized = ai_request(matrix, request["restriction"])
    elif kind == "optimizer":
        require(set(request) == {"kind", "gradient"}, "Optimizer request fields invalid")
        matrix = _matrix(request["gradient"], shape)
        normalized = optimizer_request(matrix)
    elif kind == "stored_endpoint":
        require(set(request) == {"kind", "weight_words"}, "Stored endpoint request fields invalid")
        normalized = endpoint_request(request["weight_words"])
    else:
        raise UpdateRejected("Unsupported request; numerical/geometric receipts are not update authority")
    return normalized


def _config(config):
    require(type(config) is cu.OptimizerConfig and config.kind in ("sgd", "momentum"),
            "C1 reference supports exact SGD or EMA momentum only")
    require(config.clip_mode == "none" and config.clip_bound is None and config.weight_decay == 0,
            "C1 optimizer configuration excludes clipping and weight decay")
    return cu.OptimizerConfig(config.kind, config.learning_rate, momentum=config.momentum,
                              beta1=config.beta1, beta2=config.beta2, epsilon=config.epsilon,
                              weight_decay=0, clip_mode="none", clip_bound=None)


@dataclass(frozen=True)
class OwnedBank:
    weights: tuple
    state_words: tuple
    ticks: int
    version: int
    optimizer: object
    accepted_ledger: tuple[str, ...]
    tick_ledger: tuple[str, ...]


class CompiledOwner:
    __slots__ = ("_state", "_artifact_text", "_source_text", "_budget_text", "_response_text",
                 "_fmt", "_config", "_target", "_initial_index", "_max_updates", "_max_ticks", "_origin",
                 "_implementation")

    def __init__(self, source, budget, fmt, config, artifact=None, response_request=None,
                 initial_index=0, target=None, max_updates=128, max_ticks=256):
        require(not hasattr(self, "_state"), "An owner cannot be reinitialized")
        self._max_updates = _bounded(max_updates, 128, "Accepted-update limit")
        self._max_ticks = _bounded(max_ticks, 256, "Execution-tick limit")
        self._initial_index = _bounded(initial_index, 15, "Initial-state index")
        self._config = _config(config)
        compiled = cc.compile_program(source, budget, fmt, response_request=response_request)
        if artifact is not None:
            cc.check_artifact(artifact, source, budget, fmt, response_request=response_request)
            require(canonical(artifact) == canonical(compiled), "Compiler artifact mismatch")
        self._artifact_text = canonical(compiled)
        self._source_text = canonical(source)
        self._budget_text = canonical(budget)
        self._response_text = canonical(response_request)
        self._fmt = fmt
        words = cc.initial_weights(compiled)
        p, q = len(words)-2, len(words[0])-3
        chosen = tuple(Fraction(1 if i % 2 == 0 else -1) for i in range(p)) if target is None else target
        require(type(chosen) in (tuple, list) and len(chosen) == p, "A target dimension mismatch")
        self._target = tuple(_rat(x) for x in chosen)
        initial = cc.initial_state_words(compiled, initial_index)
        optimizer = cu.initial_optimizer_state(len(words), len(words[0]))
        self._origin = words
        self._implementation = _sources()
        self._state = OwnedBank(words, tuple(initial), 0, 0, optimizer, (), ())
        # Construction checks the fixed legal A domain; no arbitrary dense A input is inferred.
        self.all_A()

    @property
    def artifact(self): return json.loads(self._artifact_text)
    @property
    def weights(self): return self._state.weights
    @property
    def state_words(self): return self._state.state_words
    @property
    def ticks(self): return self._state.ticks
    @property
    def version(self): return self._state.version
    @property
    def accepted_count(self): return len(self._state.accepted_ledger)

    def _task(self):
        q = len(self.weights[0])-3
        one = get_fp().encode_constant(1, self._fmt)
        return {"id": "compiled_reserved_column_squared_loss_v1",
                "A_input_words": [one]+[0]*(q-1), "target_exact": [pair(v) for v in self._target],
                "loss": "half exact squared residual of decoded actual A output",
                "gradient": "continuous extension of unit-input linear loss, not derivative of word rounding",
                "initial_A_anchors_mutable_after_compilation": True, "A_to_D_feedback": False}

    def _a(self, artifact, words):
        raw = cc.evaluate_a(artifact, words, self._task()["A_input_words"])
        values = tuple(get_fp().decode_word(w, self._fmt) for w in raw["output_words"])
        loss = sum(((v-y)**2 for v, y in zip(values, self._target)), Fraction(0))/2
        return {"output_words": list(raw["output_words"]), "decoded_output": [pair(v) for v in values],
                "loss": pair(loss), "arithmetic_counts": raw["arithmetic_counts"]}

    def evaluate_a(self): return self._a(self.artifact, self.weights)

    def all_A(self, words=None):
        artifact = self.artifact
        actual = self.weights if words is None else words
        q = len(actual[0])-3
        one = get_fp().encode_constant(1, self._fmt)
        inputs = ((0,)*q,)+tuple(tuple(one if i == j else 0 for i in range(q)) for j in range(q))
        return [{"input_words": list(x), "trace": cc.evaluate_a(artifact, actual, x)} for x in inputs]

    def full_D(self, words=None):
        artifact = self.artifact
        actual = self.weights if words is None else words
        return [{"state_words": list(s), "input_words": list(u),
                 "trace": cc.execute_d(artifact, actual, s, u)}
                for s in cc.legal_states(artifact) for u in cc.legal_inputs(artifact)]

    def _d_summary(self, words):
        table = self.full_D(words)
        return {"domain": "all canonical Boolean states and inputs, not sampled reachable states",
                "cases": len(table), "complete_table_sha256": digest(table),
                "rows": [{"state_words": r["state_words"], "input_words": r["input_words"],
                          "next_state_words": r["trace"]["next_state_words"],
                          "output_words": r["trace"]["output_words"],
                          "site_count": len(r["trace"]["site_traces"]),
                          "all_site_trace_sha256": digest(r["trace"]["site_traces"])} for r in table]}

    def toy_gradient(self):
        values = tuple(Fraction(*v) for v in self.evaluate_a()["decoded_output"])
        n, d = len(self.weights), len(self.weights[0])
        return xp.matrix(tuple(tuple(values[i-2]-self._target[i-2] if i >= 2 and j == 3 else Fraction(0)
                                     for j in range(d)) for i in range(n)))

    def snapshot(self):
        state = self._state
        accepted = [json.loads(x) for x in state.accepted_ledger]
        ticks = [json.loads(x) for x in state.tick_ledger]
        artifact = self.artifact
        return {"schema": SCHEMA, "format": self._fmt, "claim": "ALG_AND_BIT",
                "schedule": SCHEDULE, "artifact": artifact, "artifact_sha256": digest(artifact),
                "implementation_sha256": dict(self._implementation),
                "expected_source": json.loads(self._source_text), "expected_budget": json.loads(self._budget_text),
                "expected_response_request": json.loads(self._response_text),
                "initial_relation": {"initial_state_index": self._initial_index,
                                     "initial_state_words": list(cc.initial_state_words(artifact, self._initial_index)),
                                     "reference": "same compiled source, initial state, legal inputs and trusted tick schedule"},
                "weights": [list(row) for row in state.weights], "state_words": list(state.state_words),
                "ticks": state.ticks, "weight_version": state.version,
                "optimizer_config": cu.config_record(self._config), "optimizer_state": cu.state_record(state.optimizer),
                "task": self._task(), "accepted_updates": len(accepted),
                "nonzero_stored_updates": sum(e["nonzero_stored_change"] for e in accepted),
                "accepted_ledger": accepted, "tick_ledger": ticks,
                "ledger_sha256": digest({"accepted": accepted, "ticks": ticks}),
                "limits": {"max_accepted_updates": self._max_updates, "max_ticks": self._max_ticks,
                           "scope": "administrative finite-reference limits, not consumed algebraic dimensions"}}

    def _prepared(self, request):
        require(_sources() == self._implementation, "Pinned compiler/owner/arithmetic implementation changed")
        current = self._state
        before = self.snapshot()
        staged = deepcopy(current)
        artifact = self.artifact
        cc.check_artifact(artifact, json.loads(self._source_text), json.loads(self._budget_text), self._fmt,
                          response_request=json.loads(self._response_text))
        old_words = cc.validate_endpoint(artifact, staged.weights)
        old = _decode(old_words, self._fmt)
        request = _request(request, old.shape)
        next_optimizer = staged.optimizer
        ideal = None
        raw = None
        audit = {"order": ["request", "final_structural_restriction", "endpoint_quantization", "endpoint_certification"],
                 "authorizes_before_endpoint_check": False}
        if request["kind"] == "stored_endpoint":
            new_words = cc.validate_endpoint(artifact, request["weight_words"])
            audit["proposal"] = "already stored endpoint; no ideal increment assumed"
        else:
            if request["kind"] == "optimizer":
                gradient = _matrix(request["gradient"], old.shape)
                proposal = cu.optimizer_proposal(old, gradient, staged.optimizer, self._config)
                raw = proposal.increment
                ideal = structural_mask(raw)
                next_optimizer = proposal.next_state
                audit["optimizer"] = proposal.audit
                audit["restriction"] = "final row-and-column structural projection after optimizer"
            else:
                raw = _matrix(request["direction"], old.shape)
                ideal = structural_mask(raw) if request["restriction"] == "structural" else raw
                audit["restriction"] = request["restriction"]
            target = xp.add(old, ideal)
            new_words = tuple(tuple(get_fp().round_fraction(v, self._fmt) for v in row) for row in target.rows)
            new_words = cc.validate_endpoint(artifact, new_words)
        new = _decode(new_words, self._fmt)
        delta = xp.sub(new, old)
        require(all(v == 0 for i, row in enumerate(delta.rows) for j, v in enumerate(row) if i < 2 or j < 3),
                "Actual endpoint changed a fixed or cross-region cell")
        require(all(delta.rows[i][j] == 0 for i in range(delta.nrows) for j in range(3)),
                "Actual endpoint fails the proved ambient activation annihilator")
        old_D = self._d_summary(old_words)
        new_D = self._d_summary(new_words)
        require(old_D == new_D, "Complete compiled D observations changed")
        A_total = self.all_A(new_words)
        # Late refusal deliberately follows successful copy-local candidate and domain checks.
        require(len(staged.accepted_ledger) < self._max_updates,
                "Administrative accepted-update budget exhausted after staging")
        require(staged.version < LIMIT, "Weight version exhausted")
        prefix = xp.sub(new, _decode(self._origin, self._fmt))
        event = {"accepted_index": len(staged.accepted_ledger)+1, "execution_tick": staged.ticks,
                 "old_snapshot_sha256": digest(before), "request": request,
                 "old_weight_words": old_words, "new_weight_words": new_words,
                 "raw_proposal": None if raw is None else cu.matrix_record(raw),
                 "ideal_increment": None if ideal is None else cu.matrix_record(ideal),
                 "effective_delta": cu.matrix_record(delta), "effective_rank": xp.rank(delta),
                 "prefix_delta": cu.matrix_record(prefix), "prefix_rank": xp.rank(prefix),
                 "nonzero_stored_change": any(v != 0 for row in delta.rows for v in row),
                 "old_A": self._a(artifact, old_words), "new_A": self._a(artifact, new_words),
                 "complete_A_domain": A_total, "D_complete_domain": new_D,
                 "D_bitwise_equal": True, "ALG_on_proved_global_upper_space": True,
                 "capacity": artifact["capacity"], "audit": audit,
                 "old_optimizer_state": cu.state_record(staged.optimizer),
                 "new_optimizer_state": cu.state_record(next_optimizer)}
        next_state = OwnedBank(new_words, staged.state_words, staged.ticks, staged.version+1,
                               next_optimizer, staged.accepted_ledger+(canonical(event),), staged.tick_ledger)
        payload = {"schema": CANDIDATE, "claim": "ALG_AND_BIT", "authorizes_exact_candidate": True,
                   "schedule": SCHEDULE, "old_snapshot": before, "old_snapshot_sha256": digest(before),
                   "request": request, "artifact_sha256": digest(artifact),
                   "source_sha256": artifact["source_sha256"], "graph_sha256": artifact["graph_sha256"],
                   "new_weight_words": new_words, "new_weight_version": next_state.version,
                   "new_optimizer_state": cu.state_record(next_optimizer), "new_accepted_event": event,
                   "unchanged_D_state_words": staged.state_words, "unchanged_ticks": staged.ticks,
                   "implementation_sha256": _sources()}
        return canonical({"payload": payload, "payload_sha256": digest(payload)}), next_state

    def prepare(self, request):
        try:
            return self._prepared(request)[0]
        except (ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Preparation refused without publication: " + str(exc)) from None

    def preview(self, request):
        supplied = parse_candidate(self.prepare(request))
        return {"authorizes_commit": False, "old_snapshot_sha256": supplied["payload"]["old_snapshot_sha256"],
                "candidate_event": supplied["payload"]["new_accepted_event"]}

    def commit(self, text):
        try:
            supplied = parse_candidate(text)
            payload = supplied["payload"]
            require(payload.get("schema") == CANDIDATE, "Not an exact compiled update candidate")
            require(payload.get("old_snapshot_sha256") == digest(self.snapshot()), "Stale complete owned snapshot")
            expected, next_state = self._prepared(payload.get("request"))
            require(text == expected, "Candidate differs from complete semantic and snapshot recomputation")
            event = json.loads(next_state.accepted_ledger[-1])
            receipt = {"accepted": True, "claim": "ALG_AND_BIT", "weight_version": next_state.version,
                       "optimizer_step": next_state.optimizer.step, "ticks": next_state.ticks,
                       "accepted_index": len(next_state.accepted_ledger),
                       "nonzero_stored_change": event["nonzero_stored_change"],
                       "effective_rank": event["effective_rank"],
                       "candidate_sha256": hashlib.sha256(expected.encode("ascii")).hexdigest()}
        except (ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Commit refused without publication: " + str(exc)) from None
        self._state = next_state
        return receipt

    def tick(self, input_words):
        try:
            require(_sources() == self._implementation, "Pinned compiler/owner/arithmetic implementation changed")
            current = self._state
            before = self.snapshot()
            staged = deepcopy(current)
            trace = cc.execute_d(self.artifact, staged.weights, staged.state_words, input_words)
            require(staged.ticks < self._max_ticks, "Administrative execution-tick budget exhausted after staging")
            event = {"tick": staged.ticks+1, "weight_version": staged.version,
                     "accepted_update_index": len(staged.accepted_ledger),
                     "old_snapshot_sha256": digest(before), "old_state_words": staged.state_words,
                     "input_words": list(input_words), "trace": trace}
            next_state = OwnedBank(staged.weights, tuple(trace["next_state_words"]), staged.ticks+1,
                                   staged.version, staged.optimizer, staged.accepted_ledger,
                                   staged.tick_ledger+(canonical(event),))
            receipt = {"tick": next_state.ticks, "weight_version": next_state.version,
                       "accepted_update_index": len(next_state.accepted_ledger), "trace": trace}
        except (ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError, get_fp().ExecutionError) as exc:
            raise UpdateRejected("Tick refused without publication: " + str(exc)) from None
        self._state = next_state
        return receipt


def _object(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, "Duplicate JSON key")
        result[k] = v
    return result


def parse_candidate(text):
    require(type(text) is str and len(text) <= 16000000, "Expected a bounded built-in candidate string")
    try:
        value = json.loads(text, object_pairs_hook=_object,
                           parse_constant=lambda _: (_ for _ in ()).throw(UpdateRejected("Nonfinite JSON token")))
    except (ValueError, TypeError, RecursionError) as exc:
        raise UpdateRejected("Invalid candidate JSON: " + str(exc)) from None
    require(type(value) is dict and set(value) == {"payload", "payload_sha256"}, "Candidate envelope mismatch")
    require(type(value["payload"]) is dict and type(value["payload_sha256"]) is str, "Candidate payload mismatch")
    return value

"""Finite publication, state-feedback, and learning checks for the C1 compiler."""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
import compiled_owner as api

ROOT = Path(__file__).resolve().parent
SEED = 20261114


class Checks:
    def __init__(self):
        self.count = 0
        self.refusals = []

    def expect(self, ok, label):
        self.count += 1
        if not ok:
            raise AssertionError(label)

    def reject(self, owner, operation, label, reason_fragment):
        before = owner.snapshot()
        try:
            operation()
        except api.UpdateRejected as error:
            self.expect(reason_fragment in str(error), label + " rejected for unexpected reason: " + str(error))
            after = owner.snapshot()
            self.expect(before == after, label + " changed the owned snapshot")
            self.refusals.append({"format": before["format"], "case": label,
                                  "reason": str(error), "whole_snapshot_preserved": True})
        else:
            raise AssertionError(label + " accepted")


def xor_source():
    return {"schema": api.cc.SCHEMA, "state_ports": ["q"], "input_ports": ["u"],
            "output_ports": ["out"], "initial_states": [[0]],
            "next_state": [["xor", ["state", 0], ["input", 0]]],
            "outputs": [["state", 0]]}


def make_owner(fmt, q=1, momentum=False, **kwargs):
    config = api.cu.OptimizerConfig("momentum" if momentum else "sgd", Fraction(1, 4),
                                    momentum=Fraction(1, 2))
    return api.CompiledOwner(xor_source(), api.cc.default_budget(2, q), fmt, config, **kwargs)


def direction(owner, cells):
    return api.xp.matrix(tuple(tuple(cells.get((i, j), 0) for j in range(len(row)))
                               for i, row in enumerate(owner.weights)))


def training(fmt, input_bits, checks):
    owner = make_owner(fmt)
    one = api.get_fp().encode_constant(1, fmt)
    reference_bit = 0
    baseline_table = owner.full_D()
    initial = owner.evaluate_a()
    checks.expect(initial["decoded_output"] == [[0, 1], [0, 1]] and initial["loss"] == [1, 1],
                  "Declared toy starts at zero A on the first unit input")
    history = []
    first_noop = None
    protected_contexts = 0
    protected_site_comparisons = 0
    for number, input_bit in enumerate(input_bits, 1):
        before = owner.snapshot()
        req = api.optimizer_request(owner.toy_gradient())
        candidate = owner.prepare(req)
        checks.expect(before == owner.snapshot(), "Preparation published staged changes")
        receipt = owner.commit(candidate)
        checks.expect(receipt["accepted"] and receipt["claim"] == "ALG_AND_BIT", "Missing exact acceptance")
        checks.expect((owner.ticks, owner.state_words) == (number - 1, (reference_bit * one,)),
                      "Publication modified protected state or tick")
        checks.expect(receipt["optimizer_step"] == number and owner.version == number, "Mismatched update clocks")
        rows = owner.full_D()
        for row, reference in zip(rows, baseline_table, strict=True):
            checks.expect(row == reference, "A change altered the complete D execution including gate words")
            q = int(row["state_words"][0] == one)
            u = int(row["input_words"][0] == one)
            checks.expect(row["trace"]["next_state_words"] == ((q ^ u) * one,) and
                          row["trace"]["output_words"] == (q * one,), "XOR/old-state observation mismatch")
            protected_contexts += 1
            protected_site_comparisons += len(row["trace"]["site_traces"])
        tick = owner.tick((input_bit * one,))
        checks.expect(tick["trace"]["output_words"] == (reference_bit * one,), "Output read post-commit state")
        reference_bit ^= input_bit
        checks.expect(owner.state_words == (reference_bit * one,), "Feedback mismatch")
        result = owner.evaluate_a()
        decoded = [Fraction(*p) for p in result["decoded_output"]]
        expected_loss = sum((v-y)**2 for v, y in zip(decoded, (1, -1))) / 2
        checks.expect(expected_loss == Fraction(*result["loss"]), "Recorded objective incorrect")
        changed = receipt["nonzero_stored_change"]
        checks.expect(receipt["effective_rank"] == int(changed), "Single-column effective rank inconsistent")
        if not changed and first_noop is None:
            first_noop = number
        history.append({"update_index": number, "tick": owner.ticks, "input_bit": input_bit,
                        "state_bit": reference_bit, "A_output_words": result["output_words"],
                        "A_loss": result["loss"], "changed": changed,
                        "effective_rank": receipt["effective_rank"]})
    final = owner.evaluate_a()
    checks.expect(Fraction(*final["loss"]) < Fraction(*initial["loss"]), "No observed toy improvement")
    return {"format": fmt, "attempts": len(history), "accepted": owner.accepted_count,
            "nonzero_stored_updates": sum(r["changed"] for r in history), "first_accepted_noop": first_noop,
            "accepted_noops": sum(not r["changed"] for r in history), "refused": 0, "paired_D_ticks": owner.ticks,
            "full_state_input_comparisons": protected_contexts, "D_site_trace_comparisons": protected_site_comparisons,
            "D_word_mismatches": 0, "initial_A": initial, "final_A": final, "history": history,
            "source": xor_source(), "capacity": owner.artifact["capacity"], "cost": owner.artifact["cost"],
            "objective": "half squared error on decoded A output at e1, target (1,-1), SGD rate 1/4"}


def rollback_fixtures(fmt, checks):
    owner = make_owner(fmt, momentum=True, max_updates=1, max_ticks=1)
    gradient = direction(owner, {(0, 0): 1, (2, 3): -1})
    owner.commit(owner.prepare(api.optimizer_request(gradient)))
    before = owner.snapshot()
    moment_cells = before["optimizer_state"]["m"]["rows"]
    event = before["accepted_ledger"][0]
    checks.expect(moment_cells[0][0][0] != 0 and moment_cells[2][3][0] != 0,
                  "Momentum fixture did not populate fixed and editable coordinates")
    checks.expect(event["raw_proposal"]["rows"][0][0][0] != 0 and event["effective_delta"]["rows"][0][0] == [0, 1],
                  "Final update mask did not protect a coordinate with nonzero optimizer moment")
    checks.reject(owner, lambda: owner.prepare(api.optimizer_request(gradient)), "late_update_limit",
                  "Administrative accepted-update budget exhausted")
    owner.tick((0,))
    checks.reject(owner, lambda: owner.tick((0,)), "late_tick_limit", "Administrative execution-tick budget")
    detached = owner.snapshot()
    detached["artifact"]["graph"]["D_calls"].clear()
    detached["optimizer_state"]["m"]["rows"][0][0] = [0, 1]
    checks.expect(owner.snapshot()["optimizer_state"]["m"]["rows"] == moment_cells and
                  bool(owner.artifact["graph"]["D_calls"]), "Snapshot aliases owner data")

    owner = make_owner(fmt)
    req = api.optimizer_request(owner.toy_gradient())
    text = owner.prepare(req)
    original = json.loads(text)
    paths = [
        (("claim",), "BIT"),
        (("source_sha256",), "another source"), (("graph_sha256",), "another graph"),
        (("schedule",), "asynchronous"), (("new_weight_version",), 100),
        (("old_snapshot", "initial_relation", "initial_state_index"), 1),
        (("old_snapshot", "artifact", "graph", "D_calls"), []),
        (("old_snapshot", "artifact", "domain", "A_to_D_feedback"), True),
        (("old_snapshot", "artifact", "layout", "fixed_bias_words", 0), 1),
        (("old_snapshot", "artifact", "graph", "nonlinearities", "D"), "identity"),
        (("old_snapshot", "artifact", "numerical_policy"), "FMA"),
        (("old_snapshot", "expected_source", "next_state"), [["const", 0]]),
        (("old_snapshot", "state_words", 0), 1), (("old_snapshot", "accepted_ledger"), ["forged"]),
        (("new_optimizer_state", "step"), 999), (("new_weight_words", 0, 3), 1),
        (("new_accepted_event", "effective_rank"), 42),
    ]
    for path, value in paths:
        packet = deepcopy(original)
        field = packet["payload"]
        for component in path[:-1]:
            field = field[component]
        field[path[-1]] = value
        if path[0] == "old_snapshot":
            packet["payload"]["old_snapshot_sha256"] = api.digest(packet["payload"]["old_snapshot"])
        packet["payload_sha256"] = api.digest(packet["payload"])
        expected = "Stale complete owned snapshot" if path[0] == "old_snapshot" else "complete semantic"
        checks.reject(owner, lambda: owner.commit(api.canonical(packet)),
                      "rehashed_" + ".".join(map(str, path)), expected)
    checks.reject(owner, lambda: owner.commit(api.canonical({"payload": {"schema": "readonly_numeric",
                      "authorizes_commit": False}, "payload_sha256": "untrusted"})), "read_only_receipt",
                      "Not an exact compiled update candidate")
    for i, j in ((0, 0), (0, 3), (2, 0)):
        endpoint = [list(row) for row in owner.weights]
        endpoint[i][j] = 0 if endpoint[i][j] else 1
        checks.reject(owner, lambda: owner.prepare(api.endpoint_request(endpoint)), f"fixed_cell_{i}_{j}",
                      "Immutable D/cross-region")
    checks.reject(owner, lambda: owner.tick((1,)), "nonboolean_input", "Boolean domain")
    owner.tick((0,))
    checks.reject(owner, lambda: owner.commit(text), "stale_tick", "Stale complete owned snapshot")
    fresh = owner.prepare(req)
    owner.commit(fresh)
    checks.reject(owner, lambda: owner.commit(fresh), "stale_version", "Stale complete owned snapshot")
    return {"format": fmt, "mutated_paths": len(paths), "nonzero_fixed_moment": moment_cells[0][0],
            "nonzero_editable_moment": moment_cells[2][3], "fixed_actual_delta": event["effective_delta"]["rows"][0][0]}


def endpoint_fixtures(fmt, checks):
    owner = make_owner(fmt, q=2)
    fp = api.get_fp()
    format_spec = fp.get_format(fmt)
    one = fp.encode_constant(1, fmt)
    for coordinates in (((2, 3),), ((3, 4),)):
        req = api.ai_request(direction(owner, {coordinates[0]: 1}))
        checks.expect(owner.commit(owner.prepare(req))["effective_rank"] == 1, "Expected rank-one increment")
    last = owner.snapshot()["accepted_ledger"][-1]
    checks.expect(last["prefix_rank"] == 2, "Two disjoint updates should individually have rank one and sum to rank two")
    checks.expect(owner.evaluate_a()["output_words"] == [one, 0], "Second direction should be silent on e1")
    endpoint = [list(row) for row in owner.weights]
    endpoint[2][3] = format_spec.max_finite_word
    endpoint[3][3] = 1
    req = api.endpoint_request(endpoint)
    receipt = owner.commit(owner.prepare(req))
    checks.expect(receipt["optimizer_step"] == 0, "AI endpoint should not increment the optimizer clock")
    observed = owner.evaluate_a()
    checks.expect(observed["output_words"] == [format_spec.max_finite_word, 1], "Fmax/subnormal basis response was lost")
    fmax = fp.decode_word(format_spec.max_finite_word, fmt)
    checks.reject(owner, lambda: owner.prepare(api.ai_request(direction(owner, {(2, 3): fmax}))),
                  "nonrepresentable_large_proposal", "overflow")
    # The full endpoint class permits inward edits even after this particular outward overflow.
    owner.commit(owner.prepare(api.ai_request(direction(owner, {(2, 3): -fmax}))))
    checks.expect(owner.evaluate_a()["output_words"] == [0, 1], "Inward update from Fmax should remain feasible")
    return {"format": fmt, "rank_one_prefix_rank": last["prefix_rank"], "saturated_word": format_spec.max_finite_word,
            "saturated_response_words": observed["output_words"], "after_inward_response": owner.evaluate_a()["output_words"]}


def run_checks():
    if not __debug__:
        raise ValueError("Run verification without -O/-OO")
    start = time.perf_counter()
    checks = Checks()
    rng = random.Random(SEED)
    inputs = [rng.randrange(2) for _ in range(32)]
    history, rollbacks, endpoints = [], [], []
    for fmt in ("BF16", "FP32"):
        history.append(training(fmt, inputs, checks))
        rollbacks.append(rollback_fixtures(fmt, checks))
        endpoints.append(endpoint_fixtures(fmt, checks))
    return {"schema": "dmwk-p2-c1-transactions-v1", "status": "passed", "seed": SEED,
            "checks": checks.count, "expected_refusals": len(checks.refusals), "unexpected_failures": 0,
            "training_runs": history, "rollback_cases": rollbacks, "endpoint_cases": endpoints,
            "refusal_records": checks.refusals, "runtime_seconds": time.perf_counter()-start,
            "scope": "Finite compiled XOR feedback and zero/basis A domain, trusted serial owner",
            "prior_suites_rerun": False, "P2_C2_started": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "transaction_results.json")
    args = parser.parse_args()
    result = run_checks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "checks", "expected_refusals", "runtime_seconds")}))


if __name__ == "__main__":
    main()

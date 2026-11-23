"""Run A3 verification and bind actual results to unchanged dependencies.

This entry point does not launch any A1/A2/P1 verification suite. Four distinct
evidence sets are kept separate, rather than added into a machine-proof claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
SECTIONS = (
    ("exact_linear", "verify_linear_cases"),
    ("pointwise_bounded", "verify_bounded_cases"),
    ("counterexamples", "verify_counterexample_cases"),
    ("bitwise_certificates", "verify_certificate_cases"),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_prior_files():
    baseline = json.loads((ROOT / "dependency_baseline.json").read_text())
    for name, expected in baseline["files"].items():
        path = ROOT.parent / name
        if not path.is_file() or sha(path) != expected:
            raise ValueError("Read-only dependency missing or changed: " + name)
    return len(baseline["files"])


def source_hashes():
    files = sorted(ROOT.glob("*.py")) + [ROOT / "requirements.txt", ROOT / "dependency_baseline.json"]
    return {p.name: sha(p) for p in files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification_results.json")
    args = parser.parse_args()
    started = time.perf_counter()
    report = {
        "schema": "dmwk-p2-a3-verification-v1", "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(), "seed": SEED,
        "planned_sections": [name for name, _ in SECTIONS], "attempted_sections": [],
        "sections": {}, "section_seconds": {}, "SMT_queries": 0,
        "proof_assistant_checked": False, "prior_stage_suites_rerun": False,
        "P2_A4_started": False,
    }
    phase = "preflight"
    try:
        if not __debug__:
            raise ValueError("Verification must run without Python -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("This recorded reference environment requires NumPy 2.3.5")
        report["unchanged_prior_artifacts"] = check_prior_files()
        before = source_hashes()
        report["source_sha256"] = before
        from a3_runtime import environment_metadata
        report["environment"] = environment_metadata()
        for name, module_name in SECTIONS:
            phase = name
            report["attempted_sections"].append(name)
            t0 = time.perf_counter()
            result = importlib.import_module(module_name).run_checks()
            if type(result) is not dict or result.get("status") != "passed":
                raise ValueError("Section did not pass: " + name)
            if result.get("seed", SEED) != SEED:
                raise ValueError("Unexpected seed: " + name)
            if result.get("failures", 0) != 0 or result.get("unexpected_failures", 0) != 0:
                raise ValueError("Section reported an unexpected failure: " + name)
            json.dumps(result, allow_nan=False)
            report["sections"][name] = result
            report["section_seconds"][name] = time.perf_counter() - t0
        phase = "postflight"
        if source_hashes() != before:
            raise ValueError("A3 source changed during this execution")
        if check_prior_files() != report["unchanged_prior_artifacts"]:
            raise ValueError("Prior-file inventory changed")
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["failure"] = {"phase": phase, "type": type(exc).__name__, "message": str(exc)}
    report["completed_sections"] = len(report["sections"])
    report["unexecuted_sections"] = [n for n, _ in SECTIONS if n not in report["attempted_sections"]]
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["total_seconds"] = time.perf_counter() - started
    report["evidence_scope"] = {
        "exact_linear": "Exact checks on finite matrices; universal basis/span theorem is separately proved by hand.",
        "pointwise_bounded": "A posteriori absolute bounds for specified stored inputs/endpoints only; never commit permission.",
        "counterexamples": "Explicit refutations of overbroad implications under specified arithmetic graphs.",
        "bitwise_certificates": "Complete finite registered models; all-finite-time program consequence needs the separate closure/induction proof.",
        "BF16": "Software RNE; no native BF16 certification.",
        "FP32": "Local CPU scalar operations audited by exact rational RNE; no universal backend certificate.",
        "excluded": "GPU, general concurrency, arbitrary compiler optimizations, full proof-assistant verification, general P2-C composition.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "completed_sections": report["completed_sections"],
                      "unexecuted_sections": report["unexecuted_sections"],
                      "seconds": report["total_seconds"], "failure": report.get("failure"),
                      "output": str(args.output)}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

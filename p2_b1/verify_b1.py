"""Aggregate B1 evidence without rerunning or modifying prior research."""
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
SECTIONS = (("constraints_and_regressions", "verify_constraints"),
            ("optimization_experiments", "verify_training"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_files():
    baseline = json.loads((ROOT / "dependency_baseline.json").read_text())
    excluded = set(baseline["excluded_directories"])
    for name, digest in baseline["files"].items():
        path = ROOT.parent / name
        if not path.is_file() or sha(path) != digest:
            raise ValueError("Previous artifact missing or changed: " + name)
    roots = {Path(name).parts[0] for name in baseline["files"]}
    current = {str(p.relative_to(ROOT.parent)) for dirname in roots
               for p in (ROOT.parent / dirname).rglob("*")
               if p.is_file() and not (set(p.relative_to(ROOT.parent).parts) & excluded)}
    if current != set(baseline["files"]):
        raise ValueError("Previous nonexcluded artifact inventory changed")
    return len(current)


def sources():
    paths = sorted(ROOT.glob("*.py")) + [ROOT / "requirements.txt", ROOT / "dependency_baseline.json"]
    return {p.name: sha(p) for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification_results.json")
    args = parser.parse_args()
    start = time.perf_counter()
    phase = "preflight"
    result = {"schema": "dmwk-p2-b1-verification-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "planned_sections": [n for n, _ in SECTIONS], "attempted_sections": [],
              "sections": {}, "section_seconds": {}, "SMT_queries": 0,
              "proof_assistant_checked": False, "prior_stage_suites_rerun": False,
              "P2_B2_started": False}
    try:
        if not __debug__:
            raise ValueError("Run verification without -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("Recorded reference requires NumPy 2.3.5")
        result["unchanged_prior_artifacts"] = previous_files()
        before = sources()
        result["source_sha256"] = before
        from b1_runtime import environment_metadata
        result["environment"] = environment_metadata()
        for name, module_name in SECTIONS:
            phase = name
            result["attempted_sections"].append(name)
            section_start = time.perf_counter()
            section = importlib.import_module(module_name).run_checks()
            if type(section) is not dict or section.get("status") != "passed":
                raise ValueError("Section did not pass: " + name)
            if section.get("seed", SEED) != SEED:
                raise ValueError("Unexpected seed: " + name)
            if section.get("unexpected_failures", 0) != 0:
                raise ValueError("Unexpected failures: " + name)
            json.dumps(section, allow_nan=False)
            result["sections"][name] = section
            result["section_seconds"][name] = time.perf_counter() - section_start
        phase = "postflight"
        if sources() != before:
            raise ValueError("B1 source changed during execution")
        if previous_files() != result["unchanged_prior_artifacts"]:
            raise ValueError("Prior artifact inventory changed")
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"phase": phase, "type": type(exc).__name__, "message": str(exc)}
    result["completed_sections"] = len(result["sections"])
    result["unexecuted_sections"] = [n for n, _ in SECTIONS if n not in result["attempted_sections"]]
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    result["total_seconds"] = time.perf_counter() - start
    result["evidence_scope"] = {
        "exact": "Finite checks corroborate handwritten conditional projection/parameterization/transaction proofs.",
        "optimization": "Toy declared A objectives, actual stored endpoints and complete local D domains; no universal learning or long-term guarantee.",
        "optimizer": "Declared host proposal arithmetic is separate from protected BF16/FP32 execution.",
        "BF16": "Software RNE, not native BF16 certification.",
        "FP32": "Local scalar CPU operations audited against exact rational RNE.",
        "transactions": "Trusted serial combined-state publication and refusal rollback; no cryptographic caller authentication or general concurrency.",
        "excluded": "GPU, arbitrary compiler optimization, process-failure atomicity, full machine proof and later P2 stages."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "completed_sections": result["completed_sections"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

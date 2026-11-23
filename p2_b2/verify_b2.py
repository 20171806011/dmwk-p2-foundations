"""Aggregate current B2 evidence while preserving previous research files."""
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
SECTIONS = (("geometry_numerics_and_boundaries", "verify_bounds"),
            ("bounded_certificates_and_B1_boundary", "verify_certificates"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_files():
    baseline = json.loads((ROOT / "dependency_baseline.json").read_text())
    for name, digest in baseline["files"].items():
        path = ROOT.parent / name
        if not path.is_file() or sha(path) != digest:
            raise ValueError("Previous artifact missing or changed: " + name)
    roots = {Path(n).parts[0] for n in baseline["files"]}
    excluded = set(baseline["excluded_directories"])
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
    result = {"schema": "dmwk-p2-b2-verification-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "planned_sections": [n for n, _ in SECTIONS], "attempted_sections": [],
              "sections": {}, "section_seconds": {}, "SMT_queries": 0,
              "proof_assistant_checked": False, "prior_stage_suites_rerun": False,
              "P2_B3_started": False}
    try:
        if not __debug__:
            raise ValueError("Run verification without -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("Recorded reference requires NumPy 2.3.5")
        result["unchanged_prior_artifacts"] = previous_files()
        before = sources()
        result["source_sha256"] = before
        from b2_runtime import environment_metadata
        result["environment"] = environment_metadata()
        for name, module_name in SECTIONS:
            phase = name
            result["attempted_sections"].append(name)
            t0 = time.perf_counter()
            value = importlib.import_module(module_name).run_checks()
            if type(value) is not dict or value.get("status") != "passed":
                raise ValueError("Section did not pass: " + name)
            if value.get("seed", SEED) != SEED or value.get("unexpected_failures", 0) != 0:
                raise ValueError("Unexpected seed or failure: " + name)
            json.dumps(value, allow_nan=False)
            result["sections"][name] = value
            result["section_seconds"][name] = time.perf_counter() - t0
        phase = "postflight"
        if sources() != before:
            raise ValueError("B2 source changed during execution")
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
        "exact": "Conditional handwritten bounds; finite exact checks are separate.",
        "execution": "Independent old/new fixed-order separate-RNE affine executions with actual endpoint differences.",
        "domains": "Point, complete registered finite envelope and analytic box claims retain separate coverage/totality premises.",
        "receipts": "Read-only numeric budget evidence; no BIT/ALG_AND_BIT or live commit authority.",
        "B1": "Frozen recorded endpoints receive new B2 analysis; earlier optimizer experiments are not rerun.",
        "backends": "Software BF16 and audited local scalar CPU FP32 only.",
        "excluded": "GPU, native BF16, general concurrency, arbitrary compiler changes, general learning and later-stage composition."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "completed_sections": result["completed_sections"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

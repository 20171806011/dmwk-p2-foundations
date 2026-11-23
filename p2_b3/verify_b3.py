"""Aggregate only the new B3 suites, binding sources and prior artifacts."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
SECTIONS = (("propagation_and_domains", "verify_propagation.py"),
            ("read_only_receipts_and_rollback", "verify_certificates.py"),
            ("control_flow_and_rounding", "verify_control.py"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_files():
    b = json.loads((ROOT / "dependency_baseline.json").read_text())
    excluded = set(b["excluded_directories"])
    for n, digest in b["files"].items():
        f = ROOT.parent / n
        if not f.is_file() or sha(f) != digest:
            raise ValueError("Previous artifact changed: " + n)
    current = {str(f.relative_to(ROOT.parent)) for d in b["root_directories"]
               for f in (ROOT.parent / d).rglob("*")
               if f.is_file() and not (set(f.relative_to(ROOT.parent).parts) & excluded)}
    current.update(f.name for f in ROOT.parent.glob("P1_*") if f.is_file())
    if current != set(b["files"]):
        raise ValueError("Previous nonexcluded inventory changed")
    return len(current)


def sources():
    files = sorted(ROOT.glob("*.py")) + [ROOT / "requirements.txt", ROOT / "dependency_baseline.json"]
    return {f.name: sha(f) for f in files}


def new_section(filename):
    path = (ROOT / filename).resolve()
    name = "_dmwk_b3_section_" + path.stem
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != path:
            raise ValueError("Section source provenance mismatch")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load current section: " + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ValueError("Section source provenance mismatch")
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification_results.json")
    args = parser.parse_args()
    start = time.perf_counter()
    phase = "preflight"
    result = {"schema": "dmwk-p2-b3-main-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "planned_sections": [n for n, _ in SECTIONS], "attempted_sections": [],
              "sections": {}, "section_seconds": {}, "prior_stage_suites_rerun": False,
              "prior_optimizer_trajectories_regenerated": False, "SMT_queries": 0,
              "proof_assistant_checked": False, "P2_B4_started": False}
    try:
        if not __debug__:
            raise ValueError("Run verification without -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("Recorded reference requires NumPy 2.3.5")
        result["unchanged_prior_artifacts"] = previous_files()
        before = sources()
        result["source_sha256"] = before
        from b3_runtime import environment_metadata
        result["environment"] = environment_metadata()
        for name, filename in SECTIONS:
            phase = name
            result["attempted_sections"].append(name)
            t0 = time.perf_counter()
            value = new_section(filename).run_checks()
            if type(value) is not dict or value.get("status") != "passed":
                raise ValueError("Section did not pass: " + name)
            if value.get("seed", SEED) != SEED or value.get("unexpected_failures", 0) != 0:
                raise ValueError("Unexpected seed or failure: " + name)
            json.dumps(value, allow_nan=False)
            result["sections"][name] = value
            result["section_seconds"][name] = time.perf_counter() - t0
        phase = "postflight"
        if sources() != before:
            raise ValueError("B3 source changed during execution")
        previous_files()
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"phase": phase, "type": type(exc).__name__, "message": str(exc)}
    result["completed_sections"] = len(result["sections"])
    result["unexecuted_sections"] = [n for n, _ in SECTIONS if n not in result["attempted_sections"]]
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    result["total_seconds"] = time.perf_counter() - start
    result["evidence_scope"] = {
        "mathematics": "Conditional handwritten nonlinear/layer/time bounds with joint domain closure.",
        "execution": "Software BF16 and available scalar CPU FP32, fixed separate arithmetic and canonical zeros.",
        "quantifiers": "Universal conditional box/tube proofs, finite complete fixtures and seeds remain distinct.",
        "receipts": "Read-only bounded-output evidence; no BIT/ALG_AND_BIT authority or live budget commits.",
        "excluded": "GPU, native BF16, general concurrency, arbitrary compiler changes, universal learning and B4."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "completed_sections": result["completed_sections"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

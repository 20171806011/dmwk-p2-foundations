"""Aggregate new B4 evidence, preserving predecessor content and inventory."""
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
SECTIONS = (("capacity_and_history", "verify_capacity.py"),
            ("switching_and_budgets", "verify_switching.py"),
            ("transactions_and_learning", "verify_transactions.py"))


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
    paths = sorted(ROOT.glob("*.py")) + [ROOT / "requirements.txt", ROOT / "dependency_baseline.json"]
    return {p.name: sha(p) for p in paths}


def new_section(filename):
    path = (ROOT / filename).resolve()
    name = "_dmwk_b4_section_" + path.stem
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != path:
            raise ValueError("Wrong current-section source")
        return module
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load B4 section: " + filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ValueError("Wrong current-section source")
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification_results.json")
    args = parser.parse_args()
    started = time.perf_counter()
    phase = "preflight"
    result = {"schema": "dmwk-p2-b4-main-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "planned_sections": [n for n, _ in SECTIONS], "attempted_sections": [],
              "sections": {}, "section_seconds": {}, "prior_stage_suites_rerun": False,
              "prior_optimizer_trajectories_regenerated": False, "SMT_queries": 0,
              "proof_assistant_checked": False, "P2_C1_started": False}
    try:
        if not __debug__:
            raise ValueError("Run verification without -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("Recorded reference requires NumPy 2.3.5")
        result["unchanged_prior_artifacts"] = previous_files()
        before = sources()
        result["source_sha256"] = before
        from b4_runtime import environment_metadata
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
            raise ValueError("B4 source changed during execution")
        previous_files()
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"phase": phase, "type": type(exc).__name__, "message": str(exc)}
    result["completed_sections"] = len(result["sections"])
    result["unexecuted_sections"] = [n for n, _ in SECTIONS if n not in result["attempted_sections"]]
    result["completed_utc"] = datetime.now(timezone.utc).isoformat()
    result["total_seconds"] = time.perf_counter() - started
    result["evidence_scope"] = {
        "mathematics": "Conditional repeated-update capacity and switched-system proofs; not machine-checked.",
        "execution": "Software BF16 and local audited CPU FP32 under fixed graphs and canonical zeros.",
        "exact_D": "New serial integration keeps existing complete-domain BIT/ALG_AND_BIT authorization.",
        "numerical_A": "Recomputed history/domain/rounding budgets are read-only evidence, not commit authority.",
        "finite": "Named finite families/histories and seeds remain separate from all-time hypotheses.",
        "excluded": "GPU, native BF16, general concurrency, arbitrary compiler/FMA changes, universal learning and C1."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "completed_sections": result["completed_sections"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

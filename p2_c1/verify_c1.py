"""Aggregate only C1 verification with predecessor preservation and source binding."""
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
SECTIONS = (("compiler_and_semantics", "verify_compiler.py"),
            ("geometric_comparison", "verify_geometry.py"),
            ("layout_selection", "verify_layout.py"),
            ("publication_and_learning", "verify_transactions.py"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def previous_files():
    b = json.loads((ROOT / "dependency_baseline.json").read_text())
    excluded = set(b["excluded_directories"])
    for name, digest in b["files"].items():
        f = ROOT.parent / name
        if not f.is_file() or sha(f) != digest:
            raise ValueError("Previous artifact changed: " + name)
    current = {str(f.relative_to(ROOT.parent)) for dirname in b["root_directories"]
               for f in (ROOT.parent / dirname).rglob("*")
               if f.is_file() and not (set(f.relative_to(ROOT.parent).parts) & excluded)}
    current.update(f.name for f in ROOT.parent.glob("P1_*") if f.is_file())
    if current != set(b["files"]):
        raise ValueError("Predecessor nonexcluded inventory changed")
    return len(current)


def sources():
    paths = sorted(ROOT.glob("*.py")) + [ROOT / "requirements.txt", ROOT / "dependency_baseline.json", ROOT / "example_request.json"]
    return {p.name: sha(p) for p in paths}


def new_section(filename):
    path = (ROOT / filename).resolve()
    name = "_dmwk_c1_section_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load current C1 verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ValueError("Verifier source mismatch")
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "verification_results.json")
    args = parser.parse_args()
    start = time.perf_counter()
    result = {"schema": "dmwk-p2-c1-main-v1", "status": "running", "seed": SEED,
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "planned_sections": [n for n, _ in SECTIONS], "attempted_sections": [],
              "sections": {}, "section_seconds": {}, "prior_stage_suites_rerun": False,
              "prior_optimizer_trajectories_regenerated": False,
              "SMT_queries": 0, "general_proofs_machine_checked": False, "P2_C2_started": False}
    phase = "preflight"
    try:
        if not __debug__:
            raise ValueError("Run verification without -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("Recorded reference requires NumPy 2.3.5")
        result["unchanged_prior_artifacts"] = previous_files()
        before = sources()
        result["source_sha256"] = before
        from c1_runtime import environment_metadata
        result["environment"] = environment_metadata()
        for name, filename in SECTIONS:
            phase = name
            result["attempted_sections"].append(name)
            t0 = time.perf_counter()
            section = new_section(filename).run_checks()
            if type(section) is not dict or section.get("status") != "passed":
                raise ValueError("Section failed: " + name)
            if section.get("seed") != SEED or section.get("unexpected_failures", 0) != 0:
                raise ValueError("Invalid seed or unexpected failures: " + name)
            json.dumps(section, allow_nan=False)
            result["sections"][name] = section
            result["section_seconds"][name] = time.perf_counter() - t0
        phase = "postflight"
        if before != sources():
            raise ValueError("C1 source changed during verification")
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
        "theory": "Conditional handwritten proofs for a closed source-to-graph-and-bank compiler.",
        "finite": "Named complete small source families/domains and separately seeded cases; not all-program machine proof.",
        "execution": "Software BF16 and audited local CPU FP32 with fixed separate multiply/add and canonical zeros.",
        "publication": "New compiled-source structural ALG_AND_BIT gate and trusted serial whole-owner rollback.",
        "geometry": "Axis-aligned structural projection certified; general rotations/projections do not gain BIT authority.",
        "excluded": "GPU/native BF16/general concurrency/crashes/arbitrary compiler/FMA/universal learning/C2-C4."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "completed_sections": result["completed_sections"],
                      "seconds": result["total_seconds"], "failure": result.get("failure"),
                      "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

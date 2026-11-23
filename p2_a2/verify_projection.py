"""Run the three P2-A2 routes and bind their actual evidence to source files.

This driver never runs a P1/P2-A1 suite or grants update permission from a
numerical residual. Independent checks have their own separate entry point.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import platform
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114
PLAN = (
    ("exact_algebra", "verify_exact_cases"),
    ("numerical_bounds", "verify_numerical_cases"),
    ("structural_bit_exact", "verify_safe_cases"),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes(p1_root: Path) -> dict:
    result = {"p2_a2/" + p.name: digest(p) for p in sorted(ROOT.glob("*.py"))}
    for p in (ROOT / "requirements.txt", ROOT / "dependency_baseline.json"):
        if p.is_file():
            result["p2_a2/" + p.name] = digest(p)
    for name in ("p1_c3/execution.py", "p1_b2/canonicalize.py"):
        result["p1_reference/" + name] = digest(p1_root / name)
    return result


def check_previous_artifacts(p1_root: Path) -> int:
    snapshot = json.loads((ROOT / "dependency_baseline.json").read_text())
    for relative, expected in snapshot["files"].items():
        if relative.startswith("dmwk-p1-foundations/"):
            path = p1_root / relative.removeprefix("dmwk-p1-foundations/")
        else:
            path = ROOT.parent / relative
        if not path.is_file() or digest(path) != expected:
            raise ValueError("Read-only prior artifact missing or changed: " + relative)
    original = ROOT / "P2_A2_User_Plan_Original.txt"
    if digest(original) != snapshot["request_sha256"]:
        raise ValueError("Preserved user request changed")
    return len(snapshot["files"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1-root", type=Path,
                        default=ROOT.parent / "dmwk-p1-foundations")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "verification_results.json")
    args = parser.parse_args()
    started = time.perf_counter()
    report = {
        "schema": "dmwk-p2-a2-verification-v1",
        "status": "running",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "planned_sections": [name for name, _ in PLAN],
        "attempted_sections": [],
        "sections": {},
        "section_seconds": {},
        "SMT_queries": 0,
        "proof_assistant_checked": False,
        "prior_stage_suites_rerun": False,
        "P2_A3_started": False,
    }
    error = None
    phase = "preflight"
    try:
        if not __debug__:
            raise ValueError("Run verification without Python -O/-OO")
        import numpy as np
        if np.__version__ != "2.3.5":
            raise ValueError("This version-bound reference requires NumPy 2.3.5")
        from p1_runtime import configure_p1_root, get_fp
        p1_root = configure_p1_root(args.p1_root)
        report["unchanged_prior_artifacts"] = check_previous_artifacts(p1_root)
        before = source_hashes(p1_root)
        report["source_sha256"] = before
        report["environment"] = {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "p1_reference_root": str(p1_root),
            "backend_metadata": get_fp().backend_metadata(),
            "svd_precision_note": "FP32 uses the explicit version-bound f->fff gufunc; output dtype alone is not a precision certificate.",
        }
        for name, module_name in PLAN:
            phase = name
            report["attempted_sections"].append(name)
            t0 = time.perf_counter()
            result = importlib.import_module(module_name).run_checks()
            if type(result) is not dict or result.get("status") != "passed":
                raise ValueError("Verification section did not pass: " + name)
            if (result.get("failures", 0) != 0
                    or result.get("unexpected_failures", 0) != 0
                    or result.get("seed", SEED) != SEED):
                raise ValueError("Unexpected failure or seed: " + name)
            # Enforce standard JSON: diagnostic infinity must be represented
            # explicitly, never emitted as a nonstandard numeric NaN/Infinity.
            json.dumps(result, allow_nan=False)
            report["sections"][name] = result
            report["section_seconds"][name] = time.perf_counter() - t0
        phase = "postflight_integrity"
        if source_hashes(p1_root) != before:
            raise ValueError("Source changed during aggregate verification")
        if check_previous_artifacts(p1_root) != report["unchanged_prior_artifacts"]:
            raise ValueError("Prior-artifact inventory changed during verification")
        report["status"] = "passed"
    except Exception as exc:
        error = exc
        report["status"] = "failed"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc),
                             "phase": phase}
    report["completed_sections"] = len(report["sections"])
    report["unexecuted_sections"] = [name for name, _ in PLAN
                                      if name not in report["attempted_sections"]]
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    report["total_seconds"] = time.perf_counter() - started
    report["evidence_scope"] = {
        "theorems": "Four separate handwritten conditional proofs, not machine proofs inferred from this run.",
        "exact": "Explicit finite rational cases, exhaustive small matrices, and seeded properties.",
        "numeric": "Exact residual accounting for actual stored values; pointwise bounds, not automatic all-time bitwise safety.",
        "structural": "Finite tests of the fixed sparse 2x2 trusted local reference; all-finite-time conclusion is the separate T4 induction.",
        "BF16": "Software RNE, not native BF16 hardware.",
        "FP32": "Local scalar CPU execution audited against exact rounding; local explicit single-precision SVD dispatch, not a certified library/toolchain.",
        "excluded": "GPU, arbitrary dense/FMA/reassociated kernels, concurrent or hostile runtime, universal nonlinear learning, later P2 stages.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"],
                      "completed_sections": report["completed_sections"],
                      "unexecuted_sections": report["unexecuted_sections"],
                      "seconds": report["total_seconds"],
                      "output": str(args.output),
                      "failure": report.get("failure")}))
    return 1 if error is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())

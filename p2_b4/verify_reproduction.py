"""Reproduce only B4 from a foreign cwd, compare evidence, and audit provenance."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic(value):
    """Remove wall-clock metadata only; preserve seeds, values, counts and paths."""
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items()
                if not (k.endswith("_seconds") or k in ("started_utc", "completed_utc"))}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


def run(script, output, flags=()):
    t0 = time.perf_counter()
    command = [sys.executable, "-B", *flags, str(ROOT / script), "--output", str(ROOT / output)]
    proc = subprocess.run(command, cwd="/tmp", capture_output=True, text=True, timeout=600)
    return {"command": command, "cwd": "/tmp", "exit_code": proc.returncode,
            "elapsed_seconds": time.perf_counter() - t0,
            "stdout": proc.stdout[-5000:], "stderr": proc.stderr[-5000:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reproduction_driver_results.json")
    args = parser.parse_args()
    result = {"schema": "dmwk-p2-b4-reproduction-v1", "status": "running",
              "foreign_cwd": "/tmp", "comparisons": [], "runs": [],
              "prior_suites_rerun": False, "P2_C1_started": False}
    start = time.perf_counter()
    try:
        if not __debug__:
            raise ValueError("Run reproduction driver without optimization")
        import verify_b4 as v
        result["unchanged_prior_artifacts"] = v.previous_files()
        protected = ("verification_results.json", "independent_results.json",
                     "capacity_results.json", "switching_results.json", "transaction_results.json")
        result["producer_sha256"] = {name: sha(ROOT / name) for name in protected}
        before = v.sources()
        result["source_sha256"] = before
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run, "verify_b4.py", "reproduction_results.json"),
                       pool.submit(run, "verify_independent.py", "independent_reproduction_results.json")]
            result["runs"] = [future.result() for future in futures]
        if any(r["exit_code"] != 0 for r in result["runs"]):
            raise ValueError("A foreign-cwd reproduction failed")
        pairs = [("verification_results.json", "reproduction_results.json"),
                 ("independent_results.json", "independent_reproduction_results.json")]
        for left, right in pairs:
            a, b = (json.loads((ROOT / p).read_text()) for p in (left, right))
            equal = semantic(a) == semantic(b)
            result["comparisons"].append({"left": left, "right": right, "equal_except_time": equal})
            if a.get("status") != "passed" or not equal:
                raise ValueError("Semantic reproduction differs: " + left)
        main_record = json.loads((ROOT / "verification_results.json").read_text())
        for section, filename in (("capacity_and_history", "capacity_results.json"),
                                  ("switching_and_budgets", "switching_results.json"),
                                  ("transactions_and_learning", "transaction_results.json")):
            producer = json.loads((ROOT / filename).read_text())
            equal = semantic(main_record["sections"][section]) == semantic(producer)
            result["comparisons"].append({"left": filename,
                "right": "verification_results.json#/sections/" + section,
                "equal_except_time": equal})
            if not equal:
                raise ValueError("Standalone producer differs from aggregate: " + filename)
        result["optimized_preflight"] = []
        for flag, name in (("-O", "optimized_O_results.json"), ("-OO", "optimized_OO_results.json")):
            receipt = run("verify_b4.py", name, (flag,))
            data = json.loads((ROOT / name).read_text())
            correct = (receipt["exit_code"] == 1 and data.get("status") == "failed" and
                       data.get("attempted_sections") == [] and
                       data.get("failure", {}).get("message") == "Run verification without -O/-OO")
            result["optimized_preflight"].append({"flag": flag, "rejected_before_tests": correct})
            if not correct:
                raise ValueError("Optimized interpreter was not refused at preflight")
        if v.sources() != before:
            raise ValueError("B4 sources changed during reproduction")
        for name, digest in result["producer_sha256"].items():
            if sha(ROOT / name) != digest:
                raise ValueError("Primary evidence overwritten during reproduction: " + name)
        if main_record.get("source_sha256") != before:
            raise ValueError("Aggregate source provenance is stale")
        v.previous_files()
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    result["total_seconds"] = time.perf_counter() - start
    result["scope"] = "B4 finite reproduction and provenance only; no new general theorem or prior-stage replay"
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "comparisons": len(result["comparisons"]),
                      "failure": result.get("failure"), "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

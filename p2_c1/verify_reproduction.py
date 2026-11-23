"""Reproduce the new C1 primary/independent records from /tmp; do not rerun old stages."""
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


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def semantic(x):
    if isinstance(x, dict):
        return {k: semantic(v) for k, v in x.items()
                if not (k.endswith("_seconds") or k in ("started_utc", "completed_utc"))}
    if isinstance(x, list): return [semantic(v) for v in x]
    return x


def run(script, output, flags=()):
    start = time.perf_counter()
    command = [sys.executable, "-B", *flags, str(ROOT / script), "--output", str(ROOT / output)]
    p = subprocess.run(command, cwd="/tmp", capture_output=True, text=True, timeout=900)
    return {"command": command, "cwd": "/tmp", "exit_code": p.returncode,
            "elapsed_seconds": time.perf_counter() - start,
            "stdout": p.stdout[-5000:], "stderr": p.stderr[-5000:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reproduction_driver_results.json")
    args = parser.parse_args()
    result = {"schema": "dmwk-p2-c1-reproduction-v1", "status": "running",
              "foreign_cwd": "/tmp", "comparisons": [], "runs": [],
              "prior_suites_rerun": False, "P2_C2_started": False}
    started = time.perf_counter()
    try:
        if not __debug__: raise ValueError("Run reproduction driver without optimization")
        import verify_c1 as primary
        result["unchanged_prior_artifacts"] = primary.previous_files()
        files = ("verification_results.json", "independent_results.json",
                 "compiler_results.json", "geometric_results.json", "layout_results.json", "transaction_results.json")
        result["producer_sha256"] = {n: sha(ROOT / n) for n in files}
        before = primary.sources()
        result["source_sha256"] = before
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run, "verify_c1.py", "reproduction_results.json"),
                       pool.submit(run, "verify_independent.py", "independent_reproduction_results.json")]
            result["runs"] = [f.result() for f in futures]
        if any(x["exit_code"] != 0 for x in result["runs"]):
            raise ValueError("A foreign-directory run failed")
        for left, right in (("verification_results.json", "reproduction_results.json"),
                            ("independent_results.json", "independent_reproduction_results.json")):
            a, b = [json.loads((ROOT / n).read_text()) for n in (left, right)]
            equal = semantic(a) == semantic(b)
            result["comparisons"].append({"left": left, "right": right, "equal_except_time": equal})
            if a.get("status") != "passed" or not equal:
                raise ValueError("Semantic reproduction mismatch: " + left)
        main_record = json.loads((ROOT / "verification_results.json").read_text())
        for section, filename in (("compiler_and_semantics", "compiler_results.json"),
                                  ("geometric_comparison", "geometric_results.json"),
                                  ("layout_selection", "layout_results.json"),
                                  ("publication_and_learning", "transaction_results.json")):
            producer = json.loads((ROOT / filename).read_text())
            equal = semantic(producer) == semantic(main_record["sections"][section])
            result["comparisons"].append({"left": filename, "right": "verification_results.json#/sections/"+section,
                                          "equal_except_time": equal})
            if not equal: raise ValueError("Producer/aggregate mismatch: " + filename)
        result["optimized_preflight"] = []
        for flag, filename in (("-O", "optimized_O_results.json"), ("-OO", "optimized_OO_results.json")):
            receipt = run("verify_c1.py", filename, (flag,))
            d = json.loads((ROOT / filename).read_text())
            ok = (receipt["exit_code"] == 1 and d.get("status") == "failed" and
                  d.get("attempted_sections") == [] and
                  d.get("failure", {}).get("message") == "Run verification without -O/-OO")
            result["optimized_preflight"].append({"flag": flag, "rejected_before_tests": ok})
            if not ok: raise ValueError("Optimized interpreter preflight did not reject")
        if before != primary.sources() or main_record["source_sha256"] != before:
            raise ValueError("C1 sources changed or aggregate binding stale")
        for n, h in result["producer_sha256"].items():
            if sha(ROOT / n) != h: raise ValueError("Primary evidence overwritten: " + n)
        ind = json.loads((ROOT / "independent_results.json").read_text())
        for group in ("source_sha256", "producer_sha256"):
            for n, h in ind.get(group, {}).items():
                if sha(ROOT / n) != h: raise ValueError("Independent binding stale: " + n)
        primary.previous_files()
        result["status"] = "passed"
    except Exception as exc:
        result["status"] = "failed"
        result["failure"] = {"type": type(exc).__name__, "message": str(exc)}
    result["total_seconds"] = time.perf_counter() - started
    result["scope"] = "Same-host foreign-working-directory reproduction and content provenance; no new theorem/backend certification"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "comparisons": len(result["comparisons"]),
                      "failure": result.get("failure"), "output": str(args.output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__": raise SystemExit(main())

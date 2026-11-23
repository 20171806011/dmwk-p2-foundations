"""Explicit read-only dependencies for B2; previous test suites are excluded."""
from __future__ import annotations
import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
ALLOWED = {
    "p2_a3": frozenset(("a3_runtime", "certificate_kernel", "linear_contracts", "bounded_contracts")),
    "p2_a4": frozenset(("a4_runtime", "capacity_algebra", "capacity_discrete", "structural_budget")),
    "p2_b1": frozenset(("b1_runtime", "constrained_updates", "optimizer_kernel")),
}


def _load(stage, name):
    if type(name) is not str or name not in ALLOWED[stage]:
        raise ValueError("Undeclared dependency; prior test suites are excluded")
    directory = ROOT.parent / stage
    expected = (directory / (name + ".py")).resolve()
    if not expected.is_file():
        raise ValueError("Missing read-only dependency: " + str(expected))
    if name in sys.modules:
        actual = getattr(sys.modules[name], "__file__", None)
        if actual is None or Path(actual).resolve() != expected:
            raise ValueError("Unexpected dependency provenance: " + name)
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    module = importlib.import_module(name)
    if Path(module.__file__).resolve() != expected:
        raise ValueError("Unexpected imported dependency: " + name)
    return module


def load_a3(name):
    return _load("p2_a3", name)


def load_a4(name):
    return _load("p2_a4", name)


def load_b1(name):
    return _load("p2_b1", name)


def load_a2(name):
    return load_a3("a3_runtime").load_a2(name)


def get_fp():
    return load_a3("a3_runtime").get_fp()


def environment_metadata():
    result = load_a3("a3_runtime").environment_metadata()
    for stage in ("p2_a3", "p2_a4", "p2_b1"):
        result[stage + "_root"] = str(ROOT.parent / stage)
    result["prior_stage_suites_rerun"] = False
    result["bounds"] = "Exact rational data and outward rational norm bounds; no SVD estimate is treated as certified."
    return result

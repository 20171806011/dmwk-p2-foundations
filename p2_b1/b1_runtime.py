"""Read-only arithmetic and contract dependencies for the B1 continuation.

Old verification modules are deliberately absent from the allow lists.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
_A3 = frozenset(("a3_runtime", "certificate_kernel", "linear_contracts", "bounded_contracts"))
_A4 = frozenset(("a4_runtime", "capacity_algebra", "capacity_discrete", "structural_budget"))


def _load(stage, name, allowed):
    if type(name) is not str or name not in allowed:
        raise ValueError("Undeclared dependency; prior verification suites are not imported")
    directory = ROOT.parent / stage
    expected = (directory / (name + ".py")).resolve()
    if not expected.is_file():
        raise ValueError("Missing read-only dependency: " + str(expected))
    if name in sys.modules:
        found = getattr(sys.modules[name], "__file__", None)
        if found is None or Path(found).resolve() != expected:
            raise ValueError("Unexpected dependency provenance: " + name)
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    module = importlib.import_module(name)
    if Path(module.__file__).resolve() != expected:
        raise ValueError("Unexpected imported dependency: " + name)
    return module


def load_a3(name):
    return _load("p2_a3", name, _A3)


def load_a4(name):
    return _load("p2_a4", name, _A4)


def load_a2(name):
    return load_a3("a3_runtime").load_a2(name)


def get_fp():
    return load_a3("a3_runtime").get_fp()


def environment_metadata():
    result = load_a3("a3_runtime").environment_metadata()
    result["A3_root"] = str(ROOT.parent / "p2_a3")
    result["A4_root"] = str(ROOT.parent / "p2_a4")
    result["prior_stage_suites_rerun"] = False
    result["optimizer_proposals"] = "Separately specified by B1; protected arithmetic metadata does not certify host optimizer operations."
    return result

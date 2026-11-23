"""Canonical read-only dependencies for this A4 continuation, not old suites."""
from __future__ import annotations
import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
A3 = ROOT.parent / "p2_a3"
_ALLOWED_A3 = frozenset(("a3_runtime", "certificate_kernel", "linear_contracts", "bounded_contracts"))


def load_a3(name):
    if type(name) is not str or name not in _ALLOWED_A3:
        raise ValueError("Only declared prior arithmetic/certificate modules may be loaded")
    expected = (A3 / (name + ".py")).resolve()
    if not expected.is_file():
        raise ValueError("Missing read-only A3 dependency: " + name)
    if name in sys.modules:
        actual = getattr(sys.modules[name], "__file__", None)
        if actual is None or Path(actual).resolve() != expected:
            raise ValueError("Unexpected prior module provenance: " + name)
    if str(A3) not in sys.path:
        sys.path.insert(0, str(A3))
    module = importlib.import_module(name)
    if Path(module.__file__).resolve() != expected:
        raise ValueError("Unexpected imported dependency: " + name)
    return module


def load_a2(name):
    return load_a3("a3_runtime").load_a2(name)


def get_fp():
    return load_a3("a3_runtime").get_fp()


def environment_metadata():
    data = load_a3("a3_runtime").environment_metadata()
    data["A3_root"] = str(A3)
    data["prior_stage_suites_rerun"] = False
    return data

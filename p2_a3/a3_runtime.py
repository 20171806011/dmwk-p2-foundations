"""Resolve the existing read-only A2/P1 arithmetic dependencies explicitly.

No previous-stage verifier is importable through this helper. File identity is
checked again by the A3 verification driver against its saved baseline.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
A2_ROOT = ROOT.parent / "p2_a2"
P1_ROOT = ROOT.parent / "dmwk-p1-foundations"
_ALLOWED = frozenset(("exact_projection", "numerical_projection", "p1_runtime"))


def load_a2(name: str):
    if type(name) is not str or name not in _ALLOWED:
        raise ValueError("Only the declared prior arithmetic modules are allowed")
    expected = (A2_ROOT / (name + ".py")).resolve()
    if not expected.is_file():
        raise ValueError("Required read-only A2 module is absent: " + name)
    if name in sys.modules:
        actual = getattr(sys.modules[name], "__file__", None)
        if actual is None or Path(actual).resolve() != expected:
            raise ValueError("Prior module name resolved to an unexpected file: " + name)
    if str(A2_ROOT) not in sys.path:
        sys.path.insert(0, str(A2_ROOT))
    module = importlib.import_module(name)
    if Path(module.__file__).resolve() != expected:
        raise ValueError("Unexpected imported module path: " + name)
    return module


def get_fp():
    runtime = load_a2("p1_runtime")
    runtime.configure_p1_root(P1_ROOT)
    return runtime.get_fp()


def environment_metadata() -> dict:
    import platform
    import numpy as np
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "A2_root": str(A2_ROOT),
        "P1_root": str(P1_ROOT),
        "arithmetic": get_fp().backend_metadata(),
        "previous_stage_suites_rerun": False,
    }

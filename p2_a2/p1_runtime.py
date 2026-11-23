"""Read-only canonical P1 arithmetic dependency for P2-A2.

Configuration is fixed before the first import. This is dependency selection,
not a new P1 verification or a mechanism for changing execution policies.
"""
from __future__ import annotations

import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
_root = Path(__file__).resolve().parents[1] / "dmwk-p1-foundations"
_loaded = None


def configure_p1_root(path) -> Path:
    global _root
    candidate = Path(path).resolve()
    if _loaded is not None and candidate != _root:
        raise ValueError("P1 dependency cannot change after arithmetic import")
    for relative in ("p1_c3/execution.py", "p1_b2/canonicalize.py"):
        if not (candidate / relative).is_file():
            raise ValueError("Required read-only P1 dependency is unavailable")
    _root = candidate
    return _root


def get_p1_root() -> Path:
    return _root.resolve()


def get_fp():
    global _loaded
    if _loaded is not None:
        return _loaded
    configure_p1_root(_root)
    sys.path.insert(0, str(_root))
    module = importlib.import_module("p1_c3.execution")
    canonical = importlib.import_module("p1_b2.canonicalize")
    if Path(module.__file__).resolve() != (_root / "p1_c3/execution.py").resolve():
        raise ValueError("Unexpected P1 arithmetic module provenance")
    if Path(canonical.__file__).resolve() != (_root / "p1_b2/canonicalize.py").resolve():
        raise ValueError("Unexpected P1 canonical-model module provenance")
    _loaded = module
    return module

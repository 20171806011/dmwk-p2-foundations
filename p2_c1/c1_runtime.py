"""Read-only arithmetic dependencies for the closed C1 compiler reference."""
from __future__ import annotations
import importlib
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
ALLOWED = {
    "p2_b1": frozenset(("b1_runtime", "constrained_updates", "optimizer_kernel")),
    "p2_a4": frozenset(("a4_runtime", "capacity_algebra", "capacity_discrete", "structural_budget")),
    "p2_a3": frozenset(("a3_runtime", "certificate_kernel", "linear_contracts", "bounded_contracts")),
}


def _load(stage, name):
    if type(name) is not str or name not in ALLOWED[stage]:
        raise ValueError("Undeclared dependency; previous verification suites are excluded")
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


def load_b1(name): return _load("p2_b1", name)
def load_a4(name): return _load("p2_a4", name)
def load_a3(name): return _load("p2_a3", name)
def load_a2(name): return load_a3("a3_runtime").load_a2(name)
def get_fp(): return load_a3("a3_runtime").get_fp()


def environment_metadata():
    data = load_b1("b1_runtime").environment_metadata()
    data["C1_root"] = str(ROOT)
    data["C1_reference"] = "Closed Boolean source compiler, explicit sparse D/A views, exact endpoint authorization"
    data["prior_stage_suites_rerun"] = False
    data["P2_C2_started"] = False
    return data

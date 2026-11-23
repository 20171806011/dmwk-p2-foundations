"""P2-A1 exact algebra and finite-state activation-space reference routines.

No weight updates are implemented. All linear algebra uses exact rationals.
A completed reachability run is exact for its explicitly supplied finite model,
not automatically for a larger source program, input language, or backend.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Hashable, Iterable


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rational(value) -> Fraction:
    require(type(value) in (int, Fraction), "Use exact int/Fraction; floats and bools are not accepted")
    return Fraction(value)


def vector(values: Iterable) -> tuple[Fraction, ...]:
    return tuple(rational(x) for x in values)


def homogeneous(values: Iterable) -> tuple[Fraction, ...]:
    return vector(values) + (Fraction(1),)


def encode_fraction(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


class Basis:
    """Deterministic exact reduced-row-echelon basis for a column-vector span.

    Each supplied column vector is stored as a row of the basis table. Row
    reduction changes spanning generators, not ambient coordinate positions.
    """
    def __init__(self, dimension: int):
        require(type(dimension) is int and dimension >= 0, "Nonnegative dimension required")
        self.dimension = dimension
        self.rows: list[tuple[Fraction, ...]] = []
        self.pivots: list[int] = []
        self.reductions = 0
        self.scalar_multiply_subtract_pairs = 0
        self.peak_rational_bits = 1

    def _track(self, values) -> None:
        for x in values:
            self.peak_rational_bits = max(self.peak_rational_bits,
                                         abs(x.numerator).bit_length(), x.denominator.bit_length())

    def residual(self, values: Iterable) -> tuple[Fraction, ...]:
        result = list(vector(values))
        require(len(result) == self.dimension, "Coordinate dimension mismatch")
        self.reductions += 1
        self._track(result)
        for pivot, row in zip(self.pivots, self.rows):
            coefficient = result[pivot]
            if coefficient:
                result = [a - coefficient*b for a, b in zip(result, row)]
                self.scalar_multiply_subtract_pairs += self.dimension
                self._track(result)
        return tuple(result)

    def add(self, values: Iterable) -> bool:
        residual = self.residual(values)
        pivot = next((i for i, value in enumerate(residual) if value), None)
        if pivot is None:
            return False
        new_row = tuple(x/residual[pivot] for x in residual)
        self._track(new_row)
        updated = []
        for row in self.rows:
            coefficient = row[pivot]
            replaced = tuple(a - coefficient*b for a, b in zip(row, new_row))
            self.scalar_multiply_subtract_pairs += self.dimension
            self._track(replaced)
            updated.append(replaced)
        position = sum(p < pivot for p in self.pivots)
        updated.insert(position, new_row)
        self.pivots.insert(position, pivot)
        self.rows = updated
        return True

    @property
    def rank(self) -> int:
        return len(self.rows)

    def contains(self, values: Iterable) -> bool:
        return not any(self.residual(values))

    def summary(self) -> dict:
        return {"ambient_dimension": self.dimension, "rank_Q_equals_rank_R": self.rank,
                "complement_dimension": self.dimension-self.rank,
                "basis": [[encode_fraction(x) for x in row] for row in self.rows],
                "pivot_positions": self.pivots.copy(),
                "rational_arithmetic_cost": {"reductions": self.reductions,
                    "multiply_subtract_pairs": self.scalar_multiply_subtract_pairs,
                    "peak_stored_numerator_or_denominator_bits": self.peak_rational_bits}}


def span(values: Iterable[Iterable], dimension: int) -> Basis:
    result = Basis(dimension)
    for v in values:
        result.add(v)
    return result


@dataclass(frozen=True)
class Call:
    """An event in a declared physical matrix's input coordinate system."""
    matrix_id: str
    site_id: str
    activation: tuple[Fraction, ...]

    def __post_init__(self):
        require(type(self.matrix_id) is str and self.matrix_id != "", "Matrix identifier required")
        require(type(self.site_id) is str and self.site_id != "", "Call-site identifier required")
        require(type(self.activation) is tuple, "Activation must be an immutable tuple")
        object.__setattr__(self, "activation", vector(self.activation))


@dataclass
class Reachability:
    states: tuple[Hashable, ...]
    edges: tuple[tuple[Hashable, Hashable, Hashable], ...]
    calls: tuple[Call, ...]
    depths: dict[Hashable, int]
    matrix_dimensions: dict[str, int] | None = None
    declared_sites: tuple[tuple[str, str], ...] = ()

    def spaces(self) -> dict:
        matrices = {} if self.matrix_dimensions is None else {
            mid: Basis(dim) for mid, dim in self.matrix_dimensions.items()}
        sites, distinct = {}, {}
        for mid, sid in self.declared_sites:
            require(mid in matrices, "Declared call site requires a declared matrix")
            sites[(mid, sid)] = Basis(matrices[mid].dimension)
            distinct[(mid, sid)] = set()
        for call in self.calls:
            mid, sid, v = call.matrix_id, call.site_id, call.activation
            if mid not in matrices:
                require(self.matrix_dimensions is None, "Call used an undeclared physical matrix")
                matrices[mid] = Basis(len(v))
            require(matrices[mid].dimension == len(v), "Shared matrix dimensions disagree")
            key = (mid, sid)
            if key not in sites:
                require(not self.declared_sites, "Call used an undeclared call site")
                sites[key] = Basis(len(v))
                distinct[key] = set()
            matrices[mid].add(v); sites[key].add(v); distinct[key].add(v)
        return {"per_matrix": {k: b.summary() for k, b in sorted(matrices.items())},
                "per_call_site": [{"matrix_id": k[0], "site_id": k[1],
                    "distinct_activation_count": len(distinct[k]), **sites[k].summary()}
                    for k in sorted(sites)],
                "registry_scope": "all declared matrices; uncalled matrices have rank zero" if self.matrix_dimensions is not None else "observed matrices only; no inference about undeclared uncalled matrices",
                "reachable_states": len(self.states), "legal_edges": len(self.edges),
                "recorded_calls": len(self.calls), "maximum_shortest_depth": max(self.depths.values(), default=-1)}


def enumerate_reachable(initial_states: tuple, inputs_for: Callable,
                        step: Callable, *, universe: frozenset,
                        state_limit: int = 100000,
                        matrix_dimensions: dict[str, int] | None = None,
                        declared_sites: tuple[tuple[str, str], ...] = ()) -> Reachability:
    """Complete BFS over a supplied finite transition system and input monitor.

    The monitor/history abstraction, if any, must be part of the hashable state.
    `inputs_for(state)` returns a finite tuple. `step` returns (next_state,
    tuple_of_calls) for that entire macro-step, including all internal calls.
    The finite universe and call/transition fidelity are caller obligations.
    A state limit raises; it never returns a completed partial analysis.
    """
    if matrix_dimensions is not None:
        require(type(matrix_dimensions) is dict and all(type(k) is str and k != "" and
                type(v) is int and v >= 0 for k, v in matrix_dimensions.items()),
                "Matrix registry must map explicit names to nonnegative dimensions")
        matrix_dimensions = matrix_dimensions.copy()
    require(type(declared_sites) is tuple and all(type(k) is tuple and len(k) == 2 and
            all(type(v) is str and v != "" for v in k) for k in declared_sites),
            "Call sites must be immutable (matrix_id,site_id) pairs")
    require(len(set(declared_sites)) == len(declared_sites), "Duplicate declared call sites")
    require(not declared_sites or matrix_dimensions is not None,
            "Declaring uncalled sites also requires a matrix registry")
    require(type(initial_states) is tuple and type(universe) is frozenset,
            "Explicit immutable initial set and finite state universe required")
    require(type(state_limit) is int and state_limit > 0, "Positive state budget required")
    require(all(s in universe for s in initial_states), "Initial state outside universe")
    seen = dict.fromkeys(initial_states, 0)
    require(len(seen) <= state_limit, "State budget exceeded")
    queue, states, edges, calls = deque(seen), [], [], []
    while queue:
        old = queue.popleft(); states.append(old)
        inputs = inputs_for(old)
        require(type(inputs) is tuple, "Legal inputs must be an explicit finite tuple")
        require(len(set(inputs)) == len(inputs), "Duplicate legal inputs obscure edge counts")
        for incoming in inputs:
            new, events = step(old, incoming)
            require(new in universe, "Transition left the declared finite universe")
            require(type(events) is tuple and all(type(e) is Call for e in events),
                    "Every executed call must be returned as an immutable Call tuple")
            edges.append((old, incoming, new)); calls.extend(events)
            if new not in seen:
                require(len(seen) < state_limit, "State budget exceeded; no all-time certificate produced")
                seen[new] = seen[old]+1; queue.append(new)
    result = Reachability(tuple(states), tuple(edges), tuple(calls), seen, matrix_dimensions, declared_sites)
    # Validate observed dimensions against the registry before declaring success.
    result.spaces()
    return result


def matrix_apply(matrix: tuple, values: tuple) -> tuple[Fraction, ...]:
    v = vector(values)
    rows = tuple(vector(row) for row in matrix)
    require(all(len(row) == len(v) for row in rows), "Matrix input dimension mismatch")
    return tuple(sum((a*b for a, b in zip(row, v)), Fraction(0)) for row in rows)


def affine_lift(matrix: tuple, offset: tuple) -> tuple:
    offset = vector(offset)
    require(len(matrix) == len(offset), "Affine output dimension mismatch")
    rows = tuple(vector(row) for row in matrix)
    require(all(len(row) == len(offset) for row in rows), "Square state generators required")
    return tuple(row+(b,) for row, b in zip(rows, offset)) + ((Fraction(0),)*len(offset)+(Fraction(1),),)


def invariant_linear_hull(initial: tuple, generators: tuple, dimension: int) -> tuple[Basis, dict]:
    """Least common invariant linear hull for the given exact linear family.

    Used for affine state updates after homogeneous lifting. An arbitrary
    nonlinear/rounded transition is not assumed to belong to this family.
    """
    generators = tuple(tuple(vector(row) for row in matrix) for matrix in generators)
    require(all(len(m) == dimension and all(len(r) == dimension for r in m) for m in generators),
            "Generator shapes must match state dimension")
    result = span(initial, dimension)
    ranks, rounds, images = [result.rank], 0, 0
    while True:
        old_basis = tuple(result.rows)
        old_rank = result.rank
        rounds += 1
        for matrix in generators:
            for v in old_basis:
                result.add(matrix_apply(matrix, v)); images += 1
        ranks.append(result.rank)
        if result.rank == old_rank:
            break
        require(rounds <= dimension, "Internal invariant-growth bound violated")
    require(all(result.contains(v) for v in initial), "Initial-vector containment failed")
    require(all(result.contains(matrix_apply(m, v)) for m in generators for v in result.rows),
            "Common invariance certificate failed")
    return result, {"rounds_including_final_closure_check": rounds,
                    "strict_growth_rounds": rounds-1, "rank_sequence": ranks,
                    "generator_count": len(generators), "generated_images": images,
                    "all_initial_vectors_contained": True,
                    "all_generator_images_of_basis_contained": True,
                    "scope": "Exact rational linear generators only; transfer to FP requires a separate refinement or error enclosure"}

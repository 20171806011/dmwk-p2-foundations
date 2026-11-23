"""Exact rational projection reference for P2-A2.

All entries are Fractions or exact Python integers, never implicit binary64
approximations. A shape is retained even for zero-column and zero-row matrices.
This module proves no floating-execution safety and applies no stored patch.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Iterable


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def rational(value: int | Fraction) -> Fraction:
    require(type(value) in (int, Fraction), "Exact int/Fraction entries required; float and bool are rejected")
    return Fraction(value)


@dataclass(frozen=True)
class Matrix:
    rows: tuple[tuple[Fraction, ...], ...]
    ncols: int

    def __post_init__(self) -> None:
        require(type(self.ncols) is int and self.ncols >= 0, "Nonnegative integer column count required")
        require(type(self.rows) is tuple and all(type(row) is tuple for row in self.rows),
                "Matrix storage must be an immutable tuple of tuples")
        require(all(len(row) == self.ncols for row in self.rows), "Ragged matrix or inconsistent shape")
        object.__setattr__(self, "rows", tuple(tuple(rational(x) for x in row) for row in self.rows))

    @property
    def nrows(self) -> int:
        return len(self.rows)

    @property
    def shape(self) -> tuple[int, int]:
        return self.nrows, self.ncols


def matrix(data: Iterable[Iterable] | Matrix, ncols: int | None = None) -> Matrix:
    if type(data) is Matrix:
        require(ncols is None or ncols == data.ncols, "Requested shape disagrees with matrix")
        return data
    rows = tuple(tuple(rational(x) for x in row) for row in data)
    width = (len(rows[0]) if rows else 0) if ncols is None else ncols
    return Matrix(rows, width)


def zeros(nrows: int, ncols: int) -> Matrix:
    require(type(nrows) is int and nrows >= 0, "Nonnegative integer row count required")
    require(type(ncols) is int and ncols >= 0, "Nonnegative integer column count required")
    return Matrix(tuple((Fraction(0),)*ncols for _ in range(nrows)), ncols)


def eye(n: int) -> Matrix:
    require(type(n) is int and n >= 0, "Nonnegative integer dimension required")
    return matrix(tuple(tuple(int(i == j) for j in range(n)) for i in range(n)), ncols=n)


@dataclass
class ArithmeticAudit:
    """Counts instrumented exact operations and observed stored coefficient bits.

    This is not a wall-time complexity theorem or peak transient memory metric.
    Construction wrappers call ``observe`` on arithmetic results before they are
    placed in matrices, including scalar products used during elimination.
    Python's internal big-integer/gcd work is not counted as a unit operation.
    """
    operations: dict[str, int] = field(default_factory=lambda: {"add": 0, "subtract": 0, "multiply": 0, "divide": 0})
    max_observed_numerator_bits: int = 1
    max_observed_denominator_bits: int = 1

    def observe(self, value: Fraction) -> Fraction:
        self.max_observed_numerator_bits = max(self.max_observed_numerator_bits, abs(value.numerator).bit_length())
        self.max_observed_denominator_bits = max(self.max_observed_denominator_bits, value.denominator.bit_length())
        return value

    def summarize(self) -> dict:
        return {"instrumented_rational_operations": dict(self.operations),
                "max_observed_numerator_bits": self.max_observed_numerator_bits,
                "max_observed_denominator_bits": self.max_observed_denominator_bits,
                "scope": "Explicit rational operations and their Fraction results, not Python bigint/gcd internals or peak memory"}


def _op(kind: str, a: Fraction, b: Fraction, audit: ArithmeticAudit | None) -> Fraction:
    if kind == "add":
        result = a+b
    elif kind == "subtract":
        result = a-b
    elif kind == "multiply":
        result = a*b
    elif kind == "divide":
        require(b != 0, "Exact division by zero")
        result = a/b
    else:
        raise ValueError("Unknown exact operation")
    if audit is not None:
        audit.operations[kind] += 1
        audit.observe(a); audit.observe(b); audit.observe(result)
    return result


def transpose(a: Matrix) -> Matrix:
    return Matrix(tuple(tuple(a.rows[i][j] for i in range(a.nrows)) for j in range(a.ncols)), a.nrows)


def add(a: Matrix, b: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    require(a.shape == b.shape, "Matrix addition shape mismatch")
    return Matrix(tuple(tuple(_op("add", x, y, audit) for x, y in zip(ar, br))
                        for ar, br in zip(a.rows, b.rows)), a.ncols)


def sub(a: Matrix, b: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    require(a.shape == b.shape, "Matrix subtraction shape mismatch")
    return Matrix(tuple(tuple(_op("subtract", x, y, audit) for x, y in zip(ar, br))
                        for ar, br in zip(a.rows, b.rows)), a.ncols)


def scale(a: Matrix, coefficient: int | Fraction, *, audit: ArithmeticAudit | None = None) -> Matrix:
    q = rational(coefficient)
    return Matrix(tuple(tuple(_op("multiply", x, q, audit) for x in row) for row in a.rows), a.ncols)


def matmul(a: Matrix, b: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    require(a.ncols == b.nrows, "Matrix multiplication shape mismatch")
    rows = []
    for i in range(a.nrows):
        row = []
        for j in range(b.ncols):
            total = Fraction(0)
            for k in range(a.ncols):
                total = _op("add", total, _op("multiply", a.rows[i][k], b.rows[k][j], audit), audit)
            row.append(total)
        rows.append(tuple(row))
    return Matrix(tuple(rows), b.ncols)


def rref(a: Matrix, *, audit: ArithmeticAudit | None = None) -> tuple[Matrix, tuple[int, ...]]:
    rows = [list(row) for row in a.rows]
    pivots = []
    prow = 0
    for column in range(a.ncols):
        pivot = next((i for i in range(prow, a.nrows) if rows[i][column]), None)
        if pivot is None:
            continue
        rows[prow], rows[pivot] = rows[pivot], rows[prow]
        divisor = rows[prow][column]
        rows[prow] = [_op("divide", value, divisor, audit) for value in rows[prow]]
        for i in range(a.nrows):
            if i == prow or not rows[i][column]:
                continue
            coefficient = rows[i][column]
            rows[i] = [_op("subtract", value, _op("multiply", coefficient, lead, audit), audit)
                       for value, lead in zip(rows[i], rows[prow])]
        pivots.append(column)
        prow += 1
        if prow == a.nrows:
            break
    return Matrix(tuple(tuple(row) for row in rows), a.ncols), tuple(pivots)


def rank(a: Matrix, *, audit: ArithmeticAudit | None = None) -> int:
    return len(rref(a, audit=audit)[1])


def column_basis(a: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    pivots = rref(a, audit=audit)[1]
    return Matrix(tuple(tuple(row[j] for j in pivots) for row in a.rows), len(pivots))


def nullspace(a: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    """Columns give an exact basis of ker(a), including all empty-shape cases."""
    reduced, pivots = rref(a, audit=audit)
    free = tuple(j for j in range(a.ncols) if j not in pivots)
    cols = []
    for column in free:
        values = [Fraction(0)]*a.ncols
        values[column] = Fraction(1)
        for i, pivot in enumerate(pivots):
            values[pivot] = -reduced.rows[i][column]
        cols.append(tuple(values))
    return Matrix(tuple(tuple(col[i] for col in cols) for i in range(a.ncols)), len(free))


def inverse(a: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    require(a.nrows == a.ncols, "Inverse requires a square matrix")
    n = a.nrows
    identity = eye(n)
    augmented = Matrix(tuple(ar+ir for ar, ir in zip(a.rows, identity.rows)), 2*n)
    reduced, _ = rref(augmented, audit=audit)
    require(tuple(row[:n] for row in reduced.rows) == identity.rows, "Singular matrix has no inverse")
    return Matrix(tuple(row[n:] for row in reduced.rows), n)


def project_onto_columns(basis: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    """The input columns must be independent; no floating pseudoinverse is used."""
    if basis.ncols == 0:
        return zeros(basis.nrows, basis.nrows)
    bt = transpose(basis)
    gram_inverse = inverse(matmul(bt, basis, audit=audit), audit=audit)
    return matmul(matmul(basis, gram_inverse, audit=audit), bt, audit=audit)


@dataclass(frozen=True)
class Projection:
    H: Matrix
    B: Matrix
    N: Matrix
    P_D: Matrix
    P_perp: Matrix
    rank: int

    @property
    def d(self) -> int:
        return self.H.nrows


def projection(h: Matrix, *, audit: ArithmeticAudit | None = None) -> Projection:
    b = column_basis(h, audit=audit)
    n = nullspace(transpose(h), audit=audit)
    pd = project_onto_columns(b, audit=audit)
    perp = sub(eye(h.nrows), pd, audit=audit)
    return Projection(h, b, n, pd, perp, b.ncols)


def project_via_nullspace(h: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    return project_onto_columns(nullspace(transpose(h), audit=audit), audit=audit)


def project_update(g: Matrix, certificate: Projection, *, audit: ArithmeticAudit | None = None) -> Matrix:
    """Exact algebraic update only; not authorization to commit FP words."""
    require(g.ncols == certificate.d, "Update columns must match protected input coordinates")
    return matmul(g, certificate.P_perp, audit=audit)


def apply_perp_matrix_free(basis: Matrix, x: Matrix, *, audit: ArithmeticAudit | None = None) -> Matrix:
    """Compute P_perp X without constructing a d-by-d projector.

    Independent columns of B are required. A persistent implementation could
    cache the Gram inverse; this simple reference computes it per invocation.
    """
    require(basis.nrows == x.nrows, "Observation and basis dimensions disagree")
    if basis.ncols == 0:
        return x
    bt = transpose(basis)
    correction = matmul(basis, matmul(inverse(matmul(bt, basis, audit=audit), audit=audit),
                                     matmul(bt, x, audit=audit), audit=audit), audit=audit)
    return sub(x, correction, audit=audit)


def frobenius_squared(a: Matrix) -> Fraction:
    return sum((x*x for row in a.rows for x in row), Fraction(0))


def max_abs(a: Matrix) -> Fraction:
    return max((abs(x) for row in a.rows for x in row), default=Fraction(0))


def serialize(a: Matrix) -> dict:
    return {"shape": list(a.shape), "rows": [[str(x) for x in row] for row in a.rows]}


def serialize_projection(value: Projection) -> dict:
    return {"dimension": value.d, "protected_rank": value.rank,
            "complement_dimension": value.d-value.rank,
            "square_update_space_dimension": value.d*(value.d-value.rank),
            "H": serialize(value.H), "B": serialize(value.B), "N": serialize(value.N),
            "P_D": serialize(value.P_D), "P_perp": serialize(value.P_perp)}

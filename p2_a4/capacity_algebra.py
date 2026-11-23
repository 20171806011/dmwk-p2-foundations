"""Exact A4 rank budgets and target-response constructions.

All objects here are rational mathematical values. Supplying generators does
not prove their global provenance, and no report authorizes stored or bitwise
updates. Fixed finite-format endpoint sets are handled by a separate route.
"""
from __future__ import annotations

from fractions import Fraction

from a4_runtime import load_a2

xp = load_a2("exact_projection")
Matrix = xp.Matrix
matrix = xp.matrix


def require(test, message):
    if not test:
        raise ValueError(message)


def _matrix(a):
    require(type(a) is Matrix, "An exact rational Matrix is required")
    return matrix(a.rows, ncols=a.ncols)


def _positive(value, name):
    require(type(value) is int and value >= 1, name + " must be a positive exact integer")
    return value


def _cap(value):
    require(value is None or (type(value) is int and value >= 0),
            "Rank cap must be a nonnegative exact integer or None")
    return value


def _columns(columns, d):
    return matrix(tuple(tuple(col[i] for col in columns) for i in range(d)), ncols=len(columns))


def concatenate(*matrices):
    require(bool(matrices), "At least one generator matrix is required")
    values = tuple(_matrix(a) for a in matrices)
    d = values[0].nrows
    _positive(d, "Input dimension")
    require(all(a.nrows == d for a in values), "Generator input dimensions differ")
    return matrix(tuple(tuple(x for a in values for x in a.rows[i]) for i in range(d)),
                  ncols=sum(a.ncols for a in values))


def merge_generators(sites, *, input_dimension=None):
    """Merge supplied sites; this helper cannot discover omitted call sites."""
    require(type(sites) is dict and all(type(k) is str and k for k in sites),
            "Exact dictionary with nonempty string site identities required")
    if sites:
        result = concatenate(*(sites[k] for k in sorted(sites)))
        require(input_dimension is None or
                (type(input_dimension) is int and input_dimension == result.nrows),
                "Explicit input dimension disagrees with sites")
        return result
    d = _positive(input_dimension, "Empty-site input dimension")
    return xp.zeros(d, 0)


def _frame(h, x=None):
    """Extend protected columns, then target columns, then coordinate axes."""
    h = _matrix(h)
    d = _positive(h.nrows, "Input dimension")
    b = xp.column_basis(h)
    columns = [tuple(b.rows[i][j] for i in range(d)) for j in range(b.ncols)]
    selected_targets = []
    if x is not None:
        x = _matrix(x)
        require(x.nrows == d, "Target input dimension differs")
        for j in range(x.ncols):
            col = tuple(x.rows[i][j] for i in range(d))
            candidate = _columns(columns + [col], d)
            if xp.rank(candidate) > len(columns):
                columns.append(col)
                selected_targets.append(j)
    for j in range(d):
        col = tuple(Fraction(i == j) for i in range(d))
        if xp.rank(_columns(columns + [col], d)) > len(columns):
            columns.append(col)
    require(len(columns) == d, "Basis extension failed")
    frame = _columns(columns, d)
    return b.ncols, frame, xp.inverse(frame), tuple(selected_targets)


def budget_report(h, output_rows, rank_cap=None, x=None):
    """Abstract budget for a supplied protected span, with optional targets.

    The rank-capped family is generally not a vector space. Its maximal rank
    is reported separately from the unrestricted annihilator-space dimension.
    """
    h = _matrix(h)
    d = _positive(h.nrows, "Input dimension")
    n = _positive(output_rows, "Output dimension")
    k = _cap(rank_cap)
    r = xp.rank(h)
    c = d-r
    result = {
        "contract": "abstract_exact_capacity_only",
        "input_dimension": d, "output_dimension": n,
        "protected_rank": r, "complement_dimension": c,
        "unrestricted_update_space_dimension": n*c,
        "maximum_individual_update_rank": min(n,c),
        "generator_rank_cap": k,
        "maximum_rank_under_cap": min(n,c) if k is None else min(k,n,c),
        "rank_cap_is_not_a_linear_space_dimension": True,
        "protection_generators": xp.serialize(h),
        "global_provenance_verified": False,
        "stored_endpoint_feasibility_verified": False,
        "authorizes_bitwise_commit": False,
        "scope": "Exact rational construction and real extension on the supplied span only",
    }
    if x is not None:
        x = _matrix(x)
        require(x.nrows == d, "Target input dimension differs")
        s = xp.rank(concatenate(h,x))-r
        result.update({
            "target_generators": xp.serialize(x), "target_count": x.ncols,
            "target_quotient_rank": s,
            "unrestricted_response_image_dimension": n*s,
            "target_silent_update_space_dimension": n*(c-s),
            "maximum_target_response_rank": min(n,s) if k is None else min(k,n,s),
            "nonzero_target_response_exists": s > 0 and (k is None or k > 0),
            "nonzero_target_silent_update_exists": c > s and (k is None or k > 0),
        })
    return result


def attaining_update(h, output_rows, rank_cap=None, *, requested_rank=None):
    """Construct a rank-q abstract annihilator with q up to the proven bound.

    Choosing G=Delta realizes Delta=G P_perp and meets the same rank cap.
    This is not a claim that the returned coefficients are target-storable.
    """
    h = _matrix(h)
    n = _positive(output_rows, "Output dimension")
    k = _cap(rank_cap)
    r, frame, inverse, _ = _frame(h)
    upper = min(n,h.nrows-r) if k is None else min(k,n,h.nrows-r)
    q = upper if requested_rank is None else requested_rank
    require(type(q) is int and 0 <= q <= upper, "Requested rank exceeds the abstract budget")
    rows = tuple(inverse.rows[r+i] if i < q else (Fraction(0),)*h.nrows
                 for i in range(n))
    delta = matrix(rows, ncols=h.nrows)
    require(xp.rank(delta) == q, "Rank-attaining construction failed")
    require(all(v == 0 for row in xp.matmul(delta,h).rows for v in row),
            "Constructed map does not annihilate protected generators")
    return delta


def annihilator_basis(h, output_rows):
    """A complete exact basis of the unrestricted abstract update space."""
    h = _matrix(h)
    n = _positive(output_rows, "Output dimension")
    r, _, inverse, _ = _frame(h)
    result = []
    for i in range(n):
        for j in range(h.nrows-r):
            rows = tuple(inverse.rows[r+j] if row == i else (Fraction(0),)*h.nrows
                         for row in range(n))
            result.append(matrix(rows, ncols=h.nrows))
    return tuple(result)


def solve_response(h, x, response, rank_cap=None):
    """Return (minimum-rank exact update or None, JSON-compatible report).

    Failure can mean an inconsistent quotient relation or an insufficient
    rank budget. An inconsistent relation includes alpha with X alpha in V
    but response alpha nonzero, which independently witnesses impossibility.
    """
    h, x, response = _matrix(h), _matrix(x), _matrix(response)
    d = _positive(h.nrows, "Input dimension")
    n = _positive(response.nrows, "Output dimension")
    k = _cap(rank_cap)
    require(x.nrows == d and response.ncols == x.ncols,
            "Target/response shape mismatch")
    r, frame, inverse, selected = _frame(h,x)
    c, s = d-r, len(selected)
    quotient = matrix(inverse.rows[r:], ncols=d)
    y = xp.matmul(quotient,x)
    relations = xp.nullspace(y)
    bad_responses = xp.matmul(response,relations)
    bad_column = next((j for j in range(relations.ncols)
                       if any(bad_responses.rows[i][j] for i in range(n))), None)
    report = budget_report(h,n,k,x)
    report.update({"requested_response": xp.serialize(response),
                   "response_rank": xp.rank(response),
                   "quotient_coordinates": xp.serialize(y),
                   "selected_target_columns": list(selected),
                   "relation_kernel_basis": xp.serialize(relations)})
    if bad_column is not None:
        alpha = matrix(tuple((relations.rows[i][bad_column],) for i in range(x.ncols)), ncols=1)
        report.update({"status":"infeasible_target_relations",
                       "unconstrained_response_feasible":False,
                       "minimum_required_update_rank":None,
                       "impossibility_witness":{
                           "alpha":xp.serialize(alpha),
                           "X_alpha":xp.serialize(xp.matmul(x,alpha)),
                           "R_alpha":xp.serialize(xp.matmul(response,alpha)),
                           "meaning":"X alpha lies in protected V but requested R alpha is nonzero"}})
        return None, report
    q = xp.rank(response)
    report.update({"unconstrained_response_feasible":True,
                   "minimum_required_update_rank":q})
    if k is not None and q > k:
        report["status"] = "infeasible_rank_budget"
        return None, report
    # The frame has protected columns, selected independent target columns,
    # and an arbitrary remainder. Map the last part to zero; every nonzero
    # output column is then a selected column of the requested response.
    mapping_rows = []
    for i in range(n):
        mapping_rows.append((Fraction(0),)*r + tuple(response.rows[i][j] for j in selected)
                            + (Fraction(0),)*(c-s))
    mapping = matrix(tuple(mapping_rows), ncols=d)
    delta = xp.matmul(mapping,inverse)
    require(all(v == 0 for row in xp.matmul(delta,h).rows for v in row),
            "Response construction lost protection")
    require(xp.matmul(delta,x) == response, "Response construction failed target equations")
    require(xp.rank(delta) == q, "Response construction did not attain minimum rank")
    report.update({"status":"feasible_exact_response", "constructed_update":xp.serialize(delta),
                   "constructed_update_rank":q,
                   "candidate_generation":"G=Delta; Delta P_perp=Delta in exact algebra",
                   "endpoint_or_bitwise_feasibility":"Not implied by this abstract construction"})
    return delta, report

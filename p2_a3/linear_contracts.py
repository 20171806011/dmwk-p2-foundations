"""Exact endpoint-difference diagnostics for P2-A3.

These functions check exact algebra on a supplied generator family. They do not
verify where that family came from, certify a complete legal domain, authorize
a live commit, or assert equality of a floating instruction sequence. A2's
exact rational matrix implementation is consumed read-only.
"""
from __future__ import annotations

from fractions import Fraction

from a3_runtime import load_a2

xp = load_a2('exact_projection')
Matrix = xp.Matrix
matrix = xp.matrix


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _matrix(value: Matrix) -> Matrix:
    """Copy and revalidate a mathematical value; it is not an authority token."""
    _require(type(value) is Matrix, 'An exact A2 Matrix value is required')
    return xp.matrix(value.rows, ncols=value.ncols)


def _weights(old: Matrix, new: Matrix) -> tuple[Matrix, Matrix]:
    old, new = _matrix(old), _matrix(new)
    _require(old.shape == new.shape, 'Endpoint weight shapes differ')
    _require(old.nrows >= 1 and old.ncols >= 1, 'Positive output/input dimensions required')
    return old, new


def _bias(value, rows: int) -> tuple[Fraction, ...]:
    _require(type(value) is tuple and len(value) == rows,
             'Bias must be an exact tuple with one entry per output row')
    return tuple(xp.rational(x) for x in value)


def effective_delta(old: Matrix, new: Matrix) -> Matrix:
    """Exact decoded endpoint difference; never a target-format subtraction."""
    old, new = _weights(old, new)
    return xp.sub(new, old)


def merge_generators(site_generators: dict[str, Matrix], *, input_dimension=None) -> Matrix:
    """Concatenate supplied sites in sorted ID order.

    This arithmetic helper cannot discover an omitted protected call site. The
    execution certificate registry, not this helper, must establish completeness.
    """
    _require(type(site_generators) is dict, 'Exact site dictionary required')
    _require(all(type(k) is str and k for k in site_generators), 'Nonempty string site IDs required')
    values = [_matrix(site_generators[k]) for k in sorted(site_generators)]
    if values:
        d = values[0].nrows
        _require(d >= 1 and all(v.nrows == d for v in values), 'Site input dimensions differ')
        _require(input_dimension is None or (type(input_dimension) is int and input_dimension == d),
                 'Explicit input dimension disagrees with sites')
    else:
        _require(type(input_dimension) is int and input_dimension >= 1,
                 'An empty site family needs a positive explicit input dimension')
        d = input_dimension
    return xp.matrix(tuple(tuple(x for v in values for x in v.rows[i])
                           for i in range(d)), ncols=sum(v.ncols for v in values))


def contains_span(super_generators: Matrix, sub_generators: Matrix) -> bool:
    """Exact inclusion of supplied rational spans; no reachability claim."""
    upper, lower = _matrix(super_generators), _matrix(sub_generators)
    _require(upper.nrows == lower.nrows and upper.nrows >= 1, 'Input dimensions differ')
    combined = merge_generators({'upper': upper, 'lower': lower})
    return xp.rank(combined) == xp.rank(upper)


def augment_activations(activation_columns: Matrix) -> Matrix:
    """Append one to each ACTUAL activation column before taking its span.

    An arbitrary basis of the unaugmented linear span is not interchangeable
    with actual activation generators for affine constraints.
    """
    h = _matrix(activation_columns)
    _require(h.nrows >= 1, 'Positive activation dimension required')
    return xp.matrix(h.rows + ((Fraction(1),) * h.ncols,), ncols=h.ncols)


def _zero(a: Matrix) -> bool:
    return all(x == 0 for row in a.rows for x in row)


def _condition(old: Matrix, new: Matrix, h: Matrix) -> dict:
    old, new = _weights(old, new)
    h = _matrix(h)
    _require(h.nrows == old.ncols, 'Generator and weight input dimensions differ')
    delta = xp.sub(new, old)
    b = xp.column_basis(h)
    residual = xp.matmul(delta, h)
    basis_residual = xp.matmul(delta, b)
    on_generators, on_basis = _zero(residual), _zero(basis_residual)
    if on_generators != on_basis:
        raise ArithmeticError('Exact basis/generator consistency failed')
    r = b.ncols
    return {
        'contract': 'exact_algebra_only',
        'old_weights': xp.serialize(old),
        'new_weights': xp.serialize(new),
        'effective_difference': xp.serialize(delta),
        'generators': xp.serialize(h),
        'basis': xp.serialize(b),
        'generator_residual': xp.serialize(residual),
        'basis_residual': xp.serialize(basis_residual),
        'annihilates_generators': on_generators,
        'annihilates_basis': on_basis,
        'annihilates_supplied_span': on_generators,
        'input_dimension': old.ncols,
        'output_dimension': old.nrows,
        'generator_columns': h.ncols,
        'protected_rank': r,
        'complement_dimension': old.ncols-r,
        'algebraic_update_space_dimension': old.nrows*(old.ncols-r),
        'global_domain_provenance_verified': False,
        'authorizes_bitwise_commit': False,
        'scalar_semantics': 'Exact rational arithmetic; corresponding real-linear extension',
        'scope': 'Supplied generator span only; global coverage and floating execution require separate premises',
    }


def exact_linear_report(old: Matrix, new: Matrix, span_generators: Matrix) -> dict:
    """Check (new-old)H=0 for fixed identical biases and unchanged inputs."""
    result = _condition(old, new, span_generators)
    result['bias_contract'] = 'Fixed identical bias, omitted from the exact difference'
    result['generator_role'] = 'Generators of the proposed protected linear input span'
    result['output_meaning'] = 'Same exact linear/identical-bias output at each unchanged input in this span'
    return result


def exact_affine_report(old: Matrix, new: Matrix, old_bias: tuple,
                        new_bias: tuple, activation_columns: Matrix) -> dict:
    """Check joint affine endpoint changes at supplied actual activations.

    The complete affine conclusion is about span{(h,1)} after augmentation.
    This function does not infer that the supplied list is the whole legal set.
    """
    old, new = _weights(old, new)
    b0, b1 = _bias(old_bias, old.nrows), _bias(new_bias, old.nrows)
    h = _matrix(activation_columns)
    _require(h.nrows == old.ncols, 'Activation input dimension differs')
    a0 = xp.matrix(tuple(row+(b,) for row,b in zip(old.rows,b0)))
    a1 = xp.matrix(tuple(row+(b,) for row,b in zip(new.rows,b1)))
    result = _condition(a0,a1,augment_activations(h))
    result['bias_contract'] = 'Joint affine block; final column stores the exact bias endpoint'
    result['generator_role'] = 'Homogenization of supplied actual activation columns, not an arbitrary input-span basis'
    result['unaugmented_activations'] = xp.serialize(h)
    result['unaugmented_linear_rank'] = xp.rank(h)
    result['physical_input_dimension'] = old.ncols
    result['output_meaning'] = 'Same exact affine output at the supplied activations and any h whose (h,1) lies in their augmented span'
    return result


def exact_augmented_report(old_affine: Matrix, new_affine: Matrix,
                           augmented_span_generators: Matrix) -> dict:
    """Check already justified homogeneous-space generators without modifying them.

    Such generators need not themselves have last coordinate one. Their span
    must separately be shown to contain all actual (h,1) activation vectors.
    """
    result = _condition(old_affine,new_affine,augmented_span_generators)
    _require(result['input_dimension'] >= 2, 'Affine block needs an input and a bias coordinate')
    result['bias_contract'] = 'Final affine-block column is bias; already homogeneous generator space'
    result['generator_role'] = 'Proposed generators of the already augmented protected span'
    return result

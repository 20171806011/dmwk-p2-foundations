"""P2-A2 numerical proposals, exact error accounting, and fixed-order FP execution.

Numerical projections are proposals, not bit-exact update authorizations.
All certificates decode stored values as Fractions and do not treat a floating
norm or SVD rank threshold as an exact rank proof. P1 is consumed read-only.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from fractions import Fraction
from math import isqrt
import time
import numpy as np

from exact_projection import (Matrix, matrix, zeros, eye, transpose, add, sub,
                              matmul, rank, projection, serialize,
                              frobenius_squared)
from p1_runtime import get_fp


class NumericalRejected(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise NumericalRejected(message)


def qstr(value):
    return str(Fraction(value))


def sqrt_upper(value: Fraction, bits: int = 192) -> Fraction:
    """Certified dyadic upper bound on sqrt(value); never a host-float norm."""
    value = Fraction(value)
    require(value >= 0 and type(bits) is int and bits >= 0, 'Bad square-root bound input')
    scaled = value.numerator << (2*bits)
    root = isqrt(scaled // value.denominator)
    if root*root*value.denominator < scaled:
        root += 1
    result = Fraction(root, 1 << bits)
    require(result*result >= value, 'Square-root enclosure failed')
    return result


def norm_upper(a: Matrix) -> Fraction:
    return sqrt_upper(frobenius_squared(a))


def from_numpy(array) -> Matrix:
    require(type(array) is np.ndarray and array.ndim == 2,
            'Explicit 2-D ndarray required')
    require(array.dtype in (np.dtype('float32'), np.dtype('float64')),
            'Only FP32/FP64 diagnostic arrays supported')
    require(bool(np.all(np.isfinite(array))), 'Nonfinite numeric array rejected')
    # Python binary64 exactly represents every binary32 value; this reads the
    # already stored value rather than claiming its upstream calculation exact.
    return matrix(tuple(tuple(Fraction.from_float(float(x)) for x in row)
                        for row in array), ncols=array.shape[1])


def quantize_matrix(a: Matrix, format_name: str) -> tuple[Matrix, tuple]:
    fp = get_fp()
    words = tuple(tuple(fp.round_fraction(x, format_name) for x in row) for row in a.rows)
    result = matrix(tuple(tuple(fp.decode_word(w, format_name) for w in row)
                          for row in words), ncols=a.ncols)
    return result, words


def stored_words(a: Matrix, format_name: str) -> tuple:
    decoded, words = quantize_matrix(a, format_name)
    require(decoded == a, 'Operation input is not already exactly stored in the target format')
    return words


def _svd_input(h: Matrix, dtype: str):
    require(dtype in ('float32', 'float64'), 'SVD dtype must be float32 or float64')
    if dtype == 'float32':
        _, words = quantize_matrix(h, 'FP32')
        return np.asarray(words, dtype=np.uint32).reshape(h.shape).view(np.float32).copy()
    result = np.array([[float(x) for x in row] for row in h.rows], dtype=np.float64)
    result = result.reshape(h.shape)
    require(bool(np.all(np.isfinite(result))), 'FP64 input conversion overflow/nonfinite')
    return result


def svd_projection(h: Matrix, dtype='float64', *, rtol=None, atol=0.0) -> dict:
    """Return a numeric proposal and exact decoded diagnostics.

    rank uses s > max(atol, rtol*smax). A default rtol is explicitly recorded.
    No claim is made that LAPACK's internal operations are certified here.
    """
    require(h.nrows > 0 and h.ncols > 0, 'SVD experiment requires nonempty matrix dimensions')
    values = _svd_input(h, dtype)
    rtol = float(max(h.shape)*np.finfo(values.dtype).eps) if rtol is None else float(rtol)
    atol = float(atol)
    require(np.isfinite(rtol) and np.isfinite(atol) and rtol >= 0 and atol >= 0,
            'Finite nonnegative rank thresholds required')
    started = time.perf_counter()
    if dtype == 'float32':
        # NumPy 2.3.5 public linalg.svd promotes float32 internally to
        # double and casts outputs back. Force the actual single-real
        # compiled gufunc signature instead; this is version-specific.
        from numpy.linalg import _umath_linalg
        require('f->fff' in _umath_linalg.svd_f.types,
                'Explicit single-precision SVD dispatch unavailable')
        with np.errstate(invalid='raise', over='raise'):
            u, s, vh = _umath_linalg.svd_f(values, signature='f->fff')
        dispatch = 'numpy.linalg._umath_linalg.svd_f signature f->fff'
    else:
        u, s, vh = np.linalg.svd(values, full_matrices=True)
        dispatch = 'numpy.linalg.svd float64 input; d->ddd in pinned NumPy implementation'
    require(bool(np.all(np.isfinite(u))) and bool(np.all(np.isfinite(s)))
            and bool(np.all(np.isfinite(vh))), 'SVD produced nonfinite output')
    threshold = max(atol, rtol*float(s[0]))
    require(np.isfinite(threshold), 'Computed rank threshold overflowed; no rank proposal produced')
    # NumPy's weak-scalar comparison can cast a Python threshold down to
    # float32. Compare in binary64 so the recorded cutoff is the cutoff used;
    # every binary32 singular value is exactly representable in binary64.
    numerical_rank = int(np.count_nonzero(s.astype(np.float64) > threshold))
    q = u[:, :numerical_rank]
    p = np.eye(h.nrows, dtype=values.dtype) - q @ q.T
    elapsed = time.perf_counter()-started
    require(u.dtype == s.dtype == vh.dtype == p.dtype == values.dtype,
            'SVD interface or projector calculation changed dtype')
    exact_p = projection(h).P_perp
    decoded_p = from_numpy(p)
    input_decoded = from_numpy(values)
    error = sub(decoded_p, exact_p)
    residual = matmul(decoded_p, h)
    symmetry = sub(decoded_p, transpose(decoded_p))
    idempotence = sub(matmul(decoded_p, decoded_p), decoded_p)
    condition = (float(s[0])/float(s[-1])) if len(s) and s[-1] > 0 else None
    condition_reason = 'finite SVD singular-value ratio' if condition is not None else 'smallest reported singular value is zero'
    if condition is not None and not np.isfinite(condition):
        condition = None
        condition_reason = 'ratio exceeds finite binary64 diagnostic range'
    return {'proposal': decoded_p, 'array': p, 'basis_array': q,
            'diagnostics': {'dtype': str(values.dtype), 'solver_dispatch': dispatch,
                'numpy_version': np.__version__,
                'public_float32_api_warning': 'In NumPy 2.3.5 public linalg.svd promotes float32 to float64 internally; output dtype alone is insufficient. This float32 route uses the explicit f->fff gufunc.',
                'svd_output_dtypes':
                [str(u.dtype), str(s.dtype), str(vh.dtype)],
                'input_conversion': 'direct exact-rational-to-FP32 RNE' if dtype=='float32'
                                    else 'Python rational-to-binary64 conversion, then decoded exactly',
                'original_exact_rank': rank(h), 'converted_input_exact_rank': rank(input_decoded),
                'numerical_effective_rank': numerical_rank,
                'inferred_complement_dimension': h.nrows-numerical_rank,
                'rank_rule': 'singular_value_as_binary64 > max(atol, rtol*smax), with recorded binary64 cutoff',
                'rtol': rtol, 'atol': atol, 'threshold': threshold,
                'singular_values': [float(x) for x in s],
                'estimated_condition_2_from_svd': condition,
                'condition_interpretation': 'Diagnostic only; no certified condition interval.',
                'condition_diagnostic_reason': condition_reason,
                'runtime_seconds': elapsed, 'stored_projector': serialize(decoded_p),
                'converted_input': serialize(input_decoded),
                'exact_projector_error_F_squared': qstr(frobenius_squared(error)),
                'exact_protected_residual_F_squared': qstr(frobenius_squared(residual)),
                'exact_symmetry_defect_F_squared': qstr(frobenius_squared(symmetry)),
                'exact_idempotence_defect_F_squared': qstr(frobenius_squared(idempotence)),
                'certified_projector_error_norm_upper': qstr(norm_upper(error)),
                'scope': 'Actual local NumPy SVD/dtype interface; exact diagnostics of stored results; no exact-rank certification from SVD'}}


@dataclass(frozen=True)
class DotResult:
    output_word: int
    exact_dot: Fraction
    decoded_output: Fraction
    signed_error: Fraction
    local_absolute_error_bound: Fraction
    product_errors: tuple
    addition_errors: tuple
    accumulator_words: tuple
    audit: dict
    gamma_2n: Fraction | None
    gamma_bound: Fraction | None
    relative_model_holds: bool

    def record(self):
        return {'output_word_hex': hex(self.output_word), 'exact_dot': qstr(self.exact_dot),
                'decoded_output': qstr(self.decoded_output), 'signed_error': qstr(self.signed_error),
                'local_absolute_error_bound': qstr(self.local_absolute_error_bound),
                'product_errors': [qstr(x) for x in self.product_errors],
                'addition_errors': [qstr(x) for x in self.addition_errors],
                'accumulator_words_hex': [hex(x) for x in self.accumulator_words],
                'audit': self.audit,
                'relative_model_holds_for_every_performed_op': self.relative_model_holds,
                'gamma_2n': None if self.gamma_2n is None else qstr(self.gamma_2n),
                'gamma_bound': None if self.gamma_bound is None else qstr(self.gamma_bound)}


def dot_words(weights: tuple, inputs: tuple, format_name: str, *, policy='ordered') -> DotResult:
    """Zero bias, separate RNE products and left-to-right RNE adds.

    Arithmetic zeros are canonical +0. No NaN/Inf or rounded overflow is
    accepted. Native FP32 operations are individually audited by P1 C3.
    """
    require(policy == 'ordered', 'Uncertified reduction/FMA policy rejected')
    require(type(weights) is tuple and type(inputs) is tuple and len(weights)==len(inputs),
            'Equal immutable operand vectors required')
    fp=get_fp(); fmt=fp.get_format(format_name); audit=fp.Audit()
    w=tuple(fp.decode_word(v,fmt) for v in weights);h=tuple(fp.decode_word(v,fmt) for v in inputs)
    accumulator=fp.round_fraction(0,fmt); products=[]; additions=[]; words=[]
    u=Fraction(1,1 << fmt.p); relative_ok=True
    for wi,hi,wv,hv in zip(weights,inputs,w,h):
        exact_product=wv*hv
        product=fp.mul_words(wi,hi,fmt,audit)
        product_value=fp.decode_word(product,fmt)
        rho=product_value-exact_product;products.append(rho)
        exact_sum=fp.decode_word(accumulator,fmt)+product_value
        accumulator=fp.add_words(accumulator,product,fmt,audit)
        sigma=fp.decode_word(accumulator,fmt)-exact_sum;additions.append(sigma)
        words.append(accumulator)
        relative_ok &= abs(rho)<=u*abs(exact_product) and abs(sigma)<=u*abs(exact_sum)
    exact=sum((a*b for a,b in zip(w,h)),Fraction(0))
    value=fp.decode_word(accumulator,fmt)
    signed=value-exact
    require(signed==sum(products,Fraction(0))+sum(additions,Fraction(0)),
            'Local roundoff telescoping identity failed')
    bound=sum((abs(x) for x in products+additions),Fraction(0))
    require(abs(signed)<=bound,'Local error enclosure failed')
    n2=2*len(weights)
    gamma=Fraction(n2)*u/(1-Fraction(n2)*u) if n2*u<1 else None
    gamma_bound=gamma*sum((abs(a*b) for a,b in zip(w,h)),Fraction(0)) if gamma is not None and relative_ok else None
    if gamma_bound is not None:
        require(abs(signed)<=gamma_bound,'Conditional gamma bound failed')
    return DotResult(accumulator,exact,value,signed,bound,tuple(products),tuple(additions),
                     tuple(words),asdict(audit),gamma,gamma_bound,bool(relative_ok))


def dot(row: tuple, h: tuple, format_name: str, *, policy='ordered') -> DotResult:
    fp=get_fp()
    w=matrix((row,));x=matrix((h,))
    return dot_words(stored_words(w,format_name)[0],stored_words(x,format_name)[0],
                     format_name,policy=policy)


def executed_matmul(a: Matrix, b: Matrix, format_name: str) -> tuple[Matrix, list]:
    require(a.ncols==b.nrows,'Matmul shape mismatch')
    wa=stored_words(a,format_name);wb=stored_words(b,format_name)
    rows=[];records=[]
    for i in range(a.nrows):
        row=[]
        for j in range(b.ncols):
            result=dot_words(wa[i],tuple(wb[k][j] for k in range(b.nrows)),format_name)
            row.append(result.decoded_output);records.append(result)
        rows.append(tuple(row))
    return matrix(tuple(rows),ncols=b.ncols),records


def commit_weights(w: Matrix, candidate: Matrix, format_name: str) -> dict:
    """One final RNE of each exact W+candidate sum; report effective update.

    Native FP32 addition is also exercised when the candidate is already stored.
    Otherwise this is the precisely declared rational-sum/software-quantize path.
    """
    require(w.shape==candidate.shape,'Commit shape mismatch')
    fp=get_fp(); ww=stored_words(w,format_name)
    ideal_sum=add(w,candidate);new,new_words=quantize_matrix(ideal_sum,format_name)
    # The ideal delta need not itself fit one target word. Its exact sum
    # with W can still round finitely; an optional native probe must not
    # narrow the declared single-final-rounding commit domain.
    try:
        candidate_q,candidate_words=quantize_matrix(candidate,format_name)
        candidate_stored = candidate_q == candidate
    except fp.ArithmeticRejected:
        candidate_stored = False
        candidate_words = None
    native_check=False;audit=fp.Audit()
    if candidate_stored:
        for i in range(w.nrows):
            for j in range(w.ncols):
                actual=fp.add_words(ww[i][j],candidate_words[i][j],format_name,audit)
                require(actual==new_words[i][j],'Actual commit sum disagrees with exact-RNE model')
        native_check=format_name=='FP32'
    return {'new':new,'effective':sub(new,w),'quantization_error':sub(new,ideal_sum),
            'new_words':new_words,'exact_sum':ideal_sum,
            'native_FP32_additions_checked':native_check,
            'candidate_exactly_storable':candidate_stored,
            'audit':asdict(audit)}


def perturbation_certificate(w: Matrix, g: Matrix, exact_p: Matrix, q: Matrix,
                             candidate: Matrix, h: Matrix, format_name: str) -> dict:
    """Exact-rational pointwise certificate for projector/product/store/execute errors."""
    require(h.ncols==1 and w.ncols==h.nrows,'Column input needed')
    require(matmul(exact_p,h)==zeros(exact_p.nrows,1),'Input is not protected by exact projector')
    commit=commit_weights(w,candidate,format_name);new=commit['new']
    e=sub(q,exact_p);c=sub(candidate,matmul(g,q));s=commit['quantization_error']
    pterm=matmul(matmul(g,e),h);cterm=matmul(c,h);sterm=matmul(s,h)
    inputs=tuple(row[0] for row in h.rows)
    old_results=[dot(row,inputs,format_name) for row in w.rows]
    new_results=[dot(row,inputs,format_name) for row in new.rows]
    old_errors=matrix(tuple((r.signed_error,) for r in old_results),ncols=1)
    new_errors=matrix(tuple((r.signed_error,) for r in new_results),ncols=1)
    observed=matrix(tuple((b.decoded_output-a.decoded_output,) for a,b in zip(old_results,new_results)),ncols=1)
    identity=add(add(pterm,cterm),add(sterm,sub(new_errors,old_errors)))
    require(observed==identity,'Separated error identity failed')
    h_bound=norm_upper(h)
    components={'projection':norm_upper(g)*norm_upper(e)*h_bound,
                'candidate_product':norm_upper(c)*h_bound,
                'commit_quantization':norm_upper(s)*h_bound,
                'old_execution':sqrt_upper(sum((r.local_absolute_error_bound**2 for r in old_results),Fraction(0))),
                'new_execution':sqrt_upper(sum((r.local_absolute_error_bound**2 for r in new_results),Fraction(0)))}
    upper=sum(components.values(),Fraction(0));observed_sq=frobenius_squared(observed)
    require(observed_sq<=upper*upper,'Certified perturbation bound failed')
    return {'format':format_name,'old_weights':serialize(w),'candidate':serialize(candidate),
            'new_weights':serialize(new),'effective_update':serialize(commit['effective']),
            'projector_error':serialize(e),'candidate_product_error':serialize(c),
            'commit_quantization_error':serialize(s),
            'exact_projection_term':serialize(pterm),'exact_candidate_product_term':serialize(cterm),
            'exact_commit_term':serialize(sterm),'exact_observed_output_difference':serialize(observed),
            'exact_error_decomposition_holds':True,
            'norm_upper_components':{k:qstr(v) for k,v in components.items()},
            'output_2norm_upper':qstr(upper),'actual_output_2norm_squared':qstr(observed_sq),
            'bound_verified_by_rational_squared_comparison':True,
            'old_execution':[r.record() for r in old_results],
            'new_execution':[r.record() for r in new_results],
            'native_commit_addition_checked':commit['native_FP32_additions_checked'],
            'scope':'Pointwise certificate for this stored input and fixed graph; not a global/all-time or bitwise certificate'}

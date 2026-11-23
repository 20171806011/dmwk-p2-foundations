"""Finite endpoint and response capacity on explicitly declared candidate sets.

These are cardinalities, not dimensions. Prior A3 certificates are consumed
read-only and are the only live-update authority used by this module's tests.
"""
from __future__ import annotations

from collections import Counter
from fractions import Fraction
from itertools import product
import hashlib
import json
import time

from a4_runtime import get_fp, load_a2, load_a3

xp = load_a2('exact_projection')
ck = load_a3('certificate_kernel')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def decode_matrix(words, fmt):
    fp = get_fp()
    require(type(words) is tuple and len(words) > 0, 'Nonempty tuple matrix required')
    require(all(type(row) is tuple for row in words), 'Tuple rows required')
    width = len(words[0])
    require(width > 0 and all(len(row) == width for row in words), 'Consistent positive width required')
    spec = fp.get_format(fmt)
    for row in words:
        for word in row:
            require(type(word) is int and word != spec.sign_mask, 'Canonical integer word required')
            fp.decode_word(word, fmt)
    return xp.matrix(tuple(tuple(fp.decode_word(w, fmt) for w in row) for row in words))


def dense_words(words, activation, fmt):
    """Fixed bias-first zero-bias, ascending-column, separate-RNE execution."""
    fp = get_fp()
    require(type(activation) is tuple, 'Tuple activation required')
    shape = decode_matrix(words, fmt).shape
    require(len(activation) == shape[1], 'Activation width mismatch')
    for word in activation:
        require(type(word) is int and word != fp.get_format(fmt).sign_mask,
                'Canonical integer input word required')
        fp.decode_word(word, fmt)
    audit = fp.Audit()
    outputs = []
    for row in words:
        acc = 0
        for w,h in zip(row,activation):
            acc = fp.add_words(acc,fp.mul_words(w,h,fmt,audit),fmt,audit)
        outputs.append(acc)
    return tuple(outputs)


def global_generators(model_id, fmt):
    descriptor = ck.model_descriptor(model_id, fmt)
    activations = tuple(tuple(x) for s in descriptor['sites'] for x in s['activations'])
    d = descriptor['shape'][1]
    fp = get_fp()
    return xp.matrix(tuple(tuple(fp.decode_word(h[i],fmt) for h in activations)
                           for i in range(d)), ncols=len(activations))


def classify_endpoint(model_id, fmt, old_words, new_words, targets):
    """Return per-endpoint identities; BIT is recomputed by the A3 registry.

    Targets are an explicitly declared external observation set. For stateful
    registries they must be legal A inputs already admitted by that registry.
    A stateless registry allows a diagnostic observer but no program A claim.
    """
    fp = get_fp()
    descriptor = ck.model_descriptor(model_id,fmt)
    old = decode_matrix(old_words,fmt); new = decode_matrix(new_words,fmt)
    require(old.shape == new.shape == tuple(descriptor['shape']), 'Endpoint shape mismatch')
    require(type(targets) is tuple and all(type(x) is tuple for x in targets), 'Immutable target list required')
    for h in targets:
        require(len(h)==old.ncols,'Target width mismatch')
        for word in h:
            require(type(word) is int and word != fp.get_format(fmt).sign_mask,
                    'Canonical integer target words required')
            fp.decode_word(word,fmt)
    if descriptor['stateful']:
        legal = tuple(tuple(x) for x in descriptor['A_domain'])
        require(all(x in legal for x in targets), 'Target outside registered A domain')
    H = global_generators(model_id,fmt)
    delta = xp.sub(new,old)
    residual = xp.matmul(delta,H)
    alg = all(v == 0 for row in residual.rows for v in row)
    bit_reason = None
    try:
        text = ck.make_certificate(model_id,fmt,old_words,new_words)
        certificate_digest = hashlib.sha256(text.encode('utf8')).hexdigest()
        bit = True
    except ck.CertificateRejected as exc:
        bit = False; certificate_digest = None; bit_reason = str(exc)
    target_outputs=[]; old_outputs=[]; exact_responses=[]; numeric_changes=[]
    target_error=None
    for h in targets:
        require(len(h)==old.ncols,'Target width mismatch')
        hv=tuple(fp.decode_word(x,fmt) for x in h)
        exact_responses.append(tuple(sum((a*b for a,b in zip(row,hv)),Fraction(0))
                                     for row in delta.rows))
    try:
        for h in targets:
            y0=dense_words(old_words,h,fmt); y1=dense_words(new_words,h,fmt)
            old_outputs.append(y0);target_outputs.append(y1)
            numeric_changes.append(tuple(fp.decode_word(v1,fmt)-fp.decode_word(v0,fmt)
                                         for v0,v1 in zip(y0,y1)))
    except (ValueError,OverflowError) as exc:
        target_error={'type':type(exc).__name__,'message':str(exc)}
    total = target_error is None
    return {
        'endpoint_words':[list(row) for row in new_words],
        'effective_difference':xp.serialize(delta),
        'rank_effective_difference':xp.rank(delta),
        'nonzero_effective_difference':any(x != 0 for row in delta.rows for x in row),
        'ALG':alg,'BIT':bit,'E_cert':bit,'ALG_and_BIT':alg and bit,
        'BIT_field_meaning':'A3 complete-registry certificate acceptance; no claim about an unsupported external verifier',
        'exact_protected_residual':xp.serialize(residual),
        'certificate_sha256':certificate_digest,'bit_refusal_reason':bit_reason,
        'A_execution_total':total,'A_execution_error':target_error,
        'A_old_output_words':[list(x) for x in old_outputs] if total else None,
        'A_new_output_words':[list(x) for x in target_outputs] if total else None,
        'exact_A_response':[[str(x) for x in row] for row in exact_responses],
        'actual_decoded_A_change':[[str(x) for x in row] for row in numeric_changes] if total else None,
        'A_any_raw_response_changed':any(a!=b for a,b in zip(old_outputs,target_outputs)) if total else None,
        'A_per_target_raw_change':[a!=b for a,b in zip(old_outputs,target_outputs)] if total else None,
    }


def _summary(records, predicate, target_count):
    subset=[r for r in records if predicate(r)]
    total=[r for r in subset if r['A_execution_total']]
    key=lambda x:json.dumps(x,separators=(',',':'),sort_keys=True)
    return {
        'endpoints':len(subset),
        'nonzero_endpoints':sum(r['nonzero_effective_difference'] for r in subset),
        'rank_histogram':dict(sorted(Counter(str(r['rank_effective_difference']) for r in subset).items())),
        'exact_A_response_image_cardinality':len({key(r['exact_A_response']) for r in subset}),
        'A_total_execution_endpoints':len(total),
        'A_execution_refusals':len(subset)-len(total),
        'raw_A_output_image_cardinality':len({key(r['A_new_output_words']) for r in total}),
        'decoded_A_change_image_cardinality':len({key(r['actual_decoded_A_change']) for r in total}),
        'endpoints_changing_A_raw_response':sum(r['A_any_raw_response_changed'] for r in total),
        'nonzero_but_A_silent_endpoints':sum(r['nonzero_effective_difference'] and not r['A_any_raw_response_changed'] for r in total),
        'per_target_raw_output_image_cardinality':[
            len({key(r['A_new_output_words'][j]) for r in total}) for j in range(target_count)],
        'per_target_nonzero_silent_endpoints':[
            sum(r['nonzero_effective_difference'] and not r['A_per_target_raw_change'][j] for r in total)
            for j in range(target_count)],
    }


def enumerate_family(model_id, fmt, alphabet_values, target_words=None, mutable_mask=None):
    """Completely enumerate one explicit raw-word endpoint family.

    No full-format search is implied. Cardinalities are not vector-space
    dimensions, and the returned report is not an authorization capability.
    """
    start=time.perf_counter();fp=get_fp();descriptor=ck.model_descriptor(model_id,fmt)
    old_words=ck.initial_weights(model_id,fmt)
    n,d=descriptor['shape']
    require(type(alphabet_values) is tuple and len(alphabet_values)>0,'Nonempty exact alphabet tuple required')
    require(all(type(v) in (int,Fraction) for v in alphabet_values),'Exact rational alphabet required')
    words=tuple(fp.encode_constant(v,fmt) for v in alphabet_values)
    require(len(set(words))==len(words),'Alphabet values must have distinct exact stored words')
    require(all(w != fp.get_format(fmt).sign_mask for w in words),'Canonical zeros required')
    if mutable_mask is None: mutable_mask=tuple(tuple(True for _ in range(d)) for _ in range(n))
    require(type(mutable_mask) is tuple and len(mutable_mask)==n and
            all(type(row) is tuple and len(row)==d and all(type(x) is bool for x in row)
                for row in mutable_mask),'Explicit Boolean mask shape required')
    cells=tuple((i,j) for i in range(n) for j in range(d) if mutable_mask[i][j])
    one=fp.encode_constant(1,fmt)
    if target_words is None:
        require(d==2,'Explicit target words required for non-2D model')
        target_words=((one,0),(0,one),(0,0))
    require(type(target_words) is tuple,'Immutable target family required')
    expected=len(words)**len(cells)
    require(expected<=10000,'Reference family budget exceeded; no implicit unbounded search')
    records=[]
    for replacement in product(words,repeat=len(cells)):
        candidate=[list(row) for row in old_words]
        for (i,j),w in zip(cells,replacement):candidate[i][j]=w
        candidate=tuple(tuple(row) for row in candidate)
        records.append(classify_endpoint(model_id,fmt,old_words,candidate,target_words))
    H=global_generators(model_id,fmt);r=xp.rank(H)
    spec=fp.get_format(fmt)
    # Both exponent ranges have all finite encodings except the all-ones
    # exponent; the two signed zero words are merged by rejecting negative zero.
    finite_words=2*((1<<spec.exponent_bits)-1)*(1<<spec.fraction_bits)-1
    groups={
        'all_stored_candidates':_summary(records,lambda _:True,len(target_words)),
        'ALG':_summary(records,lambda x:x['ALG'],len(target_words)),
        'BIT':_summary(records,lambda x:x['BIT'],len(target_words)),
        'ALG_and_BIT':_summary(records,lambda x:x['ALG_and_BIT'],len(target_words)),
        'ALG_not_BIT':_summary(records,lambda x:x['ALG'] and not x['BIT'],len(target_words)),
        'BIT_not_ALG':_summary(records,lambda x:x['BIT'] and not x['ALG'],len(target_words)),
    }
    return {
        'model':model_id,'format':fmt,'old_words':[list(row) for row in old_words],
        'alphabet_values':[str(Fraction(v)) for v in alphabet_values],'alphabet_words':list(words),
        'mutable_mask':[list(row) for row in mutable_mask],'mutable_cells':len(cells),
        'family_size':expected,'enumerated_endpoints':len(records),
        'old_endpoint_in_family':any(r['endpoint_words']==[list(x) for x in old_words] for r in records),
        'global_generators':xp.serialize(H),'protected_rank':r,
        'abstract_ALG_dimension':n*(d-r),
        'proved_cardinality_bounds':{
            'canonical_finite_words_per_slot':finite_words,
            'all_stored_endpoints':finite_words**(n*d),
            'whole_format_ALG_endpoints':finite_words**(n*(d-r)),
            'declared_family_ALG_endpoints':min(expected,len(words)**(n*(d-r))),
            'declared_family_BIT_endpoints':expected,
            'raw_A_output_tuples_if_all_outputs_accepted':finite_words**(n*len(target_words)),
            'scope':'Bounds follow from finite encoding and an injective free-coordinate projection of the affine ALG solution set; they are not exhaustive format searches.'},
        'target_words':[list(x) for x in target_words],
        'target_scope':'Registered legal A inputs' if descriptor['stateful'] else 'Declared stateless diagnostic observer; no program A contract',
        'domain_scope':'All fixed-registry protected inputs; candidate alphabet/mask is separately finite',
        'executable_capacity_semantics':{
            'counted_set':'E_cert: endpoints accepted by the unchanged A3 complete-registry checker',
            'BIT_alias':'The BIT fields report E_cert membership and counts.',
            'agreement_condition':'For these supported fixed registries, valid initial banks, canonical finite candidate words, available correct arithmetic, and fixed version/policy, the checker exhausts every local call and invariant case. Its accepted set therefore agrees with the finite local BIT relation under the declared baseline invariant. Independent direct evaluation checks the enumerated instances.',
            'excluded':'No equality claim for arbitrary unsupported proof routes, domains, failure semantics, compilers or backends.'},
        'groups':groups,'records':records,'elapsed_seconds':time.perf_counter()-start,
        'claim':'Exact counts for this candidate family only; no full-format count or linear dimension for finite sets',
        'authorizes_commit':False,
    }

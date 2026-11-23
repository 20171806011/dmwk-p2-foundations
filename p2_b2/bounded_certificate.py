"""Read-only fixed-domain numerical budgets, never a live update authority.

The trusted A3 registry supplies complete *single-layer* input sets. A bound
does not establish closure of a perturbed feedback program. All evidence is
recomputed against explicit caller-expected endpoints and budget.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from b2_runtime import get_fp, load_a3
import certified_bounds as cb

ck=load_a3('certificate_kernel')
SCHEMA='dmwk-p2-b2-readonly-numerical-budget-v1'
METHODS=('complete_point_trace','analytic_box')
NORMS=('l2','linf')


class BudgetRejected(ValueError):
    pass


def require(value,message):
    if not value: raise BudgetRejected(message)


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def _hash(value):
    return hashlib.sha256(_json(value).encode('ascii')).hexdigest()


def _primitive(value):
    if value is None or type(value) in (str,int,bool): return value
    if type(value) in (list,tuple): return [_primitive(x) for x in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value),'Context keys must be built-in strings')
        return {k:_primitive(v) for k,v in value.items()}
    raise BudgetRejected('Context contains a noncanonical or unsupported primitive')


def _rational(value):
    require(type(value) in (int,Fraction),'Budget must be an exact built-in integer or Fraction')
    value=Fraction(value)
    require(value>=0,'Budget cannot be negative')
    return value


def _sources():
    paths=(Path(__file__),Path(cb.__file__),Path(__file__).with_name('b2_runtime.py'),
           Path(ck.__file__),Path(get_fp().__file__))
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _contract(model_id,fmt,old_words,new_words,version,snapshot_context):
    descriptor=ck.model_descriptor(model_id,fmt)
    old=ck._matrix(old_words,fmt,descriptor['shape'])
    new=ck._matrix(new_words,fmt,descriptor['shape'])
    version=ck._version(version)
    context=_primitive(snapshot_context)
    if context is not None:
        require(type(context) is dict,'Snapshot context must be a complete mapping or None')
        required={'weights','q_word','ticks','weight_version','optimizer_state','model_id','format','claim','config','schedule'}
        require(set(context)==required,'Expected complete B1 snapshot context')
        require(context['weights']==[list(r) for r in old],'Context old endpoint mismatch')
        require(context['weight_version']==version,'Context version mismatch')
        require(context['model_id']==model_id and context['format']==fmt,'Context model/format mismatch')
    return descriptor,old,new,context


def analyze_registered_domain(model_id,fmt,old_words,new_words,method='complete_point_trace',norm='l2'):
    """Pure bound on the original declared input envelope, not future reachability."""
    try:
        require(type(method) is str and method in METHODS,'Unsupported bound method')
        require(type(norm) is str and norm in NORMS,'Unsupported named output norm')
        descriptor,old,new,_=_contract(model_id,fmt,old_words,new_words,0,None)
        bias=tuple(descriptor['fixed_bias_words'])
        site_inputs=[(site['id'],tuple(h)) for site in descriptor['sites'] for h in site['activations']]
        dimension=descriptor['shape'][1]
        envelope=tuple(max(abs(get_fp().decode_word(h[j],fmt)) for _,h in site_inputs)
                       for j in range(dimension))
        if method=='complete_point_trace':
            records=[];bounds=[];linf=[];actual_sq=[];actual_inf=[]
            for site,h in site_inputs:
                point=cb.point_bound(old,new,h,fmt,old_bias=bias,new_bias=bias)
                selected=point['l2_bound'] if norm=='l2' else point['linf_bound']
                bounds.append(selected);linf.append(point['linf_bound'])
                actual_sq.append(sum((v*v for v in point['actual_change']),Fraction(0)))
                actual_inf.append(max(abs(v) for v in point['actual_change']))
                records.append({'site':site,'activation_words':list(h),'bound':cb.record(point)})
            proof={'method':method,'norm':norm,'bound':cb.record(max(bounds)),
                   'finite_actual_l2_supremum_squared':cb.record(max(actual_sq)),
                   'finite_actual_linf_supremum':cb.record(max(actual_inf)),
                   'actual_supremum_evidence':'complete finite input enumeration; not an analytic bound',
                   'call_case_count':len(records),'call_cases':records,
                   'domain':'exactly every listed input at every registered shared call site',
                   'totality':'both actual traces checked for every declared call'}
        else:
            box=cb.box_bound(old,new,envelope,fmt,old_bias=bias,new_bias=bias)
            selected=box['l2_bound'] if norm=='l2' else box['linf_bound']
            proof={'method':method,'norm':norm,'bound':cb.record(selected),
                   'input_coordinate_absolute_bounds':cb.record(envelope),
                   'included_registered_call_count':len(site_inputs),
                   'inclusion_evidence':[{'site':site,'activation_words':list(h),
                       'decoded_absolute_coordinates':cb.record(tuple(abs(get_fp().decode_word(w,fmt)) for w in h))}
                       for site,h in site_inputs],
                   'box_proof':cb.record(box),
                   'domain':'every canonical finite raw input in this proved containing coordinate box',
                   'totality':'analytic bound verifies every operation range on the box'}
        return proof
    except (ValueError,TypeError,RecursionError,OverflowError,get_fp().ExecutionError) as exc:
        if isinstance(exc,BudgetRejected): raise
        raise BudgetRejected('Domain analysis refused: '+str(exc)) from None


def make_budget_certificate(model_id,fmt,old_words,new_words,budget,method='complete_point_trace',
                            norm='l2',version=0,snapshot_context=None):
    """Build detached reproducible evidence; no publication or BIT authorization."""
    try:
        budget=_rational(budget)
        descriptor,old,new,context=_contract(model_id,fmt,old_words,new_words,version,snapshot_context)
        proof=analyze_registered_domain(model_id,fmt,old,new,method,norm)
        bound=Fraction(*proof['bound'])
        require(bound<=budget,'Certified bound exceeds the requested numerical budget')
        payload={'schema':SCHEMA,'claim':'read_only_single_layer_absolute_budget',
                 'authorizes_commit':False,'claims_BIT':False,'claims_program_noninterference':False,
                 'model_id':model_id,'format':fmt,'old_words':old,'new_words':new,
                 'expected_weight_version':version,'snapshot_context':context,
                 'snapshot_context_scope':'identity binding only; no authentication or live authority',
                 'source_descriptor':descriptor,
                 'observation':{'kind':'full_single_layer_output','ports':list(range(descriptor['shape'][0])),
                                'bias_words':descriptor['fixed_bias_words']},
                 'coverage_scope':'original registered single-layer input envelope; modified feedback reachability is unproved',
                 'candidate_state_invariant_verified':False,
                 'budget':cb.record(budget),'norm':norm,'method':method,
                 'proof':proof,'implementation_sha256':_sources()}
        return _json({'payload':payload,'payload_sha256':_hash(payload)})
    except (ValueError,TypeError,RecursionError,OverflowError,get_fp().ExecutionError) as exc:
        if isinstance(exc,BudgetRejected): raise
        raise BudgetRejected('Numerical evidence refused: '+str(exc)) from None


def _object(pairs):
    result={}
    for k,v in pairs:
        require(k not in result,'Duplicate JSON key')
        result[k]=v
    return result


def _parse(text):
    require(type(text) is str and len(text)<=4000000,'Evidence must be a bounded built-in string')
    try:
        data=json.loads(text,object_pairs_hook=_object,
                        parse_constant=lambda _: (_ for _ in ()).throw(BudgetRejected('Nonfinite JSON token')))
    except (ValueError,TypeError,RecursionError) as exc:
        raise BudgetRejected('Invalid evidence JSON: '+str(exc)) from None
    require(type(data) is dict and set(data)=={'payload','payload_sha256'},'Evidence envelope mismatch')
    require(type(data['payload']) is dict and type(data['payload_sha256']) is str,'Evidence payload mismatch')
    return data


def check_budget_certificate(text,model_id,fmt,old_words,new_words,budget,
                             method='complete_point_trace',norm='l2',version=0,snapshot_context=None):
    """Recompute all evidence against externally expected semantics and endpoints."""
    supplied=_parse(text)
    expected=make_budget_certificate(model_id,fmt,old_words,new_words,budget,method,norm,version,snapshot_context)
    require(text==expected,'Evidence differs from complete canonical semantic recomputation')
    payload=supplied['payload']
    return {'accepted_numerical_evidence':True,'authorizes_commit':False,'claims_BIT':False,
            'claims_program_noninterference':False,'norm':norm,'budget':payload['budget'],
            'bound':payload['proof']['bound'],'method':method,
            'certificate_sha256':hashlib.sha256(text.encode('ascii')).hexdigest()}

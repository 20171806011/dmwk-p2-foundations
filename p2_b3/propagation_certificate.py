"""Read-only infinity-norm propagation evidence, with no live authority.

The trusted registry and recomputed joint containment proof supply the domain
claim. Optional B3 initial context is checked against that relation. Optional
B1 context is unrelated identity metadata, never B3 state provenance.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from b3_runtime import get_fp,load_b2
import propagation_bounds as pb

SCHEMA='dmwk-p2-b3-readonly-propagation-budget-v1'
CONTEXT_SCHEMA='dmwk-p2-b3-initial-context-v1'
MODELS=('two_layer_relu_v1','shared_relu_v1','contractive_scalar_v1',
        'neutral_scalar_v1','amplifying_scalar_v1')


class PropagationRejected(ValueError):
    pass


def require(value,message):
    if not value: raise PropagationRejected(message)


def _json(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def _hash(value): return hashlib.sha256(_json(value).encode('ascii')).hexdigest()


def _primitive(value):
    if value is None or type(value) in (str,int,bool): return value
    if type(value) in (tuple,list): return [_primitive(x) for x in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value),'Context keys must be built-in strings')
        return {k:_primitive(v) for k,v in value.items()}
    raise PropagationRejected('Unsupported context primitive')


def _rational(value,name):
    require(type(value) in (int,Fraction),name+' must be an exact integer or Fraction')
    value=Fraction(value);require(value>=0,name+' must be nonnegative')
    return value


def _version(value):
    require(type(value) is int and 0<=value<(1<<63),'Version/tick must be a bounded nonnegative integer')
    return value


def _word(raw,fmt):
    fp=get_fp();spec=fp.get_format(fmt)
    require(type(raw) is int and 0<=raw<(1<<spec.total_bits),'Invalid raw initial word')
    require(((raw>>spec.fraction_bits)&spec.exponent_mask)!=spec.exponent_mask,'Nonfinite initial word')
    require(raw!=spec.sign_mask,'Initial zero must be canonical +0')
    return fp.decode_word(raw,fmt)


def _initial_context(value,descriptor,model,fmt,old,new,version,initial_error):
    value=_primitive(value)
    if value is None: return None
    expected={'schema','model_id','format','weight_version','old_banks','new_banks',
              'old_initial_words','new_initial_words','ticks','schedule'}
    require(type(value) is dict and set(value)==expected,'Incomplete B3 initial context schema')
    require(value['schema']==CONTEXT_SCHEMA,'Unknown B3 context schema')
    require(value['model_id']==model and value['format']==fmt,'B3 context model/format mismatch')
    _version(value['weight_version'])
    require(value['weight_version']==version,'B3 context version mismatch')
    require(_json(value['old_banks'])==_json(_primitive(old)) and _json(value['new_banks'])==_json(_primitive(new)),
            'B3 context physical endpoint mismatch')
    require(value['schedule']==descriptor['schedule'],'B3 context schedule mismatch')
    _version(value['ticks'])
    width=2 if model in MODELS[:2] else 1
    old_initial=value['old_initial_words'];new_initial=value['new_initial_words']
    require(type(old_initial) is list and type(new_initial) is list and
            len(old_initial)==len(new_initial)==width,'Initial context dimension mismatch')
    a=tuple(_word(w,fmt) for w in old_initial);b=tuple(_word(w,fmt) for w in new_initial)
    require(all(abs(x)<=1 for x in a+b),'Initial context is outside the registered magnitude-one domain')
    require(max(abs(x-y) for x,y in zip(a,b))<=initial_error,
            'Actual initial pair violates the declared initial relation')
    return value


def _external_context(value,fmt):
    value=_primitive(value)
    if value is None: return None
    require(type(value) is dict and set(value)=={'kind','snapshot'},'External context envelope mismatch')
    require(value['kind']=='B1_identity_only','Unknown external identity context kind')
    snapshot=value['snapshot']
    required={'model_id','format','claim','config','weights','q_word','ticks',
              'weight_version','optimizer_state','schedule'}
    require(type(snapshot) is dict and set(snapshot)==required,'Incomplete B1 external snapshot context')
    require(snapshot['format']==fmt,'External identity format mismatch')
    require(type(snapshot['schedule']) is str and bool(snapshot['schedule']),'Missing external schedule identity')
    return value


def _sources():
    cb=load_b2('certified_bounds')
    paths=(Path(__file__),Path(pb.__file__),Path(__file__).with_name('b3_runtime.py'),
           Path(cb.__file__),Path(get_fp().__file__))
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def make_propagation_certificate(model_id,fmt,old_banks,new_banks,budget,
        horizon=1,initial_error=0,method='tube',state_box=None,version=0,
        state_context=None,external_context=None):
    """Recompute a fixed-registry joint proof and emit detached numeric evidence."""
    try:
        budget=_rational(budget,'Budget');initial_error=_rational(initial_error,'Initial error')
        if state_box is not None: state_box=_rational(state_box,'State box')
        version=_version(version)
        require(type(horizon) is int and 0<=horizon<=64,'Horizon must be a built-in integer in 0..64')
        require(type(method) is str and method in ('tube','invariant'),'Unsupported domain propagation method')
        require(type(model_id) is str and model_id in MODELS,'Unknown trusted propagation registry model')
        descriptor=pb.model_descriptor(model_id,fmt)
        require(type(descriptor.get('schedule')) is str and bool(descriptor['schedule']),
                'Registry has no trusted schedule')
        initial_context=_initial_context(state_context,descriptor,model_id,fmt,old_banks,new_banks,version,initial_error)
        external=_external_context(external_context,fmt)
        proof=pb.analyze_model(model_id,fmt,old_banks,new_banks,horizon=horizon,
                              initial_error=initial_error,method=method,state_box=state_box)
        require(proof.get('domain_containment_proved') is True,'Joint domain containment was not proved')
        require(proof.get('totality_proved') is True,'Arithmetic totality was not proved')
        require(proof.get('norm')=='linf','Only a certified infinity-norm propagation claim is supported')
        require(proof['observed_bound']<=budget,'Certified observed propagation bound exceeds budget')
        payload={'schema':SCHEMA,'claim':'read_only_fixed_endpoint_full_observation_linf_budget',
            'authorizes_commit':False,'claims_BIT':False,'claims_exact_ALG':False,
            'claims_program_noninterference':False,'norm':'linf','model_id':model_id,'format':fmt,
            'old_banks':_primitive(old_banks),'new_banks':_primitive(new_banks),
            'descriptor':pb.record(descriptor),'budget':pb.record(budget),'horizon':horizon,
            'numerical_policy':pb.record(descriptor['numerical_policy']),'schedule':descriptor['schedule'],
            'domain_provenance':{'kind':'fixed trusted registry plus recomputed joint containment',
                                 'model_id':model_id,'sampled_provenance':False},
            'initial_relation':({'kind':'same canonical input vector','dimension':2,
                                  'coordinate_magnitudes_at_most':[1,1]}
                                 if model_id in MODELS[:2] else
                                 {'kind':'all paired canonical scalar states inside magnitude-one boxes',
                                  'distance_at_most':pb.record(initial_error),
                                  'zero_distance_means_same_initial_state':True}),
            'input_history':({'kind':'all same canonical input vectors in the declared box','calls':1}
                              if model_id in MODELS[:2] else
                              {'kind':'every common legal canonical scalar input history',
                               'length':horizon,'coordinate_magnitude_at_most':[1,1]}),
            'joint_domain_claim':{'old_execution':True,'new_execution':True,
                                  'through_horizon':horizon,'method':method},
            'initial_error':pb.record(initial_error),'method':method,'state_box':pb.record(state_box),
            'expected_weight_version':version,'state_context':initial_context,
            'state_context_scope':'checked initial relation and identity; not live-state authentication',
            'external_context':external,
            'external_context_scope':'unrelated B1 identity only; not B3 initial-state or endpoint provenance',
            'observation':{'scope':'all final network outputs' if model_id in MODELS[:2]
                           else 'all state coordinates at every time 0 through horizon',
                           'ports':list(range(2 if model_id in MODELS[:2] else 1))},
            'proof':pb.record(proof),'implementation_sha256':_sources()}
        return _json({'payload':payload,'payload_sha256':_hash(payload)})
    except (ValueError,TypeError,RecursionError,OverflowError,get_fp().ExecutionError) as exc:
        if isinstance(exc,PropagationRejected): raise
        raise PropagationRejected('Propagation evidence refused: '+str(exc)) from None


def _object(pairs):
    value={}
    for k,v in pairs:
        require(k not in value,'Duplicate JSON key')
        value[k]=v
    return value


def _parse(text):
    require(type(text) is str and len(text)<=16000000,'Propagation evidence must be a bounded built-in string')
    try:
        parsed=json.loads(text,object_pairs_hook=_object,
            parse_constant=lambda _: (_ for _ in ()).throw(PropagationRejected('Nonfinite JSON token')))
    except (ValueError,TypeError,RecursionError) as exc:
        raise PropagationRejected('Invalid propagation JSON: '+str(exc)) from None
    require(type(parsed) is dict and set(parsed)=={'payload','payload_sha256'},'Propagation envelope mismatch')
    require(type(parsed['payload']) is dict and type(parsed['payload_sha256']) is str,'Propagation payload mismatch')
    return parsed


def check_propagation_certificate(text,model_id,fmt,old_banks,new_banks,budget,
        horizon=1,initial_error=0,method='tube',state_box=None,version=0,
        state_context=None,external_context=None):
    supplied=_parse(text)
    expected=make_propagation_certificate(model_id,fmt,old_banks,new_banks,budget,
        horizon,initial_error,method,state_box,version,state_context,external_context)
    require(text==expected,'Propagation evidence differs from complete canonical semantic recomputation')
    payload=supplied['payload']
    return {'accepted_numerical_evidence':True,'authorizes_commit':False,'claims_BIT':False,
            'claims_exact_ALG':False,'claims_program_noninterference':False,
            'norm':'linf','bound':payload['proof']['observed_bound'],'budget':payload['budget'],
            'horizon':horizon,'method':method,'certificate_sha256':hashlib.sha256(text.encode('ascii')).hexdigest()}

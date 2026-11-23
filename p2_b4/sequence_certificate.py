"""Read-only changing-history budgets; never exact-D update authority."""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path

from b4_runtime import get_fp,load_b2,load_b3
import switching_bounds as sb
import update_sequence as us

SCHEMA='dmwk-p2-b4-readonly-switching-budget-v1'


class NumericalRejected(ValueError):
    def __init__(self,message,ledger=None):
        super().__init__(message);self.ledger=ledger


def require(test,message):
    if not test:raise NumericalRejected(message)


def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def _hash(value):return hashlib.sha256(_json(value).encode('ascii')).hexdigest()


def _primitive(value):
    if value is None or type(value) in (str,int,bool):return value
    if type(value) in (list,tuple):return [_primitive(x) for x in value]
    if type(value) is dict:
        require(all(type(k) is str for k in value),'Primitive keys must be built-in strings')
        return {k:_primitive(v) for k,v in value.items()}
    raise NumericalRejected('Unsupported identity/history primitive')


def _rat(value,name):
    require(type(value) in (int,Fraction),name+' must be an exact integer or Fraction')
    value=Fraction(value);require(value>=0,name+' must be nonnegative')
    return value


def _cap(value):
    if value is None:return None
    if type(value) in (int,Fraction):return (_rat(value,'State cap'),)
    require(type(value) in (tuple,list),'Invalid state cap type')
    return tuple(_rat(v,'State cap coordinate') for v in value)


def _context(value,fmt):
    value=_primitive(value)
    if value is None:return None
    require(type(value) is dict and set(value)=={'kind','snapshot'},'Identity context envelope mismatch')
    require(value['kind']=='B4_exact_D_identity_only','Unsupported external context kind')
    snapshot=value['snapshot']
    fields={'schema','schedule','task','D_descriptor','kernel','accepted_updates','nonzero_stored_updates',
            'accepted_ledger','tick_ledger','ledger_tail_sha256','ledger_policy','origin_kernel_sha256','capacity'}
    require(type(snapshot) is dict and set(snapshot)==fields,'Incomplete B4 combined identity snapshot')
    require(snapshot['schema']==us.SCHEMA and snapshot['schedule']==us.SCHEDULE,'Wrong B4 snapshot schedule/schema')
    kernel=snapshot['kernel']
    kernel_fields={'model_id','format','claim','config','weights','q_word','ticks','weight_version','optimizer_state','schedule'}
    require(type(kernel) is dict and set(kernel)==kernel_fields,'Incomplete nested kernel identity')
    require(kernel['format']==fmt and type(kernel['schedule']) is str,'Context numerical identity mismatch')
    return value


def _sources():
    pb=load_b3('propagation_bounds');cb=load_b2('certified_bounds')
    paths=(Path(__file__),Path(sb.__file__),Path(us.__file__),Path(pb.__file__),Path(cb.__file__),
           Path(__file__).with_name('b4_runtime.py'),Path(get_fp().__file__))
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def make_sequence_certificate(model_id,fmt,old_history,new_history,old_schedule,new_schedule,budget,
        initial_error=0,comparison='two_histories',method='tube',state_box=None,common_family=None,
        version=0,initial_pair=None,external_context=None):
    try:
        budget=_rat(budget,'Budget');initial_error=_rat(initial_error,'Initial error');state_box=_cap(state_box)
        require(type(version) is int and 0<=version<(1<<63),'Invalid analysis version')
        descriptor=sb.model_descriptor(model_id,fmt)
        require(type(descriptor.get('schedule')) is str,'Missing trusted switching schedule')
        external=_context(external_context,fmt)
        initial=None
        if initial_pair is not None:
            require(type(initial_pair) in (list,tuple) and len(initial_pair)==2,'Expected two initial state vectors')
            # With empty histories of ticks this is only a validated initial
            # relation, not a sampled substitute for future domain coverage.
            initial=sb.compare_model_traces(model_id,fmt,old_history,new_history,(),(),
                initial_pair[0],initial_pair[1],(),initial_error=initial_error,comparison='two_histories')
        proof=sb.analyze_model(model_id,fmt,old_history,new_history,old_schedule,new_schedule,
            initial_error=initial_error,comparison=comparison,method=method,state_box=state_box,
            common_family=common_family,budget=budget)
        require(proof.get('domain_containment_proved') is True and proof.get('totality_proved') is True,
                'Joint switching domain/totality proof missing')
        require(proof.get('norm')=='linf','Unsupported propagation norm')
        require(proof['observed_bound']<=budget,'Prefix observation bound exceeds budget')
        payload={'schema':SCHEMA,'claim':'read_only_full_state_prefix_linf_budget',
            'authorizes_commit':False,'claims_BIT':False,'claims_exact_ALG':False,
            'claims_program_noninterference':False,'model_id':model_id,'format':fmt,
            'descriptor':sb.record(descriptor),'old_history':_primitive(old_history),'new_history':_primitive(new_history),
            'old_schedule':_primitive(old_schedule),'new_schedule':_primitive(new_schedule),
            'horizon':len(old_schedule),'comparison':comparison,'method':method,'state_box':sb.record(state_box),
            'common_family':_primitive(common_family),'initial_error':sb.record(initial_error),
            'initial_relation':'all registered canonical initial pairs within declared boxes and distance <= initial_error',
            'same_input_history':True,'history_quantifier':'every common legal canonical input history through horizon',
            'initial_pair':_primitive(initial_pair),'initial_pair_check':sb.record(initial),
            'norm':'linf','observation':'all state coordinates at every prefix 0..T',
            'budget':sb.record(budget),'analysis_version':version,
            'numerical_policy':sb.record(descriptor['numerical_policy']),'schedule_policy':descriptor['schedule'],
            'domain_provenance':{'kind':'fixed trusted registry plus recomputed joint tube/invariant','samples':False},
            'external_context':external,
            'external_context_scope':'exact-D snapshot identity only; no mapping to switching state/history or live authority',
            'proof':sb.record(proof),'source_sha256':_sources()}
        return _json({'payload':payload,'payload_sha256':_hash(payload)})
    except (ValueError,TypeError,RecursionError,OverflowError,get_fp().ExecutionError) as exc:
        if isinstance(exc,NumericalRejected):raise
        ledger=getattr(exc,'ledger',None)
        raise NumericalRejected('Switching evidence refused: '+str(exc),ledger) from None


def _object(pairs):
    out={}
    for k,v in pairs:
        require(k not in out,'Duplicate JSON key');out[k]=v
    return out


def _parse(text):
    require(type(text) is str and len(text)<=16000000,'Evidence must be a bounded built-in string')
    try:
        value=json.loads(text,object_pairs_hook=_object,
            parse_constant=lambda _: (_ for _ in ()).throw(NumericalRejected('Nonfinite JSON token')))
    except (ValueError,TypeError,RecursionError) as exc:
        raise NumericalRejected('Invalid evidence JSON: '+str(exc)) from None
    require(type(value) is dict and set(value)=={'payload','payload_sha256'},'Evidence envelope mismatch')
    require(type(value['payload']) is dict and type(value['payload_sha256']) is str,'Evidence payload mismatch')
    return value


def check_sequence_certificate(text,model_id,fmt,old_history,new_history,old_schedule,new_schedule,budget,
        initial_error=0,comparison='two_histories',method='tube',state_box=None,common_family=None,
        version=0,initial_pair=None,external_context=None):
    supplied=_parse(text)
    expected=make_sequence_certificate(model_id,fmt,old_history,new_history,old_schedule,new_schedule,budget,
        initial_error,comparison,method,state_box,common_family,version,initial_pair,external_context)
    require(text==expected,'Evidence differs from complete canonical recomputation')
    payload=supplied['payload']
    return {'accepted_numerical_evidence':True,'authorizes_commit':False,'claims_BIT':False,
            'claims_exact_ALG':False,'claims_program_noninterference':False,'norm':'linf',
            'bound':payload['proof']['observed_bound'],'budget':payload['budget'],
            'horizon':payload['horizon'],'comparison':comparison,'method':method,
            'certificate_sha256':hashlib.sha256(text.encode('ascii')).hexdigest()}

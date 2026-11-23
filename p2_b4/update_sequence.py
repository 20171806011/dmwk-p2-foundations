"""Trusted serial exact-D updates with one kernel/history publication.

The existing B1 gate is unchanged. A private deep copy is committed and its
ledger constructed before the outer owner publishes a single CombinedState.
This is not concurrent, crash-durable or malicious-memory-safe machinery.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from b4_runtime import get_fp,load_b1

ok=load_b1('optimizer_kernel');cu=load_b1('constrained_updates');xp=cu.xp
MODEL='structural_duplicate_v1'
SCHEDULE='p2-b4-trusted-serial-copy-check-ledger-single-publication-v1'
SCHEMA='dmwk-p2-b4-exact-D-sequence-v1'


class SequenceRejected(ValueError): pass


def require(test,message):
    if not test:raise SequenceRejected(message)


def _json(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def _hash(value): return hashlib.sha256(_json(value).encode('ascii')).hexdigest()
def _pair(value): return [value.numerator,value.denominator]


def _version(value):
    require(type(value) is int and 0<=value<=(1<<63)-1,'Expected bounded nonnegative integer')
    return value


def _sources():
    paths=(Path(__file__),Path(ok.__file__),Path(cu.__file__),Path(__file__).with_name('b4_runtime.py'),Path(get_fp().__file__))
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def _task(fmt):
    one=get_fp().encode_constant(1,fmt)
    return {'task_id':'reserved_theta_squared_loss_v1','A_input_words':[0,0,one],
            'target_exact':[[1,1],[-1,1]],'loss':'half exact squared error after decoding actual A output',
            'gradient':'continuous linear squared-loss extension, not derivative of finite rounding',
            'D_model':MODEL,'D_claim':'ALG_AND_BIT','fixed_protection':True,
            'new_task_admission':False,'A_to_D_feedback':False}


def _A(words,fmt):
    fp=get_fp();one=fp.encode_constant(1,fmt)
    out=ok.evaluate_a(words,(0,0,one),fmt,MODEL)
    values=tuple(fp.decode_word(w,fmt) for w in out['output_words'])
    loss=sum(((v-target)**2 for v,target in zip(values,(Fraction(1),Fraction(-1)))),Fraction(0))/2
    return {'output_words':out['output_words'],'decoded_output':[_pair(v) for v in values],
            'loss':_pair(loss),'arithmetic_counts':out['arithmetic_counts']}


def _full_D(words,fmt):
    one=get_fp().encode_constant(1,fmt)
    return [{'q_word':q,'u_word':u,'trace':ok.evaluate_d(words,q,u,fmt,MODEL)}
            for q in (0,one) for u in (0,one)]


def _norm(matrix):
    return max(sum((abs(v) for v in row),Fraction(0)) for row in matrix.rows)


def _capacity(fmt):
    H=ok.global_generators(MODEL,fmt);r=xp.rank(H)
    augmented=xp.matrix(tuple(tuple(row)+(Fraction(int(i==2)),) for i,row in enumerate(H.rows)))
    return {'dimension_scope':'exact algebra on the fixed globally registered protected span',
        'global_generator_matrix':cu.matrix_record(H),'protected_rank':r,
        'unrestricted_annihilator_dimension':2*(3-r),'reserved_column_dimension':2,
        'max_reserved_update_rank':1,'A_e3_response_dimension':2*(xp.rank(augmented)-r),
        'global_provenance':'all two shared B1 structural sites, every canonical Boolean q/u',
        'update_count_does_not_consume_fixed_space':True,
        'storable_or_BIT_capacity_is_not_this_dimension':True}


@dataclass(frozen=True)
class CombinedState:
    kernel:object
    accepted_ledger:tuple[str,...]
    tick_ledger:tuple[str,...]


class SequenceKernel:
    __slots__=('_state','_fmt','_max_updates','_origin_json')

    def __init__(self,fmt,config,max_updates=128):
        require(not hasattr(self,'_state'),'A sequence owner cannot be reinitialized')
        _version(max_updates)
        kernel=ok.OptimizerKernel(MODEL,fmt,config,claim='ALG_AND_BIT')
        self._fmt=fmt;self._max_updates=max_updates;self._origin_json=_json(kernel.snapshot())
        self._state=CombinedState(kernel,(),())

    def snapshot(self):
        state=self._state
        ledger=[json.loads(s) for s in state.accepted_ledger]
        return {'schema':SCHEMA,'schedule':SCHEDULE,'task':_task(self._fmt),
            'D_descriptor':ok.model_descriptor(MODEL,self._fmt),'kernel':state.kernel.snapshot(),
            'accepted_updates':len(ledger),'nonzero_stored_updates':sum(x['nonzero_stored_change'] for x in ledger),
            'accepted_ledger':ledger,'tick_ledger':[json.loads(s) for s in state.tick_ledger],
            'ledger_tail_sha256':_hash(ledger),'ledger_policy':{'max_accepted_updates':self._max_updates,
                'scope':'administrative history limit, not algebraic capacity or D error budget'},
            'origin_kernel_sha256':hashlib.sha256(self._origin_json.encode('ascii')).hexdigest(),
            'capacity':_capacity(self._fmt)}

    @property
    def weights(self):return self._state.kernel.weights
    @property
    def state_word(self):return self._state.kernel.state_word
    @property
    def accepted_count(self):return len(self._state.accepted_ledger)
    @property
    def ticks(self):return self._state.kernel.ticks

    def evaluate_a(self):return _A(self._state.kernel.weights,self._fmt)
    def full_D(self):return _full_D(self._state.kernel.weights,self._fmt)

    def toy_gradient(self):
        values=tuple(Fraction(*v) for v in self.evaluate_a()['decoded_output'])
        return xp.matrix(((0,0,values[0]-1),(0,0,values[1]+1)))

    def _prepared(self,request):
        before=self.snapshot();current=self._state
        staged=deepcopy(current.kernel)
        inner_text=staged.prepare(request)
        inner_record=json.loads(inner_text)
        inner_receipt=staged.commit(inner_text)
        # This deliberately follows copy-local commit: a late ledger refusal
        # must not publish even the successfully staged optimizer/endpoint.
        require(len(current.accepted_ledger)<self._max_updates,'Administrative accepted-ledger limit exhausted after staging')
        old_words=current.kernel.weights;new_words=staged.weights
        old=ok.decode_matrix(old_words,self._fmt);new=ok.decode_matrix(new_words,self._fmt)
        delta=xp.sub(new,old)
        origin=json.loads(self._origin_json)
        base=ok.decode_matrix(origin['weights'],self._fmt);prefix=xp.sub(new,base)
        D_old=_full_D(old_words,self._fmt);D_new=_full_D(new_words,self._fmt)
        require(D_old==D_new,'Complete registered D observations changed')
        require(staged.state_word==current.kernel.state_word and staged.ticks==current.kernel.ticks,
                'A weight transaction changed protected q/ticks')
        previous_path=Fraction(0) if not current.accepted_ledger else Fraction(*json.loads(current.accepted_ledger[-1])['path_increment_norm_sum'])
        event={'accepted_index':len(current.accepted_ledger)+1,'execution_tick':current.kernel.ticks,
            'old_combined_sha256':_hash(before),'old_words':old_words,'new_words':new_words,
            'request':inner_record['payload']['staged']['request'],
            'ideal_increment':inner_record['payload']['staged']['increment'],
            'actual_effective_delta':cu.matrix_record(delta),'actual_effective_rank':xp.rank(delta),
            'nonzero_stored_change':any(v for row in delta.rows for v in row)!=0,
            'prefix_delta_from_initial':cu.matrix_record(prefix),'prefix_delta_rank':xp.rank(prefix),
            'path_increment_norm_sum':_pair(previous_path+_norm(delta)),
            'path_norm_scope':'descriptive adjacent-update path length; not an added execution-error term',
            'old_A':_A(old_words,self._fmt),'new_A':_A(new_words,self._fmt),
            'D_complete_observations':D_new,'D_bitwise_equal_to_previous':True,
            'capacity':_capacity(self._fmt),'inner_B1_receipt':inner_receipt,
            'old_optimizer_state':before['kernel']['optimizer_state'],
            'new_optimizer_state':staged.snapshot()['optimizer_state']}
        next_state=CombinedState(staged,current.accepted_ledger+(_json(event),),current.tick_ledger)
        payload={'schema':'dmwk-p2-b4-exact-update-candidate-v1','authorizes_exact_D_candidate':True,
            'claim':'unchanged_B1_ALG_AND_BIT_plus_serial_history',
            'old_combined_snapshot':before,'old_combined_sha256':_hash(before),
            'request':inner_record['payload']['staged']['request'],'inner_B1_prepared':inner_text,
            'new_accepted_event':event,'new_kernel_snapshot':staged.snapshot(),
            'schedule':SCHEDULE,'task':_task(self._fmt),
            'D_descriptor':ok.model_descriptor(MODEL,self._fmt),'source_sha256':_sources()}
        return _json({'payload':payload,'payload_sha256':_hash(payload)}),next_state

    def preview(self,request):
        try:
            text,_=self._prepared(request)
            payload=json.loads(text)['payload']
            return {'certified_for_publication':False,'candidate_kernel':payload['new_kernel_snapshot'],
                    'candidate_event':payload['new_accepted_event'],'old_combined_sha256':payload['old_combined_sha256']}
        except (ValueError,TypeError,OverflowError,get_fp().ExecutionError) as exc:
            raise SequenceRejected('Preview refused without publication: '+str(exc)) from None

    def prepare(self,request):
        try:return self._prepared(request)[0]
        except (ValueError,TypeError,OverflowError,get_fp().ExecutionError) as exc:
            raise SequenceRejected('Preparation refused without publication: '+str(exc)) from None

    def commit(self,text):
        try:
            supplied=_parse(text);payload=supplied['payload']
            require(payload.get('schema')=='dmwk-p2-b4-exact-update-candidate-v1','Not an exact B4 update candidate')
            require(payload.get('old_combined_sha256')==_hash(self.snapshot()),'Stale combined endpoint/state/ledger context')
            expected,next_state=self._prepared(payload.get('request'))
            require(text==expected,'Candidate differs from complete staged semantic recomputation')
            event=json.loads(next_state.accepted_ledger[-1])
            receipt={'accepted':True,'claim':'ALG_AND_BIT','accepted_index':len(next_state.accepted_ledger),
                'weight_version':next_state.kernel.version,'optimizer_step':next_state.kernel.snapshot()['optimizer_state']['step'],
                'ticks':next_state.kernel.ticks,'nonzero_stored_change':event['nonzero_stored_change'],
                'candidate_sha256':hashlib.sha256(expected.encode('ascii')).hexdigest()}
        except (ValueError,TypeError,RecursionError,OverflowError,get_fp().ExecutionError) as exc:
            raise SequenceRejected('Commit refused without publication: '+str(exc)) from None
        self._state=next_state
        return receipt

    def tick(self,u_word):
        try:
            current=self._state;before=self.snapshot();staged=deepcopy(current.kernel)
            trace=staged.tick(u_word)
            event={'tick':staged.ticks,'accepted_update_index':len(current.accepted_ledger),
                'weight_version':staged.version,'input_word':u_word,'old_q_word':current.kernel.state_word,
                'new_q_word':staged.state_word,'trace':trace,'old_combined_sha256':_hash(before)}
            next_state=CombinedState(staged,current.accepted_ledger,current.tick_ledger+(_json(event),))
            receipt={'trace':trace,'tick':staged.ticks,'accepted_update_index':len(current.accepted_ledger),
                     'weight_version':staged.version}
        except (ValueError,TypeError,OverflowError,get_fp().ExecutionError) as exc:
            raise SequenceRejected('Tick refused without publication: '+str(exc)) from None
        self._state=next_state
        return receipt


def _object(pairs):
    value={}
    for k,v in pairs:
        require(k not in value,'Duplicate JSON key');value[k]=v
    return value


def _parse(text):
    require(type(text) is str and len(text)<=16000000,'Candidate must be a bounded built-in string')
    try:
        data=json.loads(text,object_pairs_hook=_object,
            parse_constant=lambda _: (_ for _ in ()).throw(SequenceRejected('Nonfinite JSON token')))
    except (ValueError,TypeError,RecursionError) as exc:
        raise SequenceRejected('Invalid candidate JSON: '+str(exc)) from None
    require(type(data) is dict and set(data)=={'payload','payload_sha256'},'Candidate envelope mismatch')
    require(type(data['payload']) is dict and type(data['payload_sha256']) is str,'Candidate payload mismatch')
    return data

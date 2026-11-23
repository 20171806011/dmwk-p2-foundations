"""Independent finite B1 review; no prior verification module is imported.

Exact projection is characterized by direct annihilation and orthogonal
residual equations, with determinant/minor rank. IEEE rounding uses an
independent ordered-word search, including the host binary64 optimizer model.
These checks are finite evidence, not proof-assistant verification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as Q
from functools import lru_cache
from itertools import combinations, product
from pathlib import Path
import hashlib
import json
import random
import sys
import time
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def det(a):
    if not a:
        return Q(1)
    if len(a) == 1:
        return a[0][0]
    return sum(((-1)**j * a[0][j] * det(tuple(
        tuple(row[k] for k in range(len(a)) if k != j)
        for row in a[1:])) for j in range(len(a))), Q(0))


def row_basis(rows, width=None):
    width = len(rows[0]) if rows else (0 if width is None else width)
    selected = []
    for row in rows:
        if len(selected) == width:
            break
        trial = selected + [tuple(Q(x) for x in row)]
        size = len(trial)
        if any(det(tuple(tuple(r[j] for j in cols) for r in trial)) != 0
               for cols in combinations(range(width), size)):
            selected = trial
    return tuple(selected)


def rank(rows, width=None):
    return len(row_basis(rows, width))


def transpose(a, width=None):
    width = len(a[0]) if a else (0 if width is None else width)
    return tuple(tuple(row[j] for row in a) for j in range(width))


def mul(a, b, out_width=None):
    width = len(b[0]) if b else (0 if out_width is None else out_width)
    return tuple(tuple(sum((row[k]*b[k][j] for k in range(len(b))), Q(0))
                       for j in range(width)) for row in a)


def zero(a):
    return all(x == 0 for row in a for x in row)


def sub(a, b):
    return tuple(tuple(x-y for x,y in zip(ra,rb)) for ra,rb in zip(a,b))


def scale(a, s):
    return tuple(tuple(s*x for x in row) for row in a)


def add(a, b):
    return tuple(tuple(x+y for x,y in zip(ra,rb)) for ra,rb in zip(a,b))


def shape_values(values, n, d):
    return tuple(tuple(Q(x) for x in values[i*d:(i+1)*d]) for i in range(n))


def projection_equations(g, h, delta):
    """These equations uniquely characterize the orthogonal projection."""
    if not zero(mul(delta,h)):
        return False
    protected_rows = transpose(h)
    protected_rank = rank(protected_rows, len(h))
    return all(rank(protected_rows+(row,),len(h)) == protected_rank
               for row in sub(g,delta))


def format_parameters(fmt):
    return {'BF16':(8,8), 'FP32':(24,8), 'F64':(53,11)}[fmt]


@lru_cache(maxsize=None)
def word_value(raw, fmt):
    p,e = format_parameters(fmt)
    fraction_bits=p-1
    sign = -1 if raw >> (fraction_bits+e) else 1
    exp=(raw >> fraction_bits) & ((1<<e)-1)
    mant=raw & ((1<<fraction_bits)-1)
    if exp == (1<<e)-1:
        raise ValueError('Nonfinite word is outside the admitted domain')
    bias=(1<<(e-1))-1
    if exp:
        mant += 1<<fraction_bits
        power=exp-bias-fraction_bits
    else:
        power=1-bias-fraction_bits
    return sign*Q(mant)*(Q(2)**power)


@lru_cache(maxsize=None)
def round_word(value, fmt):
    """Canonical-zero finite RNE via monotone positive-word binary search."""
    value=Q(value)
    if value == 0:
        return 0
    p,e=format_parameters(fmt)
    sign=(1<<(p+e-1)) if value < 0 else 0
    value=abs(value)
    maximum=(((1<<e)-2)<<(p-1))|((1<<(p-1))-1)
    max_value=word_value(maximum,fmt)
    if value >= max_value+(max_value-word_value(maximum-1,fmt))/2:
        raise OverflowError('Finite output policy rejects rounded infinity')
    if value >= max_value:
        return sign|maximum
    lo,hi=0,maximum
    while lo+1 < hi:
        mid=(lo+hi)//2
        if word_value(mid,fmt) <= value:
            lo=mid
        else:
            hi=mid
    low=word_value(lo,fmt)
    high=word_value(hi,fmt)
    dl,dh=value-low,high-value
    result=lo if dl < dh or (dl == dh and lo%2 == 0) else hi
    return (sign|result) if result else 0


def f64(value):
    return word_value(round_word(Q(value),'F64'),'F64')


@lru_cache(maxsize=None)
def sqrt64(value):
    """Binary64 square root rounded by exact comparisons to midpoint squares."""
    value=Q(value)
    if value < 0:
        raise ValueError('Negative square root')
    if value == 0:
        return Q(0)
    maximum=((2046)<<52)|((1<<52)-1)
    lo,hi=0,maximum
    while lo+1 < hi:
        mid=(lo+hi)//2
        v=word_value(mid,'F64')
        if v*v <= value:
            lo=mid
        else:
            hi=mid
    low,high=word_value(lo,'F64'),word_value(hi,'F64')
    mid=(low+high)/2
    return low if value < mid*mid or (value == mid*mid and lo%2 == 0) else high


def dense_words(bank, inputs, fmt):
    outputs=[]
    for row in bank:
        acc=0
        for w,x in zip(row,inputs):
            term=round_word(word_value(w,fmt)*word_value(x,fmt),fmt)
            acc=round_word(word_value(acc,fmt)+word_value(term,fmt),fmt)
        outputs.append(acc)
    return tuple(outputs)


def endpoint(old_words, increment, fmt):
    return tuple(tuple(round_word(word_value(w,fmt)+x,fmt)
                       for w,x in zip(row,delta))
                 for row,delta in zip(old_words,increment))


def square_loss(output_words, target, fmt):
    return sum(((word_value(v,fmt)-Q(t))**2 for v,t in zip(output_words,target)),Q(0))/2


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ones_projection(a):
    return tuple(tuple(v-sum(row,Q(0))/len(row) for v in row) for row in a)


def direct_clip(a, mode, bound):
    if mode == 'none':
        return a
    if mode == 'element':
        return tuple(tuple(max(-bound,min(bound,x)) for x in row) for row in a)
    norm=sqrt64(f64(sum((x*x for row in a for x in row),Q(0))))
    factor=Q(1) if norm == 0 else min(Q(1),f64(f64(bound)/norm))
    return scale(a,factor)


def direct_optimizer(w, gradient, state, config, mode):
    """Independent exact/word-RNE reference for specified finite fixtures.

    Bias-correction powers are initially evaluated as exact rational powers
    rounded once. Dyadic fixture coefficients/steps make these powers exact;
    this is not a proof that arbitrary host libm pow is correctly rounded.
    """
    step,m0,v0=state
    step+=1
    g=ones_projection(gradient) if mode == 'gradient_only' else gradient
    if config.kind == 'sgd':
        m,v=m0,v0
        delta=scale(g,-config.learning_rate)
    elif config.kind == 'momentum':
        m=add(scale(m0,config.momentum),scale(g,1-config.momentum))
        v=v0
        delta=scale(m,-config.learning_rate)
    else:
        b1,b2,lr,eps=map(f64,(config.beta1,config.beta2,config.learning_rate,config.epsilon))
        d1=f64(1-f64(b1**step));d2=f64(1-f64(b2**step))
        ms=[];vs=[];ds=[]
        for grow,mrow,vrow in zip(g,m0,v0):
            mr=[];vr=[];dr=[]
            for gi,mi,vi in zip(grow,mrow,vrow):
                gf=f64(gi)
                mf=f64(f64(b1*f64(mi))+f64(f64(1-b1)*gf))
                vf=f64(f64(b2*f64(vi))+f64(f64(1-b2)*f64(gf*gf)))
                mh,vh=f64(mf/d1),f64(vf/d2)
                denominator=f64(sqrt64(vh)+eps)
                mr.append(mf);vr.append(vf);dr.append(-f64(lr*f64(mh/denominator)))
            ms.append(tuple(mr));vs.append(tuple(vr));ds.append(tuple(dr))
        m,v,delta=tuple(ms),tuple(vs),tuple(ds)
    raw=add(delta,scale(w,-config.learning_rate*config.weight_decay))
    increment=direct_clip(raw,config.clip_mode,config.clip_bound)
    if mode == 'projected':
        increment=ones_projection(increment)
    elif mode == 'structural':
        increment=tuple(tuple(x if j==2 else Q(0) for j,x in enumerate(row)) for row in increment)
    return raw,increment,(step,m,v)


def check_algebra():
    import constrained_updates as cu
    rng=random.Random(SEED)
    cases=0;null_cases=0;lowrank_cases=0
    for entries in product((0,1),repeat=6):
        h=shape_values(entries,3,2);hm=cu.Matrix(h,2)
        c=3-rank(transpose(h))
        for _ in range(8):
            g=shape_values([Q(rng.randrange(-4,5),rng.randrange(1,5)) for _ in range(6)],2,3)
            gm=cu.Matrix(g,3)
            projected=cu.project_direction(gm,hm).rows
            require(projection_equations(g,h,projected),'Projection fails independent exact characterization')
            require(cu.project_direction(cu.Matrix(projected,3),hm).rows==projected,
                    'Projection not idempotent')
            z=shape_values([rng.randrange(-2,3) for _ in range(2*c)],2,c)
            zn=cu.nullspace_update(cu.Matrix(z,c),hm).rows
            require(zero(mul(zn,h)) and rank(zn)==rank(z,c),
                    'Nullspace parameterization violates direct null/rank constraints')
            null_cases+=1
            k=rng.randrange(4)
            left=shape_values([rng.randrange(-2,3) for _ in range(2*k)],2,k)
            right=shape_values([rng.randrange(-2,3) for _ in range(k*3)],k,3)
            out=cu.lowrank_update(cu.Matrix(left,k),cu.Matrix(right,3),hm).rows
            direct_product=mul(left,right,out_width=3)
            require(projection_equations(direct_product,h,out) and rank(out)<=min(k,2,c),
                    'Low-rank parameterization violates independent projection/rank equations')
            lowrank_cases+=1;cases+=1
    return {'binary_3x2_generators':64,'projection_characterizations':cases,
            'nullspace_rank_checks':null_cases,'lowrank_projection_checks':lowrank_cases,
            'seed':SEED,'method':'Direct annihilation and residual-span equations; determinant/minor ranks',
            'scope':'Finite exact constraints; universal projection theorem remains handwritten'}


def check_optimizer():
    import constrained_updates as cu
    rng=random.Random(SEED+1)
    h=cu.Matrix(((Q(1),),(Q(1),),(Q(1),)),1)
    counts={};cases=0
    for kind in ('sgd','momentum','adamw'):
        for clip_mode in ('none','element','global_norm'):
            for mode in ('none','gradient_only','projected','structural'):
                for trial in range(4):
                    values=lambda:[Q(rng.randrange(-5,6),rng.randrange(1,5)) for _ in range(6)]
                    w=shape_values(values(),2,3);g=shape_values(values(),2,3)
                    m=shape_values(values(),2,3)
                    v=shape_values([abs(x) for x in values()],2,3)
                    config=cu.OptimizerConfig(kind,Q(1,4),momentum=Q(1,2),beta1=Q(1,2),beta2=Q(3,4),
                                              epsilon=Q(1,8),weight_decay=Q(1,16),
                                              clip_mode=clip_mode,clip_bound=None if clip_mode=='none' else Q(3,4))
                    state=cu.OptimizerState(trial,cu.Matrix(m,3),cu.Matrix(v,3))
                    staged=cu.stage_optimizer(cu.Matrix(w,3),cu.Matrix(g,3),state,config,mode,h,(2,))
                    raw,increment,next_state=direct_optimizer(w,g,(trial,m,v),config,mode)
                    require(staged.raw_increment.rows==raw,'Optimizer raw increment differs from independent reference')
                    require(staged.increment.rows==increment,'Optimizer clipping/restriction order differs')
                    require((staged.next_state.step,staged.next_state.m.rows,staged.next_state.v.rows)==next_state,
                            'Optimizer state differs from independent ordered reference')
                    if mode=='projected':require(zero(mul(increment,h.rows)),'Final projected increment is not an annihilator')
                    counts[kind]=counts.get(kind,0)+1;cases+=1
    return {'proposal_cases':cases,'cases_by_kind':counts,'seed':SEED+1,
            'host_reference':'Exact IEEE decoding and word-search RNE, including exact midpoint-square sqrt rounding',
            'bias_power_scope':'Selected dyadic coefficients and steps have exactly representable powers; no arbitrary libm certification',
            'scope':'Finite equality of moments, raw increments, clipping, final restriction and next states'}


def decoded_record(record):
    return tuple(tuple(Q(*pair) for pair in row) for row in record['rows'])


def decoded_state(record):
    return record['step'],decoded_record(record['m']),decoded_record(record['v'])


def decoded_config(record):
    return SimpleNamespace(**{key:(Q(*value) if isinstance(value,list) else value)
                              for key,value in record.items()})


def word_matrix(record):
    return tuple(tuple(row) for row in record)


def decoded_words(words,fmt):
    return tuple(tuple(word_value(v,fmt) for v in row) for row in words)


def observation(words,q,u,fmt):
    one=round_word(Q(1),fmt)
    first=tuple(tuple(row[:2]) for row in words)
    os=dense_words(first,(q,q),fmt);oi=dense_words(first,(u,u),fmt)
    legal=all(v in (0,one) for row in (os,oi) for v in row)
    successor=(one if bool(os[0])!=bool(oi[0]) else 0) if legal else None
    return {'state_output_words':list(os),'input_output_words':list(oi),
            'next_state_word':successor,'canonical_transition':legal}


def same_observation(left,right):
    return all(left[k]==right[k] for k in ('state_output_words','input_output_words','next_state_word'))


def compare_complete_record(record,words,baseline,fmt):
    one=round_word(Q(1),fmt);expected=[];safe=True
    for q,u in product((0,one),repeat=2):
        old,new=observation(baseline,q,u,fmt),observation(words,q,u,fmt)
        equal=same_observation(old,new)
        safe=safe and equal and new['canonical_transition']
        expected.append((q,u,old,new,equal))
    require(record['complete_registered_state_input_pairs']==4 and
            record['all_protected_observations_equal']==safe,'Complete-domain summary mismatch')
    require(len(record['records'])==4,'Complete-domain case omitted')
    for actual,(q,u,old,new,equal) in zip(record['records'],expected):
        require(actual['q_word']==q and actual['u_word']==u and actual['equal']==equal,
                'Complete-domain context/order differs')
        for key in old:
            require(actual['old'][key]==old[key] and actual['candidate'][key]==new[key],
                    'Complete-domain raw observation differs from independent execution')
    return safe


def check_training():
    """Read producer output, then independently replay every recorded attempt."""
    path=ROOT/'training_results.json'
    result=json.loads(path.read_text())
    require(result['status']=='passed','Training producer has no successful result')
    run_records=[];attempts=0;safe_accept=safe_reject=offline=0;domain_cases=0;bit_preserving_joint_refusals=0
    for run in result['runs']:
        fmt=run['format'];route=run['route'];config=decoded_config(run['config'])
        structural=route=='structural_final_mask_certified'
        safe=route in ('final_update_projected_certified','structural_final_mask_certified')
        mode={'unconstrained_offline':'none','gradient_only_projected_offline':'gradient_only',
              'final_update_projected_certified':'projected','structural_final_mask_certified':'structural'}[route]
        one=round_word(Q(1),fmt);width=3 if structural else 2
        baseline=((one,0,one),(0,one,0)) if structural else ((one,0),(0,one))
        words=baseline
        activation=(0,0,one) if structural else (one,0)
        state=(0,((Q(0),)*width,)*2,((Q(0),)*width,)*2)
        q=0;reference_q=0;feedback_active=True;version=0
        initial_loss=square_loss(dense_words(words,activation,fmt),(0,2),fmt)
        require(Q(run['initial_loss'])==initial_loss,'Initial training objective differs')
        accepted=refused=0
        for index,record in enumerate(run['records'],1):
            old=words;old_state=state
            out=dense_words(words,activation,fmt)
            values=tuple(word_value(v,fmt) for v in out)
            column=2 if structural else 0
            gradient=tuple(tuple((values[i]-(0 if i==0 else 2)) if j==column else Q(0)
                                 for j in range(width)) for i in range(2))
            require(record['attempt']==index and decoded_record(record['gradient'])==gradient,
                    'Training continuous-extension gradient differs')
            require(word_matrix(record['old_weights'])==old and decoded_state(record['old_optimizer_state'])==state,
                    'Training old endpoint/optimizer state differs')
            raw,increment,staged_state=direct_optimizer(decoded_words(words,fmt),gradient,state,config,mode)
            candidate=endpoint(words,increment,fmt)
            delta=sub(decoded_words(candidate,fmt),decoded_words(words,fmt))
            alg=all(sum(row[:2],Q(0))==0 for row in delta)
            require(decoded_record(record['raw_increment'])==raw and decoded_record(record['restricted_increment'])==increment,
                    'Training ordered optimizer increment differs')
            require(word_matrix(record['candidate_weights'])==candidate and
                    decoded_record(record['proposed_effective_delta'])==delta and
                    record['proposed_effective_rank']==rank(delta) and record['proposed_ALG_annihilation']==alg,
                    'Training candidate/effective rank or annihilation differs')
            require(decoded_state(record['staged_optimizer_state'])==staged_state,'Training staged state differs')
            bit=compare_complete_record(record['proposed_complete_D'],candidate,baseline,fmt)
            domain_cases+=4
            if safe:
                accepted_here=alg and bit and (not structural or tuple(row[:2] for row in candidate)==((one,0),(0,one)))
                require(record['status']==('accepted' if accepted_here else 'refused'),'Training acceptance differs from direct joint predicate')
                if accepted_here:
                    words=candidate;state=staged_state;accepted+=1;safe_accept+=1;version+=1
                else:
                    refused+=1;safe_reject+=1
                    if bit and not alg:bit_preserving_joint_refusals+=1
                    require(record['rollback_complete_snapshot_equal'] is True,'Training refusal lacks full rollback')
                feedback=record['protected_feedback'];u=one if feedback['input_bit'] else 0
                expected=observation(words,q,u,fmt)
                require(feedback['old_q_word']==q and same_observation(feedback['actual_tick'],expected)
                        and same_observation(feedback['reference_tick'],expected) and feedback['equal'] is True,
                        'Accepted route feedback differs from independent recurrence')
                q=one if bool(q)!=bool(u) else 0
                snapshot=record['snapshot_after_tick']
                require(snapshot['q_word']==q and snapshot['ticks']==index and snapshot['weight_version']==version,
                        'Combined publication/tick state differs')
                require(word_matrix(snapshot['weights'])==words and decoded_state(snapshot['optimizer_state'])==state,
                        'Combined snapshot weights or optimizer state differs')
            else:
                require(record['status']=='offline_applied_without_authorization' and not record['live_authorization'],
                        'Unsafe baseline improperly labeled authorized')
                words=candidate;state=staged_state;offline+=1
                feedback=record['protected_feedback'];u=one if feedback['input_bit'] else 0
                reference=observation(baseline,reference_q,u,fmt);reference_q=reference['next_state_word']
                if feedback_active:
                    expected=observation(words,q,u,fmt)
                    require(same_observation(feedback['actual'],expected) and
                            feedback['equal']==same_observation(expected,reference),
                            'Offline feedback diagnostic differs')
                    if expected['canonical_transition']:q=expected['next_state_word']
                    else:feedback_active=False
                    require(feedback['continued']==feedback_active,'Offline invalid-state stop differs')
                else:
                    require(feedback['kind']=='offline_feedback_stopped_after_domain_violation',
                            'Offline feedback resumed outside its declared domain')
            after=dense_words(words,activation,fmt)
            actual_delta=sub(decoded_words(words,fmt),decoded_words(old,fmt))
            require(tuple(record['old_A_output_words'])==out and tuple(record['new_A_output_words'])==after,
                    'Training A words differ')
            require(Q(record['loss_before'])==square_loss(out,(0,2),fmt) and
                    Q(record['loss_after'])==square_loss(after,(0,2),fmt),'Training exact loss differs')
            require(decoded_record(record['actual_effective_delta'])==actual_delta and
                    record['actual_effective_rank']==rank(actual_delta) and
                    decoded_state(record['actual_optimizer_state'])==state and word_matrix(record['actual_weights'])==words,
                    'Training committed endpoint or effective state differs')
            compare_complete_record(record['actual_complete_D'],words,baseline,fmt);domain_cases+=4
            require(state[0]==old_state[0]+(0 if record['status']=='refused' else 1),'Optimizer step advanced on refusal')
            attempts+=1
        final_loss=square_loss(dense_words(words,activation,fmt),(0,2),fmt)
        require(Q(run['final_loss'])==final_loss and run['accepted_commits']==accepted and
                run['refused_attempts']==refused,'Training run totals differ')
        run_records.append({'format':fmt,'optimizer':run['optimizer'],'route':route,
                            'attempts':len(run['records']),'accepted':accepted,'refused':refused,
                            'initial_loss':str(initial_loss),'final_loss':str(final_loss),
                            'all_attempts_replayed':True})
    require(result['attempts']==attempts and result['accepted_safe_commits']==safe_accept and
            result['refused_safe_attempts']==safe_reject and result['offline_applied_steps']==offline,
            'Training aggregate counts differ')
    return {'producer_result_sha256':digest(path),'runs':run_records,'attempts':attempts,
            'complete_domain_context_comparisons':domain_cases,'safe_commits':safe_accept,
            'safe_refusals':safe_reject,'BIT_preserving_but_ALG_failing_refusals':bit_preserving_joint_refusals,
            'offline_steps':offline,
            'method':'Independent word-RNE endpoint/graph execution and complete optimizer/state/loss replay',
            'scope':'All recorded toy runs; no learning-performance or general convergence inference'}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def check_transactions():
    import constrained_updates as cu
    import optimizer_kernel as ok
    records=[];refusal_count=0;context_count=0
    for fmt in ('BF16','FP32'):
        one=round_word(Q(1),fmt)
        for model in ('duplicate_feedback_v1','structural_duplicate_v1'):
            structural=model=='structural_duplicate_v1';width=3 if structural else 2
            config=cu.OptimizerConfig('momentum',Q(1,2),momentum=Q(1,2))
            kernel=ok.OptimizerKernel(model,fmt,config)
            initial=kernel.snapshot();own_config=decoded_config(initial['config'])
            # Caller-owned dataclass reinitialization must not change the owner.
            cu.OptimizerConfig.__init__(config,'sgd',Q(7))
            require(kernel.snapshot()==initial,'Caller config alias changed the live owner')
            detached=kernel.snapshot();detached['optimizer_state']['m']['rows'][0][0]=[99,1]
            detached['weights'][0][0]=0;detached['config']['learning_rate']=[99,1]
            require(kernel.snapshot()==initial,'Returned snapshot aliases live state')
            column=2 if structural else 0
            gradient=tuple(tuple(Q(1 if i==0 else -2) if j==column else Q(0)
                                 for j in range(width)) for i in range(2))
            restriction='structural' if structural else 'projected'
            request=ok.optimizer_request(cu.Matrix(gradient,width),restriction)
            preview=kernel.preview(request)
            require(kernel.snapshot()==initial,'Preview published optimizer state')
            raw,increment,next_state=direct_optimizer(decoded_words(kernel.weights,fmt),gradient,
                                                      decoded_state(initial['optimizer_state']),own_config,restriction)
            expected_endpoint=endpoint(kernel.weights,increment,fmt)
            require(word_matrix(preview['candidate_words'])==expected_endpoint and
                    decoded_state(preview['next_optimizer_state'])==next_state,
                    'Transaction preview differs from independent optimizer/endpoint')
            preview['next_optimizer_state']['step']=99;preview['candidate_words'][0][0]=0
            require(kernel.snapshot()==initial,'Returned preview aliases live state')
            prepared=kernel.prepare(request)
            require(kernel.snapshot()==initial,'Preparation published state')
            failures=[]

            def reject(label,action):
                nonlocal refusal_count
                old=kernel.snapshot()
                try:action()
                except (ValueError,TypeError,OverflowError):
                    require(kernel.snapshot()==old,'Refusal changed a combined snapshot: '+label)
                    failures.append(label);refusal_count+=1
                else:raise AssertionError('Expected refusal absent: '+label)

            def corrupt(change):
                packet=json.loads(prepared);change(packet['payload'])
                packet['payload_sha256']=hashlib.sha256(canonical(packet['payload']).encode()).hexdigest()
                return canonical(packet)

            mutations={
                'staged_next_step':lambda p:p['staged']['next_optimizer_state'].__setitem__('step',99),
                'staged_next_first_moment':lambda p:p['staged']['next_optimizer_state']['m']['rows'][0].__setitem__(0,[99,1]),
                'staged_next_second_moment':lambda p:p['staged']['next_optimizer_state']['v']['rows'][0].__setitem__(0,[99,1]),
                'candidate_endpoint':lambda p:p['staged']['candidate_words'][0].__setitem__(0,0),
                'coherently_hashed_inconsistent_request':lambda p:p['staged']['request']['gradient']['rows'][0].__setitem__(column,[99,1]),
                'schedule':lambda p:p['descriptor'].__setitem__('combined_schedule','in_place_unregistered'),
                'configuration':lambda p:p['optimizer_config'].__setitem__('learning_rate',[99,1]),
                'claim':lambda p:p.__setitem__('claim','BIT'),
                'implementation_identity':lambda p:p['source_sha256'].__setitem__('optimizer_kernel.py','0'*64),
            }
            for label,change in mutations.items():
                reject(label,lambda change=change:kernel.commit(corrupt(change)))
            reject('duplicate_JSON_key',lambda:kernel.commit('{"payload":{},"payload":{},"payload_sha256":"x"}'))
            reject('live_owner_reinitialization',lambda:ok.OptimizerKernel.__init__(kernel,model,fmt,config))
            receipt=kernel.commit(prepared)
            snap=kernel.snapshot()
            require(receipt['accepted'] and word_matrix(snap['weights'])==expected_endpoint and
                    decoded_state(snap['optimizer_state'])==next_state and snap['weight_version']==1
                    and snap['q_word']==0 and snap['ticks']==0,'Combined optimizer publication differs')
            require(any(x!=0 for row in next_state[1] for x in row),'Rollback fixture lacks nonzero first moment')
            reject('stale_after_weight_commit',lambda:kernel.commit(prepared))
            # Overflow after computing a new optimizer state must retain the old one.
            p,e=format_parameters(fmt)
            maximum=(((1<<e)-2)<<(p-1))|((1<<(p-1))-1)
            huge=16*word_value(maximum,fmt)
            large_gradient=tuple(tuple(huge if i==0 and j==column else Q(0)
                                       for j in range(width)) for i in range(2))
            oversized=ok.optimizer_request(cu.Matrix(large_gradient,width),restriction)
            reject('optimizer_endpoint_overflow',lambda:kernel.prepare(oversized))
            zero_direction=cu.Matrix(((Q(0),)*width,)*2,width)
            zero_request=ok.ai_request(zero_direction,restriction)
            before_tick_prepared=kernel.prepare(zero_request)
            kernel.tick(one)
            require(kernel.state_word==one and kernel.ticks==1,'Protected fixture tick differs')
            reject('stale_after_protected_tick',lambda:kernel.commit(before_tick_prepared))
            for q,u in product((0,one),repeat=2):
                observed=ok.evaluate_d(kernel.weights,q,u,fmt,model)
                expected=observation(kernel.weights,q,u,fmt)
                require(same_observation(observed,expected) and expected['canonical_transition'],
                        'Live complete-domain observation differs from word oracle')
                context_count+=1
            current=kernel.snapshot()
            zero_prepared=kernel.prepare(zero_request);kernel.commit(zero_prepared)
            require(kernel.snapshot()['optimizer_state']==current['optimizer_state'] and
                    kernel.state_word==current['q_word'] and kernel.ticks==current['ticks'],
                    'Accepted AI update altered optimizer/protected state')
            records.append({'format':fmt,'model':model,'rollback_refusals':failures,
                            'caller_config_and_returned_record_alias_checks':True,
                            'accepted_optimizer_updates':1,'accepted_AI_updates':1,
                            'all_publication_fields_independently_compared':True})
        # Full-rank actual domain permits a BIT-only tiny edit, but the joint
        # claim rejects the same endpoint. Direct word checks certify this fixture.
        direction=((Q(0),word_value(1,fmt)),(Q(0),Q(0)))
        request=ok.ai_request(cu.Matrix(direction,2),'none')
        bit=ok.OptimizerKernel('split_feedback_v1',fmt,cu.OptimizerConfig('sgd',Q(1)),claim='BIT')
        joint=ok.OptimizerKernel('split_feedback_v1',fmt,cu.OptimizerConfig('sgd',Q(1)),claim='ALG_AND_BIT')
        old=bit.weights;packet=bit.prepare(request)
        require(json.loads(packet)['payload']['ALG'] is False,'BIT-only edit falsely claims ALG')
        bit.commit(packet)
        for activation in ((0,0),(one,one),(one,0)):
            require(dense_words(old,activation,fmt)==dense_words(bit.weights,activation,fmt),
                    'Full-rank BIT fixture changed a protected raw input')
            context_count+=1
        require(dense_words(bit.weights,(0,one),fmt)==(1,one),'BIT-only A response vanished')
        before=joint.snapshot()
        try:joint.prepare(request)
        except ok.UpdateRejected:
            require(joint.snapshot()==before,'Joint refusal altered state');refusal_count+=1
        else:raise AssertionError('Joint contract accepted a nonannihilator')
        records.append({'format':fmt,'model':'split_feedback_v1','BIT_accepted_ALG_false':True,
                        'joint_refused_without_publication':True,'legal_A_response_word':1})
    return {'records':records,'full_snapshot_refusals':refusal_count,
            'direct_complete_domain_context_checks':context_count,
            'scope':'Trusted serial public API, detached records and recomputation; no private-memory or original-intent authentication claim'}


def check_numerical_boundaries():
    import constrained_updates as cu
    import optimizer_kernel as ok
    records=[]
    for fmt in ('BF16','FP32'):
        p,_=format_parameters(fmt);one=round_word(Q(1),fmt)
        old=((round_word(Q(1<<p),fmt),0),(0,0))
        direction=((Q(1),Q(-1)),(Q(0),Q(0)))
        new=endpoint(old,direction,fmt)
        require(ok.quantize_endpoint(old,cu.Matrix(direction,2),fmt)==new,
                'Commit endpoint differs from independent RNE')
        effective=sub(decoded_words(new,fmt),decoded_words(old,fmt))
        require(sum(effective[0],Q(0))==-1 and
                word_value(dense_words(new,(one,one),fmt)[0],fmt)-
                word_value(dense_words(old,(one,one),fmt)[0],fmt)==-1,
                'Ideal-null commit counterexample disappeared')
        thirds=tuple(tuple(round_word(Q(2,3) if i==j else Q(-1,3),fmt)
                           for j in range(3)) for i in range(3))
        require(all(sum(row,Q(0))==0 for row in decoded_words(thirds,fmt)),
                'Rounded thirds are not exact annihilators')
        require(dense_words(thirds,(one,one,one),fmt)==(0,0,0) and
                dense_words(thirds,(1,1,1),fmt)==(1,1,1),
                'Basis-only rounded check incorrectly protects the full line')
        tiny=((one,1),(1,one));old_identity=((one,0),(0,one))
        delta=sub(decoded_words(tiny,fmt),decoded_words(old_identity,fmt))
        require(rank(delta)==2 and all(dense_words(tiny,a,fmt)==dense_words(old_identity,a,fmt)
                                      for a in ((0,0),(one,one))),
                'BIT rank can exceed the exact complement bound')
        records.append({'format':fmt,'commit_effective_residual':'-1',
                        'thirds_basis_output_words':[0,0,0],'thirds_tiny_output_words':[1,1,1],
                        'BIT_effective_rank':2,'protected_complement_dimension':1,
                        'scope':'Independent exact/RNE finite counterexamples under fixed graph'})
    # Exact closure failure precedes any host/target arithmetic.
    g=((Q(2),Q(-1),Q(-1)),)
    clipped=direct_clip(g,'element',Q(1))
    require(sum(clipped[0],Q(0))==-1,'Coordinate clipping unexpectedly closed')
    for eps in (Q(0),Q(1),Q(1,8)):
        normalized=(Q(2)/(2+eps),-Q(1)/(1+eps),-Q(1)/(1+eps))
        require(sum(normalized,Q(0))==-Q(2)/((2+eps)*(1+eps)),
                'Ideal Adam closure counterexample formula differs')
    return {'format_records':records,'exact_Adam_epsilon_cases':3,
            'coordinate_clip_protected_residual':'-1',
            'scope':'Direct finite counterexamples, separate from conditional general proofs'}


def run_checks():
    started=time.perf_counter()
    names=('verify_independent.py','constrained_updates.py','optimizer_kernel.py','b1_runtime.py',
           'verify_training.py','training_results.json')
    before={name:digest(ROOT/name) for name in names}
    result={'schema':'dmwk-p2-b1-independent-review-v1','status':'running',
            'started_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,
            'algebra':check_algebra(),'optimizer':check_optimizer(),
            'training_replay':check_training(),'transactions':check_transactions(),
            'numerical_boundaries':check_numerical_boundaries()}
    require({name:digest(ROOT/name) for name in names}==before,'Reviewed source/result changed during execution')
    from b1_runtime import environment_metadata
    result.update(status='passed',elapsed_seconds=time.perf_counter()-started,
                  source_sha256=before,environment=environment_metadata(),SMT_queries=0,
                  proof_assistant_checked=False,prior_stage_suites_rerun=False,
                  evidence_scope='Independent finite exact/reference replay; universal theorems remain handwritten')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'independent_results.json')
    args=parser.parse_args()
    if not __debug__:raise SystemExit('Run without Python -O/-OO')
    result=run_checks()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'seconds':result['elapsed_seconds'],'output':str(args.output)}))


if __name__=='__main__':
    main()


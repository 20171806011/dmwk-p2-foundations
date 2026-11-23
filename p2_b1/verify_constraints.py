"""B1 exact, optimizer-closure, finite-execution and transaction checks.

Only prior implementation interfaces are imported. This is not a rerun of any
earlier verifier, and its finite cases are not universal machine proofs.
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json
import random
import time

from b1_runtime import get_fp, load_a2, load_a3, load_a4, environment_metadata
import constrained_updates as cu

xp=load_a2('exact_projection')
SEED=20261114


def zero(a):
    return all(v==0 for row in a.rows for v in row)


def row_sum(a):
    return tuple(sum(row,Fraction(0)) for row in a.rows)


def dense(words, h, fmt):
    fp=get_fp();audit=fp.Audit();out=[]
    for row in words:
        s=0
        for w,v in zip(row,h):
            s=fp.add_words(s,fp.mul_words(w,v,fmt,audit),fmt,audit)
        out.append(s)
    return tuple(out)


def exact_and_optimizer_cases():
    rng=random.Random(SEED);checks=0;records=[]
    for hs in product((0,1),repeat=2):
        H=xp.matrix(tuple((x,) for x in hs))
        P=xp.projection(H).P_perp
        for entries in product((-1,0,1),repeat=4):
            G=xp.matrix((entries[:2],entries[2:]))
            D=cu.project_direction(G,H)
            assert D==xp.matmul(G,P)
            assert zero(xp.matmul(D,H))
            assert cu.project_direction(D,H)==D
            residual=xp.sub(G,D)
            assert xp.frobenius_squared(G)==xp.frobenius_squared(D)+xp.frobenius_squared(residual)
            T=xp.scale(D,2)
            assert xp.frobenius_squared(xp.sub(G,T))==(xp.frobenius_squared(residual)+xp.frobenius_squared(xp.sub(D,T)))
            checks+=5
    named=[('zero',xp.zeros(3,0)),('full',xp.eye(3)),
           ('dependent',xp.matrix(((1,2,0),(1,2,0),(1,2,0)))),
           ('nonorthogonal_null_basis',xp.matrix(((1,),(2,),(3,))))]
    for i in range(64):
        d=rng.randrange(1,5);m=rng.randrange(0,5);n=rng.randrange(1,4)
        H=xp.matrix(tuple(tuple(Fraction(rng.randrange(-3,4),rng.randrange(1,4)) for _ in range(m)) for _ in range(d)),ncols=m)
        named.append(('seeded_'+str(i),H,n))
    for item in named:
        name,H=item[:2];n=item[2] if len(item)>2 else 2
        d=H.nrows;N=xp.nullspace(xp.transpose(H));c=N.ncols
        Z=xp.matrix(tuple(tuple(Fraction(rng.randrange(-3,4),rng.randrange(1,4)) for _ in range(c)) for _ in range(n)),ncols=c)
        D=cu.nullspace_update(Z,H)
        assert zero(xp.matmul(D,H)) and xp.rank(D)==xp.rank(Z)
        checks+=1
        ranks=[]
        for k in (0,1,2):
            L=xp.matrix(tuple(tuple(rng.randrange(-2,3) for _ in range(k)) for _ in range(n)),ncols=k)
            R=xp.matrix(tuple(tuple(rng.randrange(-2,3) for _ in range(d)) for _ in range(k)),ncols=d)
            Q=cu.lowrank_update(L,R,H)
            assert zero(xp.matmul(Q,H))
            assert xp.rank(Q)<=min(k,n,c)
            assert Q==cu.project_direction(xp.matmul(L,R),H)
            checks+=3;ranks.append({'factor_rank_budget':k,'actual_rank':xp.rank(Q)})
        records.append({'case':name,'shape':[n,d],'protected_rank':xp.rank(H),'nullity':c,
                        'null_coeff_rank':xp.rank(Z),'null_update_rank':xp.rank(D),'low_rank_cases':ranks})
    # A rank bound on one increment is not a cumulative-rank bound, and a
    # difference of two rank-k adapters need not itself have rank k.
    H0=xp.zeros(2,0);a=xp.matrix(((1,0),(0,0)));b=xp.matrix(((0,0),(0,1)))
    assert xp.rank(a)==xp.rank(b)==1 and xp.rank(xp.add(a,b))==2
    assert xp.rank(xp.sub(b,a))==2
    assert zero(xp.matmul(xp.sub(b,a),H0))
    checks+=3
    rank_counter={'id':'B1-C0_step_and_adapter_rank','each_increment_rank':1,'cumulative_rank':2,
                  'old_adapter_rank':1,'new_adapter_rank':1,'adapter_difference_rank':2,
                  'scope':'Exact algebra, V={0}; no claim that a per-step rank budget bounds accumulated rank'}
    H=xp.matrix(((1,),(1,),(1,)));g=xp.matrix(((3,0,0),));W=xp.zeros(1,3)
    safe=cu.project_direction(g,H)
    assert safe==xp.matrix(((2,-1,-1),)) and row_sum(safe)==(0,)
    checks+=1
    state=cu.initial_optimizer_state(1,3)
    adam=cu.OptimizerConfig('adamw',Fraction(1),beta1=Fraction(1,2),beta2=Fraction(1,2),epsilon=Fraction(1))
    grad_only=cu.stage_optimizer(W,g,state,adam,mode='gradient_only',H=H)
    final=cu.stage_optimizer(W,g,state,adam,mode='projected',H=H)
    expected=xp.matrix(((-Fraction.from_float(2.0/3.0),Fraction(1,2),Fraction(1,2)),))
    assert grad_only.increment==expected
    assert row_sum(grad_only.increment)!=(0,)
    assert row_sum(final.increment)==(0,)
    assert grad_only.next_state.step==final.next_state.step==1 and state.step==0
    checks+=4
    optimizer_cases=[{'id':'B1-C1_Adam_after_gradient_projection','H':xp.serialize(H),
                     'raw_gradient':xp.serialize(g),'projected_gradient':xp.serialize(safe),
                     'gradient_only_increment':xp.serialize(grad_only.increment),
                     'gradient_only_exact_row_sum':[str(x) for x in row_sum(grad_only.increment)],
                     'final_projected_increment':xp.serialize(final.increment),
                     'config':cu.config_record(adam),'audit':grad_only.audit,
                     'ideal_normalized_direction_sum':'-1/3',
                     'scope':'Actual finite host binary64 Adam proposal decoded exactly; protected BF16/FP32 execution is a separate layer'}]
    off=cu.OptimizerState(2,xp.matrix(((1,0,0),)),xp.zeros(1,3))
    momentum=cu.OptimizerConfig('momentum',Fraction(1),momentum=Fraction(1,2))
    stage=cu.optimizer_proposal(W,safe,off,momentum)
    fixed=cu.stage_optimizer(W,safe,off,momentum,mode='projected',H=H)
    assert row_sum(stage.increment)==(Fraction(-1,2),)
    assert row_sum(fixed.increment)==(0,)
    assert row_sum(fixed.next_state.m)==(Fraction(1,2),)
    checks+=3
    optimizer_cases.append({'id':'B1-C2_off_space_momentum','old_m':xp.serialize(off.m),
                            'raw_increment':xp.serialize(stage.increment),'next_m':xp.serialize(stage.next_state.m),
                            'final_projected_increment':xp.serialize(fixed.increment),
                            'scope':'Final update projection repairs this increment; it does not assert that stored moments are in the protected annihilator'})
    decay=cu.OptimizerConfig('sgd',Fraction(1),weight_decay=Fraction(1,4))
    weights=xp.matrix(((1,0,0),))
    stage=cu.stage_optimizer(weights,g,state,decay,mode='gradient_only',H=H)
    fixed=cu.stage_optimizer(weights,g,state,decay,mode='projected',H=H)
    assert row_sum(stage.increment)==(Fraction(-1,4),) and row_sum(fixed.increment)==(0,)
    checks+=1
    optimizer_cases.append({'id':'B1-C3_decay_after_gradient_projection',
                            'weights':xp.serialize(weights),'gradient_only_increment':xp.serialize(stage.increment),
                            'leak':'-1/4','final_projected_increment':xp.serialize(fixed.increment)})
    clipped,ca=cu.clip_direction(safe,'element',Fraction(1))
    global_clip,ga=cu.clip_direction(safe,'global_norm',Fraction(1))
    assert clipped==xp.matrix(((1,-1,-1),)) and row_sum(clipped)==(-1,)
    assert row_sum(global_clip)==(0,)
    assert global_clip.rows[0][0]==-2*global_clip.rows[0][1]==-2*global_clip.rows[0][2]
    checks+=3
    optimizer_cases.append({'id':'B1-C4_coordinate_clip_vs_common_scale',
                            'coordinate_increment':xp.serialize(clipped),'coordinate_audit':ca,
                            'common_scalar_increment':xp.serialize(global_clip),'global_audit':ga,
                            'scope':'Exact common-rational scaling preserves annihilation; host norm estimate is not an exact norm-threshold certificate'})
    sgd=cu.optimizer_proposal(W,safe,state,cu.OptimizerConfig('sgd',Fraction(1,4)))
    assert zero(xp.matmul(sgd.increment,H));checks+=1
    return {'status':'passed','checks':checks,'exhaustive_projection_pairs':324,
            'seeded_factor_cases':64,'named_factor_cases':4,'factor_records':records,
            'optimizer_counterexamples':optimizer_cases,'rank_counterexample':rank_counter,
            'scope':'Exact rational constraints and explicitly finite binary64 optimizer proposals; no live authority'}


def numerical_and_domain_cases():
    fp=get_fp();ck=load_a3('certificate_kernel');ca=load_a4('capacity_algebra')
    checks=0;records=[];refusals=[]
    def refused(label,fn,fmt):
        nonlocal checks
        try:fn()
        except (ValueError,TypeError,OverflowError) as exc:
            refusals.append({'format':fmt,'case':label,'error_type':type(exc).__name__});checks+=1
        else:raise AssertionError('Expected refusal: '+label)
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.encode_constant(x,fmt)
        one=enc(1);I=((one,0),(0,one));p=fp.get_format(fmt).p
        HP=xp.matrix(((1,),(3,)))
        exactP=xp.projection(HP).P_perp
        approximate_words=tuple(tuple(fp.round_fraction(v,fmt) for v in row) for row in exactP.rows)
        approximateP=xp.matrix(tuple(tuple(fp.decode_word(v,fmt) for v in row) for row in approximate_words))
        projector_leak=xp.matmul(approximateP,HP)
        assert zero(xp.matmul(exactP,HP)) and not zero(projector_leak);checks+=1
        records.append({'id':'B1-C12_quantized_projector','format':fmt,'H':xp.serialize(HP),
                        'exact_projector':xp.serialize(exactP),'quantized_projector_words':approximate_words,
                        'exact_residual_after_quantization':xp.serialize(projector_leak),
                        'scope':'Independent coefficient rounding of an exact projector is only a proposal and carries no endpoint authorization'})
        big=enc(1<<p);old=((big,0),(0,0));new=((big,enc(-1)),(0,0))
        assert fp.round_fraction(Fraction(1<<p)+1,fmt)==big
        assert dense(old,(one,one),fmt)==(big,0)
        assert tuple(fp.decode_word(x,fmt) for x in dense(new,(one,one),fmt))==(Fraction((1<<p)-1),0)
        checks+=3
        refused('effective_commit_leak',lambda:ck.make_certificate('commit_rounding_v1',fmt,old,new),fmt)
        records.append({'id':'B1-C5_commit_endpoint_rounding','format':fmt,'old_words':old,'new_words':new,
                        'ideal_increment':[['1','-1'],['0','0']],
                        'actual_effective_difference':[['0','-1'],['0','0']],
                        'exact_and_executed_protected_change':['-1','0']})
        Q=tuple(tuple(fp.round_fraction(Fraction(2,3) if i==j else Fraction(-1,3),fmt)
                      for j in range(3)) for i in range(3))
        assert all(sum((fp.decode_word(x,fmt) for x in row),Fraction(0))==0 for row in Q)
        assert dense(Q,(one,)*3,fmt)==(0,)*3
        assert dense(Q,(1,)*3,fmt)==(1,)*3
        checks+=3
        refused('thirds_subnormal',lambda:ck.make_certificate('thirds_two_inputs_v1',fmt,((0,0,0),)*3,Q),fmt)
        records.append({'id':'B1-C6_ALG_not_BIT','format':fmt,'candidate_words':Q,
                        'exact_null_on_both_inputs':True,'basis_output_words':[0,0,0],
                        'tiny_output_words':[1,1,1]})
        tiny=((one,1),(0,one));cert=json.loads(ck.make_certificate('split_feedback_v1',fmt,I,tiny))
        assert not cert['payload']['proof']['exact_effective_delta_annihilates_registered_span']
        assert dense(tiny,(0,one),fmt)==(1,one)
        checks+=2
        refused('axis_exposes_tiny_edit',lambda:ck.make_certificate('shared_axis_v1',fmt,I,tiny),fmt)
        records.append({'id':'B1-C7_full_rank_BIT_not_ALG','format':fmt,'candidate_words':tiny,
                        'protected_rank':2,'exact_ALG':False,'registered_BIT':True,
                        'A_e2_old_words':[0,one],'A_e2_new_words':[1,one]})
        ranktwo=((one,1),(1,one));ck.make_certificate('duplicate_feedback_v1',fmt,I,ranktwo)
        delta=xp.matrix(((0,fp.decode_word(1,fmt)),(fp.decode_word(1,fmt),0)))
        assert xp.rank(delta)==2;checks+=1
        records.append({'id':'B1-C8_BIT_rank_exceeds_complement','format':fmt,'candidate_words':ranktwo,
                        'protected_rank':1,'complement_dimension':1,'effective_rank':2,
                        'scope':'BIT edit, not an exact annihilator or an authorized algebraic rank-k increment'})
        maxword=fp.get_format(fmt).max_finite_word;half=enc(Fraction(1,2));sat=((maxword,maxword),)*2
        assert dense(sat,(half,half),fmt)==(maxword,maxword);checks+=1
        records.append({'id':'B1-C9_saturated_storage','format':fmt,'old_words':sat,'input_words':[half,half],
                        'abstract_ALG_dimension':2,'proved_full_format_ALG_endpoint_count':1,
                        'proof':'Finite endpoint entries <=Fmax; fixed row sum2Fmax forces every entry equalFmax.',
                        'scope':'Extremal mathematical proof with one finite execution probe, not whole-format enumeration'})
        shared=((one,0),(0,enc(2)))
        assert dense(I,(one,0),fmt)==dense(shared,(one,0),fmt)
        assert dense(I,(0,one),fmt)!=dense(shared,(0,one),fmt)
        checks+=2
        refused('missing_shared_site',lambda:ck.make_certificate('shared_axis_v1',fmt,I,shared),fmt)
        records.append({'id':'B1-C10_samples_and_shared_sites','format':fmt,'sampled_input':[one,0],
                        'omitted_legal_input':[0,one],'sample_passes':True,'global_BIT':False})
    H=xp.matrix(((1,),(0,)));X=xp.matrix(((1,0),(0,1)))
    compatible=xp.matrix(((0,2),));incompatible=xp.matrix(((1,2),))
    good_update,good=ca.solve_response(H,X,compatible)
    bad_update,bad=ca.solve_response(H,X,incompatible)
    # The prior algebra API returns explicit feasible/infeasible records;
    # a shape/rank inequality alone cannot replace target compatibility.
    assert good_update is not None and bad_update is None
    assert good['unconstrained_response_feasible'] and not bad['unconstrained_response_feasible'];checks+=2
    safe=xp.matrix(((0,1),))
    assert zero(xp.matmul(safe,H)) and xp.matmul(safe,H)==xp.zeros(1,1)
    assert xp.matmul(safe,xp.matrix(((0,),(1,)))).rows==((Fraction(1),),)
    checks+=2
    records.append({'id':'B1-C11_target_compatibility_and_silence','H':xp.serialize(H),'targets':xp.serialize(X),
                    'compatible':good,'incompatible':bad,'safe_nonzero_update':xp.serialize(safe),
                    'silent_target':[1,0],'responding_target':[0,1]})
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),
            'refusals':refusals,'scope':'Deterministic BF16 software and audited local FP32 probes; A3 implementation helpers only, no old verifier'}


def transaction_cases():
    import optimizer_kernel as ok
    fp=get_fp();checks=0;records=[];refusals=[]
    def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.encode_constant(x,fmt)
        cfg=cu.OptimizerConfig('momentum',Fraction(1),momentum=Fraction(1,2))
        kernel=ok.OptimizerKernel('duplicate_feedback_v1',fmt,cfg,claim='ALG_AND_BIT')
        grad=xp.matrix(((2,-2),(-2,2)))
        request=ok.optimizer_request(grad,restriction='projected')
        before=kernel.snapshot();text=kernel.prepare(request)
        assert kernel.snapshot()==before;checks+=1
        kernel.commit(text);after=kernel.snapshot()
        assert after['optimizer_state']['step']==before['optimizer_state']['step']+1
        assert after['optimizer_state']['m']!=before['optimizer_state']['m']
        assert after['weight_version']==before['weight_version']+1
        assert after['q_word']==before['q_word'] and after['ticks']==before['ticks']
        checks+=4
        def refuse(label,fn):
            nonlocal checks
            previous=kernel.snapshot()
            try:fn()
            except (ValueError,TypeError,OverflowError) as exc:
                assert kernel.snapshot()==previous
                checks+=1
                refusals.append({'format':fmt,'case':label,'error_type':type(exc).__name__,
                                 'whole_weight_optimizer_protected_snapshot_unchanged':True})
            else:raise AssertionError('Unsafe candidate accepted: '+label)
        refuse('replay_after_commit',lambda:kernel.commit(text))
        prepared=kernel.prepare(ok.ai_request(xp.zeros(2,2),restriction='projected'))
        kernel.tick(enc(1));current=kernel.snapshot()
        refuse('state_tick_after_prepare',lambda:kernel.commit(prepared))
        assert kernel.snapshot()==current;checks+=1
        # Explicit unsafe AI replacement and malformed candidates must not
        # advance even the already nonzero momentum state.
        refuse('unsafe_AI_endpoint',lambda:kernel.prepare(ok.ai_request(xp.eye(2),restriction='none')))
        refuse('unknown_restriction',lambda:kernel.prepare(ok.ai_request(xp.zeros(2,2),restriction='sample_only')))
        refuse('wrong_gradient_shape',lambda:kernel.prepare(ok.optimizer_request(xp.zeros(1,3),restriction='projected')))
        refuse('noncanonical_packet',lambda:kernel.commit(' {"not":"a certificate"}'))
        # Prepared records are data-only. Rehash all recognizable envelope
        # digests after mutations so refusal cannot rely solely on a stale hash.
        fresh=kernel.prepare(ok.ai_request(xp.zeros(2,2),restriction='projected'))
        packet=json.loads(fresh)
        payload_key='payload' if 'payload' in packet else 'candidate'
        assert payload_key in packet and type(packet[payload_key]) is dict
        checks+=1
        def mutate_key(obj,wanted,replacement):
            if isinstance(obj,dict):
                for key in list(obj):
                    if key==wanted:obj[key]=replacement;return True
                for value in obj.values():
                    if mutate_key(value,wanted,replacement):return True
            elif isinstance(obj,list):
                for value in obj:
                    if mutate_key(value,wanted,replacement):return True
            return False
        fields=[('graph','unverified_fused_graph'),('numerical_policy','fma'),('schedule','async'),
                ('model_id','sample_domain'),('weight_version',-1),('optimizer_state',{}),
                ('config',{}),('request',{}),('candidate_words',[[0,0],[0,0]])]
        mutation_records=[]
        for field,value in fields:
            altered=json.loads(fresh)
            found=mutate_key(altered[payload_key],field,value)
            if not found:
                raise AssertionError('Expected B1 binding field absent: '+field)
            if 'payload_sha256' in altered:
                altered['payload_sha256']=hashlib.sha256(canonical(altered['payload']).encode('ascii')).hexdigest()
            if 'candidate_sha256' in altered:
                altered['candidate_sha256']=hashlib.sha256(canonical(altered['candidate']).encode('ascii')).hexdigest()
            tampered=canonical(altered)
            refuse('tampered_'+field,lambda tampered=tampered:kernel.commit(tampered))
            mutation_records.append(field)
        # Selecting BIT alone must not silently assert ALG; the stronger
        # joint contract refuses the same non-algebraic stored tiny update.
        tiny=xp.matrix(((0,fp.decode_word(1,fmt)),(0,0)))
        bit=ok.OptimizerKernel('split_feedback_v1',fmt,cu.OptimizerConfig('sgd',Fraction(1)),claim='BIT')
        joint=ok.OptimizerKernel('split_feedback_v1',fmt,cu.OptimizerConfig('sgd',Fraction(1)),claim='ALG_AND_BIT')
        bit_req=ok.ai_request(tiny,restriction='none')
        bit.commit(bit.prepare(bit_req));joint_before=joint.snapshot()
        try:joint.prepare(bit_req)
        except (ValueError,TypeError,OverflowError) as exc:
            assert joint.snapshot()==joint_before
            checks+=1
            refusals.append({'format':fmt,'case':'joint_claim_refuses_BIT_nonALG_endpoint',
                             'error_type':type(exc).__name__,
                             'whole_weight_optimizer_protected_snapshot_unchanged':True})
        else:raise AssertionError('Joint contract accepted non-ALG tiny endpoint')
        records.append({'format':fmt,'initial_snapshot':before,'after_optimizer_commit':after,
                        'tick_invalidates_full_snapshot_candidate':True,'tampering_fields':mutation_records,
                        'BIT_accepts_nonALG_tiny_endpoint':True,'joint_claim_refuses_same_endpoint':True,
                        'scope':'New B1 combined publication; full optimizer moments/step included in each rollback comparison'})
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),
            'refusals':refusals}


def run_checks():
    started=time.perf_counter()
    exact=exact_and_optimizer_cases();numeric=numerical_and_domain_cases();transactions=transaction_cases()
    return {'schema':'dmwk-p2-b1-constraints-v1','status':'passed','seed':SEED,
            'checks':exact['checks']+numeric['checks']+transactions['checks'],'unexpected_failures':0,
            'sections':{'exact_and_optimizer':exact,'numerical_and_domain':numeric,'transactions':transactions},
            'environment':environment_metadata(),'elapsed_seconds':time.perf_counter()-started,
            'SMT_queries':0,'proof_assistant_checked':False,'prior_stage_suites_rerun':False,
            'scope':'Finite exact, host-optimizer and fixed-execution adversarial checks; universal proofs separate'}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run verification without -O/-OO')
    result=run_checks();out=Path(__file__).resolve().parent/'constraint_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sections','environment')}))

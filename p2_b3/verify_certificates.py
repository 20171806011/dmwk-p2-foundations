"""B3 read-only propagation receipts and unchanged B1 refusal boundary.

Prior suites and frozen optimizer trajectories are never replayed.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import time

from b3_runtime import get_fp,load_b1,environment_metadata
import propagation_bounds as pb
import propagation_certificate as pc

ROOT=Path(__file__).resolve().parent
SEED=20261114


def _json(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def _rehash(data):
    data['payload_sha256']=hashlib.sha256(_json(data['payload']).encode('ascii')).hexdigest()
    return _json(data)


def _patched(old,fmt,delta=Fraction(1,64)):
    new=deepcopy(old);bank=next(iter(new));bias=list(new[bank]['bias'])
    bias[0]=get_fp().round_fraction(get_fp().decode_word(bias[0],fmt)+delta,fmt)
    new[bank]['bias']=tuple(bias)
    return new


def _context(model,fmt,old,new,version,initial_error=Fraction(0)):
    dimension=2 if model in pc.MODELS[:2] else 1
    a=[0]*dimension;b=[0]*dimension
    if dimension==1:b[0]=get_fp().round_fraction(initial_error,fmt)
    return {'schema':pc.CONTEXT_SCHEMA,'model_id':model,'format':fmt,'weight_version':version,
        'old_banks':pb.record(old),'new_banks':pb.record(new),'old_initial_words':a,'new_initial_words':b,
        'ticks':3,'schedule':pb.model_descriptor(model,fmt)['schedule']}


def run_checks():
    start=time.perf_counter();rng=random.Random(SEED);fp=get_fp()
    checks=0;refusals=[];cases=[];tamper_cases=[];rollback_cases=[]
    ok=load_b1('optimizer_kernel');cu=load_b1('constrained_updates')

    def reject(name,fn):
        nonlocal checks
        try:fn()
        except (pc.PropagationRejected,ok.UpdateRejected) as exc:
            record={'case':name,'reason':str(exc)};refusals.append(record);checks+=1
            return record
        raise AssertionError('Expected refusal: '+name)

    def accepted_case(model,fmt,horizon,initial_error=Fraction(0),method='tube',state_box=None,delta=Fraction(1,64)):
        nonlocal checks
        old=pb.initial_banks(model,fmt);new=_patched(old,fmt,delta)
        proof=pb.analyze_model(model,fmt,old,new,horizon=horizon,initial_error=initial_error,method=method,state_box=state_box)
        budget=proof['observed_bound'];version=7
        context=_context(model,fmt,old,new,version,initial_error)
        text=pc.make_propagation_certificate(model,fmt,old,new,budget,horizon,initial_error,method,state_box,version,context)
        receipt=pc.check_propagation_certificate(text,model,fmt,old,new,budget,horizon,initial_error,method,state_box,version,context)
        assert receipt['norm']=='linf' and receipt['authorizes_commit'] is False
        assert receipt['claims_BIT'] is False and receipt['claims_exact_ALG'] is False
        assert receipt['claims_program_noninterference'] is False
        assert proof['domain_containment_proved'] is True and proof['totality_proved'] is True
        checks+=7
        if model not in pc.MODELS[:2]:
            assert budget==max(proof['error_bounds']);checks+=1
        if budget>0:
            reject(fmt+':'+model+':'+str(horizon)+':'+str(initial_error)+':'+method+':insufficient_budget',
                lambda:pc.make_propagation_certificate(model,fmt,old,new,budget/2,horizon,initial_error,method,state_box,version,context))
        cases.append({'model':model,'format':fmt,'horizon':horizon,'initial_error':pb.record(initial_error),
            'method':method,'state_box':pb.record(state_box),'version':version,
            'old_banks':pb.record(old),'new_banks':pb.record(new),'state_context':context,
            'proof':pb.record(proof),'receipt':receipt,'budget':pb.record(budget)})
        return old,new,proof,budget,context,text

    for fmt in ('BF16','FP32'):
        for model in pc.MODELS[:2]:accepted_case(model,fmt,1)
        for model in pc.MODELS[2:]:
            for horizon in (0,1,4):
                for initial_error in (Fraction(0),Fraction(1,4)):
                    accepted_case(model,fmt,horizon,initial_error)
        for initial_error in (Fraction(0),Fraction(1,4)):
            accepted_case('contractive_scalar_v1',fmt,4,initial_error,'invariant',Fraction(2))

        model='shared_relu_v1';old=pb.initial_banks(model,fmt);new=_patched(old,fmt)
        proof=pb.analyze_model(model,fmt,old,new);budget=proof['observed_bound'];context=_context(model,fmt,old,new,7)
        text=pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=context)
        base=json.loads(text);bank=next(iter(new))
        mutations={
            'missing_schedule':lambda p:p.pop('schedule'),
            'missing_provenance':lambda p:p.pop('domain_provenance'),
            'sampled_provenance':lambda p:p['domain_provenance'].__setitem__('sampled_provenance',True),
            'omitted_shared_site':lambda p:p['descriptor']['graph'].pop(),
            'wrong_shared_bank':lambda p:p['descriptor']['graph'][1].__setitem__('bank_id','invented_bank'),
            'wrong_nonlinearity':lambda p:p['descriptor']['graph'][0].__setitem__('activation','identity'),
            'FMA_policy':lambda p:p.__setitem__('numerical_policy','FMA'),
            'asynchronous_schedule':lambda p:p.__setitem__('schedule','in_place_unsynchronized'),
            'changed_old_bank':lambda p:p['old_banks'][bank]['weights'][0].__setitem__(0,0),
            'changed_new_bias':lambda p:p['new_banks'][bank]['bias'].__setitem__(0,0),
            'stale_version':lambda p:p.__setitem__('expected_weight_version',8),
            'changed_horizon':lambda p:p.__setitem__('horizon',2),
            'omitted_output_port':lambda p:p['observation']['ports'].pop(),
            'unproved_initial_relation':lambda p:p['initial_relation'].__setitem__('kind','overlapping boxes imply equality'),
            'different_input_histories':lambda p:p['input_history'].__setitem__('kind','independent arbitrary inputs'),
            'old_only_containment':lambda p:p['joint_domain_claim'].__setitem__('new_execution',False),
            'forged_bound':lambda p:p['proof'].__setitem__('observed_bound',[0,1]),
            'changed_budget':lambda p:p.__setitem__('budget',[0,1]),
            'claims_live_authority':lambda p:p.__setitem__('authorizes_commit',True),
            'claims_BIT':lambda p:p.__setitem__('claims_BIT',True),
            'changed_context_tick':lambda p:p['state_context'].__setitem__('ticks',4),
            'missing_context_schedule':lambda p:p['state_context'].pop('schedule'),
            'changed_source_identity':lambda p:p['implementation_sha256'].__setitem__('propagation_bounds.py','0'*64),
        }
        for name,mutate in mutations.items():
            changed=deepcopy(base);mutate(changed['payload']);changed=_rehash(changed)
            result=reject(fmt+':'+name,lambda:pc.check_propagation_certificate(
                changed,model,fmt,old,new,budget,version=7,state_context=context))
            tamper_cases.append({'format':fmt,'rehash_used':True,**result})

        reject(fmt+':stale_expected_version',lambda:pc.check_propagation_certificate(text,model,fmt,old,new,budget,version=8,state_context=context))
        later_context=deepcopy(context);later_context['ticks']+=1
        reject(fmt+':stale_expected_context_tick',lambda:pc.check_propagation_certificate(text,model,fmt,old,new,budget,version=7,state_context=later_context))
        missing_schedule=deepcopy(context);missing_schedule.pop('schedule')
        reject(fmt+':producer_missing_context_schedule',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=missing_schedule))
        changed_initial=deepcopy(context);changed_initial['new_initial_words'][0]=fp.encode_constant(1,fmt)
        reject(fmt+':zero_E0_different_actual_initial_state',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=changed_initial))
        outside=deepcopy(context);outside['old_initial_words'][0]=fp.encode_constant(2,fmt);outside['new_initial_words'][0]=fp.encode_constant(2,fmt)
        reject(fmt+':initial_pair_outside_domain',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=outside))
        wrong_banks=deepcopy(context);wrong_banks['new_banks'][bank]['weights'][0][0]=0
        reject(fmt+':context_endpoint_mismatch',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=wrong_banks))
        omitted=deepcopy(old);omitted.pop(bank)
        reject(fmt+':missing_actual_physical_bank',lambda:pc.make_propagation_certificate(model,fmt,omitted,new,budget))
        reject(fmt+':unknown_sample_registry',lambda:pc.make_propagation_certificate('sampled_model',fmt,old,new,budget))
        reject(fmt+':negative_budget',lambda:pc.make_propagation_certificate(model,fmt,old,new,Fraction(-1)))
        reject(fmt+':float_budget',lambda:pc.make_propagation_certificate(model,fmt,old,new,0.5))
        reject(fmt+':invalid_horizon',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,horizon=65))
        reject(fmt+':Boolean_horizon',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,horizon=True))
        reject(fmt+':unknown_method',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,method='sampled'))
        reject(fmt+':negative_initial_error',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,initial_error=Fraction(-1)))
        reject(fmt+':duplicate_json_key',lambda:pc.check_propagation_certificate('{"payload":{},"payload":{},"payload_sha256":"x"}',model,fmt,old,new,budget))
        reject(fmt+':nonfinite_json',lambda:pc.check_propagation_certificate('{"payload":NaN,"payload_sha256":"x"}',model,fmt,old,new,budget))

        # A claimed cap/invariant must be proved jointly rather than truncating
        # either endpoint's enclosure. This may conservatively refuse.
        neutral='neutral_scalar_v1';nold=pb.initial_banks(neutral,fmt);nnew=_patched(nold,fmt)
        reject(fmt+':uncertified_neutral_invariant',lambda:pc.make_propagation_certificate(neutral,fmt,nold,nnew,100,horizon=4,method='invariant',state_box=2))
        reject(fmt+':perturbed_tube_outside_claimed_cap',lambda:pc.make_propagation_certificate(neutral,fmt,nold,nnew,100,horizon=4,state_box=1))
        reject(fmt+':initial_box_not_contained',lambda:pc.make_propagation_certificate(neutral,fmt,nold,nnew,100,horizon=0,state_box=Fraction(1,2)))

        # New B3 boundary fixture, not a replay of frozen B1 optimization.
        cfg=cu.OptimizerConfig('adamw',Fraction(1),beta1=Fraction(0),beta2=Fraction(0),epsilon=Fraction(1))
        kernel=ok.OptimizerKernel('duplicate_feedback_v1',fmt,cfg,claim='ALG_AND_BIT')
        request=ok.optimizer_request(cu.xp.matrix(((1,0),(0,0))),restriction='projected')
        kernel.commit(kernel.prepare(request));kernel.tick(fp.encode_constant(1,fmt));snapshot=kernel.snapshot()
        assert snapshot['optimizer_state']['m']['rows'][0][0]!=[0,1]
        assert snapshot['optimizer_state']['v']['rows'][0][0]!=[0,1]
        checks+=2
        external={'kind':'B1_identity_only','snapshot':snapshot}
        certificate=pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=context,external_context=external)
        receipt=pc.check_propagation_certificate(certificate,model,fmt,old,new,budget,version=7,state_context=context,external_context=external)
        refusal=reject(fmt+':numeric_propagation_is_not_B1_commit',lambda:kernel.commit(certificate))
        after=kernel.snapshot();assert after==snapshot;checks+=1
        missing_external=deepcopy(external);missing_external['snapshot'].pop('schedule')
        reject(fmt+':missing_external_full_schedule',lambda:pc.make_propagation_certificate(model,fmt,old,new,budget,version=7,state_context=context,external_context=missing_external))
        kernel.tick(fp.encode_constant(1,fmt));later=kernel.snapshot();later_external={'kind':'B1_identity_only','snapshot':later}
        reject(fmt+':stale_external_snapshot',lambda:pc.check_propagation_certificate(certificate,model,fmt,old,new,budget,version=7,state_context=context,external_context=later_external))
        assert kernel.snapshot()==later;checks+=1
        rollback_cases.append({'format':fmt,'snapshot_before_refusal':snapshot,'snapshot_after_refusal':after,
            'later_tick_snapshot':later,'nonzero_m_and_v':True,'receipt':receipt,'refusal':refusal,
            'external_context_not_B3_state_provenance':True,'old_optimizer_trajectory_replayed':False})

    # A handful of seeded proposals are finite parameter examples only. The
    # returned domain proof for each chosen endpoint still covers its registry.
    seeded=[]
    for fmt in ('BF16','FP32'):
        for index in range(4):
            delta=Fraction(rng.randrange(-4,5),128)
            model='contractive_scalar_v1';old=pb.initial_banks(model,fmt);new=_patched(old,fmt,delta)
            proof=pb.analyze_model(model,fmt,old,new,horizon=3,method='invariant',state_box=2)
            text=pc.make_propagation_certificate(model,fmt,old,new,proof['observed_bound'],horizon=3,method='invariant',state_box=2)
            receipt=pc.check_propagation_certificate(text,model,fmt,old,new,proof['observed_bound'],horizon=3,method='invariant',state_box=2)
            assert receipt['authorizes_commit'] is False;checks+=1
            seeded.append({'format':fmt,'case':index,'bias_delta':pb.record(delta),'old_banks':pb.record(old),
                           'new_banks':pb.record(new),'proof':pb.record(proof),'receipt':receipt})

    path=ROOT.parent/'p2_b1'/'training_results.json';raw=path.read_bytes();frozen=json.loads(raw)
    refused=[s for r in frozen['runs'] for s in r['records'] if s['status']=='refused']
    adam=next(r for r in frozen['runs'] if r['format']=='FP32' and r['optimizer']=='adamw'
              and r['route']=='final_update_projected_certified')
    assert len(refused)==21
    assert all(s['proposed_complete_D']['all_protected_observations_equal'] is True for s in refused)
    assert all(s['proposed_ALG_annihilation'] is False for s in refused)
    assert adam['accepted_commits']==0 and adam['refused_attempts']==8
    assert adam['initial_loss']==adam['final_loss']=='5/2'
    checks+=6
    preserved={'source_sha256':hashlib.sha256(raw).hexdigest(),'refused_endpoints':len(refused),
        'all_frozen_BIT_equal':True,'all_frozen_ALG_false':True,'optimizer_replayed':False,
        'FP32_AdamW_joint':{'accepted':0,'refused':8,'initial_loss':'5/2','final_loss':'5/2'}}
    return {'schema':'dmwk-p2-b3-certificate-tests-v1','status':'passed','seed':SEED,'checks':checks,
        'unexpected_failures':0,'expected_refusals':len(refusals),'refusal_records':refusals,
        'registered_receipt_case_count':len(cases),'registered_receipt_cases':cases,
        'rehash_tamper_case_count':len(tamper_cases),'rehash_tamper_cases':tamper_cases,
        'rollback_cases':rollback_cases,'seeded_receipt_cases':seeded,'frozen_B1_preservation':preserved,
        'claim':'Read-only full-observation linf evidence with jointly recomputed domain containment',
        'norm':'linf','SMT_queries':0,'prior_stage_suites_rerun':False,
        'environment':environment_metadata(),'runtime_seconds':time.perf_counter()-start}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks();(ROOT/'certificate_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','seed','checks','unexpected_failures','expected_refusals',
        'registered_receipt_case_count','rehash_tamper_case_count','runtime_seconds')}))

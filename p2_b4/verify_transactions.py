"""B4 new exact-D sequences and detached changing-history receipts."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import time

from b4_runtime import get_fp,environment_metadata
import update_sequence as us
import sequence_certificate as sc
import switching_bounds as sb
import capacity_history as ch

ROOT=Path(__file__).resolve().parent
SEED=20261114


def _json(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
def _rehash(value):
    value['payload_sha256']=hashlib.sha256(_json(value['payload']).encode('ascii')).hexdigest()
    return _json(value)
def _words(value):return tuple(tuple(x for x in row) for row in value)


def _bias(bank,fmt,value):
    bank=deepcopy(bank);key=next(iter(bank));bias=list(bank[key]['bias'])
    bias[0]=get_fp().round_fraction(Fraction(value),fmt);bank[key]['bias']=tuple(bias)
    return bank


def run_checks():
    start=time.perf_counter();fp=get_fp();rng=random.Random(SEED)
    inputs=tuple(rng.randrange(2) for _ in range(32));checks=0;refusals=[];runs=[];tamper_records=[]
    boundary_records=[];stalls=[];numerical_cases=[];budget_exhaustions=[]

    def reject(name,fn):
        nonlocal checks
        try:fn()
        except (us.SequenceRejected,sc.NumericalRejected,us.ok.UpdateRejected) as exc:
            result={'case':name,'reason':str(exc),'ledger':sb.record(getattr(exc,'ledger',None))}
            refusals.append(result);checks+=1
            return result
        raise AssertionError('Expected refusal: '+name)

    for fmt in ('BF16','FP32'):
        t0=time.perf_counter();one=fp.encode_constant(1,fmt)
        cfg=us.cu.OptimizerConfig('sgd',Fraction(1,4));owner=us.SequenceKernel(fmt,cfg)
        peer=us.ok.OptimizerKernel(us.MODEL,fmt,cfg,claim='ALG_AND_BIT')
        baseline=owner.full_D();initial=owner.snapshot();history=[owner.weights]
        records=[];q_reference=0;last_loss=Fraction(*owner.evaluate_a()['loss'])
        for attempt,u_bit in enumerate(inputs,1):
            request=us.ok.optimizer_request(owner.toy_gradient(),restriction='structural')
            prepared=owner.prepare(request);receipt=owner.commit(prepared)
            snapshot=owner.snapshot();event=snapshot['accepted_ledger'][-1]
            actual=owner.evaluate_a();loss=Fraction(*actual['loss'])
            assert receipt['accepted_index']==attempt and receipt['weight_version']==attempt
            assert snapshot['kernel']['optimizer_state']['step']==attempt
            assert owner.full_D()==baseline
            assert event['D_bitwise_equal_to_previous'] is True
            assert event['actual_effective_rank']<=1 and event['prefix_delta_rank']<=1
            assert event['capacity']['unrestricted_annihilator_dimension']==4
            assert event['capacity']['reserved_column_dimension']==2
            assert event['capacity']['A_e3_response_dimension']==2
            assert loss<=last_loss
            checks+=11
            tick=owner.tick(one if u_bit else 0);unchanged=peer.tick(one if u_bit else 0)
            q_reference^=u_bit
            assert tick['trace']==unchanged
            assert owner.state_word==peer.state_word==(one if q_reference else 0)
            assert owner.ticks==attempt and owner.accepted_count==attempt
            checks+=3
            records.append({'attempt':attempt,'accepted_index':receipt['accepted_index'],'tick':owner.ticks,
                'receipt':receipt,'effective_delta':event['actual_effective_delta'],
                'effective_rank':event['actual_effective_rank'],'prefix_rank':event['prefix_delta_rank'],
                'nonzero_stored_change':event['nonzero_stored_change'],
                'ideal_increment':event['ideal_increment'],'A':actual,'loss_decreased':loss<last_loss,
                'capacity':event['capacity'],'kernel_snapshot_after_tick':owner.snapshot()['kernel'],
                'paired_tick':tick,'unchanged_peer_trace':unchanged})
            history.append(owner.weights);last_loss=loss
        final=owner.snapshot();nonzero=sum(r['nonzero_stored_change'] for r in records)
        assert final['accepted_updates']==32 and final['kernel']['ticks']==32
        assert Fraction(*owner.evaluate_a()['loss'])<Fraction(1,2)
        assert nonzero>1
        checks+=4
        H=us.ok.global_generators(us.MODEL,fmt);X=us.xp.matrix(((0,),(0,),(1,)))
        capacity_diagnostic=ch.analyze_history(tuple(history),fmt,(H,),mode='fixed',targets=X,rank_cap=1)
        runs.append({'format':fmt,'optimizer':'sgd','learning_rate':[1,4],'attempts':32,'accepted':32,
            'refused':0,'nonzero_stored_updates':nonzero,'accepted_noops':32-nonzero,
            'initial_loss':[1,2],'final_A':owner.evaluate_a(),'shared_input_bits':inputs,
            'records':records,'final_combined_snapshot':final,
            'capacity_diagnostic':ch.record(capacity_diagnostic),
            'global_provenance':{'descriptor':us.ok.model_descriptor(us.MODEL,fmt),
                'statement':'fixed first columns, all two Boolean shared sites and exact-D invariant; not sample-derived'},
            'runtime_seconds':time.perf_counter()-t0})

        # A zero stored proposal does not exhaust the fixed safe family.
        stalled=us.SequenceKernel(fmt,cfg)
        tiny=us.xp.matrix(((0,0,0),(0,0,-Fraction(1,1<<150))))
        tiny_receipt=stalled.commit(stalled.prepare(us.ok.ai_request(tiny,restriction='structural')))
        assert tiny_receipt['nonzero_stored_change'] is False
        assert stalled.snapshot()['kernel']['optimizer_state']['step']==0
        nonzero=us.xp.matrix(((0,0,0),(0,0,Fraction(-1,4))))
        changed_receipt=stalled.commit(stalled.prepare(us.ok.ai_request(nonzero,restriction='structural')))
        assert changed_receipt['nonzero_stored_change'] is True
        assert stalled.accepted_count==2 and stalled.ticks==0
        checks+=5
        stalls.append({'format':fmt,'tiny_receipt':tiny_receipt,'following_nonzero_AI_receipt':changed_receipt,
                       'final_snapshot':stalled.snapshot(),'meaning':'proposal-specific storage stall, not loss of the entire safe endpoint class'})

        # Nonzero moment setup is a new integration fixture, not old training.
        adam=us.cu.OptimizerConfig('adamw',Fraction(1),beta1=Fraction(0),beta2=Fraction(0),epsilon=Fraction(1))
        limited=us.SequenceKernel(fmt,adam,max_updates=1)
        limited.commit(limited.prepare(us.ok.optimizer_request(limited.toy_gradient(),restriction='structural')))
        limited.tick(one);before=limited.snapshot()
        assert before['kernel']['optimizer_state']['m']['rows'][1][2]!=[0,1]
        assert before['kernel']['optimizer_state']['v']['rows'][1][2]!=[0,1]
        checks+=2
        late=reject(fmt+':late_ledger_limit_after_copy_commit',lambda:limited.prepare(
            us.ok.optimizer_request(limited.toy_gradient(),restriction='structural')))
        assert limited.snapshot()==before;checks+=1
        reject(fmt+':invalid_tick_full_rollback',lambda:limited.tick(fp.encode_constant(2,fmt)))
        assert limited.snapshot()==before;checks+=1
        boundary_records.append({'format':fmt,'kind':'late_admin_ledger_failure',
            'before':before,'after':limited.snapshot(),'refusal':late,'nonzero_moments':True})

        owner=us.SequenceKernel(fmt,adam)
        owner.commit(owner.prepare(us.ok.optimizer_request(owner.toy_gradient(),restriction='structural')))
        owner.tick(one);baseline_snapshot=owner.snapshot()
        exported=owner.snapshot();exported['task']['target_exact'][0][0]=999
        exported['kernel']['optimizer_state']['m']['rows'][1][2]=[999,1]
        exported['accepted_ledger'][0]['new_words'][0][0]=0
        assert owner.snapshot()==baseline_snapshot;checks+=1
        request=us.ok.optimizer_request(owner.toy_gradient(),restriction='structural')
        preview=owner.preview(request);preview['candidate_kernel']['weights'][0][0]=0
        preview['candidate_event']['new_optimizer_state']['m']['rows'][1][2]=[999,1]
        assert owner.snapshot()==baseline_snapshot;checks+=1
        prepared=owner.prepare(request);base=json.loads(prepared)
        mutations={
            'schedule':lambda p:p.__setitem__('schedule','concurrent'),
            'task':lambda p:p['task']['target_exact'][0].__setitem__(0,999),
            'omitted_D_shared_site':lambda p:p['D_descriptor']['sites'].pop(),
            'D_graph':lambda p:p['D_descriptor']['graph'].__setitem__('D','FMA'),
            'D_policy':lambda p:p['D_descriptor'].__setitem__('numerical_policy','other'),
            'D_domain':lambda p:p['D_descriptor'].__setitem__('domain_id','samples'),
            'new_endpoint':lambda p:p['new_kernel_snapshot']['weights'][0].__setitem__(0,0),
            'new_optimizer':lambda p:p['new_kernel_snapshot']['optimizer_state']['m']['rows'][1].__setitem__(2,[999,1]),
            'new_state':lambda p:p['new_kernel_snapshot'].__setitem__('q_word',0),
            'new_version':lambda p:p['new_kernel_snapshot'].__setitem__('weight_version',99),
            'ledger_delta':lambda p:p['new_accepted_event'].__setitem__('actual_effective_rank',99),
            'ledger_accepted_k':lambda p:p['new_accepted_event'].__setitem__('accepted_index',99),
            'old_ledger':lambda p:p['old_combined_snapshot'].__setitem__('accepted_ledger',[]),
            'source':lambda p:p['source_sha256'].__setitem__('update_sequence.py','0'*64),
        }
        for name,mutate in mutations.items():
            data=deepcopy(base);mutate(data['payload']);changed=_rehash(data)
            refusal=reject(fmt+':exact_transaction_tamper:'+name,lambda:owner.commit(changed))
            assert owner.snapshot()==baseline_snapshot;checks+=1
            tamper_records.append({'format':fmt,'kind':'exact_transaction','name':name,'rehash_used':True,'refusal':refusal})
        bad_direction=us.xp.matrix(((1,0,0),(0,0,0)))
        reject(fmt+':AI_cannot_bypass_D_gate',lambda:owner.prepare(us.ok.ai_request(bad_direction,restriction='none')))
        assert owner.snapshot()==baseline_snapshot;checks+=1
        owner.tick(one);after_tick=owner.snapshot()
        reject(fmt+':stale_after_tick',lambda:owner.commit(prepared));assert owner.snapshot()==after_tick;checks+=1
        fresh=owner.prepare(us.ok.optimizer_request(owner.toy_gradient(),restriction='structural'))
        owner.commit(fresh);after_update=owner.snapshot()
        reject(fmt+':replay_after_update',lambda:owner.commit(fresh));assert owner.snapshot()==after_update;checks+=1

        # Valid numerical histories are a separate comparison object. They are
        # not claimed to be the exact-D bank or its Boolean state trajectory.
        def numeric_case(model,old_hist,new_hist,os,ns,comparison='two_histories',method='tube',
                         state_box=None,initial_error=Fraction(0),initial_pair=None,external=None):
            nonlocal checks
            proof=sb.analyze_model(model,fmt,old_hist,new_hist,os,ns,initial_error=initial_error,
                comparison=comparison,method=method,state_box=state_box)
            budget=proof['observed_bound']
            text=sc.make_sequence_certificate(model,fmt,old_hist,new_hist,os,ns,budget,
                initial_error,comparison,method,state_box,version=3,initial_pair=initial_pair,external_context=external)
            receipt=sc.check_sequence_certificate(text,model,fmt,old_hist,new_hist,os,ns,budget,
                initial_error,comparison,method,state_box,version=3,initial_pair=initial_pair,external_context=external)
            assert receipt['authorizes_commit'] is False and receipt['claims_BIT'] is False
            assert proof['observed_bound']==max(proof['error_bounds'])
            checks+=3
            record={'format':fmt,'model':model,'old_history':sb.record(old_hist),'new_history':sb.record(new_hist),
                'old_schedule':os,'new_schedule':ns,'comparison':comparison,'method':method,
                'state_box':sb.record(state_box),'initial_error':sb.record(initial_error),
                'initial_pair':sb.record(initial_pair),'proof':sb.record(proof),'receipt':receipt}
            numerical_cases.append(record)
            if budget>0:
                failure=reject(fmt+':numeric_prefix_budget:'+model+':'+method,lambda:sc.make_sequence_certificate(
                    model,fmt,old_hist,new_hist,os,ns,budget/2,initial_error,comparison,method,state_box))
                assert failure['ledger'] is not None;checks+=1
                budget_exhaustions.append(failure)
            return text,budget,record

        scalar='scalar_switching_v1';b=sb.initial_banks(scalar,fmt)
        hist=(b,_bias(b,fmt,Fraction(1,64)),_bias(b,fmt,Fraction(1,32)),_bias(b,fmt,Fraction(3,64)))
        os=(0,0,0,0);ns=(0,1,1,2)
        external={'kind':'B4_exact_D_identity_only','snapshot':owner.snapshot()}
        text,budget,numeric=numeric_case(scalar,(b,),hist,os,ns,'original_reference',initial_pair=((0,),(0,)),external=external)
        bound_context=owner.snapshot()
        reject(fmt+':numeric_receipt_not_B4_authority',lambda:owner.commit(text));assert owner.snapshot()==bound_context;checks+=1
        b1=us.ok.OptimizerKernel(us.MODEL,fmt,adam,claim='ALG_AND_BIT')
        setup=us.ok.optimizer_request(us.xp.matrix(((0,0,0),(0,0,1))),restriction='structural')
        b1.commit(b1.prepare(setup));b1.tick(one);b1_snapshot=b1.snapshot()
        reject(fmt+':numeric_receipt_not_B1_authority',lambda:b1.commit(text));assert b1.snapshot()==b1_snapshot;checks+=1
        boundary_records.append({'format':fmt,'kind':'numeric_no_authority','B4_before':bound_context,
            'B4_after':owner.snapshot(),'B1_before':b1_snapshot,'B1_after':b1.snapshot(),
            'numeric_receipt':numeric['receipt'],'external_context_not_numeric_state_provenance':True})
        numeric_case(scalar,(b,),hist,os,ns,'original_reference','common_invariant',(Fraction(2),),initial_pair=((0,),(0,)))
        numeric_case(scalar,hist[:3],hist[:3],(0,1),(1,2),'adjacent_endpoints',initial_error=Fraction(1,4),initial_pair=((0,),(fp.encode_constant(Fraction(1,4),fmt),)))
        relu='relu_scalar_switching_v1';rb=sb.initial_banks(relu,fmt)
        numeric_case(relu,(rb,),(rb,_bias(rb,fmt,Fraction(-1,64))),(0,0,0),(0,1,1))
        nilpotent='nilpotent_switching_v1';a=sb.initial_banks(nilpotent,fmt);transpose=deepcopy(a)
        key=next(iter(a));w=a[key]['weights'];transpose[key]['weights']=tuple(tuple(w[j][i] for j in range(2)) for i in range(2))
        numeric_case(nilpotent,(a,),(a,transpose,a),(0,0,0,0),(0,1,2,2))
        shared='shared_relu_switching_v1';s=sb.initial_banks(shared,fmt);sh=(s,_bias(s,fmt,Fraction(1,64)),_bias(s,fmt,Fraction(1,32)))
        sharedtext,sharedbudget,_=numeric_case(shared,(s,),sh,(0,0),(0,1))
        sharedbase=json.loads(sharedtext)
        numeric_mutations={
            'missing_schedule':lambda p:p.pop('schedule_policy'),
            'missing_provenance':lambda p:p.pop('domain_provenance'),
            'sample_domain':lambda p:p['domain_provenance'].__setitem__('samples',True),
            'omitted_shared_call':lambda p:p['descriptor']['graph'].pop(),
            'wrong_nonlinearity':lambda p:p['descriptor']['graph'][0].__setitem__('activation','identity'),
            'FMA_policy':lambda p:p.__setitem__('numerical_policy','FMA'),
            'changed_schedule':lambda p:p.__setitem__('new_schedule',[0,0]),
            'changed_comparison':lambda p:p.__setitem__('comparison','original_reference'),
            'changed_initial_relation':lambda p:p.__setitem__('initial_error',[1,1]),
            'changed_initial_history_quantifier':lambda p:p.__setitem__('same_input_history',False),
            'changed_version':lambda p:p.__setitem__('analysis_version',4),
            'changed_budget':lambda p:p.__setitem__('budget',[0,1]),
            'forged_prefix_ledger':lambda p:p['proof'].__setitem__('budget_ledger',{}),
            'claims_authority':lambda p:p.__setitem__('authorizes_commit',True),
            'changed_unused_endpoint':lambda p:p['new_history'][-1][next(iter(s))]['bias'].__setitem__(0,0),
        }
        for name,mutate in numeric_mutations.items():
            value=deepcopy(sharedbase);mutate(value['payload']);changed=_rehash(value)
            refusal=reject(fmt+':numeric_tamper:'+name,lambda:sc.check_sequence_certificate(
                changed,shared,fmt,(s,),sh,(0,0),(0,1),sharedbudget,version=3))
            tamper_records.append({'format':fmt,'kind':'read_only_numeric','name':name,'rehash_used':True,'refusal':refusal})
        changed_hist=deepcopy(hist);changed_hist=list(changed_hist);changed_hist[-1]=_bias(b,fmt,Fraction(1,8))
        reject(fmt+':externally_changed_unused_tail',lambda:sc.check_sequence_certificate(
            text,scalar,fmt,(b,),tuple(changed_hist),os,ns,budget,comparison='original_reference',version=3,initial_pair=((0,),(0,)),external_context=external))
        stale=deepcopy(external);stale['snapshot']['kernel']['ticks']+=1
        reject(fmt+':stale_full_external_context',lambda:sc.check_sequence_certificate(
            text,scalar,fmt,(b,),hist,os,ns,budget,comparison='original_reference',version=3,initial_pair=((0,),(0,)),external_context=stale))
        reject(fmt+':nonmonotone_schedule',lambda:sc.make_sequence_certificate(scalar,fmt,(b,),hist,(0,0),(1,0),100))
        reject(fmt+':unproved_initial_zero_relation',lambda:sc.make_sequence_certificate(scalar,fmt,(b,),hist,os,ns,100,initial_pair=((0,),(one,))))
        reject(fmt+':unproved_common_box',lambda:sc.make_sequence_certificate(nilpotent,fmt,(a,),(a,transpose),(0,0),(0,1),100,method='common_invariant',state_box=(1,1)))
        reject(fmt+':float_budget',lambda:sc.make_sequence_certificate(scalar,fmt,(b,),hist,os,ns,0.25))
        # Final cancellation cannot erase prefix budget consumption.
        zero=deepcopy(b);key=next(iter(zero));zero[key]['weights']=((0,0),);zero[key]['bias']=(0,)
        pulse=_bias(zero,fmt,Fraction(1,2))
        no_budget=sb.analyze_model(scalar,fmt,(zero,),(pulse,zero),(0,0),(0,1))
        assert no_budget['final_error_bound']<Fraction(1,4)<no_budget['observed_bound'];checks+=1
        failure=reject(fmt+':final_cancellation_does_not_erase_prefix',lambda:sc.make_sequence_certificate(
            scalar,fmt,(zero,),(pulse,zero),(0,0),(0,1),Fraction(1,4)))
        assert failure['ledger'] is not None;checks+=1
        budget_exhaustions.append({'format':fmt,'final_bound':sb.record(no_budget['final_error_bound']),
            'observed_bound':sb.record(no_budget['observed_bound']),'refusal':failure})

    frozen_path=ROOT.parent/'p2_b1'/'training_results.json';raw=frozen_path.read_bytes();frozen=json.loads(raw)
    refused=[s for r in frozen['runs'] for s in r['records'] if s['status']=='refused']
    adam=next(r for r in frozen['runs'] if r['format']=='FP32' and r['optimizer']=='adamw' and r['route']=='final_update_projected_certified')
    assert len(refused)==21 and all(s['proposed_complete_D']['all_protected_observations_equal'] for s in refused)
    assert all(s['proposed_ALG_annihilation'] is False for s in refused)
    assert adam['accepted_commits']==0 and adam['refused_attempts']==8 and adam['final_loss']==adam['initial_loss']=='5/2'
    checks+=6
    return {'schema':'dmwk-p2-b4-transaction-tests-v1','status':'passed','seed':SEED,'checks':checks,
        'unexpected_failures':0,'expected_refusals':len(refusals),'refusal_records':refusals,
        'training_runs':runs,'training_attempts':sum(x['attempts'] for x in runs),
        'accepted_training_updates':sum(x['accepted'] for x in runs),
        'nonzero_training_updates':sum(x['nonzero_stored_updates'] for x in runs),
        'training_D_ticks':sum(len(x['records']) for x in runs),'stall_and_AI_cases':stalls,
        'rollback_boundary_cases':boundary_records,'rehash_tamper_cases':tamper_records,
        'numerical_cases':numerical_cases,'budget_exhaustion_cases':budget_exhaustions,
        'frozen_B1_preservation':{'source_sha256':hashlib.sha256(raw).hexdigest(),'refused':21,
            'all_BIT_equal':True,'all_ALG_false':True,'FP32_AdamW_accepted':0,'FP32_AdamW_refused':8,
            'FP32_AdamW_initial_and_final_loss':'5/2','optimizer_replayed':False},
        'SMT_queries':0,'prior_stage_suites_rerun':False,'environment':environment_metadata(),
        'runtime_seconds':time.perf_counter()-start}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks();(ROOT/'transaction_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','seed','checks','unexpected_failures','expected_refusals',
        'training_attempts','accepted_training_updates','nonzero_training_updates','training_D_ticks','runtime_seconds')}))

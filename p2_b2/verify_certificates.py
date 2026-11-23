"""New B2 read-only budget checks and frozen B1 endpoint analysis.

No prior verifier is imported, and no frozen optimizer trajectory is rerun.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import time

from b2_runtime import get_fp,load_a3,load_b1,environment_metadata
import certified_bounds as cb
import bounded_certificate as bc

SEED=20261114
ROOT=Path(__file__).resolve().parent
ck=load_a3('certificate_kernel')


def _words(rows): return tuple(tuple(v for v in row) for row in rows)
def _fraction(record): return Fraction(*record)
def _json(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def _rehash(data):
    data['payload_sha256']=hashlib.sha256(_json(data['payload']).encode('ascii')).hexdigest()
    return _json(data)


def _changed(old,fmt):
    rows=[list(r) for r in old]
    rows[0][-1]=get_fp().round_fraction(get_fp().decode_word(rows[0][-1],fmt)+Fraction(1,4),fmt)
    return _words(rows)


def run_checks():
    start=time.perf_counter();rng=random.Random(SEED);fp=get_fp()
    checks=0;refusals=[];registered=[];tamper_records=[];rollback_records=[]

    def expect_refusal(name,fn):
        nonlocal checks
        try: fn()
        except (bc.BudgetRejected,load_b1('optimizer_kernel').UpdateRejected) as exc:
            refusals.append({'case':name,'reason':str(exc)});checks+=1
            return str(exc)
        raise AssertionError('Expected refusal: '+name)

    models=('duplicate_feedback_v1','split_feedback_v1','thirds_two_inputs_v1',
            'commit_rounding_v1','shared_axis_v1')
    for fmt in ('BF16','FP32'):
        for model in models:
            old=ck.initial_weights(model,fmt);new=_changed(old,fmt)
            point=bc.analyze_registered_domain(model,fmt,old,new)
            actual_sq=_fraction(point['finite_actual_l2_supremum_squared'])
            actual_inf=_fraction(point['finite_actual_linf_supremum'])
            for method in bc.METHODS:
                for norm in bc.NORMS:
                    proof=bc.analyze_registered_domain(model,fmt,old,new,method,norm)
                    bound=_fraction(proof['bound'])
                    assert actual_sq<=bound*bound if norm=='l2' else actual_inf<=bound
                    text=bc.make_budget_certificate(model,fmt,old,new,bound,method,norm)
                    receipt=bc.check_budget_certificate(text,model,fmt,old,new,bound,method,norm)
                    assert receipt['authorizes_commit'] is False and receipt['claims_BIT'] is False
                    assert receipt['claims_program_noninterference'] is False
                    checks+=4
                    if bound>0:
                        expect_refusal(fmt+':'+model+':'+method+':'+norm+':insufficient_budget',
                            lambda:bc.make_budget_certificate(model,fmt,old,new,bound/2,method,norm))
                    registered.append({'format':fmt,'model':model,'method':method,'norm':norm,
                                       'old_words':old,'new_words':new,'proof':proof,'receipt':receipt,
                                       'finite_actual_l2_supremum_squared':cb.record(actual_sq),
                                       'finite_actual_linf_supremum':cb.record(actual_inf)})

        model='duplicate_feedback_v1';old=ck.initial_weights(model,fmt);new=_changed(old,fmt)
        proof=bc.analyze_registered_domain(model,fmt,old,new)
        budget=_fraction(proof['bound'])
        text=bc.make_budget_certificate(model,fmt,old,new,budget,version=4)
        base=json.loads(text)
        mutations={
            'omitted_shared_site':lambda p:p['source_descriptor']['sites'].pop(),
            'sample_only_coverage':lambda p:p['source_descriptor'].__setitem__('coverage','sampled_only'),
            'omitted_state_activation':lambda p:p['source_descriptor']['sites'][0]['activations'].pop(),
            'FMA_graph':lambda p:p['source_descriptor']['graph'].__setitem__('arithmetic','FMA'),
            'reordered_graph':lambda p:p['source_descriptor']['graph'].__setitem__('matrix_evaluation','descending columns'),
            'changed_policy':lambda p:p['source_descriptor'].__setitem__('numerical_policy','other'),
            'changed_schedule':lambda p:p['source_descriptor'].__setitem__('schedule','concurrent'),
            'omitted_output_port':lambda p:p['observation']['ports'].pop(),
            'changed_bias':lambda p:p['observation']['bias_words'].__setitem__(0,fp.encode_constant(1,fmt)),
            'changed_old_endpoint':lambda p:p['old_words'][0].__setitem__(0,0),
            'changed_new_endpoint':lambda p:p['new_words'][0].__setitem__(0,0),
            'changed_version':lambda p:p.__setitem__('expected_weight_version',5),
            'false_feedback_closure':lambda p:p.__setitem__('candidate_state_invariant_verified',True),
            'false_authority':lambda p:p.__setitem__('authorizes_commit',True),
            'false_BIT':lambda p:p.__setitem__('claims_BIT',True),
            'lowered_bound':lambda p:p['proof'].__setitem__('bound',[0,1]),
            'changed_norm':lambda p:p.__setitem__('norm','linf'),
            'changed_source':lambda p:p['implementation_sha256'].__setitem__('bounded_certificate.py','0'*64),
        }
        for name,mutate in mutations.items():
            data=deepcopy(base);mutate(data['payload']);changed=_rehash(data)
            reason=expect_refusal(fmt+':'+name,lambda:bc.check_budget_certificate(changed,model,fmt,old,new,budget,version=4))
            tamper_records.append({'format':fmt,'case':name,'rehash_used':True,'refused':True,'reason':reason})
        # Analytic envelopes are derived from the trusted registry, not user guesses.
        box=bc.analyze_registered_domain(model,fmt,old,new,'analytic_box')
        boxbudget=_fraction(box['bound'])
        boxtext=bc.make_budget_certificate(model,fmt,old,new,boxbudget,'analytic_box')
        changed=json.loads(boxtext)
        changed['payload']['proof']['input_coordinate_absolute_bounds'][0]=[0,1]
        expect_refusal(fmt+':shrunk_box',lambda:bc.check_budget_certificate(_rehash(changed),model,fmt,old,new,boxbudget,'analytic_box'))
        expect_refusal(fmt+':stale_external_version',lambda:bc.check_budget_certificate(text,model,fmt,old,new,budget,version=5))
        expect_refusal(fmt+':unexpected_external_endpoint',lambda:bc.check_budget_certificate(text,model,fmt,old,old,budget,version=4))
        expect_refusal(fmt+':negative_budget',lambda:bc.make_budget_certificate(model,fmt,old,new,Fraction(-1)))
        expect_refusal(fmt+':float_budget',lambda:bc.make_budget_certificate(model,fmt,old,new,0.25))
        expect_refusal(fmt+':unknown_sample_domain',lambda:bc.make_budget_certificate('sampled_domain',fmt,old,new,1))
        expect_refusal(fmt+':unsupported_norm',lambda:bc.make_budget_certificate(model,fmt,old,new,1,norm='estimated_spectral'))
        expect_refusal(fmt+':duplicate_json_key',lambda:bc.check_budget_certificate('{"payload":{},"payload":{},"payload_sha256":"x"}',model,fmt,old,new,budget))
        expect_refusal(fmt+':nonfinite_json',lambda:bc.check_budget_certificate('{"payload":NaN,"payload_sha256":"x"}',model,fmt,old,new,budget))
        spec=fp.get_format(fmt)
        invalid=(spec.sign_mask,spec.exponent_mask<<spec.fraction_bits,
                 (spec.exponent_mask<<spec.fraction_bits)|1)
        for word in invalid:
            bad=((word,0),old[1])
            expect_refusal(fmt+':invalid_word:'+str(word),lambda:bc.make_budget_certificate(model,fmt,old,bad,1))
        maximum=((spec.exponent_mask-1)<<spec.fraction_bits)|((1<<spec.fraction_bits)-1)
        bad=((maximum,maximum),(0,0))
        for method in bc.METHODS:
            expect_refusal(fmt+':overflow_or_uncertified_totality:'+method,
                           lambda:bc.make_budget_certificate(model,fmt,old,bad,Fraction(10)**100,method))

        # This new B2 integration fixture uses the unchanged B1 API, not an old suite.
        ok=load_b1('optimizer_kernel');cu=load_b1('constrained_updates')
        cfg=cu.OptimizerConfig('adamw',Fraction(1),beta1=Fraction(0),beta2=Fraction(0),epsilon=Fraction(1))
        kernel=ok.OptimizerKernel(model,fmt,cfg,claim='ALG_AND_BIT')
        request=ok.optimizer_request(cu.xp.matrix(((1,0),(0,0))),restriction='projected')
        kernel.commit(kernel.prepare(request));kernel.tick(fp.encode_constant(1,fmt))
        snapshot=kernel.snapshot();liveold=_words(snapshot['weights']);livenew=_changed(liveold,fmt)
        assert snapshot['optimizer_state']['m']['rows'][0][0]!=[0,1]
        assert snapshot['optimizer_state']['v']['rows'][0][0]!=[0,1]
        checks+=2
        analysis=bc.analyze_registered_domain(model,fmt,liveold,livenew)
        budget=_fraction(analysis['bound'])
        evidence=bc.make_budget_certificate(model,fmt,liveold,livenew,budget,
                                           version=snapshot['weight_version'],snapshot_context=snapshot)
        receipt=bc.check_budget_certificate(evidence,model,fmt,liveold,livenew,budget,
                                           version=snapshot['weight_version'],snapshot_context=snapshot)
        reason=expect_refusal(fmt+':numeric_receipt_is_not_B1_commit',lambda:kernel.commit(evidence))
        assert kernel.snapshot()==snapshot
        checks+=1
        kernel.tick(fp.encode_constant(1,fmt));later=kernel.snapshot()
        expect_refusal(fmt+':stale_snapshot_context',lambda:bc.check_budget_certificate(
            evidence,model,fmt,liveold,livenew,budget,version=snapshot['weight_version'],snapshot_context=later))
        assert kernel.snapshot()==later;checks+=1
        rollback_records.append({'format':fmt,'snapshot_before_refusal':snapshot,
            'snapshot_after_refusal':snapshot,'nonzero_m_and_v':True,'reason':reason,
            'numeric_receipt':receipt,'new_integration_fixture_not_old_optimization_replay':True,
            'later_tick_snapshot':later,'stale_context_refused':True})

    # Seeded endpoint variations on complete domains; these are properties of
    # the 16 generated pairs, not all possible matrices or optimizer trajectories.
    random_records=[]
    for fmt in ('BF16','FP32'):
        for index in range(8):
            model=models[index%len(models)];old=ck.initial_weights(model,fmt)
            new=_words(tuple(fp.round_fraction(fp.decode_word(w,fmt)+Fraction(rng.randrange(-4,5),8),fmt)
                             for w in row) for row in old)
            proof=bc.analyze_registered_domain(model,fmt,old,new)
            bound=_fraction(proof['bound']);actual_sq=_fraction(proof['finite_actual_l2_supremum_squared'])
            assert actual_sq<=bound*bound;checks+=1
            random_records.append({'format':fmt,'case':index,'model':model,'old_words':old,'new_words':new,
                                   'bound':proof['bound'],'actual_l2_supremum_squared':proof['finite_actual_l2_supremum_squared']})

    frozen_path=ROOT.parent/'p2_b1'/'training_results.json'
    frozen_bytes=frozen_path.read_bytes();frozen=json.loads(frozen_bytes)
    frozen_records=[]
    for run in frozen['runs']:
        for step in run['records']:
            if step['status']!='refused': continue
            t=time.perf_counter();fmt=run['format'];model=run['model']
            old=_words(step['old_weights']);new=_words(step['candidate_weights'])
            point=bc.analyze_registered_domain(model,fmt,old,new)
            box=bc.analyze_registered_domain(model,fmt,old,new,'analytic_box')
            assert step['proposed_ALG_annihilation'] is False
            assert step['proposed_complete_D']['all_protected_observations_equal'] is True
            assert _fraction(point['finite_actual_l2_supremum_squared'])==0
            assert _fraction(point['finite_actual_linf_supremum'])==0
            delta=cb.decode_matrix(new,fmt);previous=cb.decode_matrix(old,fmt)
            descriptor=ck.model_descriptor(model,fmt)
            exact_residuals=[]
            for site in descriptor['sites']:
                for h in site['activations']:
                    values=cb.decode_vector(tuple(h),fmt)
                    exact_residuals.extend(sum(((b-a)*x for a,b,x in zip(ro,rn,values)),Fraction(0))
                                           for ro,rn in zip(previous.rows,delta.rows))
            assert any(v!=0 for v in exact_residuals)
            assert _fraction(point['bound'])>0
            checks+=6
            evidence=bc.make_budget_certificate(model,fmt,old,new,_fraction(point['bound']))
            receipt=bc.check_budget_certificate(evidence,model,fmt,old,new,_fraction(point['bound']))
            frozen_records.append({'format':fmt,'optimizer':run['optimizer'],'attempt':step['attempt'],
                'old_words':old,'proposed_words':new,'original_status':'refused',
                'original_refusal_reason':step['refusal_reason'],
                'new_finite_domain_BIT_observation':True,'new_exact_ALG_observation':False,
                'point_proof':point,'box_proof':box,'read_only_receipt':receipt,
                'point_bound_less_than_box_bound':_fraction(point['bound'])<_fraction(box['bound']),
                'original_state_and_optimizer_unchanged':True,
                'runtime_seconds':time.perf_counter()-t})
    assert len(frozen_records)==21;checks+=1
    frozen_adam=next(r for r in frozen['runs'] if r['format']=='FP32' and r['optimizer']=='adamw'
                     and r['route']=='final_update_projected_certified')
    assert frozen_adam['accepted_commits']==0 and frozen_adam['refused_attempts']==8
    assert frozen_adam['initial_loss']==frozen_adam['final_loss']=='5/2'
    checks+=2
    return {'schema':'dmwk-p2-b2-certificate-tests-v1','status':'passed','seed':SEED,
        'checks':checks,'unexpected_failures':0,'expected_refusals':len(refusals),
        'refusal_records':refusals,'registered_receipt_cases':registered,
        'registered_receipt_case_count':len(registered),'tamper_cases':tamper_records,
        'rollback_cases':rollback_records,'seeded_endpoint_cases':random_records,
        'frozen_B1_analysis':frozen_records,'frozen_B1_refused_endpoint_count':len(frozen_records),
        'frozen_B1_source_sha256':hashlib.sha256(frozen_bytes).hexdigest(),
        'frozen_B1_FP32_AdamW_joint':{'accepted':0,'refused':8,'initial_loss':'5/2','final_loss':'5/2',
                                   'optimizer_reexecuted':False},
        'bound_scope':'Single-layer original registered envelope; no candidate feedback closure or live authorization',
        'norms':['l2','linf'],'SMT_queries':0,'prior_stage_suites_rerun':False,
        'environment':environment_metadata(),'runtime_seconds':time.perf_counter()-start}


if __name__=='__main__':
    if not __debug__: raise SystemExit('Run without -O/-OO')
    result=run_checks();(ROOT/'certificate_results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','seed','checks','unexpected_failures','expected_refusals',
                'registered_receipt_case_count','frozen_B1_refused_endpoint_count','runtime_seconds')}))

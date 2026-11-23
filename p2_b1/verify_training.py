"""B1 fixed toy optimization comparison with isolated unsafe baselines.

This is a finite experiment, not a universal learning theorem. Baselines do
not receive live authorization. Safe routes publish only through the new B1
combined-bank transaction and compare protected ticks with an unchanged peer.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import time

from b1_runtime import get_fp, load_a2, environment_metadata
import constrained_updates as cu
import optimizer_kernel as ok

SEED = 20261114
STEPS = 8
ROOT = Path(__file__).resolve().parent
xp = load_a2("exact_projection")


def configurations():
    return (
        cu.OptimizerConfig("sgd", Fraction(1)),
        cu.OptimizerConfig("momentum", Fraction(1,2), momentum=Fraction(1,2)),
        cu.OptimizerConfig("adamw", Fraction(1,4), beta1=Fraction(1,2),
                           beta2=Fraction(3,4), epsilon=Fraction(1,1024),
                           weight_decay=Fraction(1,8)),
    )


def _words(value):
    return tuple(tuple(x for x in row) for row in value)


def _decode(words, fmt):
    fp = get_fp()
    return xp.matrix(tuple(tuple(fp.decode_word(x,fmt) for x in row) for row in words))


def _audit(a):
    return {k:getattr(a,k) for k in ("native_multiply","native_add","software_multiply",
                                    "software_add","exact_sums","native_oracle_checks")}


def _local_observation(weights, q, u, fmt, model):
    """Offline fixed-graph diagnostic; never publish a protected state.

    Non-Boolean call outputs stop before the Boolean transition. Baseline
    endpoint probes are explicitly outside safety-authorized execution.
    """
    fp=get_fp();one=fp.encode_constant(1,fmt);audit=fp.Audit()
    structural=model=='structural_duplicate_v1'
    state_input=(q,q,0) if structural else (q,q)
    input_input=(u,u,0) if structural else (u,u)
    columns=(0,1)
    outputs=[]
    for activation in (state_input,input_input):
        current=[]
        for row in weights:
            acc=0
            for j in columns:
                p=fp.mul_words(row[j],activation[j],fmt,audit)
                acc=fp.add_words(acc,p,fmt,audit)
            current.append(acc)
        outputs.append(tuple(current))
    legal=all(x in (0,one) for row in outputs for x in row)
    successor=None
    if legal:
        left,right=outputs[0][0],outputs[1][0]
        p=fp.mul_words(left,right,fmt,audit)
        twice=fp.mul_words(fp.encode_constant(2,fmt),p,fmt,audit)
        neg=fp.mul_words(fp.encode_constant(-1,fmt),twice,fmt,audit)
        summed=fp.add_words(left,right,fmt,audit)
        successor=fp.add_words(summed,neg,fmt,audit)
        legal=successor in (0,one)
    return {'state_output_words':list(outputs[0]),'input_output_words':list(outputs[1]),
            'next_state_word':successor,'canonical_transition':legal,'audit':_audit(audit)}


def _complete_domain(weights, baseline, fmt, model):
    fp=get_fp();one=fp.encode_constant(1,fmt)
    records=[];same=True
    for q in (0,one):
        for u in (0,one):
            old=_local_observation(baseline,q,u,fmt,model)
            new=_local_observation(weights,q,u,fmt,model)
            equal=all(old[k]==new[k] for k in ('state_output_words','input_output_words','next_state_word'))
            same &= equal and new['canonical_transition']
            records.append({'q_word':q,'u_word':u,'equal':equal,
                            'old':old,'candidate':new})
    return {'complete_registered_state_input_pairs':4,
            'all_protected_observations_equal':bool(same),'records':records,
            'scope':'Offline full-domain diagnostic; it is not a live commit certificate'}


def _response(weights, fmt, model):
    fp=get_fp();one=fp.encode_constant(1,fmt)
    activation=(0,0,one) if model=='structural_duplicate_v1' else (one,0)
    result=ok.evaluate_a(weights,activation,fmt,model)
    words=tuple(result['output_words'])
    values=tuple(fp.decode_word(w,fmt) for w in words)
    target=(Fraction(0),Fraction(2))
    loss=sum(((v-t)**2 for v,t in zip(values,target)),Fraction(0))/2
    return words,values,loss


def _gradient(values, width, structural):
    errors=(values[0],values[1]-2)
    column=2 if structural else 0
    return xp.matrix(tuple(tuple(e if j==column else Fraction(0) for j in range(width))
                           for e in errors))


def _run(fmt,cfg,route,inputs):
    started=time.perf_counter();fp=get_fp();one=fp.encode_constant(1,fmt)
    structural=route=='structural_final_mask_certified'
    model='structural_duplicate_v1' if structural else 'duplicate_feedback_v1'
    safe=route in ('final_update_projected_certified','structural_final_mask_certified')
    mode={'unconstrained_offline':'none','gradient_only_projected_offline':'gradient_only',
          'final_update_projected_certified':'projected','structural_final_mask_certified':'structural'}[route]
    weights=ok.initial_weights(model,fmt);baseline=weights
    H=ok.global_generators(model,fmt)
    state=cu.initial_optimizer_state(len(weights),len(weights[0]))
    kernel=ok.OptimizerKernel(model,fmt,cfg,claim='ALG_AND_BIT') if safe else None
    peer=ok.OptimizerKernel(model,fmt,cfg,claim='ALG_AND_BIT') if safe else None
    initial_response,_,initial_loss=_response(weights,fmt,model)
    feedback_q=0;reference_q=0;feedback_active=True
    checks=accepted=rejected=applied=0;records=[]
    for index,u_bit in enumerate(inputs,1):
        old_weights=weights;old_state=state
        old_response,values,loss_before=_response(weights,fmt,model)
        gradient=_gradient(values,len(weights[0]),structural)
        before_snapshot=kernel.snapshot() if safe else None
        staged=cu.stage_optimizer(_decode(weights,fmt),gradient,state,cfg,mode=mode,
                                  H=H,free_columns=(2,) if structural else ())
        candidate=ok.quantize_endpoint(weights,staged.increment,fmt)
        proposed_delta=xp.sub(_decode(candidate,fmt),_decode(weights,fmt))
        proposal_domain=_complete_domain(candidate,baseline,fmt,model)
        record={'attempt':index,'route':route,'gradient':cu.matrix_record(gradient),
                'raw_increment':cu.matrix_record(staged.raw_increment),
                'restricted_increment':cu.matrix_record(staged.increment),
                'proposal_audit':staged.audit,'old_weights':old_weights,
                'candidate_weights':candidate,'proposed_effective_delta':cu.matrix_record(proposed_delta),
                'proposed_effective_rank':xp.rank(proposed_delta),
                'proposed_ALG_annihilation':all(v==0 for row in xp.matmul(proposed_delta,H).rows for v in row),
                'proposed_complete_D':proposal_domain,'old_optimizer_state':cu.state_record(state),
                'staged_optimizer_state':cu.state_record(staged.next_state),
                'loss_before':str(loss_before),'old_A_output_words':old_response}
        if safe:
            request=ok.optimizer_request(gradient,restriction=mode)
            preview=kernel.preview(request)
            assert _words(preview['candidate_words'])==candidate
            assert preview['next_optimizer_state']==cu.state_record(staged.next_state)
            checks+=2
            try:
                prepared=kernel.prepare(request)
                receipt=kernel.commit(prepared)
            except ok.UpdateRejected as exc:
                assert kernel.snapshot()==before_snapshot
                checks+=1;rejected+=1
                record.update(status='refused',refusal_reason=str(exc),rollback_complete_snapshot_equal=True)
            else:
                accepted+=1;weights=candidate;state=staged.next_state
                assert _words(kernel.snapshot()['weights'])==weights
                assert kernel.snapshot()['optimizer_state']==cu.state_record(state)
                assert proposal_domain['all_protected_observations_equal']
                assert record['proposed_ALG_annihilation']
                checks+=4
                record.update(status='accepted',receipt=receipt,
                              certificate_sha256=hashlib.sha256(prepared.encode('ascii')).hexdigest())
            # Every successful or refused attempt is followed by a real legal
            # protected tick; prepare/commit always precedes that tick.
            prior_state=kernel.state_word
            expected=_local_observation(weights,prior_state,one if u_bit else 0,fmt,model)
            live_tick=kernel.tick(one if u_bit else 0)
            reference_tick=peer.tick(one if u_bit else 0)
            assert kernel.state_word==peer.state_word==expected['next_state_word']
            assert live_tick==reference_tick
            checks+=2
            record['protected_feedback']={'kind':'authorized_paired_ticks','input_bit':u_bit,
                                          'old_q_word':prior_state,'actual_tick':live_tick,
                                          'reference_tick':reference_tick,'equal':True}
            record['snapshot_after_tick']=kernel.snapshot()
        else:
            weights=candidate;state=staged.next_state;applied+=1
            record.update(status='offline_applied_without_authorization',live_authorization=False)
            reference=_local_observation(baseline,reference_q,one if u_bit else 0,fmt,model)
            reference_q=reference['next_state_word']
            if feedback_active:
                diagnostic=_local_observation(weights,feedback_q,one if u_bit else 0,fmt,model)
                equal=all(diagnostic[k]==reference[k] for k in ('state_output_words','input_output_words','next_state_word'))
                if diagnostic['canonical_transition']:
                    feedback_q=diagnostic['next_state_word']
                else:
                    feedback_active=False
                record['protected_feedback']={'kind':'offline_diagnostic_only','input_bit':u_bit,
                                              'actual':diagnostic,'reference':reference,
                                              'equal':equal,'continued':feedback_active,
                                              'authorized':False}
            else:
                record['protected_feedback']={'kind':'offline_feedback_stopped_after_domain_violation',
                                              'input_bit':u_bit,'reference':reference,'authorized':False}
        delta=xp.sub(_decode(weights,fmt),_decode(old_weights,fmt))
        new_response,_,loss_after=_response(weights,fmt,model)
        assert state.step==old_state.step+(0 if record['status']=='refused' else 1)
        checks+=1
        record.update(actual_weights=weights,actual_effective_delta=cu.matrix_record(delta),
                      actual_effective_rank=xp.rank(delta),actual_optimizer_state=cu.state_record(state),
                      new_A_output_words=new_response,loss_after=str(loss_after),
                      actual_complete_D=_complete_domain(weights,baseline,fmt,model))
        if safe:
            assert record['actual_complete_D']['all_protected_observations_equal']
            checks+=1
        records.append(record)
    final_response,_,final_loss=_response(weights,fmt,model)
    return {'format':fmt,'optimizer':cfg.kind,'route':route,'model':model,'config':cu.config_record(cfg),
            'safe_live_route':safe,'acceptance_claim':'ALG_AND_BIT' if safe else None,
            'steps':len(records),'accepted_commits':accepted,'refused_attempts':rejected,
            'offline_applied_steps':applied,'initial_A_output_words':initial_response,
            'final_A_output_words':final_response,'initial_loss':str(initial_loss),
            'final_loss':str(final_loss),'loss_decreased':final_loss<initial_loss,
            'changed_stored_endpoint':weights!=baseline,'final_optimizer_state':cu.state_record(state),
            'all_actual_endpoints_D_equivalent':all(r['actual_complete_D']['all_protected_observations_equal'] for r in records),
            'records':records,'checks':checks,'runtime_seconds':time.perf_counter()-started}


def run_checks():
    started=time.perf_counter();rng=random.Random(SEED)
    inputs=tuple(rng.randrange(2) for _ in range(STEPS))
    runs=[];checks=0
    routes=('unconstrained_offline','gradient_only_projected_offline',
            'final_update_projected_certified','structural_final_mask_certified')
    for fmt in ('BF16','FP32'):
        for cfg in configurations():
            for route in routes:
                result=_run(fmt,cfg,route,inputs)
                checks+=result['checks'];runs.append(result)
    for fmt in ('BF16','FP32'):
        safe_sgd=next(r for r in runs if r['format']==fmt and r['optimizer']=='sgd' and r['route']=='final_update_projected_certified')
        assert safe_sgd['accepted_commits']==STEPS and safe_sgd['refused_attempts']==0
        assert Fraction(safe_sgd['final_loss'])==Fraction(5,2)*(Fraction(1,4)**STEPS)
        structural=next(r for r in runs if r['format']==fmt and r['optimizer']=='sgd' and r['route']=='structural_final_mask_certified')
        assert structural['accepted_commits']==STEPS and Fraction(structural['final_loss'])==0
        gradient_adam=next(r for r in runs if r['format']==fmt and r['optimizer']=='adamw' and r['route']=='gradient_only_projected_offline')
        assert not gradient_adam['all_actual_endpoints_D_equivalent']
        checks+=4
    for run in runs:
        if run['safe_live_route']:
            assert run['all_actual_endpoints_D_equivalent']
            checks+=1
    return {'schema':'dmwk-p2-b1-training-v1','status':'passed','seed':SEED,'checks':checks,
            'unexpected_failures':0,'runs':runs,'run_count':len(runs),
            'attempts':sum(r['steps'] for r in runs),'shared_feedback_input_bits':inputs,
            'accepted_safe_commits':sum(r['accepted_commits'] for r in runs),
            'refused_safe_attempts':sum(r['refused_attempts'] for r in runs),
            'accepted_nonzero_stored_updates':sum(
                step['status']=='accepted' and step['actual_weights']!=step['old_weights']
                for run in runs for step in run['records']),
            'refused_candidates_passing_registered_BIT_diagnostic':sum(
                step['status']=='refused' and step['proposed_complete_D']['all_protected_observations_equal']
                for run in runs for step in run['records']),
            'paired_authorized_feedback_ticks':sum(
                len(run['records']) for run in runs if run['safe_live_route']),
            'complete_D_diagnostic_state_input_pairs':sum(
                len(step[key]['records']) for run in runs for step in run['records']
                for key in ('proposed_complete_D','actual_complete_D')),
            'offline_applied_steps':sum(r['offline_applied_steps'] for r in runs),
            'objective':'One fixed legal A basis input; exact decoded 1/2 squared Euclidean loss to (0,2)',
            'gradient_scope':'Gradient of the continuous linear squared-loss extension at decoded endpoints, not derivative of target-format rounding',
            'comparison_limit':'Dense and structural routes have different parameterizations/domains; no performance, generalization or universal convergence claim',
            'environment':environment_metadata(),'SMT_queries':0,'prior_stage_suites_rerun':False,
            'runtime_seconds':time.perf_counter()-started}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks()
    out=ROOT/'training_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('runs','environment')}))

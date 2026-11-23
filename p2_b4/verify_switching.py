"""B4 fixed-domain finite switching checks; no prior verification suite is run."""
from __future__ import annotations
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import hashlib
import json
import random
import time

from b4_runtime import get_fp,load_a2,load_b3,environment_metadata
import switching_bounds as sb

xp=load_a2('exact_projection')
SEED=20261114


def record(x):
    if isinstance(x,F):return str(x)
    if isinstance(x,xp.Matrix):return xp.serialize(x)
    if isinstance(x,dict):return {k:record(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [record(v) for v in x]
    return x


def compact_range_records(value):
    """Keep every endpoint/trajectory/coefficient; digest repeated range details.

    This changes result storage only. Every range proof is still constructed
    and checked by the same execution before its deterministic digest is saved.
    Two unabridged network proofs remain as inspectable representative records.
    """
    range_keys={'old_range','new_range','joint_operation_range_proof'}
    if isinstance(value,list):return [compact_range_records(v) for v in value]
    if isinstance(value,dict):
        out={}
        for key,item in value.items():
            if key=='unabridged_reference_proofs':out[key]=item
            elif key in range_keys:
                exact=json.dumps(item,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
                out[key]={'canonical_full_record_sha256':hashlib.sha256(exact.encode('ascii')).hexdigest(),
                          'recording':'Repeated nested range details omitted; exact endpoint/box/coefficient fields retained',
                          'reproduce':'Run switching_bounds.analyze_model/analyze_switching on the recorded histories and domains'}
            else:out[key]=compact_range_records(item)
        return out
    return value


def norm(v):return max(map(abs,v),default=F(0))
def dec(v,fmt):return tuple(get_fp().decode_word(w,fmt) for w in v)
def enc(v,fmt):return tuple(get_fp().round_fraction(F(x),fmt) for x in v)
def graph(bank_id='dynamics',activation='identity'):
    return ({'call_id':'state_update','bank_id':bank_id,'activation':activation},)
def endpoint(rows,bias,fmt,bank_id='dynamics'):
    return {bank_id:{'weights':tuple(enc(r,fmt) for r in rows),'bias':enc(bias,fmt)}}


def exact_network(g,banks,h,fmt):
    current=tuple(h)
    for site in g:
        bank=banks[site['bank_id']]
        current=tuple(b+sum((a*x for a,x in zip(dec(row,fmt),current)),F(0))
                      for row,b in zip(bank['weights'],dec(bank['bias'],fmt)))
        if site['activation']=='relu':current=tuple(max(F(0),x) for x in current)
    return current


def raw_network(g,banks,h,fmt):
    fp=get_fp();current=tuple(h);audit=fp.Audit()
    for site in g:
        bank=banks[site['bank_id']];out=[]
        for row,bias in zip(bank['weights'],bank['bias']):
            acc=bias
            for w,x in zip(row,current):acc=fp.add_words(acc,fp.mul_words(w,x,fmt,audit),fmt,audit)
            if site['activation']=='relu' and fp.decode_word(acc,fmt)<=0:acc=0
            out.append(acc)
        current=tuple(out)
    return current


def reference_history(g,history,schedule,initial,inputs,fmt):
    raw=tuple(initial);real=dec(raw,fmt);states=[raw];real_states=[real];errors=[]
    for index,u in zip(schedule,inputs):
        local_exact=exact_network(g,history[index],dec(raw,fmt)+dec(u,fmt),fmt)
        raw=raw_network(g,history[index],raw+tuple(u),fmt)
        errors.append(tuple(a-b for a,b in zip(dec(raw,fmt),local_exact)))
        real=exact_network(g,history[index],real+dec(u,fmt),fmt)
        states.append(raw);real_states.append(real)
    return {'states':tuple(states),'exact_real_states':tuple(real_states),'local_execution_errors':tuple(errors)}


def direct_product_sum(Ls,betas,E0):
    out=[F(E0)]
    for t in range(1,len(Ls)+1):
        value=F(E0)
        for L in Ls[:t]:value*=L
        for j in range(t):
            term=betas[j]
            for L in Ls[j+1:t]:term*=L
            value+=term
        out.append(value)
    return tuple(out)


def compare_reference(g,oh,nh,os,ns,oi,ni,inputs,fmt,analysis):
    old=reference_history(g,oh,os,oi,inputs,fmt);new=reference_history(g,nh,ns,ni,inputs,fmt)
    errors=tuple(norm(tuple(b-a for a,b in zip(dec(x,fmt),dec(y,fmt)))) for x,y in zip(old['states'],new['states']))
    assert all(e<=b for e,b in zip(errors,analysis['error_bounds']))
    assert all(all(abs(x)<=b for x,b in zip(dec(state,fmt),box)) for state,box in zip(old['states'],analysis['old_state_tube']))
    assert all(all(abs(x)<=b for x,b in zip(dec(state,fmt),box)) for state,box in zip(new['states'],analysis['new_state_tube']))
    actual=max(errors);bound=analysis['observed_bound']
    return {'old_trace':old,'new_trace':new,'observed_errors':errors,'observed_prefix_max':actual,
            'certified_prefix_bound':bound,'absolute_slack':bound-actual,
            'bound_to_observed_ratio':None if actual==0 else bound/actual},3


def check_recurrence(analysis,E0):
    expected=direct_product_sum(tuple(analysis['Ls']),tuple(analysis['betas']),E0)
    assert tuple(analysis['error_bounds'])==expected
    assert analysis['final_error_bound']==expected[-1] and analysis['observed_bound']==max(expected)
    assert tuple(analysis['product_sum']['product_sum_prefixes'])==expected
    assert tuple(analysis['budget_ledger']['prefix_maxima'])==tuple(max(expected[:i+1]) for i in range(len(expected)))
    return expected,4


def complete_and_seeded_cases():
    rng=random.Random(SEED);checks=0;families=[];points=[];g=graph()
    for fmt in ('BF16','FP32'):
        base=endpoint(((F(1,2),F(1,8)),),(0,),fmt)
        modes=[endpoint(((F(1,4),F(1,8)),),(0,),fmt),endpoint(((F(1,2),F(1,8)),),(F(1,64),),fmt)]
        definitions=[]
        for seq in product((0,1),repeat=3):
            history=[base]+[modes[m] for m in seq]
            definitions.append(('original_reference',seq,(base,),tuple(history),(0,)*3,(1,2,3),3))
            definitions.append(('adjacent_endpoints',seq,tuple(history),tuple(history),(0,1,2),(1,2,3),3))
        for old_modes in product((0,1),repeat=2):
            for new_modes in product((0,1),repeat=2):
                definitions.append(('two_histories',(old_modes,new_modes),tuple(modes[m] for m in old_modes),
                                    tuple(modes[m] for m in new_modes),(0,1),(0,1),2))
        for family_index,(comparison,mode_ids,oh,nh,os,ns,T) in enumerate(definitions):
            analysis=sb.analyze_model('scalar_switching_v1',fmt,oh,nh,os,ns,comparison=comparison)
            _,n=check_recurrence(analysis,0);checks+=n
            family_id=f'{fmt}:complete:{family_index}:{comparison}';observed=[]
            for input_index,sequence in enumerate(product((-1,0,1),repeat=T)):
                inputs=tuple(enc((u,),fmt) for u in sequence)
                row,n=compare_reference(g,oh,nh,os,ns,(0,),(0,),inputs,fmt,analysis);checks+=n
                if input_index==0:
                    a=sb.trace_model('scalar_switching_v1',fmt,oh,os,(0,),inputs,side='old')
                    b=sb.trace_model('scalar_switching_v1',fmt,nh,ns,(0,),inputs,side='new')
                    assert tuple(tuple(x) for x in a['states'])==row['old_trace']['states']
                    assert tuple(tuple(x) for x in b['states'])==row['new_trace']['states'];checks+=2
                row.update({'family_id':family_id,'inputs':sequence});points.append(row);observed.append(row['observed_prefix_max'])
            maximum=max(observed)
            families.append({'family_id':family_id,'comparison':comparison,'format':fmt,'mode_ids':mode_ids,
                             'old_history':oh,'new_history':nh,'old_schedule':os,'new_schedule':ns,
                             'horizon':T,'complete_input_history_count':3**T,'analysis':analysis,'observed_max':maximum,
                             'bound_to_observed_ratio':None if maximum==0 else analysis['observed_bound']/maximum,
                             'scope':'All input histories over the stated ternary alphabet for this exact mode history and initial pair'})
        # Longer histories are sampled, never used to infer a time-uniform theorem.
        stress_modes=modes+[endpoint(((F(1,4),F(1,8)),),(F(-1,64),),fmt)]
        for j in range(6):
            T=12;oh=tuple(stress_modes[rng.randrange(3)] for _ in range(T));nh=tuple(stress_modes[rng.randrange(3)] for _ in range(T))
            schedule=tuple(range(T));E0=F(1,8) if j%2 else F(0)
            inputs=tuple(enc((rng.choice((-1,0,1)),),fmt) for _ in range(T))
            analysis=sb.analyze_model('scalar_switching_v1',fmt,oh,nh,schedule,schedule,initial_error=E0)
            _,n=check_recurrence(analysis,E0);checks+=n
            row,n=compare_reference(g,oh,nh,schedule,schedule,(0,),enc((E0,),fmt),inputs,fmt,analysis);checks+=n
            row.update({'family_id':fmt+':seeded:'+str(j),'input_words':inputs,'initial_error':E0,
                        'old_history':oh,'new_history':nh,'analysis':analysis,'scope':'One seeded length-12 history pair'})
            points.append(row)
        # Prove a common family invariant separately from the finite sampled paths.
        family=(base,)+tuple(stress_modes)
        invariant=sb.analyze_model('scalar_switching_v1',fmt,(base,),tuple([base]+stress_modes),(0,0,0),(1,2,3),
                                   comparison='original_reference',method='common_invariant',state_box=(F(1),),common_family=family)
        proof=invariant['common_family_proof']
        assert proof['common_invariant_verified'] and proof['all_history_versions_covered'] and proof['strict_common_contraction']
        assert proof['uniform_L']==F(1,2) and proof['mode_count']==4 and proof['ordered_pair_count']==16;checks+=2
        families.append({'family_id':fmt+':common_contraction_family','format':fmt,'analysis':invariant,
                         'scope':'Uniform conclusion only for continuations within the same declared finite mode family and domains'})
        # Version 1 is stored but never ticked; 0 and 3 are each ticked twice.
        schedule=(0,0,2,3,3);hist=(base,modes[0],modes[1],stress_modes[2]);inputs=(enc((0,),fmt),)*5
        analysis=sb.analyze_model('scalar_switching_v1',fmt,(base,),hist,(0,)*5,schedule,comparison='original_reference')
        row,n=compare_reference(g,(base,),hist,(0,)*5,schedule,(0,),(0,),inputs,fmt,analysis);checks+=n
        assert len(schedule)!=len(hist)-1 and 1 not in schedule and schedule.count(0)==schedule.count(3)==2;checks+=1
        row.update({'case':'version_index_is_not_tick_count','format':fmt,'stored_version_count':4,'ticks':5,
                    'new_schedule':schedule,'analysis':analysis,'authorization':'Stored numeric history premise only; B1 acceptance belongs to separate transaction evidence'})
        points.append(row)
        # Changing endpoints can still give identical paired trajectories.
        hist=(base,modes[0],modes[1]);schedule=(0,1,2);inputs=(enc((1,),fmt),)*3
        analysis=sb.analyze_model('scalar_switching_v1',fmt,hist,hist,schedule,schedule)
        row,n=compare_reference(g,hist,hist,schedule,schedule,(0,),(0,),inputs,fmt,analysis);checks+=n
        assert row['observed_prefix_max']==0 and analysis['observed_bound']>0;checks+=1
        row.update({'case':'identical_changing_histories_zero_actual_positive_bound','format':fmt,'analysis':analysis});points.append(row)
    return {'status':'passed','checks':checks,'complete_mode_pair_families':64,'complete_trajectory_pairs':1152,
            'seeded_trajectory_pairs':12,'seeded_horizon':12,'families':families,'trajectory_records':points,
            'scope':'Complete finite mode/input sets and separately labelled seeded histories; same legal input per compared pair'}


def switching_and_budget_cases():
    checks=0;records=[];refusals=[];fp=get_fp();pb=load_b3('propagation_bounds')
    A=xp.matrix(((0,2),(0,0)));B=xp.transpose(A)
    assert xp.matmul(A,A)==xp.zeros(2,2) and xp.matmul(B,B)==xp.zeros(2,2)
    assert xp.matmul(B,A)==xp.matrix(((0,0),(0,4)));checks+=2
    for fmt in ('BF16','FP32'):
        a=endpoint(A.rows,(0,0),fmt);b=endpoint(B.rows,(0,0),fmt)
        new=(a,b,a,b,a,b);old=(a,);os=(0,)*6;ns=tuple(range(6));inputs=((),)*6
        analysis=sb.analyze_model('nilpotent_switching_v1',fmt,old,new,os,ns,comparison='original_reference')
        initial=enc((0,F(1,8)),fmt)
        row,n=compare_reference(graph(),old,new,os,ns,initial,initial,inputs,fmt,analysis);checks+=n
        expected=(F(1,8),F(1,4),F(1,2),F(1),F(2),F(4),F(8))
        assert tuple(norm(dec(s,fmt)) for s in row['new_trace']['states'])==expected
        assert row['old_trace']['states'][2:]==((0,0),)*5;checks+=2
        row.update({'case':'individually_nilpotent_switched_amplification','format':fmt,'A':A,'B':B,'BA':xp.matmul(B,A),
                    'analysis':analysis,'individual_weighted_norms':{'A_weights':(1,4),'B_weights':(4,1),'individual_gain':F(1,2)},
                    'scope':'Real switching counterexample plus six finite-format steps; no infinite hardware-range claim'})
        records.append(row)
        # A B3 constant L,beta pair is tied to the old fixed endpoint.
        base=endpoint(((F(1,2),0),),(0,),fmt);strong=endpoint(((2,0),),(0,),fmt)
        oh=(base,);nh=(base,strong,strong);os=(0,0,0);ns=(0,1,2)
        current=sb.analyze_model('scalar_switching_v1',fmt,oh,nh,os,ns,comparison='original_reference')
        stale_one=sb.analyze_model('scalar_switching_v1',fmt,oh,oh,(0,),(0,))
        stale=pb.constant_recurrence(stale_one['Ls'][0],stale_one['betas'][0],3,initial_error=0)
        row,n=compare_reference(graph(),oh,nh,os,ns,enc((F(1,8),),fmt),enc((F(1,8),),fmt),(enc((0,),fmt),)*3,fmt,current);checks+=n
        assert row['observed_errors'][-1]>stale['final_error_bound'];checks+=1
        row.update({'case':'fixed_B3_coefficients_expire_after_patch','format':fmt,'stale_reused_recurrence':stale,'current_analysis':current});records.append(row)
        zero=endpoint(((0,0),),(0,),fmt);pulse=endpoint(((0,0),),(1,),fmt)
        oh=(zero,);nh=(zero,pulse,zero,zero);os=(0,0,0);ns=(1,2,3)
        analysis=sb.analyze_model('scalar_switching_v1',fmt,oh,nh,os,ns,comparison='original_reference')
        row,n=compare_reference(graph(),oh,nh,os,ns,(0,),(0,),(enc((0,),fmt),)*3,fmt,analysis);checks+=n
        assert row['observed_errors']==(0,1,0,0) and analysis['final_error_bound']<F(1,2);checks+=1
        try:sb.analyze_model('scalar_switching_v1',fmt,oh,nh,os,ns,comparison='original_reference',budget=F(1,2))
        except sb.BudgetExceeded as exc:
            assert exc.ledger['accepted'] is False and exc.ledger['first_exhausted_index']==1;checks+=1
            refusals.append({'case':'prefix_budget_exhausted_despite_small_final','format':fmt,'ledger':exc.ledger});checks+=1
        else:raise AssertionError('Prefix budget violation accepted')
        row.update({'case':'prefix_budget_not_final_only','format':fmt,'analysis':analysis});records.append(row)
        # A cap is a condition to prove, never a clipping operation.
        try:sb.analyze_model('scalar_switching_v1',fmt,(base,),(base,strong),(0,),(1,),comparison='original_reference',state_box=(F(1),))
        except (ValueError,TypeError,OverflowError) as exc:
            actual=raw_network(graph(),strong,enc((1,0),fmt),fmt)
            assert dec(actual,fmt)==(2,);checks+=1
            refusals.append({'case':'actual_domain_exit_after_patch','format':fmt,'error_type':type(exc).__name__,'actual_state_after_patch':actual})
        else:raise AssertionError('Unproved fixed cap accepted')
        # The old identity case is finite yet the generic padding proof is conservative.
        identity=endpoint(((1,0),),(0,),fmt)
        try:sb.analyze_model('scalar_switching_v1',fmt,(identity,),(identity,),(0,),(0,),state_box=(F(1),))
        except (ValueError,TypeError,OverflowError) as exc:
            assert raw_network(graph(),identity,enc((1,0),fmt),fmt)==enc((1,),fmt);checks+=1
            refusals.append({'case':'conservative_domain_refusal_no_actual_exit','format':fmt,'error_type':type(exc).__name__})
        else:raise AssertionError('Expected conservative box refusal')
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),'refusals':refusals}


def generic_bound(g,oh,nh,os,ns,fmt,state_dimension,initial_bounds,input_bounds,**kwargs):
    return sb.analyze_switching(g,oh,nh,os,ns,fmt,state_dimension=state_dimension,
                               old_initial_bounds=initial_bounds,new_initial_bounds=initial_bounds,
                               input_bounds=input_bounds,**kwargs)


def retained_numeric_cases():
    fp=get_fp();cf=load_b3('control_flow');checks=0;records=[];refusals=[]
    for fmt in ('BF16','FP32'):
        p=fp.get_format(fmt).p;one=enc((1,),fmt)[0];eta=fp.decode_word(1,fmt)
        # Switching from a rounded-thirds map to an identity preserves its tiny drift.
        zero=endpoint(((0,0,0),),(0,),fmt);thirds=endpoint(((F(2,3),F(-1,3),F(-1,3)),),(0,),fmt)
        identity=endpoint(((1,0,0),),(0,),fmt);g=graph()
        oh=(zero,identity);nh=(thirds,identity);schedule=(0,1)
        for name,value in [('basis',F(1)),('subnormal',eta)]:
            analysis=generic_bound(g,oh,nh,schedule,schedule,fmt,1,(value,),(value,value))
            initial=enc((value,),fmt);inputs=(enc((value,value),fmt),)*2
            row,n=compare_reference(g,oh,nh,schedule,schedule,initial,initial,inputs,fmt,analysis);checks+=n
            assert row['new_trace']['exact_real_states'][-1]==(0,)
            assert row['new_trace']['states'][-1]==((0,) if name=='basis' else (1,));checks+=2
            row.update({'case':'thirds_then_identity_'+name,'format':fmt,'analysis':analysis});records.append(row)
        # Two ideal proposals sum to zero; actual stored increments do not.
        big=F(1<<p);w0=((big,0),(0,0));w1=((big+1,-1),(0,0))
        e0=endpoint(w0,(0,0),fmt);e1=endpoint(w1,(0,0),fmt)
        actual1=tuple(dec(row,fmt) for row in e1['dynamics']['weights'])
        e2=endpoint(((actual1[0][0]-1,actual1[0][1]+1),(0,0)),(0,0),fmt)
        actual0=xp.matrix(tuple(dec(r,fmt) for r in e0['dynamics']['weights']))
        actual2=xp.matrix(tuple(dec(r,fmt) for r in e2['dynamics']['weights']))
        assert xp.sub(actual2,actual0)==xp.matrix(((-1,0),(0,0)));checks+=1
        oh=(e0,);nh=(e0,e1,e2);os=(0,0);ns=(1,2)
        analysis=generic_bound(g,oh,nh,os,ns,fmt,2,(F(1),F(1)),(),comparison='original_reference')
        row,n=compare_reference(g,oh,nh,os,ns,enc((1,1),fmt),enc((1,1),fmt),((),()),fmt,analysis);checks+=n
        assert row['observed_errors'][1]==1 and row['observed_errors'][2]==2*big;checks+=1
        row.update({'case':'repeated_commit_quantization_path_dependence','format':fmt,'history':nh,'analysis':analysis,
                    'ideal_increment_sum':((0,0),(0,0)),'actual_cumulative_delta':xp.sub(actual2,actual0)});records.append(row)
        # A new cancelling map can have nonzero real response but zero executed response.
        cancel=endpoint(((big,1,-big),),(0,),fmt);zero3=endpoint(((0,0,0),),(0,),fmt)
        oh=(zero3,);nh=(zero3,cancel,zero3);os=(0,0);ns=(1,2)
        analysis=generic_bound(g,oh,nh,os,ns,fmt,1,(F(1),),(F(1),F(1)),comparison='original_reference')
        row,n=compare_reference(g,oh,nh,os,ns,(one,),(one,),((one,one),)*2,fmt,analysis);checks+=n
        assert row['new_trace']['exact_real_states'][1]==(1,) and row['observed_errors']==(0,0,0);checks+=1
        row.update({'case':'zero_executed_change_after_canceling_patch','format':fmt,'analysis':analysis});records.append(row)
        # One-round fusion is a different policy; this is a mathematical reference,
        # not a native FMA backend certification.
        epsilon=F(1,1<<(p-1));a=1+epsilon;b=1-epsilon
        product_word=fp.mul_words(enc((a,),fmt)[0],enc((b,),fmt)[0],fmt,fp.Audit())
        separate=fp.add_words(enc((-1,),fmt)[0],product_word,fmt,fp.Audit())
        fused_reference=fp.round_fraction(a*b-1,fmt)
        assert separate==0 and fp.decode_word(fused_reference,fmt)==-epsilon*epsilon;checks+=1
        records.append({'case':'policy_change_separate_vs_single_round_fusion','format':fmt,'a':a,'b':b,'bias':-1,
                        'separate_output_word':separate,'one_round_reference_word':fused_reference,
                        'scope':'Exact one-round reference only; no native FMA test or authorization for modified policy'})
        # A guard certificate must be recomputed after each changing endpoint.
        safe=cf.certify_guard_margin((0,),(0,),one,enc((F(3,4),),fmt)[0],fmt,(F(0),),(F(0),),F(0))
        old_guard=cf.trace_guard((0,),one,(0,),fmt);crossed=cf.trace_guard((0,),0,(0,),fmt)
        assert old_guard['decoded_output'][0]>0 and crossed['decoded_output'][0]==0;checks+=1
        try:cf.certify_guard_margin((0,),(0,),one,0,fmt,(F(0),),(F(0),),F(0))
        except (ValueError,TypeError,OverflowError) as exc:
            refusals.append({'case':'guard_margin_expires_after_later_patch','format':fmt,'error_type':type(exc).__name__,
                             'earlier_safe_certificate':safe,'original_guard':old_guard,'later_guard':crossed});checks+=1
        else:raise AssertionError('Crossed guard margin accepted')
        maximum=fp.get_format(fmt).max_finite_word
        bad={'dynamics':{'weights':((maximum,0),),'bias':(0,)}}
        safe_zero=endpoint(((0,0),),(0,),fmt)
        try:sb.analyze_model('scalar_switching_v1',fmt,(safe_zero,),(safe_zero,bad),(0,0),(1,1),comparison='original_reference')
        except (ValueError,TypeError,OverflowError) as exc:
            # The first tick at s=1 is finite, the second repeats max*max.
            first=raw_network(g,bad,enc((1,0),fmt),fmt)
            try:raw_network(g,bad,first+(0,),fmt)
            except (fp.ExecutionError,OverflowError,ValueError):checks+=1
            else:raise AssertionError('Expected actual second-step overflow')
            refusals.append({'case':'overflow_after_large_patch','format':fmt,'error_type':type(exc).__name__,
                             'finite_first_state':first,'actual_later_overflow':True});checks+=1
        else:raise AssertionError('Uncertified overflowing history accepted')
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),'refusals':refusals,
            'scope':'New changing-endpoint probes; prior control/numerical implementation helpers only'}


def run_checks():
    start=time.perf_counter()
    sections={'complete_and_seeded':complete_and_seeded_cases(),'switching_and_budget':switching_and_budget_cases(),
              'numeric_boundaries':retained_numeric_cases()}
    representatives=[]
    for fmt in ('BF16','FP32'):
        sample=next(f for f in sections['complete_and_seeded']['families'] if f['format']==fmt)
        representatives.append({'format':fmt,'family_id':sample['family_id'],
                                'first_network_proof':sample['analysis']['steps'][0]['network_proof']})
    return compact_range_records(record({'schema':'dmwk-p2-b4-switching-tests-v1','status':'passed','seed':SEED,
                   'checks':sum(s['checks'] for s in sections.values()),'unexpected_failures':0,
                   'expected_refusals':sum(s.get('expected_refusals',0) for s in sections.values()),
                   'sections':sections,'environment':environment_metadata(),'elapsed_seconds':time.perf_counter()-start,
                   'unabridged_reference_proofs':representatives,
                   'evidence_recording':'All trajectory words and endpoints retained. Repeated nested range proofs have exact canonical digests; two full network proofs retained; all proofs reproducible from supplied code.',
                   'prior_stage_suites_rerun':False,'SMT_queries':0,'proof_assistant_checked':False,
                   'scope':'Finite mode/input-history tests and conditional analytic bounds; no live authorization or infinite-time inference from stress tests'}))


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    value=run_checks();path=Path(__file__).resolve().parent/'switching_results.json'
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k not in ('sections','environment','unabridged_reference_proofs')}))

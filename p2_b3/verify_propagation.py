"""B3 finite propagation validation, separate from general mathematical proofs."""
from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import random
import time

from b3_runtime import get_fp, load_a2, load_a4, environment_metadata
import propagation_bounds as pb

xp=load_a2('exact_projection')
SEED=20261114


def record(x):
    if isinstance(x,F):return str(x)
    if isinstance(x,xp.Matrix):return xp.serialize(x)
    if isinstance(x,dict):return {k:record(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [record(v) for v in x]
    return x


def norm(v):return max(map(abs,v),default=F(0))


def decode(v,fmt):return tuple(get_fp().decode_word(x,fmt) for x in v)


def encode(v,fmt):return tuple(get_fp().round_fraction(F(x),fmt) for x in v)


def bank(weights,bias,fmt):
    return {'weights':tuple(encode(row,fmt) for row in weights),'bias':encode(bias,fmt)}


def graph(*calls):
    return tuple({'call_id':c,'bank_id':b,'activation':a} for c,b,a in calls)


def actual_network(g,banks,h,fmt):
    """Own ordered primitive loop and separate exact real-network evaluation."""
    fp=get_fp();raw=tuple(h);exact=decode(h,fmt);calls=[];audit=fp.Audit()
    for site in g:
        b=banks[site['bank_id']];input_words=raw;actual_input=decode(raw,fmt)
        weights=tuple(decode(row,fmt) for row in b['weights']);bias=decode(b['bias'],fmt)
        exact_affine=tuple(c+sum((a*x for a,x in zip(row,exact)),F(0)) for row,c in zip(weights,bias))
        exact_at_rounded_input=tuple(c+sum((a*x for a,x in zip(row,actual_input)),F(0)) for row,c in zip(weights,bias))
        pre=[]
        for wrow,bword in zip(b['weights'],b['bias']):
            acc=bword
            for w,x in zip(wrow,raw):
                acc=fp.add_words(acc,fp.mul_words(w,x,fmt,audit),fmt,audit)
            pre.append(acc)
        if site['activation']=='relu':
            raw=tuple(x if fp.decode_word(x,fmt)>0 else 0 for x in pre)
            exact=tuple(max(F(0),x) for x in exact_affine)
            exact_local=tuple(max(F(0),x) for x in exact_at_rounded_input)
        else:
            raw=tuple(pre);exact=exact_affine;exact_local=exact_at_rounded_input
        calls.append({'call_id':site['call_id'],'bank_id':site['bank_id'],'input_words':input_words,
                      'preactivation_words':tuple(pre),'output_words':raw,'exact_local_output':exact_local,
                      'local_execution_error':tuple(a-b for a,b in zip(decode(raw,fmt),exact_local))})
    return {'output_words':raw,'exact_output':exact,'calls':calls}


def direct_product_sum(Ls,bs,E0):
    values=[F(E0)]
    for t in range(1,len(Ls)+1):
        value=F(E0)
        for L in Ls[:t]:value*=L
        for j in range(t):
            term=bs[j]
            for L in Ls[j+1:t]:term*=L
            value+=term
        values.append(value)
    return tuple(values)


def recurrence_cases():
    rng=random.Random(SEED);checks=0;records=[]
    for i in range(64):
        T=rng.randrange(0,9);Ls=tuple(F(rng.randrange(0,7),rng.randrange(1,5)) for _ in range(T))
        bs=tuple(F(rng.randrange(0,5),rng.randrange(1,8)) for _ in range(T));E0=F(rng.randrange(0,4),4)
        result=pb.propagate_recurrence(Ls,bs,initial_error=E0)
        expected=direct_product_sum(Ls,bs,E0)
        assert tuple(result['error_bounds'])==expected
        assert result['final_error_bound']==expected[-1] and result['product_sum_final']==expected[-1];checks+=2
        records.append({'case':'seeded_nonhomogeneous_'+str(i),'L':Ls,'beta':bs,'E0':E0,'result':result,'independent_product_sum':expected})
    for L in (F(0),F(1,2),F(1),F(2)):
        for E0 in (F(0),F(1,8)):
            for T in (0,1,3,8):
                beta=F(1,64);result=pb.constant_recurrence(L,beta,T,initial_error=E0)
                expected=direct_product_sum((L,)*T,(beta,)*T,E0)
                assert tuple(result['error_bounds'])==expected and result['final_error_bound']==expected[-1] and result['closed_form']==expected[-1];checks+=1
                records.append({'case':'constant_exact_scalar','L':L,'beta':beta,'T':T,'E0':E0,
                                'independent_product_sum':expected,'result':result,
                                'attainment':'Exact recurrence attained by scalar differences z_next=L*z+beta; no claim that analytic rounding envelopes are tight'})
    return {'status':'passed','checks':checks,'seeded_nonhomogeneous_cases':64,'constant_scalar_cases':32,'records':records}


def inspect_network(g,old,new,ho,hn,fmt,bound):
    a=actual_network(g,old,ho,fmt);b=actual_network(g,new,hn,fmt)
    ta=pb.trace_network(g,old,ho,fmt);tb=pb.trace_network(g,new,hn,fmt)
    assert tuple(ta['output_words'])==a['output_words'] and tuple(tb['output_words'])==b['output_words']
    assert tuple(ta['exact_output'])==a['exact_output'] and tuple(tb['exact_output'])==b['exact_output']
    errors=[norm(tuple(y-x for x,y in zip(decode(ho,fmt),decode(hn,fmt))))]
    for ac,bc in zip(a['calls'],b['calls']):
        errors.append(norm(tuple(y-x for x,y in zip(decode(ac['output_words'],fmt),decode(bc['output_words'],fmt)))))
    assert all(e<=B for e,B in zip(errors,bound['error_bounds']))
    assert all(abs(x)<=B for x,B in zip(decode(a['output_words'],fmt),bound['old_output_bounds']))
    assert all(abs(x)<=B for x,B in zip(decode(b['output_words'],fmt),bound['new_output_bounds']))
    observed=errors[-1];B=bound['final_error_bound']
    return {'format':fmt,'old_input_words':ho,'new_input_words':hn,'old_trace':a,'new_trace':b,
            'observed_layer_errors':errors,'actual_final_error':observed,'certified_final_bound':B,
            'absolute_slack':B-observed,'bound_to_observed_ratio':None if observed==0 else B/observed},5


def recurrent_cases():
    fp=get_fp();rng=random.Random(SEED);checks=0;families=[];histories=[];refusals=[]
    regimes=[('contractive_scalar_v1',F(1,2)),('neutral_scalar_v1',F(1)),('amplifying_scalar_v1',F(2))]
    alphabet=(-1,0,1);complete_T=3;seeded_T=6
    g=graph(('state_step','update','identity'))
    for fmt in ('BF16','FP32'):
        for model,L in regimes:
            old={'update':bank(((L,F(1,8)),),(0,),fmt)}
            new={'update':bank(((L,F(1,8)),),(F(1,64),),fmt)}
            for initial in (F(0),F(1,8)):
                for kind,T,seqs in [('complete',complete_T,list(product(alphabet,repeat=complete_T))),
                                    ('seeded',seeded_T,[tuple(rng.choice(alphabet) for _ in range(seeded_T)) for _ in range(8)])]:
                    analysis=pb.analyze_model(model,fmt,old,new,horizon=T,initial_error=initial,method='tube')
                    family_id=f'{fmt}:{model}:E0={initial}:{kind}'
                    actual_max=F(0)
                    for seq_index,seq in enumerate(seqs):
                        so=encode((0,),fmt);sn=encode((initial,),fmt)
                        old_states=[so];new_states=[sn];errs=[initial]
                        for u in seq:
                            uword=encode((u,),fmt)[0]
                            ao=actual_network(g,old,(so[0],uword),fmt)
                            an=actual_network(g,new,(sn[0],uword),fmt)
                            so=ao['output_words'];sn=an['output_words'];old_states.append(so);new_states.append(sn)
                            errs.append(norm(tuple(y-x for x,y in zip(decode(so,fmt),decode(sn,fmt)))))
                        assert all(e<=B for e,B in zip(errs,analysis['error_bounds']))
                        assert all(abs(decode(s,fmt)[0])<=r[0] for s,r in zip(old_states,analysis['old_state_tube']))
                        assert all(abs(decode(s,fmt)[0])<=r[0] for s,r in zip(new_states,analysis['new_state_tube']))
                        checks+=3
                        if seq_index==0:
                            input_words=tuple(encode((u,),fmt) for u in seq)
                            observed_old=pb.trace_model(model,fmt,old,initial_state_words=encode((0,),fmt),input_sequence=input_words)
                            observed_new=pb.trace_model(model,fmt,new,initial_state_words=encode((initial,),fmt),input_sequence=input_words)
                            assert tuple(tuple(s) for s in observed_old['states'])==tuple(old_states)
                            assert tuple(tuple(s) for s in observed_new['states'])==tuple(new_states);checks+=2
                        exact_expected=direct_product_sum((L,)*T,(F(1,64),)*T,initial)
                        if kind=='complete':
                            # These short dyadic cases have representable intermediates.
                            assert tuple(errs)==exact_expected;checks+=1
                        actual_max=max(actual_max,max(errs))
                        histories.append({'family_id':family_id,'inputs':seq,'old_state_words':old_states,'new_state_words':new_states,
                                          'observed_errors':errs,'exact_scalar_recurrence':exact_expected,
                                          'evidence_scope':f'All {len(seqs)} histories over stated alphabet through T={T}' if kind=='complete' else 'Eight seeded histories; no global guarantee inferred'})
                    families.append({'family_id':family_id,'model_id':model,'format':fmt,'L':L,'old_banks':old,'new_banks':new,
                                     'E0':initial,'history_kind':kind,'history_count':len(seqs),'horizon':T,'analysis':analysis,
                                     'observed_max_error':actual_max,'certified_observed_bound':analysis['observed_bound'],
                                     'absolute_slack':analysis['observed_bound']-actual_max,
                                     'bound_to_observed_ratio':None if actual_max==0 else analysis['observed_bound']/actual_max})
            if L<1:
                inv=pb.analyze_model(model,fmt,old,new,horizon=6,initial_error=F(1,8),method='invariant',state_box=(F(1),))
                assert inv['observed_bound']>=F(1,8);checks+=1
                families.append({'family_id':fmt+':contraction_invariant','format':fmt,'model_id':model,'analysis':inv,
                                 'scope':'Analytic common invariant, not inferred from the finite histories'})
        # L>1 in an upper bound alone does not imply any observed growth.
        same={'update':bank(((2,0),),(0,),fmt)}
        analysis=pb.analyze_model('amplifying_scalar_v1',fmt,same,same,horizon=4,initial_error=0)
        old_state=new_state=encode((F(1,8),),fmt)
        for _ in range(4):
            old_state=actual_network(g,same,(old_state[0],0),fmt)['output_words']
            new_state=actual_network(g,same,(new_state[0],0),fmt)['output_words']
        assert old_state==new_state;checks+=1
        families.append({'family_id':fmt+':L_gt_1_identical_endpoints','format':fmt,'analysis':analysis,
                         'actual_error':F(0),'scope':'Amplifying upper coefficient does not prove actual error growth'})
        for label,W,initial in [('conservative_identity_invariant',((1,0),),F(1)),('actual_exit_amplifying',((2,0),),F(1))]:
            banks={'update':bank(W,(0,),fmt)}
            try:pb.analyze_model('neutral_scalar_v1',fmt,banks,banks,horizon=1,initial_error=0,method='invariant',state_box=(F(1),))
            except (ValueError,TypeError,OverflowError) as exc:
                out=actual_network(g,banks,encode((initial,0),fmt),fmt)['output_words']
                actual_radius=abs(decode(out,fmt)[0])
                assert (actual_radius<=1) if label.startswith('conservative') else (actual_radius>1)
                checks+=1;refusals.append({'case':label,'format':fmt,'error_type':type(exc).__name__,
                                          'actual_initial':initial,'actual_output_words':out,'actual_output_radius':actual_radius,
                                          'actual_domain_exit':actual_radius>1})
            else:raise AssertionError('Expected invariant refusal: '+label)
    return {'status':'passed','checks':checks,'complete_horizon':complete_T,'complete_alphabet':alphabet,
            'complete_histories_per_family':27,'complete_families':12,'seeded_horizon':seeded_T,'seeded_histories_per_family':8,
            'seeded_families':12,'families':families,'histories':histories,'expected_refusals':len(refusals),'refusals':refusals}


def multilayer_cases():
    checks=0;records=[];families=[]
    for fmt in ('BF16','FP32'):
        cases=[]
        g=graph(('first_call','first','relu'),('second_call','second','identity'))
        old={'first':bank(((1,F(1,2)),(-1,F(1,2))),(F(-1,4),F(1,4)),fmt),
             'second':bank(((F(1,2),F(1,4)),(F(-1,4),F(1,2))),(0,0),fmt)}
        new={'first':bank(((1,F(3,4)),(-1,F(1,2))),(F(-1,4),F(1,4)),fmt),
             'second':bank(((F(1,2),F(3,8)),(F(-1,4),F(1,2))),(0,0),fmt)}
        cases.append(('two_layer_relu',g,old,new))
        shared=graph(('shared_first','shared','relu'),('shared_second','shared','identity'))
        so={'shared':bank(((F(1,2),F(1,4)),(F(-1,4),F(1,2))),(0,0),fmt)}
        sn={'shared':bank(((F(1,2),F(3,8)),(F(-1,4),F(1,2))),(0,0),fmt)}
        cases.append(('shared_two_calls',shared,so,sn))
        for name,g,old,new in cases:
            B=pb.network_bound(g,old,new,(F(1),F(1)),(F(1),F(1)),fmt)
            maxima=[]
            for h in product((-1,0,1),repeat=2):
                hw=encode(h,fmt);r,n=inspect_network(g,old,new,hw,hw,fmt,B);checks+=n
                r['case']=name;records.append(r);maxima.append(r['actual_final_error'])
            assert len(B['calls'])==2 and {c['call_id'] for c in B['calls']}=={c['call_id'] for c in g};checks+=1
            if name=='shared_two_calls':
                assert len(old)==1 and B['calls'][0]['bank_id']==B['calls'][1]['bank_id'];checks+=1
            families.append({'case':name,'format':fmt,'graph':g,'old_banks':old,'new_banks':new,'analysis':B,
                             'finite_domain_size':9,'observed_domain_max':max(maxima),
                             'absolute_slack':B['final_error_bound']-max(maxima),
                             'bound_to_observed_ratio':None if max(maxima)==0 else B['final_error_bound']/max(maxima)})
    return {'status':'passed','checks':checks,'families':families,'point_records':records,'complete_inputs_per_case':9}


def retained_boundaries():
    fp=get_fp();checks=0;records=[];refusals=[]
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.round_fraction(F(x),fmt)
        one=enc(1);p=fp.get_format(fmt).p
        I3=tuple(tuple(one if i==j else 0 for j in range(3)) for i in range(3))
        Q=tuple(tuple(enc(F(2,3) if i==j else F(-1,3)) for j in range(3)) for i in range(3))
        g=graph(('thirds','first','relu'),('downstream','second','identity'))
        old={'first':{'weights':((0,0,0),)*3,'bias':(0,0,0)},'second':{'weights':I3,'bias':(0,0,0)}}
        new={'first':{'weights':Q,'bias':(0,0,0)},'second':old['second']}
        B=pb.network_bound(g,old,new,(F(1),)*3,(F(1),)*3,fmt)
        for name,h in [('basis',(one,)*3),('subnormal',(1,)*3)]:
            r,n=inspect_network(g,old,new,h,h,fmt,B);checks+=n
            assert r['old_trace']['exact_output']==r['new_trace']['exact_output']==(F(0),)*3
            assert r['new_trace']['output_words']==((0,)*3 if name=='basis' else (1,)*3);checks+=2
            r.update({'case':'thirds_multilayer_'+name,'analysis':B});records.append(r)
        g=graph(('stored_endpoint','first','relu'),('half_downstream','second','identity'))
        old={'first':bank(((1<<p,0),),(0,),fmt),'second':bank(((F(1,2),),),(0,),fmt)}
        new={'first':bank(((F(1<<p)+1,-1),),(0,),fmt),'second':old['second']}
        B=pb.network_bound(g,old,new,(F(1),F(1)),(F(1),F(1)),fmt)
        r,n=inspect_network(g,old,new,(one,one),(one,one),fmt,B);checks+=n
        assert r['actual_final_error']==F(1,2);checks+=1
        r.update({'case':'quantized_endpoint_downstream','ideal_first_increment':(1,-1),'actual_first_increment':(0,-1),'analysis':B});records.append(r)
        shared=graph(('shared_site_a','shared','relu'),('shared_site_b','shared','identity'))
        I=((one,0),(0,one));tiny=((one,1),(0,one));ranktwo=((one,1),(1,one))
        for name,W,domain in [('full_rank_BIT_nonALG',tiny,((0,0),(one,0),(one,one))),
                              ('BIT_rank_exceeds_complement',ranktwo,((0,0),(one,one)))]:
            old={'shared':{'weights':I,'bias':(0,0)}};new={'shared':{'weights':W,'bias':(0,0)}}
            delta=xp.matrix(tuple(tuple(fp.decode_word(W[i][j],fmt)-fp.decode_word(I[i][j],fmt) for j in range(2)) for i in range(2)))
            H=xp.matrix(tuple(tuple(fp.decode_word(h[j],fmt) for h in domain) for j in range(2)))
            protected_rank=xp.rank(H);delta_rank=xp.rank(delta)
            assert protected_rank==(2 if name=='full_rank_BIT_nonALG' else 1)
            assert delta_rank==(1 if name=='full_rank_BIT_nonALG' else 2)
            assert xp.matmul(delta,H)!=xp.zeros(2,len(domain));checks+=3
            B=pb.network_bound(shared,old,new,(F(1),F(1)),(F(1),F(1)),fmt)
            for h in domain:
                r,n=inspect_network(shared,old,new,h,h,fmt,B);checks+=n
                assert r['actual_final_error']==0 and all(e==0 for e in r['observed_layer_errors']);checks+=1
                r.update({'case':name+'_shared_depth_two','analysis':B,'effective_delta':delta,
                          'effective_delta_rank':delta_rank,'global_protected_span_rank':protected_rank,
                          'all_protected_call_outputs_equal':True});records.append(r)
        maxword=fp.get_format(fmt).max_finite_word;half=enc(F(1,2))
        g=graph(('saturated','first','identity'),('readout','second','identity'))
        banks={'first':{'weights':((maxword,maxword),),'bias':(0,)},'second':bank(((1,),),(0,),fmt)}
        trace=actual_network(g,banks,(half,half),fmt)
        assert trace['output_words']==(maxword,);checks+=1
        try:pb.network_bound(g,banks,banks,(F(1,2),F(1,2)),(F(1,2),F(1,2)),fmt)
        except (ValueError,TypeError,OverflowError) as exc:
            refusals.append({'format':fmt,'case':'saturated_finite_trace_conservative_box_refusal','error_type':type(exc).__name__,
                             'actual_trace':trace,'actual_overflow':False,
                             'first_layer_algebraic_annihilator_dimension':1,'first_layer_full_format_ALG_endpoint_count':1,
                             'capacity_scope':'Extremal finite-coordinate proof; not whole-format enumeration or BIT-only singleton claim'});checks+=1
        else:raise AssertionError('Expected conservative saturation envelope refusal')
    ca=load_a4('capacity_algebra');H=xp.matrix(((1,),(0,)));X=xp.eye(2)
    good,good_info=ca.solve_response(H,X,xp.matrix(((0,2),)))
    bad,bad_info=ca.solve_response(H,X,xp.matrix(((1,2),)))
    assert good is not None and bad is None;checks+=1
    records.append({'case':'target_relation_with_fixed_identity_downstream','H':H,'targets':X,'feasible':good_info,'impossible':bad_info,
                    'scope':'Protected first-layer response cannot be changed at e1; a fixed identity downstream cannot restore requested incompatible response'})
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),'refusals':refusals,
            'scope':'New two-call B3 probes; no previous verification suite rerun'}


def run_checks():
    started=time.perf_counter()
    sections={'recurrences':recurrence_cases(),'recurrent_execution':recurrent_cases(),
              'multilayer':multilayer_cases(),'retained_boundaries':retained_boundaries()}
    return record({'schema':'dmwk-p2-b3-propagation-tests-v1','status':'passed','seed':SEED,
                   'checks':sum(x['checks'] for x in sections.values()),'unexpected_failures':0,
                   'expected_refusals':sum(x.get('expected_refusals',0) for x in sections.values()),'sections':sections,
                   'environment':environment_metadata(),'elapsed_seconds':time.perf_counter()-started,
                   'prior_stage_suites_rerun':False,'SMT_queries':0,'proof_assistant_checked':False,
                   'scope':'Exact finite recurrence checks, complete small histories, seeded histories and fixed-graph probes; general proofs separate'})


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks();out=Path(__file__).resolve().parent/'propagation_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sections','environment')}))

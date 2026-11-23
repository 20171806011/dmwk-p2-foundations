"""Finite exact and fixed-execution B2 bound checks; prior suites are not run."""
from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json
import random
import time

from b2_runtime import get_fp, load_a2, load_a3, load_a4, environment_metadata
import certified_bounds as cb

xp=load_a2('exact_projection')
SEED=20261114


def record(value):
    if isinstance(value,F): return str(value)
    if isinstance(value,xp.Matrix): return xp.serialize(value)
    if isinstance(value,dict): return {k:record(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)): return [record(v) for v in value]
    return value


def vector(values):
    return xp.matrix(tuple((F(v),) for v in values),ncols=1)


def column(a):
    return tuple(row[0] for row in a.rows)


def squared(values):
    return sum((v*v for v in values),F(0))


def words(values,fmt):
    fp=get_fp()
    return tuple(tuple(fp.round_fraction(F(v),fmt) for v in row) for row in values)


def exact_affine(bank,h,fmt,bias=None):
    """Direct rational sum; does not call the producer's trace/bound routines."""
    fp=get_fp();hs=tuple(fp.decode_word(v,fmt) for v in h)
    bias=(0,)*len(bank) if bias is None else bias
    return tuple(fp.decode_word(b,fmt)+sum((fp.decode_word(w,fmt)*x for w,x in zip(row,hs)),F(0))
                 for row,b in zip(bank,bias))


def actual_affine(bank,h,fmt,bias=None):
    """Independent invocation of fixed ordered primitive execution."""
    fp=get_fp();bias=(0,)*len(bank) if bias is None else bias
    audit=fp.Audit();out=[]
    for row,b in zip(bank,bias):
        acc=b
        for w,x in zip(row,h):
            term=fp.mul_words(w,x,fmt,audit)
            acc=fp.add_words(acc,term,fmt,audit)
        out.append(acc)
    return tuple(out)


def geometry_cases():
    rng=random.Random(SEED);checks=0;records=[];refusals=[]
    # Norm intervals use integer arithmetic, including nonsquares and zero.
    norm_cases=[F(0),F(1),F(9,25),F(2),F(1,10**80)]
    norm_cases += [F(rng.randrange(0,1000),rng.randrange(1,1000)) for _ in range(64)]
    for q in norm_cases:
        lo,hi=cb.sqrt_bounds(q,bits=80)
        assert 0<=lo<=hi and lo*lo<=q<=hi*hi
        # The implementation normalizes the root exponent before allocating
        # fractional bits; this is relative-scale, not a fixed absolute grid.
        assert (hi-lo)*(1<<80)<=lo;checks+=2
    Qaxis=xp.matrix(((1,),(0,)))
    Qrot=xp.matrix(((F(3,5),),(F(4,5),)))
    Qfull=xp.matrix(((F(3,5),F(-4,5)),(F(4,5),F(3,5))))
    fixtures=[('protected_term_tight',xp.matrix(((3,0),)),Qaxis,(F(1),F(0))),
              ('residual_term_tight',xp.matrix(((0,5),)),Qaxis,(F(0),F(1))),
              ('coupled_norm_slack',xp.matrix(((3,4),)),Qaxis,(F(1),F(1))),
              ('zero_input',xp.matrix(((3,4),)),Qaxis,(F(0),F(0))),
              ('zero_protected_rank',xp.matrix(((0,5),)),xp.zeros(2,0),(F(0),F(1))),
              ('full_protected_rank',xp.matrix(((3,4),)),Qfull,(F(1),F(0))),
              ('zero_update',xp.zeros(2,2),Qrot,(F(2),F(-1)))]
    for i in range(64):
        n=rng.randrange(1,4);Q=(Qaxis,Qrot,Qfull,xp.zeros(2,0))[i%4]
        D=xp.matrix(tuple(tuple(F(rng.randrange(-5,6),rng.randrange(1,5)) for _ in range(2)) for _ in range(n)))
        h=tuple(F(rng.randrange(-5,6),rng.randrange(1,5)) for _ in range(2))
        fixtures.append(('seeded_'+str(i),D,Q,h))
    for name,D,Q,h in fixtures:
        # Different generating columns describe the same protected space.
        H=xp.scale(Q,2);hv=vector(h)
        result=cb.geometry_bound(D,H,h,U=Q,basis_route='orthonormal')
        actual=column(xp.matmul(D,hv));normsq=squared(actual)
        Pi=xp.project_onto_columns(Q);projected=xp.matmul(Pi,hv)
        residual=xp.sub(hv,projected)
        assert tuple(result['actual_change'])==actual
        assert result['bound']>=0 and normsq<=result['bound']**2
        assert result['actual_norm_lower']**2<=normsq<=result['actual_norm_upper']**2
        assert xp.matmul(xp.transpose(Q),residual)==xp.zeros(Q.ncols,1)
        epsilon=cb.spectral_upper(xp.matmul(D,Q));M=cb.spectral_upper(D)
        aa=cb.norm2_bounds(column(projected))[1];ee=cb.norm2_bounds(column(residual))[1]
        basic=epsilon*aa+M*ee
        assert normsq<=basic**2
        checks+=5
        if name in ('protected_term_tight','residual_term_tight'):
            assert basic**2==normsq;checks+=1
        if name=='coupled_norm_slack':
            assert actual==(7,) and basic==8;checks+=1
        records.append({'case':name,'delta':D,'Q':Q,'H':H,'input':h,'actual_norm_squared':normsq,
                        'basic_bound':basic,'result':result})
    D=xp.matrix(((1,0),));H=Qaxis;h=(F(1),F(0))
    for name,U in [('half_scale',xp.scale(Qaxis,F(1,2))),('right_angle_wrong_space',xp.matrix(((0,),(1,)))),
                   ('rational_rotation',Qrot)]:
        result=cb.geometry_bound(D,H,h,U=U,basis_route='approximate')
        assert result['bound']>=1 and result['gram_error_upper']<1;checks+=1
        if name=='right_angle_wrong_space':
            assert xp.matmul(D,U)==xp.zeros(1,1) and result['projector_deviation_upper']>=1;checks+=1
        records.append({'case':name,'delta':D,'H':H,'U':U,'input':h,'result':result})
    for name,U,route in [('double_scale',xp.scale(Qaxis,2),'approximate'),
                         ('zero_column',xp.zeros(2,1),'approximate'),
                         ('false_orthonormal_label',xp.scale(Qaxis,2),'orthonormal'),
                         ('wrong_true_space',xp.matrix(((0,),(1,))),'orthonormal')]:
        try:cb.geometry_bound(D,H,h,U=U,basis_route=route)
        except (ValueError,TypeError,OverflowError) as exc:
            refusals.append({'case':name,'error_type':type(exc).__name__});checks+=1
        else:raise AssertionError('Invalid basis accepted: '+name)
    return {'status':'passed','checks':checks,'sqrt_interval_cases':len(norm_cases),
            'seeded_geometry_cases':64,'named_geometry_cases':7,'approximate_basis_cases':3,
            'records':records,'expected_refusals':len(refusals),'refusals':refusals,
            'scope':'Exact squared-rational comparisons; finite examples complement general proofs'}


def ledger_cases():
    fp=get_fp();checks=0;records=[]
    P=xp.matrix(((0,0),(0,1)));Pt=xp.matrix(((F(1,4),0),(0,F(3,4))))
    G=xp.matrix(((1,2),));Gh=xp.matrix(((2,3),));Dh=xp.matrix(((F(5,8),F(19,8)),))
    C=xp.matmul(G,P);repr_stage=xp.matmul(G,Pt);opt_stage=xp.matmul(Gh,Pt)
    for fmt in ('BF16','FP32'):
        p=fp.get_format(fmt).p;old=words(((1<<p,0),),fmt)
        new=words(((F(1<<p)+F(5,8),F(19,8)),),fmt)
        delta=xp.sub(cb.decode_matrix(new,fmt),cb.decode_matrix(old,fmt))
        chain=[('ideal',C),('represented',repr_stage),('optimizer',opt_stage),('generated',Dh),('stored',delta)]
        result=cb.error_ledger(chain,h=(F(1),F(0)))
        errors=[xp.sub(chain[i][1],chain[i-1][1]) for i in range(1,len(chain))]
        assert all(xp.frobenius_squared(e)>0 for e in errors)
        total=C
        for e in errors:total=xp.add(total,e)
        assert total==delta==xp.matrix(((0,F(19,8)),))
        assert result['net_increment']==delta and result['bound']>0
        direct=cb.geometry_bound(delta,xp.matrix(((1,),(0,))),(F(1),F(0)))
        assert direct['bound']==0 and column(xp.matmul(delta,vector((1,0))))==(0,)
        checks+=4
        records.append({'format':fmt,'old_words':old,'new_words':new,'G_star':G,'P':P,'P_tilde':Pt,'G_hat':Gh,
                        'D_hat':Dh,'chain':chain,'signed_terms':errors,'ledger':result,'direct_endpoint':direct,
                        'accounting':'Alternatives only: direct endpoint plus ledger is not used as a disjoint budget'})
    return {'status':'passed','checks':checks,'records':records}


def inspect_point(old,new,h,fmt,old_bias=None,new_bias=None):
    fp=get_fp();effective_new_bias=old_bias if new_bias is None else new_bias
    result=cb.point_bound(old,new,h,fmt,old_bias=old_bias,new_bias=new_bias)
    exact_old=exact_affine(old,h,fmt,old_bias);exact_new=exact_affine(new,h,fmt,effective_new_bias)
    raw_old=actual_affine(old,h,fmt,old_bias);raw_new=actual_affine(new,h,fmt,effective_new_bias)
    decoded_old=tuple(fp.decode_word(v,fmt) for v in raw_old)
    decoded_new=tuple(fp.decode_word(v,fmt) for v in raw_new)
    exact_delta=tuple(b-a for a,b in zip(exact_old,exact_new))
    actual_delta=tuple(b-a for a,b in zip(decoded_old,decoded_new))
    assert tuple(result['exact_change'])==exact_delta and tuple(result['actual_change'])==actual_delta
    assert tuple(result['old_trace']['output_words'])==raw_old and tuple(result['new_trace']['output_words'])==raw_new
    assert tuple(result['old_trace']['exact_output'])==exact_old and tuple(result['new_trace']['exact_output'])==exact_new
    for trace,decoded,exact in [(result['old_trace'],decoded_old,exact_old),(result['new_trace'],decoded_new,exact_new)]:
        errors=tuple(a-b for a,b in zip(decoded,exact))
        assert tuple(trace['row_signed_errors'])==errors
        assert all(abs(e)<=b for e,b in zip(errors,trace['row_error_bounds']))
    assert all(abs(v)<=b for v,b in zip(actual_delta,result['coordinate_bounds']))
    normsq=squared(actual_delta)
    assert normsq<=result['l2_bound']**2 and max(map(abs,actual_delta),default=F(0))<=result['linf_bound']
    assert result['actual_norm_lower']**2<=normsq<=result['actual_norm_upper']**2
    actual_inf=max(map(abs,actual_delta),default=F(0));bound=result['linf_bound']
    return {'format':fmt,'old_words':old,'new_words':new,'input_words':h,'old_bias':old_bias,'new_bias':new_bias,
            'exact_old':exact_old,'exact_new':exact_new,'actual_old_words':raw_old,'actual_new_words':raw_new,
            'actual_linf':actual_inf,'bound_linf':bound,'absolute_slack':bound-actual_inf,
            'bound_to_observed_ratio':None if actual_inf==0 else bound/actual_inf,'point_bound':result},10


def finite_execution_cases():
    fp=get_fp();rng=random.Random(SEED);checks=0;records=[];boxes=[];refusals=[]
    alphabet=(F(-1),F(0),F(1));domain=list(product(alphabet,repeat=2))
    endpoint_pairs=[]
    for i in range(12):
        old=tuple(tuple(F(rng.randrange(-4,5),2) for _ in range(2)) for _ in range(2))
        new=tuple(tuple(F(rng.randrange(-4,5),2) for _ in range(2)) for _ in range(2))
        endpoint_pairs.append((old,new))
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.round_fraction(F(x),fmt)
        for i,(old_values,new_values) in enumerate(endpoint_pairs):
            old=words(old_values,fmt);new=words(new_values,fmt)
            box=cb.box_bound(old,new,(F(1),F(1)),fmt)
            observed=[]
            for hvalues in domain:
                h=tuple(enc(v) for v in hvalues)
                result,n=inspect_point(old,new,h,fmt);checks+=n
                assert squared(result['point_bound']['actual_change'])<=box['l2_bound']**2
                assert all(abs(v)<=b for v,b in zip(result['point_bound']['actual_change'],box['coordinate_bounds']))
                checks+=2;result.update({'case':'complete_ternary_domain','pair_index':i})
                records.append(result);observed.append(result['actual_linf'])
            maximum_observed=max(observed)
            boxes.append({'format':fmt,'pair_index':i,'old_words':old,'new_words':new,
                          'input_value_domain':domain,'finite_domain_size':len(domain),'box_bound':box,
                          'observed_domain_max_linf':maximum_observed,
                          'absolute_slack':box['linf_bound']-maximum_observed,
                          'bound_to_observed_ratio':None if maximum_observed==0 else box['linf_bound']/maximum_observed,
                          'scope':'Point comparisons exhaust exactly 9 stated inputs; analytic box theorem covers all admitted raw inputs with |h_j|<=1'})
        # Nonzero fixed and changed biases are part of the same fixed bias-first graph.
        old=words(((1,F(-1,2)),),fmt);new=words(((F(3,2),-1),),fmt)
        ob=(enc(F(1,4)),);nb=(enc(F(-1,4)),);h=(enc(1),enc(F(1,2)))
        result,n=inspect_point(old,new,h,fmt,ob,nb);checks+=n;result['case']='explicit_bias_difference';records.append(result)
        box=cb.box_bound(old,new,(F(1),F(1)),fmt,old_bias=ob,new_bias=nb)
        assert result['actual_linf']<=box['linf_bound'];checks+=1
        boxes.append({'format':fmt,'case':'explicit_bias_difference','box_bound':box,'observed_domain_max_linf':result['actual_linf']})
    return {'status':'passed','checks':checks,'seeded_endpoint_pairs':12,'complete_input_domain_size':9,
            'point_records':records,'box_records':boxes,'expected_refusals':len(refusals),'refusals':refusals,
            'scope':'BF16 software and audited local FP32; exact rational affine references independent of bound producer'}


def counterexample_cases():
    fp=get_fp();ca=load_a4('capacity_algebra');checks=0;records=[];refusals=[]
    def expect_refusal(name,fmt,fn):
        nonlocal checks
        try:fn()
        except (ValueError,TypeError,OverflowError,fp.ExecutionError) as exc:
            refusals.append({'case':name,'format':fmt,'error_type':type(exc).__name__});checks+=1
        else:raise AssertionError('Expected refusal: '+name)
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.round_fraction(F(x),fmt)
        one=enc(1);eta=fp.decode_word(1,fmt);p=fp.get_format(fmt).p
        # Relative-only |fl(z)-z|<=u|z| fails on a subnormal half-way product.
        old=((0,),);new=((enc(F(1,2)),),);h=(1,)
        r,n=inspect_point(old,new,h,fmt);checks+=n
        exact=eta/2;u=F(1,1<<p)
        assert r['actual_new_words']==(0,) and exact>u*exact;checks+=1
        r.update({'case':'subnormal_relative_only_failure','exact_product':exact,'observed_product_error':exact,
                  'relative_only_bound':u*exact,'mixed_underflow_term':eta/2});records.append(r)
        # An exact cancellation output has no nonzero relative denominator.
        old=words(((1,-1),),fmt);new=words(((1,F(-1,2)),),fmt);h=(one,one)
        r,n=inspect_point(old,new,h,fmt);checks+=n
        assert r['point_bound']['relative_bound'] is None and r['actual_linf']==F(1,2);checks+=1
        r['case']='zero_reference_output';records.append(r)
        # Multiplication is exact here; ordered reduction loses the middle one.
        bank=words(((1<<p,1,-(1<<p)),),fmt)
        r,n=inspect_point(((0,0,0),),bank,(one,)*3,fmt);checks+=n
        assert r['exact_new']==(1,) and r['actual_new_words']==(0,);checks+=1
        r['case']='ordered_cancellation_rounding';records.append(r)
        Q=tuple(tuple(enc(F(2,3) if i==j else F(-1,3)) for j in range(3)) for i in range(3))
        for label,h in [('basis',(one,)*3),('tiny',(1,)*3)]:
            r,n=inspect_point(((0,0,0),)*3,Q,h,fmt);checks+=n
            assert r['point_bound']['exact_change']==(F(0),)*3;checks+=1
            assert r['actual_new_words']==((0,)*3 if label=='basis' else (1,)*3);checks+=1
            r['case']='thirds_'+label;records.append(r)
        old=words(((1<<p,0),),fmt);new=words(((F(1<<p)+1,-1),),fmt)
        r,n=inspect_point(old,new,(one,one),fmt);checks+=n
        assert r['point_bound']['exact_change']==(F(-1),) and r['actual_linf']==1;checks+=1
        r.update({'case':'commit_rounding','ideal_increment':(1,-1),'actual_increment':(0,-1)});records.append(r)
        I=((one,0),(0,one));tiny=((one,1),(0,one));ranktwo=((one,1),(1,one))
        for label,new,activation_set,rank in [('full_rank_BIT_nonALG',tiny,((0,0),(one,one),(one,0)),1),
                                           ('BIT_rank_exceeds_complement',ranktwo,((0,0),(one,one)),2)]:
            for h in activation_set:
                r,n=inspect_point(I,new,h,fmt);checks+=n
                assert r['actual_linf']==0;checks+=1
                r.update({'case':label,'effective_rank':rank});records.append(r)
        maxword=fp.get_format(fmt).max_finite_word
        saturated=((maxword,maxword),);half=enc(F(1,2))
        r,n=inspect_point(saturated,saturated,(half,half),fmt);checks+=n
        assert r['actual_new_words']==(maxword,) and r['actual_linf']==0;checks+=1
        r.update({'case':'saturated_storage','algebraic_dimension':1,'full_format_ALG_endpoints':1,
                  'scope':'Extremal row-sum proof plus one probe; not format-wide enumeration'});records.append(r)
        expect_refusal('actual_overflow',fmt,lambda:cb.point_bound(((0,),),((maxword,),),(enc(2),),fmt))
        expect_refusal('box_overflow_uncertified',fmt,lambda:cb.box_bound(((0,),),((maxword,),),(F(2),),fmt))
        sign=fp.get_format(fmt).sign_mask
        exponent_all=((1<<8)-1)<<(p-1)
        for label,bad in [('negative_zero',sign),('infinity',exponent_all),('NaN',exponent_all|1)]:
            expect_refusal(label+'_weight',fmt,lambda bad=bad:cb.point_bound(((0,),),((bad,),),(one,),fmt))
            expect_refusal(label+'_input',fmt,lambda bad=bad:cb.point_bound(((0,),),((one,),),(bad,),fmt))
            expect_refusal(label+'_bias',fmt,lambda bad=bad:cb.point_bound(((0,),),((one,),),(one,),fmt,old_bias=(bad,)))
    H=xp.matrix(((1,),(0,)));X=xp.eye(2)
    feasible,good=ca.solve_response(H,X,xp.matrix(((0,2),)))
    impossible,bad=ca.solve_response(H,X,xp.matrix(((1,2),)))
    assert feasible is not None and impossible is None;checks+=1
    records.append({'case':'target_relation_incompatibility','H':H,'X':X,'feasible':good,'impossible':bad})
    # A mixed bound remains meaningful when the reference lower bound is zero.
    mixed=cb.mixed_budget(F(1,2),F(0),F(1,2),F(10))
    insufficient=cb.mixed_budget(F(1,2),F(0),F(1,4),F(10))
    assert mixed['accepted'] is True and mixed['certified_threshold']==F(1,2)
    assert insufficient['accepted'] is False and insufficient['certified_threshold']==F(1,4);checks+=2
    records.append({'case':'mixed_zero_reference','result':mixed,'insufficient_absolute_budget':insufficient})
    return {'status':'passed','checks':checks,'records':records,'expected_refusals':len(refusals),'refusals':refusals,
            'scope':'Concrete fixed-graph probes and exact counterexamples, not a universal backend certification'}


def run_checks():
    started=time.perf_counter()
    sections={'geometry':geometry_cases(),'ledger':ledger_cases(),'finite_execution':finite_execution_cases(),
              'counterexamples':counterexample_cases()}
    return record({'schema':'dmwk-p2-b2-bounds-v1','status':'passed','seed':SEED,
                   'checks':sum(v['checks'] for v in sections.values()),'unexpected_failures':0,
                   'expected_refusals':sum(v.get('expected_refusals',0) for v in sections.values()),
                   'sections':sections,'environment':environment_metadata(),'elapsed_seconds':time.perf_counter()-started,
                   'prior_stage_suites_rerun':False,'SMT_queries':0,'proof_assistant_checked':False,
                   'claims':'Finite checks and counterexamples; universal theorems separately stated; numerical bounds authorize no live commit'})


if __name__=='__main__':
    if not __debug__:raise SystemExit('Verification requires assertions; do not use -O/-OO')
    result=run_checks();out=Path(__file__).resolve().parent/'bound_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('sections','environment')}))

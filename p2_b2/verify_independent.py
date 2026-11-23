"""Independent finite B2 algebra, rounding, envelope and receipt review.

No earlier test suite or producer assertion module is imported. The reference
uses exact matrix equations and an independent positive-word RNE search.
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

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
SEED=20261114


def require(condition,message):
    if not condition:raise AssertionError(message)


def det(a):
    if not a:return Q(1)
    if len(a)==1:return a[0][0]
    return sum(((-1)**j*a[0][j]*det(tuple(tuple(row[k] for k in range(len(a)) if k!=j)
                                         for row in a[1:])) for j in range(len(a))),Q(0))


def transpose(a,width=None):
    width=len(a[0]) if a else (0 if width is None else width)
    return tuple(tuple(row[j] for row in a) for j in range(width))


def row_basis(rows,width=None):
    width=len(rows[0]) if rows else (0 if width is None else width)
    selected=[]
    for row in rows:
        if len(selected)==width:break
        trial=selected+[tuple(Q(v) for v in row)];k=len(trial)
        if any(det(tuple(tuple(r[j] for j in cols) for r in trial))
               for cols in combinations(range(width),k)):selected=trial
    return tuple(selected)


def rank(a,width=None):return len(row_basis(a,width))


def mul(a,b,out_width=None):
    width=len(b[0]) if b else (0 if out_width is None else out_width)
    return tuple(tuple(sum((row[k]*b[k][j] for k in range(len(b))),Q(0))
                       for j in range(width)) for row in a)


def matvec(a,x):return tuple(sum((v*w for v,w in zip(row,x)),Q(0)) for row in a)


def sub(a,b):return tuple(tuple(x-y for x,y in zip(ra,rb)) for ra,rb in zip(a,b))


def normsq(x):return sum((v*v for v in x),Q(0))


def inverse(a):
    n=len(a);denominator=det(a)
    require(denominator!=0,'Independent inverse got singular input')
    return tuple(tuple(((-1)**(i+j))*det(tuple(tuple(a[r][c] for c in range(n) if c!=i)
                                              for r in range(n) if r!=j))/denominator
                       for j in range(n)) for i in range(n))


def projector(h):
    d=len(h);columns=row_basis(transpose(h),d)
    if not columns:return ((Q(0),)*d,)*d
    basis=transpose(columns)
    return mul(mul(basis,inverse(mul(columns,basis))),columns)


def spectral_majorant_square(a,ncols=None):
    if not a:return Q(0)
    width=len(a[0]) if ncols is None else ncols
    frob=sum((v*v for row in a for v in row),Q(0))
    one=max((sum((abs(row[j]) for row in a),Q(0)) for j in range(width)),default=Q(0))
    infinity=max((sum(map(abs,row),Q(0)) for row in a),default=Q(0))
    return min(frob,one*infinity)


def precision(fmt):return {'BF16':8,'FP32':24}[fmt]


@lru_cache(maxsize=None)
def word_value(raw,fmt):
    p=precision(fmt);f=p-1
    require(type(raw) is int and 0<=raw<(1<<(p+8)),'Independent word domain')
    require(raw!=(1<<(p+7)),'Negative zero is not a canonical stored word')
    sign=-1 if raw>>(p+7) else 1
    exp=(raw>>f)&255;mant=raw&((1<<f)-1)
    require(exp!=255,'Nonfinite input word')
    if exp:mant+=1<<f;power=exp-127-f
    else:power=1-127-f
    return sign*Q(mant)*(Q(2)**power)


def constants(fmt):
    p=precision(fmt);f=p-1
    maximum=(254<<f)|((1<<f)-1)
    return Q(1,1<<p),word_value(1,fmt),word_value(maximum,fmt),maximum


@lru_cache(maxsize=None)
def round_word(value,fmt):
    value=Q(value)
    if not value:return 0
    p=precision(fmt);sign=1<<(p+7) if value<0 else 0;value=abs(value)
    _,_,maximum,high=constants(fmt)
    gap=maximum-word_value(high-1,fmt)
    if value>=maximum+gap/2:raise OverflowError('Rounded nonfinite result')
    if value>=maximum:return sign|high
    low=0
    while low+1<high:
        middle=(low+high)//2
        if word_value(middle,fmt)<=value:low=middle
        else:high=middle
    dl,dh=value-word_value(low,fmt),word_value(high,fmt)-value
    chosen=low if dl<dh or (dl==dh and low%2==0) else high
    return sign|chosen if chosen else 0


def reference_trace(weights,h,fmt,bias=None):
    bias=(0,)*len(weights) if bias is None else bias
    decoded_h=tuple(word_value(v,fmt) for v in h)
    output=[];exact=[];row_signed=[];row_absolute=[];row_events=[]
    for row,b in zip(weights,bias):
        acc=b;events=[]
        ideal=word_value(b,fmt)+sum((word_value(w,fmt)*x for w,x in zip(row,decoded_h)),Q(0))
        for j,(w,x) in enumerate(zip(row,decoded_h)):
            product_arg=word_value(w,fmt)*x
            rounded_product=round_word(product_arg,fmt)
            pe=word_value(rounded_product,fmt)-product_arg
            addition_arg=word_value(acc,fmt)+word_value(rounded_product,fmt)
            rounded_add=round_word(addition_arg,fmt)
            ae=word_value(rounded_add,fmt)-addition_arg
            events.extend((('multiply',j,product_arg,rounded_product,pe),
                           ('add',j,addition_arg,rounded_add,ae)))
            acc=rounded_add
        signed=sum((e[4] for e in events),Q(0));absolute=sum((abs(e[4]) for e in events),Q(0))
        require(word_value(acc,fmt)-ideal==signed,'Reference telescope failure')
        output.append(acc);exact.append(ideal);row_signed.append(signed);row_absolute.append(absolute);row_events.append(events)
    return {'output_words':tuple(output),'decoded_output':tuple(word_value(v,fmt) for v in output),
            'exact_output':tuple(exact),'signed':tuple(row_signed),'absolute':tuple(row_absolute),'events':row_events}


def reference_box_endpoint(weights,envelope,fmt,bias):
    u,eta,maximum,_=constants(fmt)
    errors=[];row_ranges=[]
    for row,b in zip(weights,bias):
        acc=abs(word_value(b,fmt));error=Q(0);events=[]
        for j,(w,hmax) in enumerate(zip(row,envelope)):
            x=abs(word_value(w,fmt))*hmax
            if x>maximum:raise OverflowError('Cannot certify product range')
            pe=u*x+eta/2;p=min(maximum,x+pe)
            z=acc+p
            if z>maximum:raise OverflowError('Cannot certify addition range')
            ae=u*z+eta/2;acc=min(maximum,z+ae)
            error+=pe+ae;events.append((j,x,pe,p,z,ae,acc))
        errors.append(error);row_ranges.append(events)
    return tuple(errors),row_ranges


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def check_interval(q,lower,upper,bits):
    require(0<=lower<=upper and lower*lower<=q<=upper*upper,'Invalid exact square-root enclosure')
    if lower!=upper:
        require(lower>0 and upper-lower<=lower/Q(1<<bits),'Root interval lost normalized relative scale')


def check_psd(matrix):
    n=len(matrix)
    return all(det(tuple(tuple(matrix[i][j] for j in indices) for i in indices))>=0
               for k in range(1,n+1) for indices in combinations(range(n),k))


def check_operator_upper(a,bound,width=None):
    width=len(a[0]) if a else (0 if width is None else width)
    ata=mul(transpose(a,width),a,out_width=width)
    residual=tuple(tuple((bound*bound if i==j else Q(0))-ata[i][j]
                         for j in range(width)) for i in range(width))
    require(bound>=0 and check_psd(residual),'Norm certificate fails independent principal-minor PSD criterion')


def check_norm_geometry():
    import certified_bounds as cb
    rng=random.Random(SEED);roots=operators=geometries=0
    values=(Q(0),Q(1),Q(2),Q(1,3),Q(9,16),Q(1,1<<500),Q(3,1<<500),Q(7)*(1<<300))
    for bits in (1,8,32,80):
        for q in values:
            lo,hi=cb.sqrt_bounds(q,bits);check_interval(q,lo,hi,bits);roots+=1
    for n,d in product(range(1,4),repeat=2):
        for _ in range(8):
            a=tuple(tuple(Q(rng.randrange(-4,5),rng.randrange(1,5)) for _ in range(d)) for _ in range(n))
            upper=cb.spectral_upper(cb.Matrix(a,d));check_operator_upper(a,upper)
            require(upper*upper>=spectral_majorant_square(a),'Reported majorant does not enclose its named norm inequality')
            operators+=1
    hspace=((Q(1),),(Q(0),));hm=cb.Matrix(hspace,1);unit=hm
    for a,b in product((-1,0,1),repeat=2):
        delta=((Q(a),Q(b)),);dm=cb.Matrix(delta,2)
        for x,y in product((-2,-1,0,1,2),repeat=2):
            h=(Q(x),Q(y))
            for route in ('projector','orthonormal'):
                r=cb.geometry_bound(dm,hm,h,U=None if route=='projector' else unit,basis_route=route)
                require(r['protected_component']==(h[0],0) and r['residual']==(0,h[1]),
                        'Orthogonal split does not match independent exact coordinates')
                require(r['actual_change']==matvec(delta,h),'Geometric exact response differs')
                require(r['bound']==r['protected_action_norm_upper']*r['protected_component_norm_upper']+
                        r['delta_norm_upper']*r['residual_norm_upper'],'Split bound uses wrong component')
                require(normsq(r['actual_change'])<=r['bound']**2 and
                        normsq(r['actual_change'])<=r['uniform_bound']**2,'Geometric point norm exceeds a reported bound')
                check_operator_upper(delta,r['delta_norm_upper']);geometries+=1
    approximate=[]
    for u in (((Q(3,4),),(Q(0),)),((Q(0),),(Q(1),)),((Q(3,5),),(Q(4,5),))):
        um=cb.Matrix(u,1);delta=((Q(1),Q(0)),);dm=cb.Matrix(delta,2)
        r=cb.geometry_bound(dm,hm,(Q(1),Q(1)),um,'approximate')
        pu=projector(u);pv=projector(hspace)
        require(r['approximate_projector'].rows==pu and r['protected_projector'].rows==pv,
                'Approximate/true projector differs from independent adjugate construction')
        require(r['gram_error_upper']<1 and
                r['inverse_condition_upper']**2*(1-r['gram_error_upper'])>=1,
                'Approximate conditioning inequality not certified')
        check_operator_upper(sub(pv,pu),r['projector_deviation_upper'])
        require(normsq(r['actual_change'])<=r['bound']**2,'Approximate-basis geometry misses actual response')
        approximate.append({'basis':[[str(v) for v in row] for row in u],
                            'gram_error_upper':str(r['gram_error_upper']),
                            'gap_upper':str(r['projector_deviation_upper']),
                            'bound':str(r['bound'])})
    refusals=0
    for u,route in ((((Q(0),),(Q(1),)),'orthonormal'),(((Q(2),),(Q(0),)),'orthonormal'),
                    (((Q(2),),(Q(0),)),'approximate')):
        try:cb.geometry_bound(cb.Matrix(((Q(1),Q(0)),),2),hm,(Q(1),Q(0)),cb.Matrix(u,1),route)
        except cb.BoundRefused:refusals+=1
        else:raise AssertionError('Unsupported basis condition accepted')
    random_cases=0
    for _ in range(48):
        h=tuple(tuple(Q(rng.randrange(-2,3)) for _ in range(2)) for _ in range(3))
        delta=tuple(tuple(Q(rng.randrange(-3,4),rng.randrange(1,4)) for _ in range(3)) for _ in range(2))
        x=tuple(Q(rng.randrange(-2,3),rng.randrange(1,4)) for _ in range(3))
        r=cb.geometry_bound(cb.Matrix(delta,3),cb.Matrix(h,2),x)
        pv=projector(h);v=matvec(pv,x);e=tuple(a-b for a,b in zip(x,v))
        require(r['protected_projector'].rows==pv and r['protected_component']==v and r['residual']==e,
                'Seeded geometry does not match independent rational projector')
        require(sum((a*b for a,b in zip(v,e)),Q(0))==0,'Projection components not orthogonal')
        check_operator_upper(delta,r['delta_norm_upper'])
        check_operator_upper(mul(delta,pv),r['protected_action_norm_upper'])
        require(normsq(matvec(delta,x))<=r['bound']**2,'Seeded split bound invalid')
        random_cases+=1
    degenerate=0
    for space in (cb.Matrix(((),()),0),cb.Matrix(((Q(1),Q(0)),(Q(0),Q(1))),2)):
        for x in ((Q(0),Q(0)),(Q(1),Q(-1))):
            for route in ('projector','orthonormal'):
                delta=((Q(1),Q(2)),(Q(3),Q(4)))
                r=cb.geometry_bound(cb.Matrix(delta,2),space,x,None if route=='projector' else space,route)
                expected=projector(space.rows)
                require(r['protected_projector'].rows==expected and normsq(matvec(delta,x))<=r['bound']**2,
                        'Zero/full-space geometry interpretation failed')
                degenerate+=1
    # Joint sharpness fixture: ||Delta||=5, restricted norm=3, h=(1,1).
    # The coupled class optimum is 3+4=7; simpler split is 3+5=8.
    require(normsq((Q(3),Q(4)))==25 and matvec(((Q(3),Q(4)),),(Q(1),Q(1)))==(Q(7),),
            'Sharp joint rank-one fixture failed')
    return {'sqrt_intervals':roots,'spectral_PSD_certificates':operators,'two_dimensional_geometry_cases':geometries,
            'approximate_basis_cases':approximate,'basis_refusals':refusals,'seeded_three_dimensional_cases':random_cases,
            'zero_full_space_cases':degenerate,
            'seed':SEED,'sharp_joint_example':{'exact_response':7,'split_bound':8,'uniform_bound_squared':50},
            'method':'Exact interval containment, all principal minors, adjugate projector and direct products'}


def inspect_trace(actual,reference,fmt):
    u,eta,maximum,_=constants(fmt)
    require(actual['output_words']==reference['output_words'] and
            actual['decoded_output']==reference['decoded_output'] and actual['exact_output']==reference['exact_output'],
            'Actual trace outputs differ from independent word execution')
    require(actual['row_signed_errors']==reference['signed'] and actual['row_error_bounds']==reference['absolute'],
            'Trace error decomposition differs')
    require(len(actual['rows'])==len(reference['events']),'Trace row omitted')
    for produced,expected in zip(actual['rows'],reference['events']):
        require(len(produced['events'])==len(expected),'Trace operation omitted')
        for event,(operation,column,argument,word,error) in zip(produced['events'],expected):
            require(event['operation']==operation and event['column']==column and
                    event['exact_argument']==argument and event['output_word']==word and
                    event['signed_error']==error and event['absolute_error']==abs(error),
                    'Local operation/residual differs from independent trace')
            valid=abs(argument)<=maximum
            require(event['mixed_range_proved']==valid and event['mixed_bound']==(u*abs(argument)+eta/2 if valid else None),
                    'Mixed local range/bound annotation differs')
            if valid:require(abs(error)<=u*abs(argument)+eta/2,'Independent mixed rounding inequality failed')
    require(actual['rho_l2']**2>=normsq(reference['absolute']) and
            actual['rho_linf']==max(reference['absolute'],default=Q(0)),'Trace error norm is invalid')


def inspect_point(old,new,h,fmt,old_bias=None,new_bias=None):
    import certified_bounds as cb
    old_bias=(0,)*len(old) if old_bias is None else old_bias
    new_bias=old_bias if new_bias is None else new_bias
    before=reference_trace(old,h,fmt,old_bias);after=reference_trace(new,h,fmt,new_bias)
    r=cb.point_bound(old,new,h,fmt,old_bias,new_bias)
    inspect_trace(r['old_trace'],before,fmt);inspect_trace(r['new_trace'],after,fmt)
    exact=tuple(a-b for a,b in zip(after['exact_output'],before['exact_output']))
    actual=tuple(a-b for a,b in zip(after['decoded_output'],before['decoded_output']))
    coordinate=tuple(abs(v)+ro+rn for v,ro,rn in zip(exact,before['absolute'],after['absolute']))
    require(r['exact_change']==exact and r['actual_change']==actual and r['coordinate_bounds']==coordinate,
            'Two-sided point decomposition differs')
    require(r['exact_change_norm_upper']**2>=normsq(exact),'Exact-change norm upper bound is invalid')
    require(r['linf_bound']==max(coordinate) and r['l2_bound']==r['exact_change_norm_upper']+
            r['old_trace']['rho_l2']+r['new_trace']['rho_l2'],'Point bound omits/double-counts a trace error')
    require(all(abs(v)<=bound for v,bound in zip(actual,coordinate)) and normsq(actual)<=r['l2_bound']**2,
            'Independent executed difference exceeds point certificate')
    lower=max(map(abs,before['decoded_output']))
    require(r['reference_output_norm_lower']==lower and
            r['relative_bound']==(r['l2_bound']/lower if lower>0 else None),'Relative denominator policy differs')
    return r


def inspect_box(old,new,envelope,fmt,old_bias=None,new_bias=None):
    import certified_bounds as cb
    old_bias=(0,)*len(old) if old_bias is None else old_bias
    new_bias=old_bias if new_bias is None else new_bias
    old_error,old_ranges=reference_box_endpoint(old,envelope,fmt,old_bias)
    new_error,new_ranges=reference_box_endpoint(new,envelope,fmt,new_bias)
    r=cb.box_bound(old,new,envelope,fmt,old_bias,new_bias)
    for proof,errors,ranges in ((r['old_range_proof'],old_error,old_ranges),(r['new_range_proof'],new_error,new_ranges)):
        require(proof['row_error_bounds']==errors,'Box omits endpoint error contribution')
        for row,events in zip(proof['rows'],ranges):
            require(len(row['steps'])==len(events),'Box omitted an operation range')
            for step,(j,x,pe,p,z,ae,acc) in zip(row['steps'],events):
                require((step['column'],step['product_argument_bound'],step['product_error_bound'],
                         step['rounded_product_bound'],step['addition_argument_bound'],step['addition_error_bound'],
                         step['new_accumulator_bound'])==(j,x,pe,p,z,ae,acc),'Box range induction differs')
    algebraic=tuple(abs(word_value(nb,fmt)-word_value(ob,fmt))+
                    sum((abs(word_value(nv,fmt)-word_value(ov,fmt))*hmax
                         for ov,nv,hmax in zip(orow,nrow,envelope)),Q(0))
                    for orow,nrow,ob,nb in zip(old,new,old_bias,new_bias))
    coordinates=tuple(a+b+c for a,b,c in zip(algebraic,old_error,new_error))
    require(r['algebraic_coordinate_bounds']==algebraic and r['coordinate_bounds']==coordinates and
            r['linf_bound']==max(coordinates),'Box total bound differs from independent recurrence')
    require(r['l2_bound']>=0 and r['global_domain_inclusion_verified'] is False and
            r['authorizes_live_commit'] is False,'Box helper claims unsupported global authority')
    for proof,errors in ((r['old_range_proof'],old_error),(r['new_range_proof'],new_error)):
        require(proof['rho_l2']>=0 and proof['rho_l2']**2>=normsq(errors),'Box endpoint L2 error bound invalid')
    algebraic_upper=r['l2_bound']-r['old_range_proof']['rho_l2']-r['new_range_proof']['rho_l2']
    require(algebraic_upper>=0 and algebraic_upper**2>=normsq(algebraic),'Box algebraic L2 component invalid')
    return r


def check_points_boxes():
    import certified_bounds as cb
    rng=random.Random(SEED+1);points=seeded=boxes=box_inputs=0;boundaries=[];refusals=[]
    for fmt in ('BF16','FP32'):
        one=round_word(Q(1),fmt);u,eta,maximum,maxword=constants(fmt)
        coefficients=tuple(round_word(x,fmt) for x in (Q(-1),Q(1,2),Q(1)))
        inputs=tuple(round_word(x,fmt) for x in (-eta,eta,Q(1)))
        rows=tuple(product(coefficients,repeat=2))
        for old_row,new_row,h in product(rows,rows,tuple(product(inputs,repeat=2))):
            inspect_point((old_row,),(new_row,),h,fmt);points+=1
        pool=tuple(round_word(v,fmt) for v in (Q(-2),Q(-1),Q(-1,3),-eta,Q(0),eta,Q(1,2),Q(1),Q(2)))
        for index in range(64):
            old=tuple(tuple(rng.choice(pool) for _ in range(3)) for _ in range(2))
            new=tuple(tuple(rng.choice(pool) for _ in range(3)) for _ in range(2))
            h=tuple(rng.choice(pool) for _ in range(3))
            ob=tuple(round_word(Q(rng.randrange(-1,2)),fmt) for _ in range(2))
            nb=tuple(round_word(Q(rng.randrange(-1,2)),fmt) for _ in range(2))
            inspect_point(old,new,h,fmt,ob,nb);seeded+=1
        small=tuple(round_word(v,fmt) for v in (Q(-1),Q(0),Q(1,2),Q(1)))
        domain=tuple(product(small,repeat=2));envelope=(Q(1),Q(1))
        for index in range(12):
            old=tuple(tuple(rng.choice(small) for _ in range(2)) for _ in range(2))
            new=tuple(tuple(rng.choice(small) for _ in range(2)) for _ in range(2))
            ob=(0,one);nb=(one,0)
            box=inspect_box(old,new,envelope,fmt,ob,nb);boxes+=1
            for h in domain:
                before=reference_trace(old,h,fmt,ob);after=reference_trace(new,h,fmt,nb)
                change=tuple(a-b for a,b in zip(after['decoded_output'],before['decoded_output']))
                require(max(map(abs,change))<=box['linf_bound'] and normsq(change)<=box['l2_bound']**2,
                        'Complete small box member exceeds certificate')
                box_inputs+=1
        half=round_word(Q(1,2),fmt)
        under=inspect_point(((0,),),((1,),),(half,),fmt)
        event=under['new_trace']['rows'][0]['events'][0]
        require(event['absolute_error']==eta/2 and event['absolute_error']>u*abs(event['exact_argument']),
                'Relative-only underflow counterexample missing')
        gap=inspect_point(((0,),),((1,),),(one,),fmt)
        equal=inspect_point(((0,),),((0,),),(one,),fmt)
        require(gap['linf_bound']==eta and gap['actual_change']==(eta,) and
                gap['old_trace']['output_words']!=gap['new_trace']['output_words'],
                'Non-strict eta bound falsely implies equality')
        require(equal['linf_bound']==0<eta and equal['old_trace']['output_words']==equal['new_trace']['output_words'],
                'Strict canonical zero witness differs')
        s=word_value(round_word(Q(1,3),fmt),fmt)
        two=inspect_point(((round_word(s,fmt),),),((round_word(2*s,fmt),),),(1,),fmt)
        exact=abs(two['exact_change'][0]);old_error=two['old_trace']['row_error_bounds'][0];new_error=two['new_trace']['row_error_bounds'][0]
        require(two['actual_change']==(eta,) and exact+old_error<eta and exact+new_error<eta and
                two['linf_bound']==eta,'Two independently rounded executions do not demonstrate both needed errors')
        zero_ref=inspect_point(((one,round_word(Q(-1),fmt)),),((one,0),),(one,one),fmt)
        require(zero_ref['relative_bound'] is None and zero_ref['actual_change']==(Q(1),),
                'Cancellation reference improperly supports finite relative-only division')
        empty=inspect_point(((),),((),),(),fmt,(one,),(0,))
        require(empty['old_trace']['row_error_bounds']==(Q(0),) and empty['linf_bound']==1,
                'Zero-column bias-only graph acquired arithmetic error')
        # The displayed half-maximum input executes finitely; the generic
        # absolute-range box certificate can still be inconclusive.
        saturated=((maxword,maxword),)
        inspect_point(saturated,saturated,(half,half),fmt)
        cases=(('negative_zero',lambda:cb.point_bound(((1<<(precision(fmt)+7),),),((0,),),(one,),fmt)),
               ('actual_overflow',lambda:cb.point_bound(((0,0),),saturated,(one,one),fmt)),
               ('conservative_range_refusal',lambda:cb.box_bound(saturated,saturated,(Q(1,2),Q(1,2)),fmt)))
        for label,action in cases:
            try:action()
            except cb.BoundRefused:refusals.append({'format':fmt,'case':label})
            else:raise AssertionError('Expected numeric-policy/range refusal absent: '+label)
        boundaries.append({'format':fmt,'eta':str(eta),'relative_only_underflow_fails':True,
                           'non_strict_eta_bound_equal_but_words_differ':True,'strict_zero_bound_words_equal':True,
                           'both_old_and_new_rounding_errors_necessary':True,
                           'two_sided_exact_change':str(exact),'old_error':str(old_error),'new_error':str(new_error),
                           'zero_reference_relative_bound':None,'bias_only_error':'0',
                           'finite_probe_with_conservative_box_refusal':True})
    mixed=0
    for bound,reference,absolute,relative in product((Q(0),Q(1,2),Q(1)),repeat=4):
        r=cb.mixed_budget(bound,reference,absolute,relative)
        require(r['accepted']==(bound<=absolute+relative*reference),'Mixed budget uses wrong lower-reference condition')
        mixed+=1
    return {'exhaustive_point_pairs':points,'seeded_affine_point_pairs':seeded,'seed':SEED+1,
            'analytic_box_certificates':boxes,'exhausted_named_box_inputs':box_inputs,
            'mixed_budget_cases':mixed,'boundaries':boundaries,'expected_refusals':refusals,
            'scope':'Complete specified small sets and seeded pairs; box universality comes from the separate range-induction proof'}


def check_ledger():
    import certified_bounds as cb
    base=((Q(1),Q(-1)),(Q(0),Q(0)))
    differences=(((Q(0),Q(1,8)),(Q(1,4),Q(0))),
                 ((Q(1,4),Q(0)),(Q(0),Q(-1,8))),
                 ((Q(-1,8),Q(1,4)),(Q(1,8),Q(0))),
                 ((Q(1,16),Q(0)),(Q(0),Q(1,16))))
    stages=[base]
    for error in differences:
        stages.append(tuple(tuple(a+b for a,b in zip(ra,rb)) for ra,rb in zip(stages[-1],error)))
    names=('ideal','represented','optimizer','generated','stored_effective')
    chain=tuple((name,cb.Matrix(a,2)) for name,a in zip(names,stages))
    counts=0
    for h in (None,(Q(1),Q(1)),(Q(-1),Q(2))):
        r=cb.error_ledger(chain,h)
        require(r['net_increment'].rows==stages[-1] and r['baseline_increment'].rows==base,
                'Ledger changed the baseline or net endpoint')
        require(len(r['stages'])==4 and all(s['error'].rows==e for s,e in zip(r['stages'],differences)),
                'Ledger omitted/overlapped a telescoping difference')
        require(r['bound']==r['baseline_bound']+sum((s['bound'] for s in r['stages']),Q(0)) and
                r['accounting']=='telescoping_alternative_to_direct_endpoint','Ledger adds a direct bound to its own errors')
        if h is None:check_operator_upper(stages[-1],r['bound'])
        else:
            require(normsq(matvec(stages[-1],h))<=r['bound']**2,'Point ledger underbounds endpoint response')
            require(all(s['point_error']==matvec(e,h) for s,e in zip(r['stages'],differences)),
                    'Ledger point application differs')
        counts+=1
    try:cb.error_ledger((chain[0],chain[0]))
    except cb.BoundRefused:pass
    else:raise AssertionError('Duplicated stage label accepted')
    return {'all_four_errors_nonzero':True,'distinct_ledger_modes':counts,
            'duplicate_label_refused':True,'method':'Independent successive exact differences; direct products/principal minors',
            'scope':'Accounting only; no invented ideal optimizer provenance'}


def declared_calls(model,fmt):
    one=round_word(Q(1),fmt)
    return {
        'duplicate_feedback_v1':(('state',(0,0)),('state',(one,one)),('input',(0,0)),('input',(one,one))),
        'split_feedback_v1':(('state',(0,0)),('state',(one,one)),('input',(0,0)),('input',(one,0))),
        'thirds_two_inputs_v1':(('all_declared_inputs',(one,one,one)),('all_declared_inputs',(1,1,1))),
        'commit_rounding_v1':(('unit_pair',(one,one)),),
        'shared_axis_v1':(('axis_0',(one,0)),('axis_1',(0,one))),
    }[model]


def fraction_record(value):return Q(*value)


def analyze_calls(old,new,model,fmt):
    import bounded_certificate as bc
    calls=declared_calls(model,fmt)
    descriptor=bc.ck.model_descriptor(model,fmt)
    actual_calls=tuple((site['id'],tuple(h)) for site in descriptor['sites'] for h in site['activations'])
    require(calls==actual_calls,'Trusted registry differs from explicitly reviewed complete-site set')
    points=tuple(inspect_point(old,new,h,fmt) for _,h in calls)
    envelope=tuple(max(abs(word_value(h[j],fmt)) for _,h in calls) for j in range(len(old[0])))
    box=inspect_box(old,new,envelope,fmt)
    actual_sq=max(normsq(point['actual_change']) for point in points)
    actual_inf=max(max(map(abs,point['actual_change'])) for point in points)
    return calls,points,envelope,box,actual_sq,actual_inf


def check_receipts():
    import certified_bounds as cb
    import bounded_certificate as bc
    from b2_runtime import load_b1
    records=[];refusals=[];case_count=0;context_count=0
    models=('duplicate_feedback_v1','split_feedback_v1','thirds_two_inputs_v1','commit_rounding_v1','shared_axis_v1')

    def rejected(label,action):
        try:action()
        except ValueError:refusals.append(label)
        else:raise AssertionError('Expected evidence refusal absent: '+label)

    for fmt in ('BF16','FP32'):
        one=round_word(Q(1),fmt)
        for model in models:
            old=bc.ck.initial_weights(model,fmt)
            new=list(map(list,old));new[0][-1]=round_word(word_value(new[0][-1],fmt)+Q(1,4),fmt)
            new=tuple(map(tuple,new))
            calls,points,envelope,box,actual_sq,actual_inf=analyze_calls(old,new,model,fmt)
            context_count+=len(calls)
            for method,norm in product(('complete_point_trace','analytic_box'),('l2','linf')):
                expected=max(p[norm+'_bound'] for p in points) if method=='complete_point_trace' else box[norm+'_bound']
                proof=bc.analyze_registered_domain(model,fmt,old,new,method,norm)
                require(fraction_record(proof['bound'])==expected,'Registered bound differs from checked point/box bounds')
                if method=='complete_point_trace':
                    require(proof['call_case_count']==len(calls) and
                            fraction_record(proof['finite_actual_l2_supremum_squared'])==actual_sq and
                            fraction_record(proof['finite_actual_linf_supremum'])==actual_inf,
                            'Registered domain maximum omits inputs or misstates actual difference')
                    require(tuple((r['site'],tuple(r['activation_words'])) for r in proof['call_cases'])==calls,
                            'Registered receipt changes site coverage')
                else:
                    require(tuple(fraction_record(v) for v in proof['input_coordinate_absolute_bounds'])==envelope and
                            proof['included_registered_call_count']==len(calls),'Box envelope fails complete-call inclusion')
                text=bc.make_budget_certificate(model,fmt,old,new,expected,method,norm,version=3)
                receipt=bc.check_budget_certificate(text,model,fmt,old,new,expected,method,norm,version=3)
                payload=json.loads(text)['payload']
                require(receipt['authorizes_commit'] is False and receipt['claims_BIT'] is False and
                        receipt['claims_program_noninterference'] is False and
                        payload['candidate_state_invariant_verified'] is False,
                        'Numerical receipt improperly grants stronger authority')
                records.append({'format':fmt,'model':model,'method':method,'norm':norm,
                                'bound':str(expected),'actual_supremum_l2_squared':str(actual_sq),
                                'actual_supremum_linf':str(actual_inf),'authorizes_commit':False})
                case_count+=1
        model='duplicate_feedback_v1';old=bc.ck.initial_weights(model,fmt)
        new=((old[0][0],round_word(Q(1,4),fmt)),old[1])
        calls,points,envelope,box,_,_=analyze_calls(old,new,model,fmt)
        budget=max(p['l2_bound'] for p in points)
        text=bc.make_budget_certificate(model,fmt,old,new,budget,version=7)

        def altered(change,source=text):
            packet=json.loads(source);change(packet['payload'])
            packet['payload_sha256']=hashlib.sha256(canonical(packet['payload']).encode()).hexdigest()
            return canonical(packet)

        mutations={
            'omitted_shared_site':lambda p:p['source_descriptor']['sites'].pop(),
            'sample_only':lambda p:p['source_descriptor'].__setitem__('coverage','observed_samples'),
            'omitted_activation':lambda p:p['source_descriptor']['sites'][0]['activations'].pop(),
            'FMA_graph':lambda p:p['source_descriptor']['graph'].__setitem__('arithmetic','FMA'),
            'changed_policy':lambda p:p['source_descriptor'].__setitem__('numerical_policy','unregistered'),
            'changed_schedule':lambda p:p['source_descriptor'].__setitem__('schedule','concurrent'),
            'omitted_output':lambda p:p['observation']['ports'].pop(),
            'false_BIT':lambda p:p.__setitem__('claims_BIT',True),
            'false_live_authority':lambda p:p.__setitem__('authorizes_commit',True),
            'false_candidate_invariant':lambda p:p.__setitem__('candidate_state_invariant_verified',True),
            'lowered_proof_bound':lambda p:p['proof'].__setitem__('bound',[0,1]),
            'changed_old_endpoint':lambda p:p['old_words'][0].__setitem__(0,0),
        }
        for label,change in mutations.items():
            rejected(fmt+':'+label,lambda change=change:bc.check_budget_certificate(
                altered(change),model,fmt,old,new,budget,version=7))
        rejected(fmt+':under_budget',lambda:bc.make_budget_certificate(model,fmt,old,new,budget/2))
        rejected(fmt+':external_version',lambda:bc.check_budget_certificate(text,model,fmt,old,new,budget,version=8))
        rejected(fmt+':sample_registry',lambda:bc.make_budget_certificate('sample_domain',fmt,old,new,budget))
        boxtext=bc.make_budget_certificate(model,fmt,old,new,box['l2_bound'],'analytic_box')
        badbox=altered(lambda p:p['proof']['input_coordinate_absolute_bounds'].__setitem__(0,[0,1]),boxtext)
        rejected(fmt+':shrunk_box',lambda:bc.check_budget_certificate(badbox,model,fmt,old,new,box['l2_bound'],'analytic_box'))
        # New B2 integration fixture, not a replay of the B1 optimizer suite.
        # beta=0, epsilon=3: first moment and second moment become 1 exactly;
        # first parameter step is -1/4, projected to (-1/8,+1/8).
        ok=load_b1('optimizer_kernel');cu=load_b1('constrained_updates')
        cfg=cu.OptimizerConfig('adamw',Q(1),beta1=Q(0),beta2=Q(0),epsilon=Q(3))
        kernel=ok.OptimizerKernel(model,fmt,cfg,claim='ALG_AND_BIT')
        request=ok.optimizer_request(cu.Matrix(((Q(1),Q(0)),(Q(0),Q(0))),2),'projected')
        kernel.commit(kernel.prepare(request));kernel.tick(one)
        snapshot=kernel.snapshot()
        require(tuple(map(tuple,snapshot['weights']))==((round_word(Q(7,8),fmt),round_word(Q(1,8),fmt)),(0,one)) and
                snapshot['optimizer_state']['m']['rows'][0][0]==[1,1] and
                snapshot['optimizer_state']['v']['rows'][0][0]==[1,1],
                'Independent B1 integration fixture does not have expected nonzero moments/endpoint')
        liveold=kernel.weights;livenew=((liveold[0][0],round_word(Q(3,8),fmt)),liveold[1])
        _,livepoints,_,_,_,_=analyze_calls(liveold,livenew,model,fmt)
        livebudget=max(p['l2_bound'] for p in livepoints)
        evidence=bc.make_budget_certificate(model,fmt,liveold,livenew,livebudget,
                                            version=kernel.version,snapshot_context=snapshot)
        receipt=bc.check_budget_certificate(evidence,model,fmt,liveold,livenew,livebudget,
                                           version=kernel.version,snapshot_context=snapshot)
        require(receipt['authorizes_commit'] is False,'Budget receipt grants a live commit')
        rejected(fmt+':B1_rejects_numeric_receipt',lambda:kernel.commit(evidence))
        require(kernel.snapshot()==snapshot,'Numeric receipt changed B1 weights/state/moments')
        partial=dict(snapshot);partial.pop('schedule')
        rejected(fmt+':missing_snapshot_schedule',lambda:bc.make_budget_certificate(
            model,fmt,liveold,livenew,livebudget,version=kernel.version,snapshot_context=partial))
        kernel.tick(one);later=kernel.snapshot()
        rejected(fmt+':later_snapshot_context',lambda:bc.check_budget_certificate(
            evidence,model,fmt,liveold,livenew,livebudget,version=kernel.version,snapshot_context=later))
        require(kernel.snapshot()==later,'Read-only context rejection changed newer protected state')
    return {'registered_receipts':records,'receipt_count':case_count,'distinct_complete_call_checks':context_count,
            'expected_refusals':refusals,'full_nonzero_moment_B1_rollback_fixtures':2,
            'scope':'Read-only fixed-domain evidence, not candidate feedback closure or publication authority'}


def check_frozen_B1():
    import bounded_certificate as bc
    path=ROOT.parent/'p2_b1'/'training_results.json';original=path.read_bytes()
    frozen=json.loads(original);records=[]
    for run in frozen['runs']:
        for step in run['records']:
            if step['status']!='refused':continue
            old=tuple(map(tuple,step['old_weights']));new=tuple(map(tuple,step['candidate_weights']))
            fmt=run['format'];model=run['model']
            calls,points,envelope,box,squared,inf=analyze_calls(old,new,model,fmt)
            require(squared==0 and inf==0 and any(v for p in points for v in p['exact_change']),
                    'Frozen refused endpoint changed its BIT/ALG classification')
            bound=max(p['l2_bound'] for p in points)
            proof=bc.analyze_registered_domain(model,fmt,old,new)
            require(fraction_record(proof['bound'])==bound and bound>0 and box['l2_bound']>bound,
                    'Frozen endpoint point/box comparison differs')
            require(step['proposed_ALG_annihilation'] is False and
                    step['proposed_complete_D']['all_protected_observations_equal'] is True,
                    'Frozen B1 original classification unexpectedly differs')
            records.append({'format':fmt,'optimizer':run['optimizer'],'attempt':step['attempt'],
                            'point_l2_bound':str(bound),'box_l2_bound':str(box['l2_bound']),
                            'actual_l2_difference_squared':'0','exact_ALG_residual_nonzero':True,
                            'registered_call_count':len(calls),'optimizer_rerun':False})
    require(len(records)==21 and path.read_bytes()==original,'Frozen B1 evidence count/content changed')
    adam=next(r for r in frozen['runs'] if r['format']=='FP32' and r['optimizer']=='adamw' and
              r['route']=='final_update_projected_certified')
    require(adam['accepted_commits']==0 and adam['refused_attempts']==8 and adam['final_loss']=='5/2',
            'Frozen FP32 Adam joint-refusal fact changed')
    return {'source_sha256':hashlib.sha256(original).hexdigest(),'endpoint_pairs':records,'pair_count':len(records),
            'registered_call_checks':sum(r['registered_call_count'] for r in records),
            'original_FP32_Adam_joint_fact':{'accepted':0,'refused':8,'final_loss':'5/2'},
            'scope':'New single-layer bounds on saved endpoints only; no old optimization suite or trajectory rerun'}


def run_checks():
    started=time.perf_counter()
    names=('verify_independent.py','certified_bounds.py','bounded_certificate.py','b2_runtime.py')
    before={name:digest(ROOT/name) for name in names}
    result={'schema':'dmwk-p2-b2-independent-review-v1','status':'running',
            'started_utc':datetime.now(timezone.utc).isoformat(),'seed':SEED,
            'norm_geometry':check_norm_geometry(),'point_box':check_points_boxes(),
            'ledger':check_ledger(),'receipts':check_receipts(),'frozen_B1':check_frozen_B1()}
    require({name:digest(ROOT/name) for name in names}==before,'Reviewed source changed during independent run')
    from b2_runtime import environment_metadata
    result.update(status='passed',elapsed_seconds=time.perf_counter()-started,source_sha256=before,
                  environment=environment_metadata(),SMT_queries=0,proof_assistant_checked=False,
                  prior_stage_suites_rerun=False,
                  scope='Independent finite exact, word-rounding, range and read-only receipt checks; general results remain handwritten proofs')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'independent_results.json')
    args=parser.parse_args()
    if not __debug__:raise SystemExit('Run without Python -O/-OO')
    result=run_checks()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'seconds':result['elapsed_seconds'],'output':str(args.output)}))


if __name__=='__main__':main()

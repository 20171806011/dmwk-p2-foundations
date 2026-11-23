"""A4 exact rank/response finite verification, separate from general proofs."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json
import random
import time

import capacity_algebra as ca

xp = ca.xp
SEED = 20261114


def _stack(a,b):
    if a.ncols != b.ncols:
        raise ValueError("Stack width mismatch")
    return xp.matrix(a.rows+b.rows,ncols=a.ncols)


def _zero(a):
    return all(x == 0 for row in a.rows for x in row)


def _unpack(value):
    return xp.matrix(tuple(tuple(Fraction(x) for x in row) for row in value['rows']),
                     ncols=value['shape'][1])


def _flatten_columns(matrices, rows, cols):
    return xp.matrix(tuple(tuple(a.rows[i][j] for a in matrices)
                           for i in range(rows) for j in range(cols)), ncols=len(matrices))


def run_checks():
    started=time.perf_counter()
    checks=0
    def check(value,message):
        nonlocal checks
        if not value:raise AssertionError(message)
        checks+=1
    def validate_response(h,x,r,cap):
        delta,report=ca.solve_response(h,x,r,cap)
        a=ca.concatenate(h,x)
        required=xp.matrix(tuple((Fraction(0),)*h.ncols+row for row in r.rows),ncols=a.ncols)
        feasible=xp.rank(_stack(a,required))==xp.rank(a)
        expected=feasible and (cap is None or xp.rank(r)<=cap)
        check((delta is not None)==expected,"Row-space response feasibility disagrees")
        check(report['unconstrained_response_feasible']==feasible,"Reported feasibility differs")
        check(report['authorizes_bitwise_commit'] is False,"Algebra report gave live authority")
        if delta is not None:
            check(_zero(xp.matmul(delta,h)),"Constructed response changes protected space")
            check(xp.matmul(delta,x)==r,"Constructed response misses target")
            check(xp.rank(delta)==xp.rank(r),"Constructed response is not minimum rank")
            if cap is not None:check(xp.rank(delta)<=cap,"Rank cap exceeded")
        elif not feasible:
            witness=report['impossibility_witness'];alpha=_unpack(witness['alpha'])
            xa=xp.matmul(x,alpha);ra=xp.matmul(r,alpha)
            check(xp.rank(ca.concatenate(h,xa))==xp.rank(h),"Witness X alpha is not protected")
            check(not _zero(ra),"Witness R alpha is zero")
            check(xa==_unpack(witness['X_alpha']) and ra==_unpack(witness['R_alpha']),
                  "Serialized relation witness differs")
        else:
            check(report['status']=='infeasible_rank_budget',"Wrong rank-budget refusal label")
            check(report['minimum_required_update_rank']==xp.rank(r),"Wrong necessary rank")
        return delta,report

    binary=[xp.matrix((bits[:2],bits[2:])) for bits in product((0,1),repeat=4)]
    responses=[xp.matrix((row,)) for row in product((-1,0,1),repeat=2)]
    exhaustive_instances=0;query_count=0;feasible_uncapped=0
    for h in binary:
        for x in binary:
            for r in responses:
                exhaustive_instances+=1
                for cap in (None,0,1):
                    delta,report=validate_response(h,x,r,cap)
                    query_count+=1
                    if cap is None and delta is not None:feasible_uncapped+=1

    attainment_records=[]
    for h in binary:
        for n in (1,2,3):
            for cap in (0,1,2,3):
                budget=ca.budget_report(h,n,cap)
                upper=min(n,h.nrows-xp.rank(h),cap)
                check(budget['maximum_rank_under_cap']==upper,"Incorrect capped rank budget")
                for q in range(upper+1):
                    delta=ca.attaining_update(h,n,cap,requested_rank=q)
                    check(xp.rank(delta)==q and _zero(xp.matmul(delta,h)),"Rank attainment failed")
                    p=xp.projection(h).P_perp
                    check(xp.matmul(delta,p)==delta,"G=Delta projection realization failed")
                attainment_records.append({'protected_rank':xp.rank(h),'output_rows':n,
                                           'rank_cap':cap,'attained_maximum':upper})

    dimension_records=[]
    for h in binary:
        basis=ca.annihilator_basis(h,2)
        check(xp.rank(_flatten_columns(basis,2,2))==2*(2-xp.rank(h)),
              "Abstract annihilator basis dimension failed")
        for x in binary:
            report=ca.budget_report(h,2,x=x)
            image=tuple(xp.matmul(delta,x) for delta in basis)
            image_rank=xp.rank(_flatten_columns(image,2,x.ncols))
            check(image_rank==report['unrestricted_response_image_dimension'],"Response image dimension failed")
            check(len(basis)-image_rank==report['target_silent_update_space_dimension'],
                  "Silent-kernel dimension failed")
            dimension_records.append({'protected_rank':report['protected_rank'],
                                      'target_quotient_rank':report['target_quotient_rank'],
                                      'response_image_rank':image_rank})

    rng=random.Random(SEED);seeded=[];max_num=max_den=1
    for index in range(80):
        d=rng.randint(1,4);n=rng.randint(1,3);mh=rng.randint(0,d+1);mx=rng.randint(0,d+1)
        make=lambda rows,cols:xp.matrix(tuple(tuple(Fraction(rng.randint(-3,3),rng.randint(1,5))
                                                        for _ in range(cols)) for _ in range(rows)),ncols=cols)
        h=make(d,mh);x=make(d,mx);g=make(n,d)
        p=xp.projection(h).P_perp
        desired=xp.matmul(xp.matmul(g,p),x)
        delta,report=validate_response(h,x,desired,None)
        check(delta is not None,"Generated feasible rational response was refused")
        cap=xp.rank(desired)
        capped,capped_report=validate_response(h,x,desired,cap)
        check(capped is not None,"Minimum sufficient rank cap refused")
        if cap>0:
            too_small,_=validate_response(h,x,desired,cap-1)
            check(too_small is None,"Impossible smaller rank cap accepted")
        arbitrary=make(n,mx)
        _,arbitrary_report=validate_response(h,x,arbitrary,None)
        for value in (h,x,g,p,delta):
            for row in value.rows:
                for z in row:
                    max_num=max(max_num,abs(z.numerator).bit_length())
                    max_den=max(max_den,z.denominator.bit_length())
        seeded.append({'index':index,'shape':[n,d],'protected_columns':mh,'target_columns':mx,
                       'protected_rank':report['protected_rank'],'target_quotient_rank':report['target_quotient_rank'],
                       'minimum_response_rank':report['minimum_required_update_rank'],
                       'arbitrary_response_status':arbitrary_report['status'],
                       'constructed_response':report})

    named={}
    empty=xp.zeros(3,0);full=xp.eye(3);x=xp.eye(3)
    for label,h in [('zero_rank',empty),('full_rank',full)]:
        report=ca.budget_report(h,2,x=x)
        delta=ca.attaining_update(h,2)
        check(xp.rank(delta)==report['maximum_individual_update_rank'],"Rank edge attainment failed")
        named[label]={'budget':report,'attaining_update':xp.serialize(delta)}
    e1=xp.matrix(((1,),(0,)));e2=xp.matrix(((0,),(1,)))
    merged=ca.merge_generators({'state':e1,'input':e2})
    check(ca.budget_report(e1,2)['unrestricted_update_space_dimension']==2,"Local rank-one budget")
    check(ca.budget_report(merged,2)['unrestricted_update_space_dimension']==0,"Merged full-rank budget")
    named['local_low_rank_global_full_rank']={'local_ranks':[xp.rank(e1),xp.rank(e2)],
        'merged':xp.serialize(merged),'global_budget':ca.budget_report(merged,2)}
    nonzero=xp.matrix(((0,1),))
    check(_zero(xp.matmul(nonzero,e1)) and not _zero(xp.matmul(nonzero,xp.eye(2))),
          "Conservative upper space did not reject extra directions")
    named['conservative_overfreezing']={'true_budget':ca.budget_report(e1,1),
        'containing_budget':ca.budget_report(xp.eye(2),1),'safe_true_update':xp.serialize(nonzero)}
    named['sample_underprotection']={'sample_budget':ca.budget_report(e1,1),
        'actual_global_budget':ca.budget_report(xp.eye(2),1),
        'sample_safe_update':xp.serialize(nonzero),'unseen_response':xp.serialize(xp.matmul(nonzero,e2))}
    h3=xp.matrix(((1,),(0,),(0,)));x3=xp.matrix(((0,),(1,),(0,)))
    silent=ca.attaining_update(ca.concatenate(h3,x3),1)
    useful,_=ca.solve_response(h3,x3,xp.matrix(((2,),)))
    check(xp.rank(silent)==1 and _zero(xp.matmul(silent,x3)),"Nonzero target-silent witness failed")
    check(useful is not None and xp.matmul(useful,x3)==xp.matrix(((2,),)),"Nonzero response witness failed")
    named['silent_and_responding']={'budget':ca.budget_report(h3,1,x=x3),
        'silent_update':xp.serialize(silent),'responding_update':xp.serialize(useful)}
    no_response=ca.budget_report(h3,1,x=h3)
    check(not no_response['nonzero_target_response_exists'] and no_response['nonzero_target_silent_update_exists'],
          "Protected target impossibility failed")
    named['all_targets_protected']=no_response
    duplicated=xp.matrix(((0,0),(1,2)))
    impossible,impossible_report=validate_response(e1,duplicated,xp.matrix(((1,1),)),None)
    check(impossible is None,"Inconsistent dependent target responses accepted")
    named['target_relation_impossibility']=impossible_report
    empty_targets=xp.zeros(3,0)
    solved,empty_report=validate_response(h3,empty_targets,xp.zeros(2,0),0)
    check(solved==xp.zeros(2,3),"Empty target rank-zero response failed")
    named['empty_targets']=empty_report
    chain=[xp.zeros(3,0),h3,ca.concatenate(h3,x3),xp.eye(3)]
    budgets=[ca.budget_report(h,2,x=xp.eye(3)) for h in chain]
    check([v['unrestricted_update_space_dimension'] for v in budgets]==[6,4,2,0],"Protection monotonicity failed")
    check([v['unrestricted_response_image_dimension'] for v in budgets]==[6,4,2,0],"Response monotonicity failed")
    named['protection_chain']=budgets
    e11=xp.matrix(((1,0),(0,0)));e22=xp.matrix(((0,0),(0,1)))
    check(xp.rank(e11)==xp.rank(e22)==1 and xp.rank(xp.add(e11,e22))==2,
          "Rank-capped set nonlinearity witness failed")
    named['rank_cap_not_linear_space']={'rank_cap':1,'first':xp.serialize(e11),'second':xp.serialize(e22),
                                      'sum_rank':2,'unrestricted_dimension':4}
    p3=xp.projection(h3).P_perp
    badg=xp.matrix(((1,0,0),));goodg=xp.matrix(((0,1,0),))
    check(xp.rank(badg)==xp.rank(goodg)==1 and xp.rank(xp.matmul(badg,p3))==0
          and xp.rank(xp.matmul(goodg,p3))==1,"Generator orientation witness failed")
    named['generator_orientation_matters']={'same_generator_rank':1,'projected_ranks':[0,1]}

    refusals=[]
    def refuse(label,fn):
        try:fn()
        except (ValueError,TypeError) as exc:
            refusals.append({'case':label,'type':type(exc).__name__})
            check(True,'expected refusal')
        else:raise AssertionError('Invalid API input accepted: '+label)
    for label,fn in [
        ('zero_output_rows',lambda:ca.budget_report(e1,0)),
        ('boolean_output_rows',lambda:ca.budget_report(e1,True)),
        ('negative_rank_cap',lambda:ca.budget_report(e1,1,-1)),
        ('boolean_rank_cap',lambda:ca.budget_report(e1,1,True)),
        ('float_rank_cap',lambda:ca.budget_report(e1,1,1.0)),
        ('target_shape',lambda:ca.budget_report(e1,1,x=xp.eye(3))),
        ('response_shape',lambda:ca.solve_response(e1,e2,xp.eye(2))),
        ('requested_rank_too_high',lambda:ca.attaining_update(e1,1,1,requested_rank=2)),
        ('requested_boolean_rank',lambda:ca.attaining_update(e1,1,requested_rank=True)),
        ('empty_sites_no_dimension',lambda:ca.merge_generators({})),
        ('site_dimension_conflict',lambda:ca.merge_generators({'a':e1},input_dimension=3)),
        ('non_matrix',lambda:ca.budget_report(((1,),),1)),
    ]:refuse(label,fn)
    root=Path(__file__).resolve().parent
    sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
             for name in ('capacity_algebra.py','verify_algebra_cases.py','a4_runtime.py')}
    return {'schema':'dmwk-p2-a4-algebra-v1','status':'passed','seed':SEED,
            'checks':checks,'unexpected_failures':0,
            'exhaustive_response_instances':exhaustive_instances,
            'exhaustive_rank_cap_queries':query_count,
            'exhaustive_response_family':{'H':'all 16 binary 2x2 matrices','X':'all 16 binary 2x2 matrices',
                                          'R':'all 9 ternary 1x2 rows','caps':[None,0,1],
                                          'uncapped_feasible_instances':feasible_uncapped},
            'rank_attainment_budget_cases':len(attainment_records),
            'response_image_dimension_cases':len(dimension_records),
            'seeded_rectangular_rational_cases':len(seeded),
            'expected_refusals':len(refusals),'refusals':refusals,
            'named_cases':named,'seeded_cases':seeded,
            'observed_rational_size':{'max_numerator_bits':max_num,'max_denominator_bits':max_den,
                'scope':'Observed stored inputs/projectors/constructed updates in seeded cases only, not all intermediate bigint/gcd memory'},
            'elapsed_seconds':time.perf_counter()-started,'source_sha256':sources,
            'scope':'Finite exact-rational verification; unrestricted algebraic proofs are separate, no stored/BIT authorization',
            'SMT_queries':0,'prior_stage_suites_rerun':False}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run without -O/-OO')
    result=run_checks()
    out=Path(__file__).resolve().parent/'algebra_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','checks','exhaustive_response_instances',
         'exhaustive_rank_cap_queries','seeded_rectangular_rational_cases','expected_refusals','elapsed_seconds')}))

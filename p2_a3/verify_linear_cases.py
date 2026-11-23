"""P2-A3 finite algebra checks, separate from its universal handwritten proofs."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from pathlib import Path
import json
import random
import sys
import time

sys.dont_write_bytecode = True
from linear_contracts import (xp, matrix, effective_delta, merge_generators,
    contains_span, augment_activations, exact_linear_report, exact_affine_report,
    exact_augmented_report)

SEED=20261114


class Checks:
    def __init__(self): self.count=0
    def check(self,condition,message):
        self.count+=1
        if not condition: raise AssertionError(message)
    def reject(self,fn,message):
        try: fn()
        except ValueError: self.check(True,message); return
        raise AssertionError('Expected rejection: '+message)


def direct_product(rows, columns):
    """Simple scalar reference; no production matmul or basis reduction."""
    return tuple(tuple(sum((x*y for x,y in zip(row,col)),Fraction(0))
                       for col in columns) for row in rows)


def vectors(h):
    return tuple(tuple(h.rows[i][j] for i in range(h.nrows)) for j in range(h.ncols))


def is_zero(rows): return all(x==0 for row in rows for x in row)


def run_checks():
    t0=time.perf_counter(); ck=Checks(); rng=random.Random(SEED)
    fixtures=[]
    w0=matrix(((2,-3),(5,7)))
    alph=(-1,0,1)
    all_matrices=[matrix((v[:2],v[2:])) for v in product(alph,repeat=4)]
    rank_histogram={0:0,1:0,2:0}; annihilating=0; pairs=0
    for h in all_matrices:
        columns=vectors(h); r=xp.rank(h); rank_histogram[r]+=1
        probes=tuple(tuple(sum((Fraction(c[j])*h.rows[i][j] for j in range(2)),Fraction(0))
                           for i in range(2)) for c in product(alph,repeat=2))
        for delta in all_matrices:
            w1=xp.add(w0,delta)
            report=exact_linear_report(w0,w1,h)
            expected=is_zero(direct_product(delta.rows,columns))
            ck.check(report['annihilates_generators']==expected,'Direct generator product mismatch')
            ck.check(report['annihilates_basis']==expected,'Exact basis equivalence mismatch')
            ck.check(is_zero(direct_product(delta.rows,probes))==expected,'Finite span probes mismatch')
            ck.check(effective_delta(w0,w1)==delta,'Endpoint difference mismatch')
            ck.check(report['algebraic_update_space_dimension']==2*(2-r),'Rectangular dimension formula mismatch')
            ck.check(not report['authorizes_bitwise_commit'] and not report['global_domain_provenance_verified'],
                     'Algebra cannot authorize execution/global coverage')
            pairs+=1; annihilating+=int(expected)
    random_records=[]
    for index in range(80):
        k=rng.randint(1,3); d=rng.randint(1,4); m=rng.randint(0,5)
        q=lambda:Fraction(rng.randint(-5,5),rng.randint(1,7))
        old=matrix(tuple(tuple(q() for _ in range(d)) for _ in range(k)))
        new=matrix(tuple(tuple(q() for _ in range(d)) for _ in range(k)))
        h=matrix(tuple(tuple(q() for _ in range(m)) for _ in range(d)),ncols=m)
        if index%3==0:
            candidate=matrix(tuple(tuple(q() for _ in range(d)) for _ in range(k)))
            new=xp.add(old,xp.matmul(candidate,xp.projection(h).P_perp))
        delta=effective_delta(old,new); report=exact_linear_report(old,new,h)
        expected=is_zero(direct_product(delta.rows,vectors(h)))
        ck.check(report['annihilates_supplied_span']==expected,'Seeded rectangular exact result')
        coeffs=tuple(Fraction(rng.randint(-4,4),rng.randint(1,5)) for _ in range(m))
        x=tuple(sum((coeffs[j]*h.rows[i][j] for j in range(m)),Fraction(0)) for i in range(d))
        if expected:ck.check(is_zero(direct_product(delta.rows,(x,))),'Rational linear combination')
        b0=tuple(q() for _ in range(k));b1=tuple(q() for _ in range(k))
        affine=exact_affine_report(old,new,b0,b1,h)
        direct=tuple(tuple(sum((delta.rows[i][j]*x[j] for j in range(d)),Fraction(0))+(b1[i]-b0[i])
                           for x in vectors(h)) for i in range(k))
        ck.check(affine['annihilates_supplied_span']==is_zero(direct),'Direct affine difference')
        if b0==b1:
            ck.check(affine['annihilates_supplied_span']==expected,'Fixed-bias equivalence')
        random_records.append({'index':index,'weight_shape':[k,d],'generator_columns':m,
            'rank':report['protected_rank'],'annihilates':expected,
            'augmented_rank':affine['protected_rank'],'affine_annihilates':affine['annihilates_supplied_span']})

    zero=matrix(((0,0),(0,0))); update=matrix(((0,2),(0,-1)))
    empty=xp.zeros(2,0); full=xp.eye(2); one=matrix(((1,),(0,)))
    for name,h,expected in [('empty',empty,True),('full',full,False),('partial',one,True),
                            ('zero_repeated',matrix(((0,0),(0,0))),True),
                            ('dependent_repeated',matrix(((1,2,0,1),(0,0,0,0))),True)]:
        r=exact_linear_report(zero,update,h)
        ck.check(r['annihilates_supplied_span']==expected,'Named rank edge '+name)
        fixtures.append({'name':name,'report':r})

    local0=matrix(((1,),(0,)));local1=matrix(((0,),(1,)))
    merged=merge_generators({'later':local1,'earlier':local0})
    first=exact_linear_report(zero,update,local0)
    global_report=exact_linear_report(zero,update,merged)
    ck.check(first['annihilates_supplied_span'] and not global_report['annihilates_supplied_span'],
             'Shared-site union must be checked')
    ck.check(contains_span(full,one) and not contains_span(one,full),'Conservative span containment')
    ck.check(not exact_linear_report(zero,update,full)['annihilates_supplied_span']
             and exact_linear_report(zero,update,one)['annihilates_supplied_span'],
             'Superspace criterion is sufficient, not necessary for true smaller domain')
    ck.check(merge_generators({},input_dimension=2)==empty,'Empty declared site family shape')
    fixed_bias=exact_affine_report(zero,update,(3,-2),(3,-2),one)
    ck.check(fixed_bias['annihilates_supplied_span']==first['annihilates_supplied_span'],
             'Explicit nonzero fixed-bias case reduces to linear condition')

    # Equal unaugmented spans do not imply equal affine constraints.
    h01=matrix(((0,1),));h1=matrix(((1,),));wold=matrix(((0,),));wnew=matrix(((1,),))
    a01=exact_affine_report(wold,wnew,(0,),(-1,),h01)
    a1=exact_affine_report(wold,wnew,(0,),(-1,),h1)
    ck.check(xp.rank(h01)==xp.rank(h1)==1,'Affine regression has same linear rank')
    ck.check(a01['protected_rank']==2 and a1['protected_rank']==1,'Augmented spans differ')
    ck.check(not a01['annihilates_supplied_span'] and a1['annihilates_supplied_span'],
             'Augment actual activations before reducing basis')
    a_empty=exact_affine_report(wold,wnew,(0,),(2,),xp.zeros(1,0))
    ck.check(a_empty['annihilates_supplied_span'],'No calls gives empty augmented span')
    aff0=matrix(((0,0),));aff1=matrix(((1,-1),))
    augmented=exact_augmented_report(aff0,aff1,augment_activations(h01))
    ck.check(augmented['annihilates_supplied_span']==a01['annihilates_supplied_span'],
             'Already-augmented route agreement')

    # Same weights do not protect changed inputs: equality presumes a common h.
    ident=xp.eye(2); delta_report=exact_linear_report(ident,ident,full)
    before=direct_product(ident.rows,((Fraction(0),Fraction(0)),))
    after=direct_product(ident.rows,((Fraction(1),Fraction(0)),))
    ck.check(delta_report['annihilates_supplied_span'] and before!=after,'Changed-input caveat')
    rejections=[
        ('wrong endpoint shape',lambda:effective_delta(zero,matrix(((0,),)))),
        ('empty output rows',lambda:effective_delta(xp.zeros(0,2),xp.zeros(0,2))),
        ('wrong generator dimension',lambda:exact_linear_report(zero,update,h01)),
        ('site dimension mismatch',lambda:merge_generators({'a':one,'b':h01})),
        ('missing empty-family dimension',lambda:merge_generators({})),
        ('bool dimension',lambda:merge_generators({},input_dimension=True)),
        ('float bias',lambda:exact_affine_report(wold,wnew,(0.0,),(-1,),h1)),
        ('bias list',lambda:exact_affine_report(wold,wnew,[0],(-1,),h1)),
        ('wrong bias length',lambda:exact_affine_report(wold,wnew,(),(-1,),h1)),
        ('wrong affine activation dimension',lambda:exact_affine_report(wold,wnew,(0,),(-1,),one)),
        ('unaugmented one-column affine block',lambda:exact_augmented_report(wold,wnew,h1)),
        ('float exact matrix',lambda:matrix(((1.0,),))),
    ]
    for label,fn in rejections:ck.reject(fn,label)
    return {'schema':'dmwk-p2-a3-linear-checks-v1','status':'passed','seed':SEED,
        'checks':ck.count,'unexpected_failures':0,'expected_rejections':len(rejections),
        'runtime_seconds':time.perf_counter()-t0,
        'exhaustive':{'generator_shape':[2,2],'generator_alphabet':list(alph),'generator_matrices':len(all_matrices),
          'update_shape':[2,2],'update_alphabet':list(alph),'update_matrices':len(all_matrices),
          'fixed_old_weights':xp.serialize(w0),
          'endpoint_pairs':pairs,'annihilating_pairs':annihilating,
          'rank_histogram':{str(k):v for k,v in rank_histogram.items()},
          'finite_coefficient_vectors_per_pair':9,'checks_per_pair':6,
          'scope':'All stated small matrices; finite coefficient probes do not prove the universal theorem'},
        'seeded_rectangular_affine_cases':random_records,'named_cases':fixtures,
        'fixed_nonzero_bias_case':fixed_bias,
        'counterexamples':{
          'shared_site_omission':{'local':first,'merged':global_report},
          'sample_only':{'observed_activation':[1,0],'omitted_legal_activation':[0,1],
                         'sample_passes':True,'complete_domain_fails':True},
          'affine_basis_compression':{'full_actual_activations':a01,'compressed_unaugmented_basis':a1},
          'changed_inputs':{'zero_endpoint_difference':True,'old_input':[0,0],'new_input':[1,0],
                            'outputs_differ':True}},
        'rejections':[label for label,_ in rejections],
        'scope':'Exact rational diagnostics only; not global-domain provenance, floating safety, or a live-update authorization',
        'SMT_queries':0,'prior_stage_suites_rerun':False}


def main():
    result=run_checks()
    path=Path(__file__).resolve().parent/'algebra_results.json'
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'checks':result['checks'],
                      'endpoint_pairs':result['exhaustive']['endpoint_pairs'],'output':str(path)}))


if __name__=='__main__':main()

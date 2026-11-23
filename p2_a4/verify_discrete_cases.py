"""A4 finite-capacity and live-certificate experiments, not old-stage suites."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import hashlib
import json
import random
import time

from a4_runtime import get_fp, load_a2, load_a3, environment_metadata
from capacity_discrete import enumerate_family, classify_endpoint, dense_words

SEED=20261114
xp=load_a2('exact_projection')
ck=load_a3('certificate_kernel')


def canonical(x):
    return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)


def rehash(packet):
    p=packet['payload']
    if 'descriptor' in p:
        p['descriptor_sha256']=hashlib.sha256(canonical(p['descriptor']).encode('ascii')).hexdigest()
    packet['payload_sha256']=hashlib.sha256(canonical(p).encode('ascii')).hexdigest()
    return canonical(packet)


def run_checks():
    start=time.perf_counter();fp=get_fp();rng=random.Random(SEED)
    checks=0;families=[];boundaries=[];transactions=[];refusals=[]
    for fmt in ('BF16','FP32'):
        enc=lambda x:fp.encode_constant(x,fmt)
        one=enc(1);eta=fp.decode_word(1,fmt)
        fmt_families={}
        for name,alphabet in [('small_integer',(-1,0,1,2)),('tiny_nonnegative',(0,eta,1))]:
            for model in ('duplicate_feedback_v1','split_feedback_v1','shared_axis_v1'):
                result=enumerate_family(model,fmt,alphabet)
                assert result['family_size']==len(alphabet)**4==result['enumerated_endpoints']
                assert result['old_endpoint_in_family'] and not result['authorizes_commit']
                checks+=2
                groups=result['groups']
                bounds=result['proved_cardinality_bounds']
                assert groups['ALG']['endpoints']<=bounds['declared_family_ALG_endpoints']<=bounds['whole_format_ALG_endpoints']
                assert groups['BIT']['endpoints']<=bounds['declared_family_BIT_endpoints']<=bounds['all_stored_endpoints']
                assert groups['BIT']['raw_A_output_image_cardinality']<=min(groups['BIT']['A_total_execution_endpoints'],bounds['raw_A_output_tuples_if_all_outputs_accepted'])
                checks+=3
                assert groups['ALG_and_BIT']['endpoints'] <= min(groups['ALG']['endpoints'],groups['BIT']['endpoints'])
                assert groups['ALG']['endpoints']+groups['BIT_not_ALG']['endpoints']==groups['BIT']['endpoints']+groups['ALG_not_BIT']['endpoints']
                checks+=2
                for r in result['records']:
                    assert r['ALG_and_BIT']==(r['ALG'] and r['BIT'])
                    assert r['nonzero_effective_difference']==(r['rank_effective_difference']>0)
                    assert r['A_execution_total']
                    checks+=3
                for g in groups.values():
                    assert g['raw_A_output_image_cardinality']<=g['A_total_execution_endpoints']<=g['endpoints']
                    assert sum(g['rank_histogram'].values())==g['endpoints']
                    checks+=2
                result['family_name']=name
                families.append(result);fmt_families[(name,model)]=result
        # Directly justified finite integer count: each row summing to one has
        # exactly four choices in {-1,0,1,2}, independently across the two rows.
        integer=fmt_families[('small_integer','duplicate_feedback_v1')]
        assert integer['groups']['ALG']['endpoints']==integer['groups']['BIT']['endpoints']==16
        assert fmt_families[('small_integer','split_feedback_v1')]['groups']['BIT']['endpoints']==1
        assert fmt_families[('small_integer','shared_axis_v1')]['groups']['BIT']['endpoints']==1
        checks+=3
        # Same dense call evaluator and nested actual raw input sets, rather
        # than an unsupported statement about differently prepared programs.
        for family_name in ('small_integer','tiny_nonnegative'):
            dup=fmt_families[(family_name,'duplicate_feedback_v1')]
            split=fmt_families[(family_name,'split_feedback_v1')]
            keys=lambda z,tag:{canonical(r['endpoint_words']) for r in z['records'] if r[tag]}
            assert keys(split,'ALG') <= keys(dup,'ALG')
            assert keys(split,'BIT') <= keys(dup,'BIT')
            checks+=2
        tiny=fmt_families[('tiny_nonnegative','split_feedback_v1')]
        assert tiny['protected_rank']==2 and tiny['groups']['ALG']['endpoints']==1
        assert tiny['groups']['BIT_not_ALG']['endpoints']>0
        checks+=2
        # Frozen mask: one finite endpoint, not zero real algebraic dimension.
        frozen=enumerate_family('duplicate_feedback_v1',fmt,(-1,0,1,2),mutable_mask=((False,False),(False,False)))
        assert frozen['family_size']==1 and frozen['groups']['BIT']['endpoints']==1
        assert frozen['abstract_ALG_dimension']==2
        checks+=2
        boundaries.append({'id':'A4-D1_mask_capacity_collapse','format':fmt,
                           'family_size':1,'abstract_ALG_dimension':2,
                           'scope':'Explicit mask restriction; no claim that the full format has only one endpoint'})
        # A concrete finite family's delta set is not closed under addition.
        half_patch=((enc(2),enc(-1)),(0,one))
        r=classify_endpoint('duplicate_feedback_v1',fmt,((one,0),(0,one)),half_patch,((one,0),(0,one),(0,0)))
        assert r['ALG'] and r['BIT'] and r['nonzero_effective_difference']
        twice_endpoint=((enc(3),enc(-2)),(0,one))
        assert any(x not in integer['alphabet_words'] for row in twice_endpoint for x in row)
        checks+=2
        boundaries.append({'id':'A4-D2_finite_family_not_vector_space','format':fmt,
                           'endpoint':r['endpoint_words'],'twice_delta_endpoint':[list(x) for x in twice_endpoint],
                           'reason':'Twice an admitted family delta leaves its declared alphabet; finite set has no claimed linear dimension'})
        # Full-format storage obstruction, not just a finite alphabet result.
        maximum=fp.get_format(fmt).max_finite_word
        M=fp.decode_word(maximum,fmt);half=enc(Fraction(1,2))
        saturated=((maximum,maximum),(maximum,maximum))
        result=dense_words(saturated,(half,half),fmt)
        assert result==(maximum,maximum)
        neighbor=((maximum-1,maximum),(maximum,maximum))
        neighbor_delta=fp.decode_word(maximum-1,fmt)-M
        assert neighbor_delta<0
        assert neighbor_delta*Fraction(1,2)!=0
        checks+=3
        boundaries.append({'id':'A4-D3_full_format_ALG_singleton','format':fmt,
                           'old_words':[list(x) for x in saturated],'legal_D_input':[half,half],
                           'old_output_words':list(result),'protected_rank':1,'abstract_ALG_dimension':2,
                           'whole_format_stored_ALG_endpoint_count_proved':1,
                           'proof':'Each finite endpoint entry is <=Fmax; preserving each row sum2Fmax forces both entries to Fmax.',
                           'neighbor_words':[list(x) for x in neighbor],'neighbor_exact_first_output_change':str(neighbor_delta/2),
                           'scope':'The singleton count is a separate extremal proof, not a full-format enumeration. BIT singleton is not asserted.'})
        # Exact algebra preserves both legal inputs, but their finite execution
        # differs: retain A3's basis/subnormal boundary without rerunning A3.
        Q=tuple(tuple(fp.round_fraction(Fraction(2,3) if i==j else Fraction(-1,3),fmt)
                      for j in range(3)) for i in range(3))
        old3=((0,0,0),)*3
        thirds=classify_endpoint('thirds_two_inputs_v1',fmt,old3,Q,((one,0,0),))
        assert thirds['ALG'] and not thirds['BIT']
        assert dense_words(Q,(one,one,one),fmt)==(0,0,0)
        assert dense_words(Q,(1,1,1),fmt)==(1,1,1)
        checks+=3
        boundaries.append({'id':'A4-D4_ALG_without_BIT','format':fmt,'record':thirds,
                           'basis_output_words':[0,0,0],'tiny_output_words':[1,1,1]})
        # Actual commit differs from ideal null proposal.
        p=fp.get_format(fmt).p;big=enc(1<<p)
        old2=((big,0),(0,0));new2=((big,enc(-1)),(0,0))
        actual=classify_endpoint('commit_rounding_v1',fmt,old2,new2,((one,one),))
        assert fp.round_fraction(Fraction(1<<p)+1,fmt)==big
        assert not actual['ALG'] and not actual['BIT']
        assert actual['actual_decoded_A_change']==[['-1','0']]
        checks+=3
        boundaries.append({'id':'A4-D5_commit_changes_effective_update','format':fmt,
                           'ideal_delta':[['1','-1'],['0','0']],'record':actual})

        # Reuse the unchanged A3 live interface: new A4 patch/trajectory cases.
        kernel=ck.CertificateKernel(fmt);reference=ck.CertificateKernel(fmt)
        strong=((0,one),(enc(2),enc(-1)))
        before_A=kernel.a_output((one,0));cert=kernel.prepare(strong)
        receipt=kernel.commit(cert)
        after_A=kernel.a_output((one,0))
        assert before_A==(one,0) and after_A==(0,enc(2))
        assert receipt[1]!=receipt[2]
        checks+=2
        def refusal(label,fn):
            nonlocal checks
            before=kernel.snapshot()
            try:fn()
            except (ValueError,TypeError,OverflowError) as exc:
                assert kernel.snapshot()==before
                checks+=1
                refusals.append({'format':fmt,'case':label,'type':type(exc).__name__,
                                 'complete_snapshot_unchanged':True})
            else:raise AssertionError('Unsafe request accepted: '+label)
        refusal('stale_replay',lambda:kernel.commit(cert))
        good=kernel.prepare(((one,0),(0,one)))
        def altered(fn):
            p=json.loads(good);fn(p['payload']);return rehash(p)
        changes={
            'ideal_instead_of_effective':lambda p:p.__setitem__('effective_delta',[[[0,1],[0,1]],[[0,1],[0,1]]]),
            'old_endpoint':lambda p:p['old_weights'][0].__setitem__(0,one),
            'unsafe_endpoint':lambda p:p['new_weights'][0].__setitem__(0,enc(2)),
            'version':lambda p:p.__setitem__('expected_weight_version',0),
            'missing_site':lambda p:p['descriptor']['sites'].pop(),
            'missing_legal_activation':lambda p:p['descriptor']['sites'][0]['activations'].pop(),
            'sample_only':lambda p:p['descriptor'].__setitem__('coverage','samples_only'),
            'invariant':lambda p:p['descriptor'].__setitem__('invariant_id','caller_claim'),
            'schedule':lambda p:p['descriptor'].__setitem__('schedule','in_place'),
            'policy_fma':lambda p:p['descriptor'].__setitem__('numerical_policy','fma'),
            'graph_reordering':lambda p:p['descriptor']['graph'].__setitem__('matrix_evaluation','reverse'),
            'graph_fusion':lambda p:p['descriptor']['graph'].__setitem__('arithmetic','fused'),
            'algebra_only_claim':lambda p:p.__setitem__('claim','exact_algebra_only'),
            'forged_proof':lambda p:p['proof'].__setitem__('call_cases',[]),
        }
        for label,fn in changes.items():
            text=altered(fn);refusal(label,lambda text=text:kernel.commit(text))
        refusal('uncertified_model',lambda:ck.make_certificate('sample_only',fmt,kernel.weights,kernel.weights,kernel.version))
        refusal('negative_zero_endpoint',lambda:kernel.prepare(((one,fp.get_format(fmt).sign_mask),(0,one))))
        refusal('invalid_input',lambda:kernel.d_tick(enc(2)))
        refusal('altered_tick_schedule',lambda:kernel.d_tick(one,schedule='async'))
        # Global evidence survives a legal tick at unchanged weight version.
        assert kernel.d_tick(one)==reference.d_tick(one)
        kernel.commit(good)
        checks+=1
        accepted=[tuple(tuple(row) for row in r['endpoint_words']) for r in integer['records'] if r['BIT']]
        q=1;tick_count=1
        for _ in range(48):
            candidate=rng.choice(accepted)
            text=kernel.prepare(candidate)
            old_snapshot=kernel.snapshot()
            kernel.commit(text)
            assert kernel.state_word==old_snapshot[-2]
            bit=rng.randrange(2);word=one if bit else 0
            observation=kernel.d_tick(word)
            assert observation==reference.d_tick(word)
            assert observation[0]==(one if q else 0,)*2
            assert observation[1]==(word,word)
            q^=bit
            assert observation[2]==(one if q else 0)
            checks+=5;tick_count+=1
        # A zero target supplies a legal silent observation despite nonzero
        # stored edits; basis targets expose the strong patch.
        assert kernel.a_output((0,0))==(0,0)
        checks+=1
        transactions.append({'format':fmt,'strong_before_A_words':list(before_A),'strong_after_A_words':list(after_A),
                             'seeded_accepted_patch_ticks':48,'total_trace_ticks':tick_count,
                             'global_certificate_survives_state_advance':True,
                             'safe_zero_A_target_output':[0,0],
                             'scope':'Trusted A3 serial API; no prior suite rerun or new arbitrary-domain authorization'})
    return {'schema':'dmwk-p2-a4-discrete-v1','status':'passed','seed':SEED,'checks':checks,
            'unexpected_failures':0,'family_count':len(families),
            'enumerated_endpoint_cases':sum(f['family_size'] for f in families),
            'families':families,'boundaries':boundaries,'transactions':transactions,
            'expected_transaction_refusals':len(refusals),'refusals':refusals,
            'environment':environment_metadata(),'elapsed_seconds':time.perf_counter()-start,
            'SMT_queries':0,'prior_stage_suites_rerun':False,
            'scope':'Complete explicit candidate families, separate full-format extremal proof, and finite transactions; no universal floating capacity classification'}


if __name__=='__main__':
    if not __debug__:raise SystemExit('Run verification without -O/-OO')
    result=run_checks();out=Path(__file__).resolve().parent/'discrete_results.json'
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('families','boundaries','transactions','refusals','environment')}))

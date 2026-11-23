"""New C1 compiler/source/capacity checks; no predecessor suite is invoked."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import hashlib
from itertools import product
import json
from pathlib import Path
import random
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SEED = 20261114


class Recorder:
    def __init__(self):
        self.checks = 0
        self.counts = Counter()
        self.refusals = []

    def check(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def reject(self, label, function, *, compilation=False):
        self.checks += 1
        try:
            function()
        except ValueError as exc:
            self.refusals.append({"case": label, "error_type": type(exc).__name__, "reason": str(exc)})
            if compilation:
                self.counts["rejected_compile_requests"] += 1
            return
        raise AssertionError("Expected explicit refusal: " + label)

    def compile(self, cc, source, budget, fmt, response_request=None, mode="structural"):
        artifact = cc.compile_program(source, budget, fmt, response_request=response_request, mode=mode)
        self.counts["accepted_compile_requests"] += 1
        return artifact


def primitive_count(expr):
    op = expr[0]
    if op in ("const", "state", "input"):
        return 0
    return {"not": 1, "and": 1, "or": 4, "xor": 7, "mux": 7}[op] + sum(primitive_count(e) for e in expr[1:])


def node_count(expr):
    return 1 if expr[0] in ("const", "state", "input") else 1 + sum(node_count(e) for e in expr[1:])


def source_reference(source, state, inputs):
    """Plain Boolean denotation; no compiled wires, gate templates or floating operations."""
    def value(expr):
        op = expr[0]
        if op == "const": return expr[1]
        if op == "state": return state[expr[1]]
        if op == "input": return inputs[expr[1]]
        children = tuple(value(e) for e in expr[1:])
        if op == "not": return 1 - children[0]
        if op == "and": return int(all(children))
        if op == "or": return int(any(children))
        if op == "xor": return int(children[0] != children[1])
        if op == "mux": return children[1] if children[0] else children[2]
        raise AssertionError("Unknown reference constructor")
    return (tuple(value(e) for e in source["next_state"]),
            tuple(value(e) for e in source["outputs"]))


def make_source(next_state, outputs, states=1, inputs=1, initial=None):
    return {"schema": "dmwk-p2-c1-bool-fsm-v1",
            "state_ports": ["q" + str(i) for i in range(states)],
            "input_ports": ["u" + str(i) for i in range(inputs)],
            "output_ports": ["o" + str(i) for i in range(len(outputs))],
            "initial_states": initial if initial is not None else [list(s) for s in product((0, 1), repeat=states)],
            "next_state": copy.deepcopy(next_state), "outputs": copy.deepcopy(outputs)}


def atoms(states=1, inputs=1):
    return [["const", 0], ["const", 1]] + [["state", i] for i in range(states)] + [["input", i] for i in range(inputs)]


def complete_programs():
    leaf = atoms()
    small = leaf + [["not", copy.deepcopy(e)] for e in leaf]
    small += [["and", copy.deepcopy(a), copy.deepcopy(b)] for a, b in product(leaf, repeat=2)]
    for i, (nxt, out) in enumerate(product(small, repeat=2)):
        yield "not_and_pairs", i, make_source([nxt], [out])
    derived = [[op, copy.deepcopy(a), copy.deepcopy(b)] for op in ("or", "xor") for a, b in product(leaf, repeat=2)]
    derived += [["mux", copy.deepcopy(c), copy.deepcopy(a), copy.deepcopy(b)] for c, a, b in product(leaf, repeat=3)]
    for i, expr in enumerate(derived):
        # Two syntax occurrences must not become implicit CSE.
        yield "derived_atom_macros", i, make_source([expr], [expr])


def seeded_programs():
    rng = random.Random(SEED)
    leaf = atoms(2, 2)
    def expr(depth):
        if depth == 0 or rng.randrange(4) == 0:
            return copy.deepcopy(rng.choice(leaf))
        op = rng.choice(("not", "and", "or", "xor", "mux"))
        arity = 1 if op == "not" else 3 if op == "mux" else 2
        return [op] + [expr(depth-1) for _ in range(arity)]
    for i in range(12):
        yield i, make_source([expr(3), expr(3)], [expr(3), expr(3)], 2, 2, [[0, 0], [1, 1]])


def encode_bits(fp, values, fmt):
    one = fp.encode_constant(1, fmt)
    return tuple(one if value else 0 for value in values)


def fingerprint(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _word_matrix(fp, matrix, fmt):
    return tuple(tuple(fp.encode_constant(Q(v), fmt) for v in row) for row in matrix)


def _row(fp, weights, values, fmt, relu=False):
    audit = fp.Audit()
    acc = 0
    for w, x in zip(weights, values):
        acc = fp.add_words(acc, fp.mul_words(w, x, fmt, audit), fmt, audit)
    if relu and fp.decode_word(acc, fmt) < 0:
        acc = 0
    return acc, {key: getattr(audit, key) for key in ("native_multiply", "native_add", "software_multiply", "software_add", "native_oracle_checks")}


def inspect_program(cc, runtime, rec, source, fmt, budget, family, index):
    fp = runtime.get_fp();xp = runtime.load_a2("exact_projection")
    artifact = rec.compile(cc, source, budget, fmt)
    check = cc.check_artifact(artifact, source, budget, fmt)
    rec.check(check["accepted"] and not check["authorizes_weight_update"], "Compile receipt gained endpoint authority")
    rec.counts["accepted_artifact_reconstructions"] += 1
    bank = cc.initial_weights(artifact)
    altered = [list(row) for row in bank]
    for i, j in artifact["layout"]["writable_cells"]:
        altered[i][j] = fp.get_format(fmt).max_finite_word
    altered = cc.validate_endpoint(artifact, altered)
    expected_calls = sum(primitive_count(e) for e in source["next_state"]+source["outputs"])
    expected_nodes = sum(node_count(e) for e in source["next_state"]+source["outputs"])
    calls = artifact["graph"]["D_calls"];cost = artifact["cost"]
    p,q = budget["a_rows"],budget["a_cols"]
    rec.check(len(calls) == expected_calls == cost["primitive_D_calls_per_tick"], "Lowering call count differs from syntax occurrence count")
    rec.check(cost["source_node_occurrences"] == expected_nodes and cost["D_binary_float_operations_per_tick"] == 12*expected_calls, "Incorrect source/operation overhead")
    rec.check(cost["physical_shared_banks"] == 1 and cost["dense_matrix_word_slots"] == (2+p)*(3+q), "Incorrect physical reservation size")
    rec.check(cost["maximum_structural_nonzero_coefficients"] == 5+p*q, "Structural sparsity count mismatch")
    rec.check(artifact["capacity"]["protected_containing_rank"] == 3, "Conservative containing rank mislabeled")
    rec.check(artifact["proof"]["coverage"]["samples_used"] is False and artifact["proof"]["coverage"]["exact_reachable_span_claimed"] is False, "All-state coverage mislabeled as sampled or reachable-exact")
    words = artifact["domain"]["canonical_bit_words"]
    rec.check(words == [0,fp.encode_constant(1,fmt)], "Noncanonical Boolean domain")
    one=words[1];site_sets=[set() for _ in calls];context_count=0;site_count=0
    digest=hashlib.sha256();ops=Counter();example=None
    states=tuple(product((0,1),repeat=len(source["state_ports"])))
    inputs=tuple(product((0,1),repeat=len(source["input_ports"])))
    rec.check(len(cc.legal_states(artifact))==len(states) and len(cc.legal_inputs(artifact))==len(inputs), "Complete context count differs")
    for state,inp in product(states,inputs):
        expected_next,expected_out=source_reference(source,state,inp)
        source_value=cc.source_step(source,state,inp)
        rec.check(tuple(source_value["next_state_bits"])==expected_next and tuple(source_value["output_bits"])==expected_out,"Primary source denotations disagree")
        sw,uw=encode_bits(fp,state,fmt),encode_bits(fp,inp,fmt)
        actual=cc.execute_d(artifact,bank,sw,uw)
        changed=cc.execute_d(artifact,altered,sw,uw)
        rec.check(tuple(actual["next_state_words"])==encode_bits(fp,expected_next,fmt) and tuple(actual["output_words"])==encode_bits(fp,expected_out,fmt),"Compiled graph differs from Boolean source")
        rec.check(changed==actual,"Reserved finite A endpoint changed D observations or arithmetic")
        rec.check(actual["same_old_snapshot"] is True,"Missing same-snapshot marker")
        rec.check(len(actual["site_traces"])==expected_calls,"Missing executed shared site")
        for k,(call,trace) in enumerate(zip(calls,actual["site_traces"])):
            a,b=trace["argument_words"]
            rec.check(a in (0,one) and b in (0,one),"Non-Boolean intermediate gate argument")
            ab=(int(a==one),int(b==one));h=(ab[0],ab[1],1)+(0,)*q
            rec.check(trace["id"]==call["id"] and call["bank_id"]=="shared_weights" and trace["op"]==call["op"],"Shared site identity/order differs")
            rec.check(tuple(trace["physical_activation_words"])==encode_bits(fp,h,fmt),"Input preparation left protected coordinates")
            rec.check(tuple(trace["preactivation_words"])==(fp.encode_constant(sum(ab)-1,fmt),fp.encode_constant(1-ab[0],fmt)),"Primitive preactivation not exact")
            rec.check(tuple(trace["D_output_words"])==encode_bits(fp,(ab[0]&ab[1],1-ab[0]),fmt),"Primitive full D outputs differ")
            rec.check(trace["selected_row"]==call["selected_row"] and trace["result_word"]==trace["D_output_words"][call["selected_row"]],"Wrong selected primitive result")
            if call["op"]=="not":rec.check(b==0,"NOT has an unexpected live second argument")
            site_sets[k].add(h);site_count+=1
        audit=actual["arithmetic_counts"]
        mode="software" if fmt=="BF16" else "native"
        rec.check(audit[mode+"_multiply"]==6*expected_calls and audit[mode+"_add"]==6*expected_calls,"Floating graph operation count differs")
        if fmt=="FP32":
            rec.check(audit["native_oracle_checks"]==12*expected_calls,"FP32 operation lacked exact rounding audit")
            rec.check(audit["native_dtype_signatures"]==([("float32","float32","float32")] if expected_calls else []),"FP32 dtype silently promoted")
        for name,value in audit.items():
            if type(value) is int:ops[name]+=2*value
        event={"state":state,"input":inp,"next":actual["next_state_words"],"output":actual["output_words"],
               "sites":actual["site_traces"]}
        digest.update(json.dumps(event,sort_keys=True,separators=(",", ":")).encode()+b"\n")
        if example is None:example=event
        context_count+=1
    union=sorted(set().union(*site_sets)) if site_sets else []
    matrix=xp.Matrix(tuple(tuple(Q(h[j]) for h in union) for j in range(3+q)),len(union))
    coverage=artifact["proof"]["coverage"]
    rec.check(coverage["state_input_contexts"]==context_count and coverage["D_call_observations"]==site_count,"Coverage size does not include every shared call/context")
    rec.check(coverage["per_site"]==[{"id":c["id"],"activation_bits":[list(h) for h in sorted(hs)]} for c,hs in zip(calls,site_sets)],"Complete per-site activation sets differ")
    rec.check(coverage["all_state_activation_bits"]==[list(h) for h in union] and coverage["all_state_call_span_rank"]==xp.rank(matrix),"Complete union/rank differs from actual call traces")
    for z in artifact["domain"]["A_input_words"]:
        out=cc.evaluate_a(artifact,altered,z)
        rec.check(tuple(out["output_words"])==((fp.get_format(fmt).max_finite_word,)*p if any(z) else (0,)*p),"Finite saturated A endpoint is not total/exact on declared basis domain")
        rec.check(out["arithmetic_counts"][mode+"_multiply"]==p*q and out["arithmetic_counts"][mode+"_add"]==p*q,"A sparse arithmetic operation count differs")
    return {"family":family,"index":index,"format":fmt,"source_sha256":artifact["source_sha256"],
            "graph_sha256":artifact["graph_sha256"],"contexts":context_count,
            "endpoint_context_executions":2*context_count,"primitive_sites":expected_calls,
            "site_observations_per_endpoint":site_count,"all_state_rank":xp.rank(matrix),
            "dense_bank_words":cost["dense_matrix_word_slots"],"source_nodes":expected_nodes,
            "D_float_ops_per_tick":12*expected_calls,"trace_sha256":digest.hexdigest(),
            "arithmetic_totals_both_endpoints":dict(ops),"representative_trace":example},artifact,bank,altered


def complete_source_checks(cc,runtime,rec):
    entries=[];by_family=Counter();contexts=executions=observations=0;rank_counts=Counter();op_totals=Counter()
    extremes={}
    for fmt in ("BF16","FP32"):
        for family,index,source in complete_programs():
            row,_,_,_=inspect_program(cc,runtime,rec,source,fmt,cc.default_budget(),family,index)
            by_family[family]+=1;contexts+=row["contexts"];executions+=row["endpoint_context_executions"]
            observations+=row["site_observations_per_endpoint"];rank_counts[str(row["all_state_rank"])]+=1
            op_totals.update(row["arithmetic_totals_both_endpoints"])
            if row["primitive_sites"] not in extremes and len(extremes)<12:extremes[row["primitive_sites"]]=copy.deepcopy(row)
            row.pop("representative_trace");row.pop("arithmetic_totals_both_endpoints")
            entries.append(row)
    rec.check(by_family=={"not_and_pairs":1152,"derived_atom_macros":192},"Complete grammar enumeration size changed")
    rec.check(contexts==5376 and executions==10752,"Complete finite context enumeration size changed")
    return {"compiled_format_instances":len(entries),"families":dict(by_family),"complete_source_contexts":contexts,
            "endpoint_context_executions":executions,"primitive_site_observations_per_endpoint":observations,
            "all_state_rank_histogram":dict(rank_counts),"arithmetic_totals_both_endpoints":dict(op_totals),
            "records_sha256":fingerprint(entries),"records":entries,"representatives":list(extremes.values()),
            "scope":"All576 ordered next/output pairs over24 NOT/AND terms and96 derived atom macros; each format/all4 Boolean contexts, at zero and saturated A endpoints. Not every admitted AST."}


def seeded_source_checks(cc,runtime,rec):
    fp=runtime.get_fp();entries=[];contexts=executions=ticks=0;trace_hash=hashlib.sha256()
    for fmt in ("BF16","FP32"):
        for index,source in seeded_programs():
            row,artifact,bank,altered=inspect_program(cc,runtime,rec,source,fmt,cc.default_budget(2,2),"seeded_depth3",index)
            contexts+=row["contexts"];executions+=row["endpoint_context_executions"]
            rng=random.Random(SEED+1000+index);state=(0,0);actual=encode_bits(fp,state,fmt)
            for tick in range(16):
                inp=(rng.randrange(2),rng.randrange(2));expected_next,expected_out=source_reference(source,state,inp)
                endpoint=bank if tick%2==0 else altered
                result=cc.execute_d(artifact,endpoint,actual,encode_bits(fp,inp,fmt))
                rec.check(tuple(result["next_state_words"])==encode_bits(fp,expected_next,fmt) and tuple(result["output_words"])==encode_bits(fp,expected_out,fmt),"State feedback or endpoint alternation changed source semantics")
                trace_hash.update(json.dumps([fmt,index,tick,state,inp,result["next_state_words"],result["output_words"]]).encode()+b"\n")
                state=expected_next;actual=tuple(result["next_state_words"]);ticks+=1
            row.pop("representative_trace");entries.append(row)
    rec.check(len(entries)==24 and contexts==384 and ticks==384,"Seeded test accounting changed")
    return {"seed":SEED,"compiled_format_instances":len(entries),"complete_contexts_within_seeded_programs":contexts,
            "endpoint_context_executions":executions,"feedback_ticks":ticks,"feedback_sha256":trace_hash.hexdigest(),
            "records":entries,"scope":"12 seeded depth≤3 two-state/two-input programs; all16 contexts per chosen program, then16 feedback ticks each format. Endpoint alternation is a pure graph test, not live publication authority."}


def capacity_checks(cc,runtime,rec):
    fp=runtime.get_fp();rows=[];candidates=0;response_checks=0;D_checks=0;digest=hashlib.sha256()
    source=make_source([["and",["state",0],["input",0]]],[["not",["state",0]]])
    for fmt in ("BF16","FP32"):
        one=fp.encode_constant(1,fmt)
        for p,q in product((1,2),repeat=2):
            budget=cc.default_budget(p,q);artifact=rec.compile(cc,source,budget,fmt);cap=artifact["capacity"]
            n,d=2+p,3+q;alphabet=65279 if fmt=="BF16" else 4278190079
            rec.check(cap["structural_update_dimension"]==p*q and cap["full_output_annihilator_dimension"]==n*q,"Masked versus full-output dimensions conflated")
            rec.check(cap["D_rows_only_linear_preactivation_constraint_dimension"]==n*d-6,"D-observation-only linear dimension incorrect")
            rec.check(cap["maximum_structural_update_rank"]==min(p,q) and cap["A_full_basis_response_dimension"]==p*q,"Rank/response budget incorrect")
            rec.check(cap["canonical_word_alphabet_size"]==alphabet and cap["structural_endpoint_count_decimal"]==str(alphabet**(p*q)),"Exact finite endpoint count formula incorrect")
            rec.check(cap["full_basis_stored_response_signature_count_decimal"]==str(alphabet**(p*q)) and cap["finite_cardinality_theorem_not_exhaustive_enumeration"] is True,"Finite response signatures mislabeled")
            bank=cc.initial_weights(artifact);signatures=set();count=0
            palette=(0,one,fp.encode_constant(-1,fmt))
            for coefficients in product(palette,repeat=p*q):
                candidate=[list(row) for row in bank]
                for (i,j),value in zip(artifact["layout"]["writable_cells"],coefficients):candidate[i][j]=value
                candidate=cc.validate_endpoint(artifact,candidate)
                responses=[]
                for z in artifact["domain"]["A_input_words"]:
                    actual=cc.evaluate_a(artifact,candidate,z)["output_words"]
                    expected=(0,)*p if not any(z) else tuple(candidate[2+i][3+z.index(one)] for i in range(p))
                    rec.check(tuple(actual)==expected,"One-hot response not exact stored column")
                    responses.append(tuple(actual));response_checks+=1
                signatures.add(tuple(responses))
                for state,inp in product((0,1),repeat=2):
                    actual=cc.execute_d(artifact,candidate,encode_bits(fp,(state,),fmt),encode_bits(fp,(inp,),fmt))
                    rec.check(tuple(actual["next_state_words"])==encode_bits(fp,(state&inp,),fmt) and tuple(actual["output_words"])==encode_bits(fp,(1-state,),fmt),"Finite mask endpoint changed complete D table")
                    D_checks+=1
                digest.update(json.dumps([fmt,p,q,coefficients,responses]).encode()+b"\n")
                count+=1;candidates+=1
            rec.check(count==len(signatures)==3**(p*q),"Basis response map not injective on the complete named endpoint palette")
            # Every prescribed coordinate column is individually exact and storable.
            anchors={"inputs":[[int(j==k) for j in range(q)] for k in range(q)],
                     "outputs":[[[i+k+1,2] if (i+k+1)%2 else [(i+k+1)//2,1] for i in range(p)] for k in range(q)]}
            anchored=rec.compile(cc,source,budget,fmt,anchors)
            for z,targets in zip(anchors["inputs"],anchors["outputs"]):
                out=cc.evaluate_a(anchored,cc.initial_weights(anchored),encode_bits(fp,z,fmt))["output_words"]
                rec.check(tuple(fp.decode_word(v,fmt) for v in out)==tuple(Q(*a) for a in targets),"Admitted initial anchor differs from actual A response")
            modified=[list(row) for row in cc.initial_weights(anchored)]
            modified[2][3]=fp.encode_constant(-1,fmt)
            rec.check(cc.validate_endpoint(anchored,modified)[2][3]==modified[2][3],"Initial A anchor was incorrectly frozen against future learning")
            rows.append({"format":fmt,"A_shape":[p,q],"full_shape":[n,d],"capacity":cap,"cost":artifact["cost"],
                         "palette_endpoints":count,"distinct_actual_A_signatures":len(signatures),
                         "initial_anchor_receipt":anchored["proof"]["initial_A_anchors"]})
        # A saturated legal basis anchor is exact; an overflowing anchor is refused.
        value=fp.decode_word(fp.get_format(fmt).max_finite_word,fmt)
        request={"inputs":[[1]],"outputs":[[[value.numerator,value.denominator]]]}
        saturated=rec.compile(cc,source,cc.default_budget(),fmt,request)
        rec.check(cc.evaluate_a(saturated,cc.initial_weights(saturated),(one,))["output_words"]==(fp.get_format(fmt).max_finite_word,),"Saturated one-hot anchor was not exactly executable")
        overflow={"inputs":[[1]],"outputs":[[[(2*value).numerator,(2*value).denominator]]]}
        rec.reject(fmt+":unstorable_overflowing_initial_anchor",lambda:cc.compile_program(source,cc.default_budget(),fmt,overflow),compilation=True)
        rec.reject(fmt+":unstorable_exact_one_third_anchor",lambda:cc.compile_program(source,cc.default_budget(),fmt,{"inputs":[[1]],"outputs":[[[1,3]]]}),compilation=True)
        # The algebraic family remains available when a small actual step is a no-op.
        all_one=rec.compile(cc,source,cc.default_budget(),fmt,{"inputs":[[1]],"outputs":[[[1,1]]]})
        old=cc.initial_weights(all_one);xp=runtime.load_a2("exact_projection")
        entries=[[Q(0)]*4 for _ in range(3)];entries[2][3]=Q(1,1<<(fp.get_format(fmt).p+1))
        rounded=cc.quantize_endpoint(all_one,old,xp.matrix(entries))
        rec.check(rounded==old and all_one["capacity"]["structural_update_dimension"]==1,"Quantized no-op mislabeled as capacity exhaustion")
        rows.append({"format":fmt,"case":"saturated_and_quantized_boundary","saturated_anchor":str(value),
                     "small_proposal":str(entries[2][3]),"stored_noop":rounded==old,"remaining_algebra_dimension":1})
    rec.check(candidates==204,"Named finite endpoint family count changed")
    return {"layout_receipts":rows,"finite_palette_candidates":candidates,"actual_A_response_checks":response_checks,
            "complete_D_context_checks":D_checks,"finite_family_sha256":digest.hexdigest(),
            "scope":"All {-1,0,1} A-block endpoints for four1..2 shapes/twoformats; whole-format cardinality is a separate handwritten theorem, not enumerated evidence"}


def refusal_checks(cc,runtime,rec):
    fp=runtime.get_fp();artifacts=[];cases=[]
    source=make_source([["xor",["state",0],["input",0]]],[["mux",["input",0],["state",0],["not",["state",0]]]])
    for fmt in ("BF16","FP32"):
        budget=cc.default_budget(2,2);artifact=rec.compile(cc,source,budget,fmt);bank=cc.initial_weights(artifact)
        one=fp.encode_constant(1,fmt);form=fp.get_format(fmt)
        # Rehashing the mutated object cannot replace reconstruction from the expected source.
        mutations={
            "omitted_shared_D_site":lambda a:a["graph"]["D_calls"].pop(),
            "reordered_shared_D_sites":lambda a:a["graph"]["D_calls"].reverse(),
            "D_cross_region_read":lambda a:a["graph"]["D_calls"][0].__setitem__("columns",[0,1,3]),
            "D_cross_region_write":lambda a:a["graph"]["D_calls"][0].__setitem__("rows",[0,2]),
            "mixed_D_activation":lambda a:a["graph"]["D_calls"][0].__setitem__("activation","mixed_rotation_relu"),
            "changed_D_bias":lambda a:a["graph"]["D_calls"][0].__setitem__("bias_words",[one,0]),
            "A_activation_change":lambda a:a["graph"]["A_calls"][0].__setitem__("activation","coordinate_relu"),
            "state_reads_A":lambda a:a["graph"]["next_state_wires"].__setitem__(0,["A",0]),
            "undeclared_A_feedback":lambda a:a["graph"].__setitem__("A_to_D_feedback",True),
            "missing_A_shared_site":lambda a:a["graph"]["A_calls"].pop(),
            "mixed_state_layout":lambda a:a["layout"].__setitem__("D_rows",[0,2]),
            "editable_protected_cell":lambda a:a["layout"]["writable_cells"].append([0,0]),
            "missing_fixed_cell":lambda a:a["layout"]["fixed_cells"].pop(),
            "changed_parameter_identity":lambda a:a["layout"]["parameter_ids"][0].__setitem__(0,"unbound_cell"),
            "missing_domain_proof":lambda a:a.__setitem__("domain",{}),
            "sample_coverage_claim":lambda a:a["proof"]["coverage"].__setitem__("samples_used",True),
            "omitted_coverage_site":lambda a:a["proof"]["coverage"]["per_site"].pop(),
            "fake_capacity":lambda a:a["capacity"].__setitem__("structural_update_dimension",100),
            "changed_numerical_policy":lambda a:a.__setitem__("numerical_policy","FMA"),
            "changed_schedule":lambda a:a.__setitem__("schedule","inplace_asynchronous"),
            "changed_implementation_binding":lambda a:a.__setitem__("implementation_sha256",{}),
            "changed_source":lambda a:a["source"]["outputs"].__setitem__(0,["const",0]),
            "changed_initial_relation":lambda a:a["domain"].__setitem__("initial_state_words",[[one]]),
        }
        for label,mutate in mutations.items():
            wrong=copy.deepcopy(artifact);mutate(wrong)
            wrong["source_sha256"]=cc.digest(wrong["source"]);wrong["graph_sha256"]=cc.digest(wrong["graph"])
            rec.reject(fmt+":"+label,lambda wrong=wrong:cc.check_artifact(wrong,source,budget,fmt))
        # Coherently recompiling a different valid program is still not the expected program.
        other=make_source([["const",0]],[["const",0]])
        coherent=rec.compile(cc,other,budget,fmt)
        rec.reject(fmt+":coherent_wrong_source_identity",lambda:cc.check_artifact(coherent,source,budget,fmt))
        # Every fixed cell and each finite-word policy is checked before execution.
        for i,j,value in artifact["layout"]["fixed_cells"]:
            wrong=[list(row) for row in bank];wrong[i][j]=one if value==0 else 0
            rec.reject(f"{fmt}:fixed_endpoint_cell_{i}_{j}",lambda wrong=wrong:cc.validate_endpoint(artifact,wrong))
        for label,value in (("stored_negative_zero",form.sign_mask),("stored_infinity",form.exponent_mask<<form.fraction_bits),
                            ("stored_NaN",(form.exponent_mask<<form.fraction_bits)|1),("stored_wrong_width",1<<form.total_bits),
                            ("stored_host_float",0.0),("stored_bool",False)):
            wrong=[list(row) for row in bank];wrong[2][3]=value
            rec.reject(fmt+":"+label,lambda wrong=wrong:cc.validate_endpoint(artifact,wrong))
        rec.reject(fmt+":nonBoolean_state",lambda:cc.execute_d(artifact,bank,(fp.encode_constant(Q(1,2),fmt),),(0,)))
        rec.reject(fmt+":nonBoolean_input",lambda:cc.execute_d(artifact,bank,(0,),(1,)))
        rec.reject(fmt+":mixed_dense_A_input",lambda:cc.evaluate_a(artifact,bank,(one,one)))
        rec.reject(fmt+":wrong_A_input_dimension",lambda:cc.evaluate_a(artifact,bank,(one,)))
        rec.reject(fmt+":initial_index_outside_declared_relation",lambda:cc.initial_state_words(artifact,2))
        # Resource failures report this construction's unmet budget, not a universal impossibility.
        for field,value in (("d_row_budget",1),("d_col_budget",2),("a_rows",0),("a_cols",3),
                            ("parameter_budget",19),("call_budget",1),("call_budget",2049),
                            ("min_A_response_dimension",5),("required_update_rank",3),("parameter_budget",True),
                            ("d_row_budget",2.0),("required_update_rank",-1)):
            wrong=dict(budget);wrong[field]=value
            rec.reject(f"{fmt}:budget_{field}_{value}",lambda wrong=wrong:cc.compile_program(source,wrong,fmt),compilation=True)
        for mode in ("geometric","rotation","dense_relaxed"):
            rec.reject(fmt+":unsupported_mode_"+mode,lambda mode=mode:cc.compile_program(source,budget,fmt,mode=mode),compilation=True)
        bad_sources={
            "A_reference_in_source":make_source([["A",0]],[["state",0]]),
            "continuous_guard_in_source":make_source([["gt",["input",0],["const",0]]],[["state",0]]),
            "bad_reference":make_source([["state",1]],[["state",0]]),
            "host_bool_constant":make_source([["const",True]],[["state",0]]),
            "host_float_constant":make_source([["const",0.0]],[["state",0]]),
            "empty_initial_domain":make_source([["state",0]],[["state",0]],initial=[]),
            "duplicate_initial_state":make_source([["state",0]],[["state",0]],initial=[[0],[0]]),
        }
        duplicated=copy.deepcopy(source);duplicated["input_ports"][0]="q0";bad_sources["aliased_port_labels"]=duplicated
        undeclared=copy.deepcopy(source);undeclared["hidden_external_call"]={};bad_sources["hidden_external_schema_field"]=undeclared
        deep=["state",0]
        for _ in range(8):deep=["not",deep]
        bad_sources["expression_depth_limit"]=make_source([deep],[["state",0]])
        cycle=["not"];cycle.append(cycle)
        cyclic=copy.deepcopy(source);cyclic["next_state"]=[cycle];bad_sources["cyclic_expression"]=cyclic
        for label,wrong in bad_sources.items():
            rec.reject(fmt+":"+label,lambda wrong=wrong:cc.compile_program(wrong,budget,fmt),compilation=True)
        for label,request in (
            ("conflicting_anchors",{"inputs":[[1,0],[1,0]],"outputs":[[[0,1],[0,1]],[[1,1],[0,1]]]}),
            ("nonzero_zero_response",{"inputs":[[0,0]],"outputs":[[[1,1],[0,1]]]}),
            ("mixed_target_input",{"inputs":[[1,1]],"outputs":[[[0,1],[0,1]]]}),
            ("noncanonical_rational",{"inputs":[[1,0]],"outputs":[[[2,2],[0,1]]]}),
            ("invalid_rational_denominator",{"inputs":[[1,0]],"outputs":[[[1,0],[0,1]]]}),
            ("host_float_anchor",{"inputs":[[1,0]],"outputs":[[0.0,[0,1]]]})):
            rec.reject(fmt+":"+label,lambda request=request:cc.compile_program(source,budget,fmt,request),compilation=True)
        # Compile outputs do not alias caller source/budget or a cached earlier artifact.
        mutable=copy.deepcopy(source);budget_copy=copy.deepcopy(budget)
        detached=rec.compile(cc,mutable,budget_copy,fmt);digest_before=cc.digest(detached)
        mutable["outputs"][0]=["const",0];budget_copy["min_A_response_dimension"]=0
        rec.check(cc.digest(detached)==digest_before,"Compiled artifact aliases caller inputs")
        damaged=copy.deepcopy(detached);damaged["layout"]["fixed_cells"].clear()
        again=rec.compile(cc,source,budget,fmt)
        rec.check(cc.digest(again)==digest_before,"Mutable returned artifact damaged cached compiler result")
        sync=make_source([["state",1],["not",["state",0]]],[["state",0],["state",1]],states=2,inputs=0,initial=[[0,1]])
        synchronous=rec.compile(cc,sync,cc.default_budget(),fmt)
        actual=cc.execute_d(synchronous,cc.initial_weights(synchronous),encode_bits(fp,(0,1),fmt),())
        rec.check(tuple(actual["next_state_words"])==encode_bits(fp,(1,1),fmt) and tuple(actual["output_words"])==encode_bits(fp,(0,1),fmt),"Simultaneous source commit became sequential in-place update")
        cases.append({"format":fmt,"same_snapshot_next_bits":[1,1],"wrong_inplace_next_bits":[1,0],
                      "old_snapshot_output_bits":[0,1],"rehashed_artifact_mutations":len(mutations),
                      "fixed_cell_refusals":len(artifact["layout"]["fixed_cells"]),"artifact_sha256":digest_before})
        artifacts.append({"format":fmt,"source_sha256":artifact["source_sha256"],"graph_sha256":artifact["graph_sha256"]})
    rec.reject("unsupported_FP16",lambda:cc.compile_program(source,cc.default_budget(),"FP16"),compilation=True)
    rec.reject("prior_verifier_not_loadable",lambda:runtime.load_a3("verify_a3"))
    return {"reference_artifacts":artifacts,"cases":cases,
            "scope":"Complete expected-source reconstruction, canonical word/IR/budget admission and pure fixed-layout interfaces; serial transaction rollback is tested separately"}


def numeric_witnesses(cc, runtime, rec):
    fp = runtime.get_fp()
    records = []
    for fmt in ("BF16", "FP32"):
        spec = fp.get_format(fmt)
        one = fp.encode_constant(1, fmt)
        eta = fp.decode_word(1, fmt)
        F = 1 << spec.p
        source = make_source([["and", ["const", 1], ["const", 1]]], [["state", 0]], inputs=0)
        artifact = rec.compile(cc, source, cc.default_budget(), fmt)
        weights = cc.initial_weights(artifact)
        wrong = [list(row) for row in weights]
        wrong[0][:3] = list(_word_matrix(fp, ((F, 1, -F),), fmt)[0])
        before, _ = _row(fp, weights[0][:3], (one, one, one), fmt, True)
        after, audit = _row(fp, wrong[0][:3], (one, one, one), fmt, True)
        rec.check(sum(fp.decode_word(v, fmt) for v in wrong[0][:3]) == 1, "Exact constant-call anchor changed")
        rec.check(before == one and after == 0, "Tighter-span ALG-not-BIT witness missing")
        rec.reject(fmt + ":proved_rank_one_ALG_not_BIT_fixed_row", lambda: cc.validate_endpoint(artifact, wrong))
        records.append({"case": "proved_rank_one_ALG_not_BIT", "format": fmt, "source_sha256": artifact["source_sha256"],
                        "activation_words": [one, one, one], "old_row_words": list(weights[0][:3]),
                        "new_row_words": wrong[0][:3], "old_output_word": before, "new_output_word": after,
                        "exact_delta_action": "0", "actual_difference": "1", "arithmetic": audit,
                        "scope": "Complete singleton call-activation span; structural endpoint rejected"})
        # Full Boolean gate table can be BIT equal while rank-three ALG fails.
        changed = [list(row) for row in weights]
        changed[1][1] = 1
        table = []
        for a, b in product((0, 1), repeat=2):
            h = encode_bits(fp, (a, b, 1), fmt)
            x, _ = _row(fp, weights[1][:3], h, fmt, True)
            y, counts = _row(fp, changed[1][:3], h, fmt, True)
            rec.check(x == y == (one if not a else 0), "Boolean NOT eta BIT equality failed")
            table.append({"bits": [a, b], "old_word": x, "new_word": y})
        rec.reject(fmt + ":BIT_equal_fixed_NOT_edit_ALG_failure", lambda: cc.validate_endpoint(artifact, changed))
        records.append({"case": "BIT_not_ALG", "format": fmt, "table": table,
                        "effective_nonzero_entry": str(eta), "exact_residual_on_second_axis": str(eta),
                        "scope": "Finite full Boolean gate table; selected structural joint contract refuses"})
        # Actual endpoint storage, not the ideal projected proposal.
        stored = (fp.encode_constant(F+1, fmt), fp.encode_constant(-1, fmt))
        actual_delta = (fp.decode_word(stored[0], fmt)-F, fp.decode_word(stored[1], fmt))
        rec.check(actual_delta == (Q(0), Q(-1)) and sum(actual_delta) == -1, "Endpoint rounding did not break ideal null action")
        records.append({"case": "ideal_projection_commit_rounding", "format": fmt, "old_exact": [str(F), "0"],
                        "ideal_increment": ["1", "-1"], "stored_endpoint_words": list(stored),
                        "actual_increment": list(map(str, actual_delta)), "actual_protected_residual": "-1",
                        "scope": "Read-only generic geometric diagnostic; not a compiler-authorized layout change"})
        s = fp.decode_word(fp.encode_constant(Q(1, 3), fmt), fmt)
        row = _word_matrix(fp, ((2*s, -s, -s),), fmt)[0]
        basis, _ = _row(fp, row, (one, one, one), fmt)
        tiny, counts = _row(fp, row, (1, 1, 1), fmt)
        rec.check(2*s-s-s == 0 and basis == 0 and tiny == 1, "Thirds/subnormal execution witness failed")
        records.append({"case": "basis_test_not_full_span_BIT", "format": fmt, "row_words": list(row),
                        "basis_output_word": basis, "subnormal_output_word": tiny, "arithmetic": counts,
                        "scope": "Subnormal triple is outside the compiled Boolean D and one-hot A domains"})
        e = Q(1, 1 << (spec.p-1))
        a, b = fp.encode_constant(1+e, fmt), fp.encode_constant(1-e, fmt)
        product_word = fp.mul_words(a, b, fmt)
        separate = fp.add_words(product_word, fp.encode_constant(-1, fmt), fmt)
        fused_reference = fp.encode_constant((1+e)*(1-e)-1, fmt)
        rec.check(separate == 0 and fp.decode_word(fused_reference, fmt) == -e*e, "FMA graph difference witness failed")
        records.append({"case": "separate_versus_single_round_reference", "format": fmt,
                        "separate_word": separate, "one_round_reference_word": fused_reference,
                        "scope": "Exact one-round mathematical reference only; no native FMA certification"})
        rec.check(fp.mul_words(fp.encode_constant(-1, fmt), 0, fmt) == 0, "Arithmetic zero was not canonicalized")
        guard_before, guard_after = (fp.decode_word(word, fmt) > 0 for word in (0, 1))
        rec.check((guard_before, guard_after) == (False, True), "Strict guard did not switch on the first positive word")
        records.append({"case": "strict_guard_boundary", "format": fmt, "old_word": 0, "new_word": 1,
                        "old_gt_zero": guard_before, "new_gt_zero": guard_after, "distance": str(eta),
                        "scope": "Hard continuous guard is unsupported; Boolean MUX has a different legal domain"})
    rotation = [[0, -1], [1, 0]]
    vector = [1, -1]
    def rotate(v):
        return [sum(a*b for a,b in zip(row, v)) for row in rotation]
    def relu(v):
        return [max(component, 0) for component in v]
    gram = [[sum(a*b for a,b in zip(left, right)) for right in rotation] for left in rotation]
    left, right = relu(rotate(vector)), rotate(relu(vector))
    rec.check(gram == [[1, 0], [0, 1]], "Rotation witness violates orthogonality")
    rec.check(left == [1, 1] and right == [0, 1], "Rotation/ReLU witness did not expose the differing component")
    records.append({"case": "rotation_relu_failure", "R": rotation, "x": vector,
                    "relu_Rx": left, "R_relu_x": right, "R_R_transpose": gram, "orthogonal": True,
                    "scope": "Exact algebraic counterexample; no rotation is an admitted compiler transformation"})
    return {"records": records, "scope": "Specified new C1 graph boundaries and labelled read-only generic diagnostics"}


def run_checks():
    if not __debug__:
        raise ValueError("Run verification without -O/-OO")
    import c1_compiler as cc
    import c1_runtime as runtime
    start = time.perf_counter()
    rec = Recorder()
    sections = {
        "complete_source_families": complete_source_checks(cc, runtime, rec),
        "seeded_sources": seeded_source_checks(cc, runtime, rec),
        "capacity_and_anchors": capacity_checks(cc, runtime, rec),
        "reconstruction_and_refusals": refusal_checks(cc, runtime, rec),
        "numeric_boundaries": numeric_witnesses(cc, runtime, rec),
    }
    return {"schema": "dmwk-p2-c1-compiler-tests-v1", "status": "passed", "seed": SEED,
            "checks": rec.checks, "unexpected_failures": 0, "expected_refusals": len(rec.refusals),
            "request_counts": dict(rec.counts), "sections": sections, "refusals": rec.refusals,
            "elapsed_seconds": time.perf_counter()-start, "environment": runtime.environment_metadata(),
            "prior_stage_suites_rerun": False, "SMT_queries": 0, "proof_assistant_checked": False,
            "scope": "Closed IR compiler, complete named finite program/context families and separately seeded cases; not every external program or backend"}


def main():
    if not __debug__:
        raise SystemExit("Run verification without -O/-OO")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "compiler_results.json")
    args = parser.parse_args()
    result = run_checks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({key: result[key] for key in ("status", "checks", "expected_refusals", "elapsed_seconds")}, allow_nan=False))


if __name__ == "__main__":
    main()

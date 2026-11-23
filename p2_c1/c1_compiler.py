"""Closed Boolean FSM -> capacity-reserved shared weight bank and complete graph.

The program is the graph plus wires plus bank; a constant gate-bank size is not
a constant-size encoding of arbitrary programs. Pure checks never publish state.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path
import re

from c1_runtime import get_fp, load_a2

xp = load_a2("exact_projection")
SCHEMA = "dmwk-p2-c1-bool-fsm-v1"
ARTIFACT_SCHEMA = "dmwk-p2-c1-compiled-reserve-v1"
POLICY = "c1-sparse-fixed-views-separate-rne-canonical-zero-gradual-underflow-v1"
SCHEDULE = "c1-ordered-eager-graph-old-state-snapshot-synchronous-commit-v1"
MAX_NODES, MAX_DEPTH, MAX_CALLS = 256, 8, 2048
ROOT = Path(__file__).resolve().parent


class CompileRefused(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise CompileRefused(message)


def canonical_json(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (ValueError, TypeError, RecursionError) as exc:
        raise CompileRefused("Noncanonical JSON data: " + str(exc)) from None


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _copy(value):
    return json.loads(canonical_json(value))


def _bits(values, size, label):
    require(type(values) in (list, tuple) and len(values) == size, label + " dimension mismatch")
    require(all(type(v) is int and v in (0, 1) for v in values), label + " must contain built-in Boolean integers")
    return tuple(values)


def _format(fmt):
    require(type(fmt) is str and fmt in ("BF16", "FP32"), "Only fixed BF16/FP32 formats are supported")
    return fmt


def _word(raw, fmt):
    try:
        f = get_fp().get_format(fmt)
        require(type(raw) is int and 0 <= raw < (1 << f.total_bits), "Canonical raw word required")
        require(raw != f.sign_mask, "Stored negative zero is not canonical")
        get_fp().decode_word(raw, fmt)
        return raw
    except get_fp().ExecutionError as exc:
        raise CompileRefused("Invalid stored word: " + str(exc)) from None


def _word_bits(values, size, fmt, label):
    require(type(values) in (tuple, list) and len(values) == size, label + " dimension mismatch")
    one = get_fp().encode_constant(1, fmt)
    result = tuple(_word(v, fmt) for v in values)
    require(all(v in (0, one) for v in result), label + " is outside the canonical Boolean domain")
    return result


def validate_source(source):
    fields = {"schema", "state_ports", "input_ports", "output_ports", "initial_states", "next_state", "outputs"}
    require(type(source) is dict and set(source) == fields, "Source schema fields differ")
    require(source["schema"] == SCHEMA and type(source["schema"]) is str, "Unsupported source schema")
    limits = {"state_ports": (1, 2), "input_ports": (0, 2), "output_ports": (1, 2)}
    names = []
    for key, (lo, hi) in limits.items():
        ports = source[key]
        require(type(ports) is list and lo <= len(ports) <= hi, "Unsupported " + key + " arity")
        require(all(type(v) is str and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,31}", v) for v in ports),
                "Port names must be bounded ASCII identifiers")
        names += ports
    require(len(names) == len(set(names)), "All source port labels must be distinct")
    s, u, o = (len(source[k]) for k in ("state_ports", "input_ports", "output_ports"))
    initial = source["initial_states"]
    require(type(initial) is list and 1 <= len(initial) <= (1 << s), "Nonempty bounded initial-state list required")
    initials = tuple(_bits(v, s, "Initial state") for v in initial)
    require(len(set(initials)) == len(initials), "Duplicate initial state")
    for key, size in (("next_state", s), ("outputs", o)):
        require(type(source[key]) is list and len(source[key]) == size, key + " expression count mismatch")
    count, depth_max = 0, 0

    def expression(expr, depth):
        nonlocal count, depth_max
        count += 1; depth_max = max(depth_max, depth)
        require(count <= MAX_NODES and depth <= MAX_DEPTH, "Source expression resource limit exceeded")
        require(type(expr) is list and len(expr) >= 1 and type(expr[0]) is str, "Malformed prefix expression")
        op = expr[0]
        if op in ("const", "state", "input"):
            require(len(expr) == 2 and type(expr[1]) is int, "Malformed leaf expression")
            bound = 2 if op == "const" else s if op == "state" else u
            require(0 <= expr[1] < bound, "Leaf bit/reference out of range")
            return
        arity = {"not": 1, "and": 2, "or": 2, "xor": 2, "mux": 3}
        require(op in arity and len(expr) == arity[op] + 1, "Unsupported Boolean operator/arity")
        for child in expr[1:]: expression(child, depth + 1)

    for expr in source["next_state"] + source["outputs"]: expression(expr, 1)
    return {"state_count": s, "input_count": u, "output_count": o, "source_node_occurrences": count,
            "maximum_expression_depth": depth_max, "initial_state_count": len(initials)}


def default_budget(a_rows=1, a_cols=1):
    return {"d_row_budget": 2, "d_col_budget": 3, "a_rows": a_rows, "a_cols": a_cols,
            "parameter_budget": (2 + a_rows) * (3 + a_cols), "call_budget": MAX_CALLS,
            "min_A_response_dimension": a_rows * a_cols,
            "required_update_rank": min(a_rows, a_cols)}


def _budget(budget):
    fields = {"d_row_budget", "d_col_budget", "a_rows", "a_cols", "parameter_budget", "call_budget",
              "min_A_response_dimension", "required_update_rank"}
    require(type(budget) is dict and set(budget) == fields, "Budget fields differ")
    require(all(type(v) is int and v >= 0 for v in budget.values()), "Budgets require nonnegative built-in integers")
    p, q = budget["a_rows"], budget["a_cols"]
    require(1 <= p <= 2 and 1 <= q <= 2, "This reference supports 1..2 A rows/columns")
    require(budget["d_row_budget"] >= 2 and budget["d_col_budget"] >= 3, "Insufficient fixed D coordinate budget")
    require(budget["parameter_budget"] >= (2+p)*(3+q), "Insufficient physical dense-bank word budget")
    require(budget["call_budget"] <= MAX_CALLS, "Call budget exceeds supported reference limit")
    require(budget["min_A_response_dimension"] <= p*q, "Requested A response dimension exceeds reserved capacity")
    require(budget["required_update_rank"] <= min(p,q), "Requested attainable update rank exceeds reserved capacity")
    return p, q


def _eval_source(expr, state, inputs):
    op = expr[0]
    if op == "const": return expr[1]
    if op == "state": return state[expr[1]]
    if op == "input": return inputs[expr[1]]
    values = tuple(_eval_source(x, state, inputs) for x in expr[1:])
    if op == "not": return 1-values[0]
    if op == "and": return values[0] & values[1]
    if op == "or": return values[0] | values[1]
    if op == "xor": return values[0] ^ values[1]
    return values[1] if values[0] else values[2]


def source_step(source, state_bits, input_bits):
    sizes = validate_source(source)
    state = _bits(state_bits, sizes["state_count"], "Source state")
    inputs = _bits(input_bits, sizes["input_count"], "Source input")
    return {"next_state_bits": tuple(_eval_source(e,state,inputs) for e in source["next_state"]),
            "output_bits": tuple(_eval_source(e,state,inputs) for e in source["outputs"])}


def _lower(source, p, q):
    calls = []

    def gate(op, a, b, path):
        index = len(calls)
        calls.append({"id": f"d_gate_{index:04d}", "bank_id": "shared_weights", "op": op,
                      "args": [a,b], "selected_row": 0 if op == "and" else 1,
                      "source_path": path, "rows": [0,1], "columns": [0,1,2],
                      "activation": "coordinate_relu", "bias_words": [0,0]})
        return ["gate",index]

    def NOT(a,path): return gate("not",a,["const",0],path)
    def AND(a,b,path): return gate("and",a,b,path)
    def OR(a,b,path):
        na=NOT(a,path+".not_left");nb=NOT(b,path+".not_right")
        return NOT(AND(na,nb,path+".and"),path+".not_result")

    def expr(e,path):
        op=e[0]
        if op in ("const","state","input"):return list(e)
        children=[expr(c,path+f".arg{i}") for i,c in enumerate(e[1:])]
        if op=="not":return NOT(children[0],path+".not")
        if op=="and":return AND(*children,path+".and")
        if op=="or":return OR(*children,path+".or")
        if op=="xor":
            a,b=children
            either=OR(a,b,path+".xor.or")
            both=AND(a,b,path+".xor.and")
            return AND(either,NOT(both,path+".xor.not"),path+".xor.result")
        c,a,b=children
        yes=AND(c,a,path+".mux.yes")
        no=AND(NOT(c,path+".mux.not"),b,path+".mux.no")
        return OR(yes,no,path+".mux.result")

    next_wires=[expr(e,f"next[{i}]") for i,e in enumerate(source["next_state"])]
    output_wires=[expr(e,f"output[{i}]") for i,e in enumerate(source["outputs"])]
    a_inputs=[[0]*q]+[[int(i==j) for i in range(q)] for j in range(q)]
    a_calls=[{"id":"a_zero" if k==0 else f"a_basis_{k-1}","bank_id":"shared_weights",
              "input_bits":z,"physical_activation_bits":[0,0,0]+z,
              "rows":list(range(2,2+p)),"columns":list(range(3,3+q)),
              "activation":"identity","bias_words":[0]*p} for k,z in enumerate(a_inputs)]
    return {"bank_id":"shared_weights","D_calls":calls,"A_calls":a_calls,
            "next_state_wires":next_wires,"output_wires":output_wires,
            "state_ports":list(source["state_ports"]),"input_ports":list(source["input_ports"]),
            "output_ports":list(source["output_ports"]),"effects":"D next state and declared old-snapshot outputs only",
            "A_to_D_feedback":False,"schedule":SCHEDULE,"nonlinearities":{"D":"coordinate_relu","A":"identity"}}


def _wire(wire, state, inputs, selected, one):
    kind,index=wire
    if kind=="const":return one if index else 0
    if kind=="state":return state[index]
    if kind=="input":return inputs[index]
    return selected[index]


def _coverage(source, graph, q):
    sites=[set() for _ in graph["D_calls"]]
    s,u=len(source["state_ports"]),len(source["input_ports"])
    contexts=0
    for state in product((0,1),repeat=s):
        for inputs in product((0,1),repeat=u):
            contexts+=1;selected=[]
            for j,call in enumerate(graph["D_calls"]):
                a,b=(_wire(w,state,inputs,selected,1) for w in call["args"])
                require(a in (0,1) and b in (0,1),"Internal Boolean lowering invariant failed")
                sites[j].add((a,b,1)+((0,)*q))
                selected.append(a&b if call["op"]=="and" else 1-a)
    union=sorted(set().union(*sites)) if sites else []
    matrix=xp.Matrix(tuple(tuple(Fraction(h[i]) for h in union) for i in range(3+q)),len(union))
    return {"method":"structural Boolean induction; complete all-Boolean-state/input step envelope as additional evidence",
            "state_input_contexts":contexts,"D_call_observations":contexts*len(sites),
            "per_site":[{"id":call["id"],"activation_bits":[list(h) for h in sorted(hs)]}
                        for call,hs in zip(graph["D_calls"],sites)],
            "all_state_activation_bits":[list(h) for h in union],"all_state_call_span_rank":xp.rank(matrix),
            "exact_reachable_span_claimed":False,"samples_used":False,
            "all_shared_D_sites_covered":True,
            "closure":"all next-state wires Boolean; selected initial subset is contained in the all-Boolean invariant"}


def _rational_pair(value):
    require(type(value) is list and len(value)==2 and all(type(x) is int for x in value),
            "Initial anchor needs a canonical [numerator,denominator] pair")
    require(value[1]>0,"Initial anchor denominator must be positive")
    result=Fraction(value[0],value[1])
    require([result.numerator,result.denominator]==value,"Initial anchor rational must be reduced canonically")
    return result


def _initial_a(request,p,q,fmt):
    exact=[[Fraction(0) for _ in range(q)] for _ in range(p)]
    anchors={}
    if request is not None:
        require(type(request) is dict and set(request)=={"inputs","outputs"},"Initial A anchor fields differ")
        ins,outs=request["inputs"],request["outputs"]
        require(type(ins) is list and type(outs) is list and 1<=len(ins)<=8 and len(ins)==len(outs),
                "Initial anchor list length mismatch")
        for z,r in zip(ins,outs):
            z=_bits(z,q,"Initial anchor input")
            require(sum(z)<=1,"Initial A anchors support only zero/coordinate inputs")
            require(type(r) is list and len(r)==p,"Initial anchor response dimension mismatch")
            values=tuple(_rational_pair(v) for v in r)
            require(z not in anchors or anchors[z]==values,"Conflicting duplicate task anchors")
            require(any(z) or not any(values),"Nonzero response on zero input violates target compatibility")
            anchors[z]=values
        for z,values in anchors.items():
            if any(z):
                j=z.index(1)
                for i,v in enumerate(values):exact[i][j]=v
    try:
        words=tuple(tuple(get_fp().round_fraction(v,fmt) for v in row) for row in exact)
    except get_fp().ExecutionError as exc:
        raise CompileRefused("Initial A anchor cannot be stored: "+str(exc)) from None
    require(all(get_fp().decode_word(w,fmt)==v for row,ws in zip(exact,words) for v,w in zip(row,ws)),
            "Exact initial A anchor is not representable in the selected format")
    return words,{"initial_only":True,"future_learning_may_change_these_A_anchors":True,
                  "distinct_input_constraints":len(anchors),"all_relations_checked_in_zero_basis_domain":True,
                  "exact_storage_checked":True,"BIT_execution_checked_on_declared_inputs":True}


def _audit_record(audit):
    result={k:getattr(audit,k) for k in ("native_multiply","native_add","software_multiply","software_add",
                                      "exact_sums","native_oracle_checks")}
    result["native_dtype_signatures"]=sorted({(e["left_dtype"],e["right_dtype"],e["result_dtype"])
                                               for e in audit.events})
    return result


def _run_a(artifact,bank,z):
    fp=get_fp();fmt=artifact["format"];p,q=artifact["layout"]["a_rows"],artifact["layout"]["a_cols"]
    audit=fp.Audit();out=[]
    for i in range(p):
        acc=0
        for j in range(q):acc=fp.add_words(acc,fp.mul_words(bank[2+i][3+j],z[j],fmt,audit),fmt,audit)
        out.append(acc)
    one=fp.encode_constant(1,fmt)
    site=next(c["id"] for c in artifact["graph"]["A_calls"] if tuple(one if b else 0 for b in c["input_bits"])==z)
    return {"site_id":site,"output_words":tuple(out),"arithmetic_counts":_audit_record(audit),
            "physical_activation_words":(0,0,0)+z}


def _implementation_sources():
    paths=(Path(__file__),ROOT/"c1_runtime.py",Path(get_fp().__file__))
    return {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


@lru_cache(maxsize=256)
def _compile_text(source_text,budget_text,fmt,response_text,mode,implementation_stamp):
    source,budget,request=(json.loads(x) for x in (source_text,budget_text,response_text))
    sizes=validate_source(source);p,q=_budget(budget);_format(fmt)
    require(mode=="structural","General geometry/rotation compilation is unsupported; use read-only diagnostics")
    graph=_lower(source,p,q);g=len(graph["D_calls"])
    require(g<=budget["call_budget"],"Insufficient D primitive-call budget")
    A,anchor_proof=_initial_a(request,p,q,fmt)
    enc=lambda n:get_fp().encode_constant(n,fmt)
    n,d=2+p,3+q
    bank=[[0]*d for _ in range(n)]
    bank[0][:3]=[enc(1),enc(1),enc(-1)];bank[1][:3]=[enc(-1),0,enc(1)]
    for i in range(p):bank[2+i][3:]=A[i]
    writable=[[i,j] for i in range(2,n) for j in range(3,d)]
    fixed=[[i,j,bank[i][j]] for i in range(n) for j in range(d) if [i,j] not in writable]
    N=2*(get_fp().get_format(fmt).max_finite_word+1)-1
    coverage=_coverage(source,graph,q)
    one=enc(1)
    artifact={"schema":ARTIFACT_SCHEMA,"format":fmt,"mode":mode,"source":source,"budget":budget,
        "response_request":request,"source_sha256":digest(source),"graph_sha256":digest(graph),"graph":graph,
        "layout":{"bank_id":"shared_weights","full_shape":[n,d],"a_rows":p,"a_cols":q,
                  "D_rows":[0,1],"D_columns":[0,1,2],"A_rows":list(range(2,n)),"A_columns":list(range(3,d)),
                  "writable_cells":writable,"fixed_cells":fixed,"fixed_bias_words":[0]*n,
                  "parameter_ids":[[f"shared_weights[{i},{j}]" for j in range(d)] for i in range(n)]},
        "domain":{"state_count":sizes["state_count"],"input_count":sizes["input_count"],
                  "output_count":sizes["output_count"],"canonical_bit_words":[0,one],
                  "initial_state_words":[[one if b else 0 for b in st] for st in source["initial_states"]],
                  "D_state_invariant":"every canonical Boolean state tuple",
                  "D_input_domain":"every canonical Boolean input tuple",
                  "A_input_words":[[one if b else 0 for b in c["input_bits"]] for c in graph["A_calls"]],
                  "source_domains_owned_by_closed_frontend":True,"A_to_D_feedback":False},
        "capacity":{"protected_containing_rank":3,"input_dimension":d,"output_dimension":n,
                    "protected_generators_columns":[[int(i==j) for i in range(d)] for j in range(3)],
                    "all_state_call_span_rank":coverage["all_state_call_span_rank"],
                    "full_output_annihilator_dimension":n*q,"structural_update_dimension":p*q,
                    "D_rows_only_linear_preactivation_constraint_dimension":n*d-6,
                    "D_rows_only_scope":"external linear-preactivation family, not structural authorization or full BIT-class dimension",
                    "maximum_structural_update_rank":min(p,q),"A_full_basis_response_dimension":p*q,
                    "rank_budget_semantics":"requested minimum attainable rank, not a per-update rank cap",
                    "rank_capped_family_is_not_a_vector_space":True,
                    "canonical_word_alphabet_size":N,"structural_endpoint_count_decimal":str(N**(p*q)),
                    "full_basis_stored_response_signature_count_decimal":str(N**(p*q)),
                    "finite_cardinality_theorem_not_exhaustive_enumeration":True,
                    "fixed_capacity_not_consumed_by_update_count":True},
        "proof":{"method":"closed-source reconstruction plus conditional handwritten Boolean/structural induction",
                 "coverage":coverage,"initial_A_anchors":anchor_proof,"all_shared_sites_derived":True,
                 "global_containment_source":"every D wire Boolean by structural and tick induction; no samples",
                 "D_exactness_scope":"fixed small-integer primitive graph under the explicit numerical contract",
                 "A_totality_scope":"all canonical finite A endpoints on zero/basis inputs",
                 "general_proof_machine_checked":False,"external_arbitrary_program_discovery":False},
        "cost":{"source_node_occurrences":sizes["source_node_occurrences"],"maximum_expression_depth":sizes["maximum_expression_depth"],
                "primitive_D_calls_per_tick":g,"declared_A_call_sites":q+1,"physical_shared_banks":1,
                "dense_matrix_word_slots":n*d,"stored_bias_word_slots":n,"editable_word_slots":p*q,
                "fixed_nonzero_D_coefficients":5,"maximum_structural_nonzero_coefficients":5+p*q,
                "initial_nonzero_coefficients":sum(v!=0 for row in bank for v in row),
                "D_binary_float_operations_per_tick":12*g,"D_relu_word_operations_per_tick":2*g,
                "A_binary_float_operations_per_call":2*p*q,"current_plus_next_state_slots":2*sizes["state_count"],
                "input_word_slots":sizes["input_count"],"output_word_slots":sizes["output_count"],
                "selected_gate_wire_slots":g,"diagnostic_site_trace_records_per_tick":g,
                "source_json_bytes":len(source_text.encode("ascii")),"graph_json_bytes":len(canonical_json(graph).encode("ascii")),
                "compile_complete_envelope_contexts":coverage["state_input_contexts"],
                "program_representation":"source/ordered graph/wires plus shared bank; graph size is not constant",
                "host_ledger_optimizer_python_object_memory_included":False},
        "initial_weight_words":bank,"numerical_policy":POLICY,"schedule":SCHEDULE,
        "implementation_sha256":_implementation_sources()}
    if request is not None:
        for z,expected in zip(request["inputs"],request["outputs"]):
            out=_run_a(artifact,tuple(map(tuple,bank)),tuple(one if b else 0 for b in z))["output_words"]
            require(tuple(get_fp().decode_word(v,fmt) for v in out)==tuple(_rational_pair(v) for v in expected),
                    "Actual initial A output differs from its exact legal anchor")
    return canonical_json(artifact)


def compile_program(source,budget,fmt,response_request=None,mode="structural"):
    validate_source(source);_budget(budget);_format(fmt)
    require(type(mode) is str and mode=="structural","Unsupported compile mode; geometry remains read-only")
    stamp=digest(_implementation_sources())
    return json.loads(_compile_text(canonical_json(source),canonical_json(budget),fmt,canonical_json(response_request),mode,stamp))


def check_artifact(artifact,expected_source,expected_budget,fmt,response_request=None,mode="structural"):
    expected=compile_program(expected_source,expected_budget,fmt,response_request,mode)
    require(canonical_json(artifact)==canonical_json(expected),"Compiled artifact differs from complete source/budget/graph reconstruction")
    return {"accepted":True,"artifact_sha256":digest(expected),"source_sha256":expected["source_sha256"],
            "graph_sha256":expected["graph_sha256"],"scope":"closed expected source and fixed compiler contract",
            "authorizes_weight_update":False}


@lru_cache(maxsize=512)
def _verified_text(text,implementation_stamp):
    require(len(text)<=4000000,"Compiled artifact exceeds reference size limit")
    try:
        artifact=json.loads(text)
        require(type(artifact) is dict,"Compiled artifact must be a dictionary")
        expected=compile_program(artifact["source"],artifact["budget"],artifact["format"],artifact["response_request"],artifact["mode"])
    except (KeyError,TypeError) as exc:
        raise CompileRefused("Malformed compiled artifact: "+str(exc)) from None
    require(text==canonical_json(expected),"Embedded compiler/source reconstruction failed")
    return text


def _artifact(artifact):
    return json.loads(_verified_text(canonical_json(artifact),digest(_implementation_sources())))


def _admit(artifact,words):
    n,d=artifact["layout"]["full_shape"];fmt=artifact["format"]
    require(type(words) in (tuple,list) and len(words)==n,"Endpoint row count mismatch")
    require(all(type(row) in (tuple,list) and len(row)==d for row in words),"Endpoint column count mismatch")
    bank=tuple(tuple(_word(v,fmt) for v in row) for row in words)
    require(all(bank[i][j]==value for i,j,value in artifact["layout"]["fixed_cells"]),
            "Immutable D/cross-region weight cell changed")
    return bank


def validate_endpoint(artifact,words):
    """Self-check graph; the live caller separately binds its expected source."""
    return _admit(_artifact(artifact),words)


def initial_weights(artifact):
    a=_artifact(artifact);return _admit(a,a["initial_weight_words"])


def initial_state_words(artifact,index=0):
    a=_artifact(artifact);states=a["domain"]["initial_state_words"]
    require(type(index) is int and 0<=index<len(states),"Initial state index outside declared set")
    return tuple(states[index])


def legal_states(artifact):
    a=_artifact(artifact)
    return tuple(product(a["domain"]["canonical_bit_words"],repeat=a["domain"]["state_count"]))


def legal_inputs(artifact):
    a=_artifact(artifact)
    return tuple(product(a["domain"]["canonical_bit_words"],repeat=a["domain"]["input_count"]))


def execute_d(artifact,words,state_words,input_words):
    a=_artifact(artifact);bank=_admit(a,words);fp=get_fp();fmt=a["format"]
    state=_word_bits(state_words,a["domain"]["state_count"],fmt,"D state")
    inputs=_word_bits(input_words,a["domain"]["input_count"],fmt,"D input")
    one=fp.encode_constant(1,fmt);selected=[];traces=[];audit=fp.Audit()
    for call in a["graph"]["D_calls"]:
        av,bv=(_wire(w,state,inputs,selected,one) for w in call["args"])
        h=(av,bv,one);pre=[];out=[]
        for i in (0,1):
            acc=0
            for j in (0,1,2):acc=fp.add_words(acc,fp.mul_words(bank[i][j],h[j],fmt,audit),fmt,audit)
            pre.append(acc);out.append(0 if fp.decode_word(acc,fmt)<0 else acc)
        require(all(v in (0,one) for v in out),"D Boolean output invariant failed")
        value=out[call["selected_row"]];selected.append(value)
        traces.append({"id":call["id"],"op":call["op"],"argument_words":(av,bv),
                       "physical_activation_words":h+(0,)*a["layout"]["a_cols"],
                       "preactivation_words":tuple(pre),"D_output_words":tuple(out),
                       "selected_row":call["selected_row"],"result_word":value})
    next_state=tuple(_wire(w,state,inputs,selected,one) for w in a["graph"]["next_state_wires"])
    outputs=tuple(_wire(w,state,inputs,selected,one) for w in a["graph"]["output_wires"])
    require(all(v in (0,one) for v in next_state+outputs),"Compiled state/output closure failed")
    return {"next_state_words":next_state,"output_words":outputs,"site_traces":traces,
            "arithmetic_counts":_audit_record(audit),"same_old_snapshot":True,
            "source_sha256":a["source_sha256"],"graph_sha256":a["graph_sha256"]}


def evaluate_a(artifact,words,a_input_words):
    a=_artifact(artifact);bank=_admit(a,words);fmt=a["format"];q=a["layout"]["a_cols"]
    z=_word_bits(a_input_words,q,fmt,"A input")
    require(list(z) in a["domain"]["A_input_words"],"A input outside the proven zero/basis domain")
    return _run_a(a,bank,z)


def decode_matrix(words,fmt):
    _format(fmt)
    require(type(words) in (list,tuple) and len(words)>0,"Nonempty matrix required")
    d=len(words[0])
    require(d>0 and all(type(row) in (list,tuple) and len(row)==d for row in words),"Ragged word matrix")
    return xp.matrix(tuple(tuple(get_fp().decode_word(_word(v,fmt),fmt) for v in row) for row in words))


def quantize_endpoint(artifact,old_words,increment):
    """Form a real proposed sum, then stored words; authorization follows separately."""
    a=_artifact(artifact);old=_admit(a,old_words);exact=decode_matrix(old,a["format"])
    require(type(increment) is xp.Matrix and increment.shape==exact.shape,"Exact increment shape/type mismatch")
    proposed=xp.add(exact,increment)
    try:words=tuple(tuple(get_fp().round_fraction(v,a["format"]) for v in row) for row in proposed.rows)
    except get_fp().ExecutionError as exc:raise CompileRefused("Endpoint quantization refused: "+str(exc)) from None
    # Do not silently mask a caller's forbidden changes; fixed-cell validation
    # is the subsequent endpoint-authorization obligation.
    return words

# P2-C1 definitions — A bounded compiler with explicit reserved capacity

## 1. Scope and evidence types

The object is a compiler-owned finite Boolean synchronous machine plus a separate stateless linear A interface. The language, lowering, graph, shared bank, preparation functions, domains and observation interface are all part of the contract. An external arbitrary program is not admitted by supplying a locally well-shaped graph. The compiler supports the finite front-end limits stated in [Compiler](P2_C1_Compiler.md); those resource limits are distinct from the conditional mathematical statements below.

Earlier P1/P2 results are read-only premises, not rerun evidence. Exact algebra is over K=Q or R. Every admitted floating word decodes to a dyadic rational, so all finite-word endpoint differences can be treated exactly over Q. General proofs in [Theorems](P2_C1_Theorems.md) are handwritten. Complete named finite program/domain checks, seeded tests and actual CPU/software operations are separate evidence types.

## 2. Source IR and synchronous semantics

A source program p specifies ordered unique state labels S_0,...,S_(s-1), ordered unique input labels U_0,...,U_(i-1), a nonempty explicit allowed initial subset I_p of {0,1}^s, s next-state expressions, and an ordered list of labelled output expressions. Labels are fixed ports, not freely permutable neuron identities. Its expressions have grammar

    e ::= 0 | 1 | S_j | U_j | NOT(e) | AND(e,e)
          | OR(e,e) | XOR(e,e) | MUX(condition, when_true, when_false).

The constants and every reference are Boolean. Expressions are finite acyclic trees. There are no numeric threshold expressions, loops inside an expression, arbitrary host callbacks, hidden mutable references, external memory, exceptions as source effects, or A-coordinate references. Input u_t may be any vector in {0,1}^i at each time. Every Boolean state lies in the machine's invariant envelope S_p={0,1}^s, even when I_p is a proper subset.

The ideal evaluation [[e]](q,u) is ordinary Boolean evaluation, with MUX selecting its true or false value by a Boolean condition. Operational lowering evaluates all child expressions eagerly; they are pure and total on this domain. Source outputs y_t and successor q_(t+1) are both computed from the same q_t and u_t:

    y_t = Output_p(q_t,u_t),
    q_(t+1) = Next_p(q_t,u_t).

In particular outputs do not accidentally read q_(t+1). Reset, hold or halt-like behavior must be explicitly expressed by these Boolean expressions (for example a MUX-selected reset value or state identity). There is no additional undocumented reset priority or stateful branch semantics. The declared D observations are the ordered source output vector and next-state vector at each completed tick; gate traces may be checked as a stronger diagnostic.

## 3. Allowed proof-producing compiler operations

The trusted front end validates the entire source and its limits, fixes a canonical serialization, resolves labels, lowers each specified Boolean macro to the documented AND/NOT circuit, assigns ordered temporary wires and unique call-site identities, and constructs explicit next/output wire selections. Leaves are existing input/state wires or constants. The entire lowered site list is generated from source traversal. Its exact traversal order and macro expansions are part of the schema/version.

The initial compiler applies no CSE, constant folding, reassociation, FMA, algebraic rotation, layout permutation, speculative branch, dead-site deletion, or externally supplied optimization. If a later compiler adds such a transformation, it needs its own source/graph and numerical proof. Recompiling the complete bound source is the current checker's authority for completeness. Checking only that the sites appearing in a purported graph obey local type rules cannot establish that a missing source operation never existed.

All primitive sites share one physical bank identity. A site records which existing Boolean wires supply its operands and which result row supplies its output. Every next-state/output wire must refer to a source leaf or a preceding valid site. There is no in-place state update during graph evaluation.

The compiled program is the pair of its graph/wire/control metadata and its stored shared bank. The constant B gate block alone does not encode arbitrary source semantics. More complex source programs generally require more site and wire metadata and more gate invocations, even though they reuse the same fixed gate coefficients. No theorem identifies arbitrary programs with a fixed low-dimensional weight tensor free of that graph cost.

## 4. Physical bank, affine lift and numerical policy

Let m>=1 and c>=1 be the declared A output and input dimensions. The total bank has n=2+m rows and d=3+c columns, with fixed labelled decomposition

    W(A) = [[B, 0_(2 by c)], [0_(m by 3), A]],
    B = [[1, 1, -1], [-1, 0, 1]].

The first two rows and first three columns belong to the D gate interface. The lower-right m-by-c block is the sole writable region. The fixed B coefficients and both zero cross blocks are immutable words. Bias is fixed canonical zero. Affine constants are represented by the third input coordinate, not by an unbound mutable bias.

A D AND call prepares h=(a,b,1,0_c), computes the two B rows using ascending columns 0,1,2, and applies coordinate ReLU. It selects row zero. A NOT call sets b=0 and selects row one. The fixed sparse D execution visits only D rows and D columns; A coefficients are not executed as part of a D gate. The physical sharing map, sparse row/column lists, selection and ReLU policy are certificate content. Treating the bank as an arbitrary dense kernel is a different graph requiring a new proof.

Admitted encodings are canonical finite BF16 or FP32 words. Stored negative zero, NaN and infinities are rejected. Arithmetic uses nearest-even correctly rounded separate multiplication and addition, gradual underflow, canonicalization of arithmetic zero to +0, and bit-preserving storage. A sum starts from a canonical zero bias; no FMA, reassociation, larger undocumented accumulator or lower-precision temporary is assumed. The local FP32 execution evidence and software BF16 model have their recorded host scopes only.

## 5. A domain and effects

The legal A interface is stateless. It prepares (0,0,0,z) for z in Z_A={0,e_1,...,e_c}, evaluates only the editable block with identity activation and ordered separate multiply/add, and observes the m output words. Its invocation, inputs and outputs do not change source D state, source input preparation, D branch conventions or the tick schedule. No A-to-D feedback path exists in this IR.

Every canonical finite A endpoint is total on Z_A: each row has at most one nonzero product and that product is a stored coefficient times one. This is an intentional restricted-domain construction. Dense A inputs, multiple nonzero summands, nonidentity A nonlinearities, A state, or interactions between two autonomous tracks are outside this domain and require new proof rather than inherited approval.

Let F_F be the finite canonical alphabet for format F and N_F=|F_F|. Excluding all nonfinite encodings and stored negative zero gives N_BF16=65279 and N_FP32=4278190079. A raw endpoint is a tuple of words, not a real vector-space element closed under arbitrary arithmetic. Decode_F embeds it in Q^(n by d). The actual increment is Delta_eff=Decode_F(w_new)-Decode_F(w_old), not an ideal proposal and not a rounded subtraction instruction.

## 6. All-time activation sets and proved containing spaces

For each emitted D site l, define H_l(p) as its prepared vectors over all q in S_p and all legal u, evaluated by the compiler-owned pure graph. The all-site envelope is H_env(p)=union_l H_l(p). Because S_p is a proved invariant and every admitted initial state lies in it, the true set of all D activations over every allowed execution and time is contained in H_env(p).

The universal containing set and space are

    H_* = {(a,b,1,0_c): a,b in {0,1}},
    V_* = span_K H_* = K^3 x {0_c}.

Thus H_env(p) is contained in H_* and dim V_*=3. This is a conservative compiler reserve, not a claim that every program activates three independent directions. A program with no emitted site has H_env empty and span zero; NOT-only or constrained programs may have lower rank.

Optional complete enumeration of the finite product S_p x {0,1}^i at every emitted site computes V_env(p)=span_K H_env(p) exactly for that envelope. If I_p is a proper initial subset, V_env need not be the exact reachable span. It is still a proved upper containment. A sampled subset of states/inputs cannot replace this envelope certificate. The initial structural authorization uses the fixed reserve V_* and immutable layout rather than granting extra writable coefficients from a favorable measured rank.

## 7. Distinct capacities and requested responses

The unrestricted full-output annihilator U(V)={Delta:Delta V=0} has dimension n(d-r) for rank r. For V_*, this is (2+m)c. It permits some coefficients that the structural mask intentionally freezes. The structural linear family is

    M={[[0,0],[0,U]]: U in K^(m by c)},

with dimension mc and maximum update rank min(m,c). A freely chosen factor rank cap q restricts its maximum rank to min(q,m,c); this rank-capped family is generally not a linear space. These counts are not the full family preserving only the final source outputs: output-observation equivalence can be less restrictive and is not classified here.

The supported exact geometric operator is the coordinate projector S(G)=R_A G P_A, where the two diagonal selectors keep only A output/input coordinates. This is the Frobenius-orthogonal projector onto M. The final ideal update may use this operator after optimizer arithmetic; stored endpoint checks remain separate. A general rotated or approximate projector is not admitted by this naming choice.

For target A-coordinate columns Z in K^(c by p), exact response increments are R=UZ. This response image has dimension m rank Z. Feasibility of a requested R requires every linear relation Z alpha=0 to imply R alpha=0; when feasible the minimal implementing rank is rank R. For general homogeneous full-coordinate inputs X, full-output annihilation on V requires X alpha in V to imply R alpha=0. A structural mask and restricted legal A input domain can add obligations beyond that general condition.

The compiler budget describes one explicit construction: maximum D resource reserve/call or cell costs, selected A dimensions and requested response/rank minima. Its exact fields and limits are in Compiler. A feasible algebraic response does not imply a representable stored endpoint or a useful learning update. A compiler resource refusal is not an impossibility theorem for every other encoding or architecture.

Finite structural endpoints have cardinality N_F^(mc), and their D behavior belongs to one fixed BIT class under this graph/domain. Full-basis A output signatures distinguish all those endpoints. The class is finite and is not a vector space. A selected optimizer's next-step reachable subset can stall while this absolute endpoint class and its algebraic dimension stay unchanged.

## 8. Compilation evidence, current snapshots and publication

A compiled artifact binds the source schema/canonical source, allowed initial/input/state envelope, precision/zero policy, physical bank/layout and parameter identities, fixed words, editable mask, all D and A sites, bias/activation conventions, complete schedule, wire selections and capacity/provenance receipts. The trusted checker reconstructs it from the expected source, budget and policy. Unkeyed digests provide consistency identifiers, not authentication of intent or independent proof of a claimed external source.

A live owner additionally maintains the current word endpoint, chosen admitted D initial state/current state, execution tick, accepted-update version, optimizer state and history/budget ledgers. Accepted-update index k is distinct from execution time t. A tick snapshots one complete old endpoint/state, evaluates all source work from that snapshot and publishes its successor. An update forms a stored endpoint and stages all checks and optimizer/counter/ledger changes before one trusted serial publication.

A prepared transaction is checked against the complete current owned snapshot and complete compiler identity. A stale tick, endpoint, optimizer, version, graph/domain/schedule or ledger makes a previously prepared record inapplicable. Refusal preserves the entire owned snapshot. Successful updates intentionally change metadata and A behavior while preserving the declared D observation trace relative to the same initial state, source input sequence and trusted tick schedule.

Numeric or geometric receipts are read-only and cannot enter the exact commit path as authority. The selected BIT/ALG_AND_BIT obligations are not weakened after a failed candidate. Direct endpoint differences already contain upstream arithmetic and storage effects; a separate numerical comparison still needs both executions' rounding terms. The contract covers trusted serial copy-and-publish only, not malicious private mutation, general concurrency, process crashes or hardware faults.

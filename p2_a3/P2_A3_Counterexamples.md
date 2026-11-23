# P2-A3 counterexamples and acceptance boundaries

This catalog distinguishes exact endpoint algebra, actual ordered floating execution, and the A3 complete-domain certificate decision. Its executable source is [verify_counterexample_cases.py](verify_counterexample_cases.py); the recorded run is [counterexample_results.json](counterexample_results.json). It imports only the prior stages' arithmetic primitives, not their verification suites. No earlier evidence is overwritten.

The actual component run passed **126 explicit assertions**, with **16 deterministic format cases** covering eight classes, **12 expected refusals**, and **two additional observational-equivalence cases**. The refusals consist of eight complete-domain certificate issuance refusals and four unsupported arithmetic-policy requests. Imported primitive assertions are not added to this count. Seed `20261114` is recorded for the common A3 schema, but this component uses no random sampling. Its elapsed time and source hashes are in the JSON. These finite cases are not a universal machine proof.

BF16 operations use the declared software RNE model. FP32 products and additions use actual local scalar operations checked against exact rational RNE. Arithmetic zero is canonicalized to +0; gradual underflow is retained. The modeled FMA is explicitly a one-round software reference. GPU and native BF16 are not certified.

## Evidence index

| Record ID | Incorrect inference or missing premise | Actual result |
|---|---|---|
| A3-C1 | An ideal null increment remains null when committed to storage | Effective residual and executed output change are -1; certificate refused |
| A3-C2 | Zero floating output on a generating basis certifies every legal input in its span | Exact null on both inputs, but the small legal input produces raw `0x1`; certificate refused |
| A3-C3 | One shared call site's low-rank domain suffices | The second site changes; complete shared-domain certificate refused |
| A3-C4 | A passing initial-state sample establishes all reachable-state safety | A later call changes and the illustrative patched recurrence leaves its Boolean invariant; registered complete-domain checker refuses the same unsafe row edit |
| A3-C5 | Keeping a D matrix unchanged makes A-to-D input feedback harmless | D inputs and outputs change despite Delta_W=0; same-input premise is absent |
| A3-C6 | A weight-only check covers independently mutable bias | Bias changes output; augmented exact check detects residual 1 |
| A3-C7 | A reduction tree can change without changing the execution contract | Ordered result -1, alternate tree 0; unsupported policy refused |
| A3-C8 | Fused and separate operations share bit semantics | Separate result 0, one-round fused reference nonzero; unsupported policy refused |
| A3-X1 | A full-rank exact protected span rules out every finite-domain observational edit | A nonzero endpoint edit fails exact annihilation yet passes complete bitwise certification and changes an A output |

Each ordinary class has one BF16 and one FP32 record under `records`. A3-X1 appears under `extra_boundaries`. These are successful detections of limits, not unexplained failed tests.

## A3-C1: commit quantization invalidates the ideal constraint

Let p=8 for BF16 and p=24 for FP32. For the relevant first row, use

\[
W=(2^p,0),\qquad \Delta_{ideal}=(1,-1),\qquad h=(1,1)^T.
\]

The proposed increment is exactly representable and satisfies Delta_ideal h=0. But the declared final-RNE commit gives

\[
W'=(2^p,-1),\qquad \Delta_{eff}=W'-W=(0,-1),\qquad
\Delta_{eff}h=-1.
\]

Adding one to 2^p is a nearest-even tie that rounds back to 2^p. The old and new ordered results are 2^p and 2^p-1. The A3 record uses a two-by-two matrix with a zero second row and records both complete stored endpoints, the ideal increment, exact effective difference, executed output words, and a pointwise error decomposition.

The trusted `commit_rounding_v1` domain contains the protected activation (1,1). Issuance of a bitwise certificate for the actual endpoints is refused because the full output changes. The checker does not substitute the ideal increment for W'-W. There is no live kernel transaction in this stateless issuance probe; transactional no-mutation checks are separately exercised by the main certificate verifier.

## A3-C2: exact span annihilation and a zero basis probe still fail floating execution

Let V=span_R{(1,1,1)^T}. The exact complement projector is I-J/3. Its stored rounded version Q has diagonal 2s and off-diagonal -s, where s=RNE(1/3), so

\[
Q(1,1,1)^T=0
\]

holds in exact rational algebra. Let the old matrix be zero and the new stored matrix be Q. Declare **two** legal stored activations:

\[
h_1=(1,1,1)^T,\qquad h_2=(\eta,\eta,\eta)^T,
\]

where eta is the format's smallest positive subnormal. Exact Delta_eff h is zero for both and, mathematically, for their entire real span.

The fixed floating execution returns canonical zeros on h_1. On h_2, each diagonal product is near (2/3)eta and rounds to eta; each off-diagonal product is near -(1/3)eta and rounds to zero. The output is therefore (eta,eta,eta), with raw word `0x1` in every row. Both formats were actually exercised under the declared primitive policy.

This is not an assumption that the finite legal set is closed under arbitrary real scaling: the second vector is explicitly included in the domain. It shows why the **exact** basis/span theorem cannot be replaced by floating evaluation on a basis. It also shows why exact algebraic annihilation alone does not authorize a floating patch.

The `thirds_two_inputs_v1` registry contains both inputs independently of the submitted certificate. The checker refuses the patch at the tiny input. A relative-only gamma bound is not issued for these underflowing products; the exact local absolute-error bound remains valid and contains the observed change.

## A3-C3: missing a shared call site

For the same physical two-column matrix, let one site use e_1 and another use e_2. Take

\[
W=I_2,\qquad W'=\operatorname{diag}(1,2).
\]

The first site's exact and floating full outputs agree before and after the edit. The second site's second output changes from one to two. Each local span is one-dimensional, while their merged span is R^2. The exact effective update is not an annihilator of that merged space.

Both sites are registered under `shared_axis_v1`; the submitted patch cannot redefine the trusted site list. Certificate issuance is refused. A smaller caller-provided list or sample set cannot become a new complete domain merely by carrying a digest or a label.

## A3-C4: initial samples omit reachable feedback states

Consider the illustrative scalar recurrence

\[
y_t=W(q_t,0)^T,\qquad q_{t+1}=1-y_t,
\]

with q_0=0. The reference row W=(1,0) has reachable states {0,1}, alternating forever. Change the row to W'=(2,0). At the initial state, both outputs are zero and both next states are one. At the next call, the reference output is one and the patched output is two, yielding next states zero and -1 respectively.

The two-tick numerical traces were executed in both formats; all relevant numbers are exactly representable. The patched execution leaves the original Boolean invariant. Passing the initial state did not establish coverage of the reachable activation (1,0), nor did it establish closure of the proposed new transition.

This trace is a deliberately separate illustrative recurrence, not a certificate-accepted execution of the reference kernel. The same unsafe first-row edit is also submitted to the actual `duplicate_feedback_v1` checker, whose complete Boolean state/input domain includes its nonzero activation. That registered check refuses it. The JSON distinguishes the scalar recurrence from the registered graph instead of claiming they are one program.

## A3-C5: an unmodeled A-to-D input channel defeats an otherwise unchanged map

Keep a D scalar weight equal to one: W_D'=W_D=1, so Delta_D=0 on every input. Let an A scalar output on input one change from theta=1 to theta'=2. Define a previously unprotected interface h=A_output-1. D receives h=0 before the change and h'=1 afterward; both are legal Boolean values, but D output changes from zero to one.

The arithmetic was performed in both formats. This does not refute the exact same-input theorem or the conditional local-to-program induction. It violates the requirement that corresponding D calls receive the same protected inputs, or equivalently that all A-to-D influences have been included in the relational interface/invariant argument.

The delivered stateful registries explicitly forbid this feedback channel. This counterexample is not a claim that an accepted patch can add it. It explains why fixed D weights and unchanged local formulas are insufficient if interfaces or input-producing state can change.

## A3-C6: a mutable bias must be represented in the constraint

Keep W=W'=1 and the input h=1, but change bias from b=0 to b'=1. The weight-only condition Delta_W h=0 holds, whereas the affine output changes from one to two. The stored products and additions were evaluated in both formats.

For the augmented row and input,

\[
\overline W=(W,b),\qquad \overline h=(h,1)^T,
\qquad \Delta\overline W=(0,1),
\]

the exact residual is one and the correct algebraic test detects the change. In a joint bias contract, this extra coordinate is required. In the delivered fixed-bias contract, a changed bias/model descriptor cannot be introduced by a certificate. Homogenization is an algebraic construction; it does not authorize changing the specified floating reduction order.

## A3-C7: reassociation changes an exact-zero dot result

Take

\[
v=(2^p,1,-2^p,-1),\qquad h=(1,1,1,1)^T.
\]

The exact dot is zero, but separate products and left-to-right additions yield -1. The accumulator first reaches 2^p; adding one rounds back to 2^p; adding -2^p yields zero; adding -1 yields -1.

The alternative tree (p_0+p_2)+(p_1+p_3) yields zero. Both computations are recorded as distinct execution graphs in BF16 and FP32. A request for the unsupported `pairwise` policy is refused by the fixed ordered primitive interface. The live certificate contract also binds its own graph and policy; its mutation tests are recorded by the certificate verifier.

These coefficients are a general floating-point boundary example, not an unannounced extension of the P1 Boolean compiler's admitted small-coefficient instruction library.

## A3-C8: modeled fusion changes the result

Let x=1+2^-k, y=1-2^-k, c=-1, with k=5 in BF16 and k=13 in FP32. All operands are representable. The separate product/add result is zero. A single rounding of the exact fused expression xy+c gives -2^(-2k):

| Format | Separate result | One-round fused reference |
|---|---:|---:|
| BF16 | 0 | -1/1024 |
| FP32 | 0 | -1/67108864 |

The fused value is an exact rational expression followed by one software RNE operation; native hardware FMA was **not** executed. The ordered executor refuses a `fma` policy request. A compiler or backend that substitutes fusion therefore requires a separately justified execution contract.

## A3-X1: exact full rank and finite observational equivalence are different

This additional boundary prevents an incorrect converse. It supplies a strict starting caution for later rank/capacity research without attempting that classification here.

In the registered `split_feedback_v1` graph, the shared D matrix receives (q,q) at the state site and (u,0) at the input site, where q,u are Boolean. Their combined legal input set is {0,(1,1),e_1}; its exact span is all of R^2. Let

\[
W=I_2,\qquad W'=\begin{pmatrix}1&\eta\\0&1\end{pmatrix},
\]

with eta the smallest positive subnormal. Delta_eff is nonzero, and Delta_eff(1,1)^T=(eta,0)^T. Thus the exact linear noninterference condition fails, as it must for a nonzero update on a full-rank protected span.

Nevertheless, the actual finite-domain floating outputs are identical. At zero and e_1 there is no changed nonzero term; at (1,1), the first-row sum 1+eta rounds to one. The complete trusted-domain checker accepts the bitwise certificate and **explicitly records that exact algebraic annihilation is false**. This is not misclassified as an algebraic certificate.

For the legal A input e_2, the full output changes from (0,1) to (eta,1). Both endpoints are stored, and the output change survives execution. The script issued and committed the certificate in both formats and compared six feedback ticks with the unchanged reference. Each certificate separately checks all four registered call cases and all four Boolean state/input transition cases; the all-finite-time lifting remains the separate conditional theorem.

Consequently, full rank removes every nonzero **exact real-linear annihilator**, but it need not remove every endpoint edit observationally equivalent on a finite floating domain. Neither the real dimension d(d-r) nor a numerical effective-rank estimate is automatically the capacity of the executable bitwise-equivalence class. This example makes no claim about optimal capacity, learning quality or robust usefulness of the tiny A response.

## Pointwise bounds and scope of refusal

For each stored endpoint/input probe in C1–C3, the script records

\[
\widehat y'-\widehat y
=\Delta_{eff}h+e'-e,
\qquad
|\widehat y'-\widehat y|
\le |\Delta_{eff}h|+\beta_{old}+\beta_{new},
\]

where each beta is the exact sum of absolute local product/add rounding errors for that performed row. Every quantity is decoded rational data, including subnormal cases. These are computable, pointwise bounds; they do not authorize a commit, establish all-time small error, or replace raw-word equality.

The certificate refusal probes here address complete-domain issuance. The separate transaction verifier checks malformed/tampered/recomputed certificates, stale versions, changed domains/sites/graphs/policies/schedules, and rollback of failed live commits. No digest is treated as proof that a user-supplied domain is global. The reference uses a small fixed trusted registry, not a general verifier for arbitrary program invariants.

All counterexamples preserve the distinction between a false stronger claim and the conditional results actually proved in A3. There is no conclusion that every floating patch fails, no extension to arbitrary hardware/compiler behavior, and no P2-A4 implementation in this catalog.

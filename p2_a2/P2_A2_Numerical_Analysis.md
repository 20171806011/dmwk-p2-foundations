# P2-A2 — Numerical projection, storage and execution analysis

This document separates an exact rational projector, the decoded value of a numerical or stored projector, the arithmetic used to form an update, its actual stored effect, and the execution of the old and new matrices. The numerical implementation is [numerical_projection.py](numerical_projection.py); finite experiments are in [verify_numerical_cases.py](verify_numerical_cases.py). The four theorem statements are in [P2_A2_Theorems.md](P2_A2_Theorems.md).

## 1. Objects and arithmetic contract

Let H be a rational generating matrix whose column space is the protected global activation space or a proved superspace, and let P be its exact orthogonal-complement projector. A sample-only H cannot supply a global protection claim. All shared call sites use the same physical column coordinates. Bias is fixed at zero in the implemented dot products; a fixed separately stored bias can be included in the mathematical error accounting, but changing it requires an explicitly augmented parameter model.

The following objects are distinct:

- P: the exact rational projector constructed by exact elimination.
- Q=P+E: the exact decoded rational value of a numerical/quantized projector. Q need not be an orthogonal projector.
- G: the declared proposal matrix, interpreted as exact values of its supplied coefficients.
- Dhat=GQ+C: the actually computed candidate, with C accounting for candidate-product arithmetic. Any input conversion not already included in G or Q must be accounted for separately.
- W: the exact decoded value of the original stored weights.
- W'=RNE_F(W+Dhat): the final stored result under the explicit single-final-rounding commit contract.
- S=W'-(W+Dhat): commit/storage error; Deff=W'-W is the actual effective update.

For BF16 and FP32, rounding is nearest, ties to even. NaN and infinity inputs and results that round to infinity are rejected. Gradual underflow is modeled, and arithmetic zero results are normalized to +0. The standalone rational-matrix interface constructs canonical stored zero words; the raw dot interface additionally accepts signed-zero inputs and normalizes arithmetic output zeros. Signed-zero distinctions are not inferred from rational equality alone.

All dot products have zero bias and perform each product followed by one accumulator addition in ascending index order. FP32 uses actual NumPy float32 scalar multiplication/addition, individually checked against exact rational RNE by the unchanged P1 C3 helper. BF16 uses that helper's software rational RNE, not native BF16. FMA, reassociation and changed reduction trees are not accepted by this executor's policy selector.

The stored-operand interface rejects a rational W or h that is not exactly representable in the chosen format rather than silently rounding it inside a claimed certificate. Projection quantization and SVD input conversion are explicit earlier operations. The ideal commit can accept a rational candidate that cannot itself be stored: only the exact sum W+Dhat must round finitely. For example, W=-Fmax and Dhat=2Fmax commit to Fmax. An optional native-addition probe is performed only when both operands are stored; failure to represent Dhat alone does not narrow the declared final-rounding commit domain.

## 2. A nonrepresentable projector need not leak on its protected space

For H=(1,1,1)^T, P=I-J/3 contains non-dyadic thirds and cannot be stored exactly in either format. However, let s=RNE_F(1/3). Correct rounding and binary scaling give RNE_F(2/3)=2s here, so

$$
Q=s(3I-J)=3sP.
$$

Therefore QH=0 exactly even though Q differs from P and is not idempotent. This is why the requested thirds example must be measured rather than described as an inevitable kernel failure.

The executed records show:

| Format | Exact squared Frobenius error of Q-P | Exact QH | Ordered FP QH |
|---|---:|---:|---:|
| BF16 | 1/131072 | zero | zero |
| FP32 | 1/562949953421312 | zero | zero |

The exact idempotence defect is nonzero in both cases and is recorded as a rational value in the JSON. The nonzero row (1,-1,0) is exactly representable and annihilates H. Thus nonrepresentability of the orthogonal projector does not imply absence of representable null directions.

An additional global-coverage counterexample keeps this same rounded thirds projector. Declare the legal activation set to include both ones(3) and eta*ones(3), where eta is the target smallest positive subnormal. Both inputs belong to the same protected one-dimensional space and Q annihilates both in exact algebra. The ordered FP result is zero at ones(3) but (eta,eta,eta) at the second input: each diagonal product rounds to eta and each negative off-diagonal product rounds to canonical zero. Actual output words are `0x1` in every row for both formats, and the relative-only gamma certificate is refused. Thus even a zero floating residual at the generating basis vector cannot certify all legal stored activations in its span. This example does not claim that arbitrary linear combinations are legal; the two accepted input vectors are declared explicitly.

A genuine kernel-breaking example uses H=1_6, P=I-J/6. In every row, the exact decoded residual is

$$
\operatorname{RNE}(5/6)-5\operatorname{RNE}(1/6).
$$

It is -3/1024 in BF16 and -3/67108864 in FP32. The separately executed ordered residual depends on the diagonal's position:

| Format | Ordered residuals, rows 0 through 5 |
|---|---|
| BF16 | (-3/512, -3/512, -1/512, -1/512, -3/1024, -1/256) |
| FP32 | (-3/33554432, -3/33554432, -1/33554432, -1/33554432, -3/67108864, -1/16777216) |

This distinguishes projector storage error from further reduction error, even though all protected activations in this example are exact Boolean ones.

## 3. Numerical rank and actual SVD precision

The numerical proposal uses the rule

$$
r_{\rm num}=\#\{i:s_i>\max(\mathrm{atol},\mathrm{rtol}\,s_{\max})\},\qquad
Q_{\rm num}=I-U_{[:,0:r_{\rm num}]}U_{[:,0:r_{\rm num}]}^T.
$$

The singular values are compared after exact widening from binary32 to binary64 when necessary, so NumPy weak-scalar casting cannot silently round the recorded cutoff to binary32. A boundary regression at singular value one and cutoff 1-2^-30 checks this distinction.

Every case records the cutoffs, singular values, converted-input exact rank, original rational exact rank, condition estimate, residuals, output dtypes, dispatch and elapsed time. A computed cutoff that overflows is rejected; an unrepresentable condition diagnostic is null with an explicit reason rather than a JSON Infinity. Condition estimates from singular values are diagnostics, not certified intervals.

### Important implementation finding

In the installed NumPy 2.3.5 public `numpy.linalg.svd`, a float32 input is promoted internally to double by `_commonType`; the result is then cast back to float32. Merely observing float32 outputs does **not** establish a single-precision SVD computation.

The FP32 experiment therefore explicitly invokes the version-specific compiled gufunc `numpy.linalg._umath_linalg.svd_f` with signature **`f->fff`**, checking that this signature exists and that all outputs are finite float32 arrays. The FP64 experiment uses the public API with float64 input, whose pinned implementation selects `d->ddd`. This is an explicit precision-dispatch observation, not a proof of the entire compiled LAPACK library or processor. Private API stability beyond the recorded NumPy version is not promised. BF16 results are obtained by quantizing input/proposal values; no BF16 SVD implementation is claimed.

For H=diag(1,2^-30), exact rank is two and the exact condition number is 2^30. Both tested precisions report numerical rank one with rtol=10^-6 and two with rtol=10^-12. Thus a threshold can invent apparent remaining capacity in a genuinely full-rank protected space.

For H=((1,1),(1,1+2^-30)), the original rational matrix has rank two. FP32 input conversion changes it into a rank-one all-ones matrix. The single-precision SVD nevertheless reports a small nonzero second singular value, approximately 1.3491e-8. At the two tested thresholds it reports rank one or two. The latter does not certify exact rank of the converted input. The estimated finite condition ratio also does not overturn the converted input's exact singularity. FP64 conversion retains the small original direction in this particular fixture.

Sign flips and orthogonal changes of a basis cancel in UU^T in exact arithmetic. Finite computation of that product has its own error. The tests include an exact rational orthogonal basis rotation and one concrete sign-flip comparison; no bitwise equality of every LAPACK basis choice or degenerate singular subspace is promised.

A small QH residual is insufficient by itself to bound Q on every unit vector of col(H). With H=diag(1,epsilon), Q=diag(0,1), the residual norm is epsilon but Qe_2=e_2. To use R=QH for a particular h=Hc, one needs a bound on c. A full-column basis B permits c=(B^T B)^-1 B^T h; an exact bound on this left inverse supplies the missing conditioning factor. Redundant H must not be inverted as though it had full column rank.

## 4. T3: separated, computable perturbation bounds

For h in the protected space, Ph=0. Exact algebra gives

$$
D_{\rm eff}h=GEh+Ch+Sh.
$$

Let e(W,h) be the actual fixed-order execution error relative to the exact dot products of the same stored operands. Then

$$
\widehat y(W',h)-\widehat y(W,h)
=GEh+Ch+Sh+e(W',h)-e(W,h).
$$

Consequently,

$$
\|\widehat y'-\widehat y\|_2
\le (\|G\|_2\|E\|_2+\|C\|_2+\|S\|_2)\|h\|_2
+\|e(W',h)\|_2+\|e(W,h)\|_2.
$$

The implementation uses exact rational Frobenius squared norms as spectral-norm upper bounds. A dyadic ceiling of each square root is computed with integer square root and then verified by an exact rational squared comparison. This avoids treating `numpy.linalg.norm` output as a rigorous upper bound. The certificate records every component, the exact separated identity, the observed output-difference squared norm, and the exact final comparison against the squared rational bound.

This is a **pointwise** certificate for the supplied stored h. A uniform claim over all legal inputs requires a proven input norm bound and uniform execution-error bounds, or complete coverage of the finite legal activation set. One measured residual is not an all-time certificate. A positive norm bound is not a bitwise zero-drift proof.

### Exact local error accounting, including subnormal results

For zero initial accumulator, write

$$
p_i=\operatorname{RNE}(w_i h_i)=w_i h_i+\rho_i,
\qquad
s_i=\operatorname{RNE}(s_{i-1}+p_i)=s_{i-1}+p_i+\sigma_i.
$$

As long as every operation is accepted finite, all values and errors are exact rationals. Telescoping yields

$$
s_n-\sum_i w_i h_i=\sum_i\rho_i+\sum_i\sigma_i,
\qquad
|e|\le\sum_i|\rho_i|+\sum_i|\sigma_i|.
$$

This bound remains valid with gradual underflow and does not assume that relative errors stay below unit roundoff. It is a posteriori but computable and exactly checkable for the particular execution. The FP32 native primitives are independently compared with exact RNE before their outputs are used.

If every performed product/addition additionally satisfies a relative error bound of u=2^-p and 2nu<1, a coarse standard product-of-perturbations argument gives

$$
|e|\le\gamma_{2n}\sum_i|w_i h_i|,
\qquad \gamma_{2n}=\frac{2nu}{1-2nu}.
$$

The factor bound follows by expanding at most 2n factors (1+delta), with |delta|<=u, and using their product's deviation bound gamma_2n; the weighted contribution of each exact product has no more factors than this. Absence of overflow and an appropriate no-underflow relative-error regime are sufficient conditions. The verifier also checks the actual per-operation relative inequalities before reporting this bound. If they fail, the gamma bound is **not** reported, while the exact local-error certificate remains available.

For eta equal to the smallest positive subnormal, eta*(1/2) rounds to +0. Its absolute error is eta/2, which violates u times the exact product for either tested precision. The executed case therefore refuses the relative-only gamma certificate and correctly retains the local absolute bound.

## 5. Commit quantization and representability distinctions

Take H=(1,1)^T, ideal update row (1,-1), and stored original row (2^p,0). The ideal update is exactly null on H and its coefficients are representable. Nevertheless, RNE(2^p+1)=2^p, so the stored result is (2^p,-1), the actual effective update is (0,-1), and its protected residual is -1. The old/new ordered outputs are 2^p and 2^p-1. Both formats execute this example and the full T3 accounting succeeds.

There is a further distinction between a standalone stored delta and a difference of stored endpoint weights. With a=2^p-1 and

$$
H=\begin{pmatrix}1&0\\a&1\\0&a\end{pmatrix},\qquad
v=(a^2,-a,1),
$$

the exact row v annihilates H, but v itself cannot be stored in one p-bit word per coordinate. The endpoint rows W=(-1,0,0) and W'=(a^2-1,-a,1) are both representable and W'-W=v. Tests establish those finite endpoint facts; the theorem document supplies the odd-significand argument for absence of any nonzero standalone representable row on this line. No floating execution invariance is inferred from this endpoint example.

## 6. Changed arithmetic graphs

For unit activations and row (2^p,1,-2^p,-1), left-to-right separate RNE gives -1, while the alternative tree that first pairs terms 0 with 2 and 1 with 3 gives zero. The alternative tree is measured separately and refused as the protected executor's policy.

For x=1+2^-k, y=1-2^-k and c=-1, use k=5 in BF16 and k=13 in FP32. Separate rounded product/add gives zero; one rounding of the exact product-plus-add gives -2^(-2k). The fused value is a software exact-RNE reference, not a claim of running native FMA. The fixed executor refuses FMA as an unsupported policy. A compiler optimization may be acceptable only if a separate proof establishes the required bit semantics for the relevant domain.

## 7. Executed coverage and costs

The numerical verifier currently records 256 explicit checks and 15 expected refusals, with zero unexpected failures. It includes four quantized-projector cases, 20 SVD cases (five fixtures, two precisions, two thresholds), 40 fixed-seed pointwise perturbation certificates, both zero-dot and arithmetic-graph counterexamples, commit/representability cases, and subnormal/special-value checks. Actual timings, each threshold and all recorded residuals are in the result JSON. The fixed random seed is 20261114; the random certificates do not establish a universal bound for every matrix.

Dense SVD and explicit projector formation have polynomial arithmetic cost in their explicit dimensions, with quadratic storage for the d-by-d projector and weights. An explicit rational projector additionally requires exact coefficient arithmetic and potentially large numerators/denominators; the exact reference records stored coefficient sizes. Matrix-free application through a basis avoids storing the full projector but still needs the basis and a Gram-system solve, and finite-precision application introduces a separate C error. The structural mask route has a different, explicitly reserved capacity and is analyzed in the main report. No speed or memory advantage is claimed from these small-instance timings.

The certified bounds here concern the fixed numerical model and the actual stored inputs. No native BF16, GPU/GEMM/FMA, concurrent memory, or complete LAPACK/NumPy/Python proof is supplied. Exact algebra, numerical boundedness, and structural bit-exact authorization remain separate results.

# P2-A2 — Counterexamples and failure mechanisms

The eight requested classes are covered below. Evidence refers to the actual aggregate [verification_results.json](verification_results.json), not merely a proposed test. `sections.exact_algebra` contains exact rational checks; `sections.numerical_bounds.sections` contains numerical probes; `sections.structural_bit_exact.formats` contains the finite structural executions. The record reports successful detection of these counterexamples, not failures that were ignored.

Universal algebra statements have separate proofs in [P2_A2_Theorems.md](P2_A2_Theorems.md). Finite execution probes establish only their stated inputs, formats and operation schedules. BF16 arithmetic is software RNE. FP32 dot products use actual scalar NumPy operations checked against exact rational RNE. Neither native BF16 nor GPU execution is claimed.

## Coverage index

| Class | Refuted inference | Recorded evidence key |
|---|---|---|
| C1 | A protected space always leaves a nonzero exact linear update | `exact_algebra.counterexamples.C1_full_rank_no_nonzero_update` |
| C2 | A local null projection is safe for every shared call site | `exact_algebra.counterexamples.C2_merged_calls_full_rank_local_projection_unsound` |
| C3 | An exact projector is necessarily storable; or nonrepresentability necessarily destroys every null direction | `numerical_bounds.sections.quantized_projectors`, ID `C3_nonrepresentable_projector` |
| C3b | Rounding an exact projector necessarily preserves its kernel | Same list, ID `C3b_quantization_breaks_kernel` |
| C3c | Zero FP residual at the generating basis certifies zero on all legal activations in its span | Same list, `scaled_stored_input_probe`, ID `C3c_basis_probe_zero_but_other_legal_input_leaks` |
| C4 | Exact zero dot product implies zero ordered FP result | `numerical_bounds.sections.zero_dot_and_optimizations.zero_dot_cases` |
| C5 | SVD threshold rank is exact rank or certifies remaining capacity | `numerical_bounds.sections.svd.cases`, ID `C5_numerical_rank_misclassification` |
| C6 | An ideal null update remains null after writing W+delta to target storage | `numerical_bounds.sections.commit_and_capacity.commit_cases` |
| C7 | Every nonzero safe direction changes a selected AI target | `exact_algebra.counterexamples.C7_safe_but_no_learning_response`; structural format records |
| C8 | Reassociation or FMA substitution preserves the specified bit semantics | `numerical_bounds.sections.zero_dot_and_optimizations.optimization_cases` |

C3b and C3c are additional cases within the requested representation/execution boundary. The final capacity example below further distinguishes a standalone stored delta from a difference of stored weights.

## C1 — Full-rank protection removes exact linear freedom

Take H=I_3. Then V=R^3, the exact complementary projector is zero, and the space of square matrices satisfying delta h=0 for all h in V has dimension 3(3-3)=0.

To see this directly, apply delta to each standard basis vector: each column must be zero. The only such update is delta=0. This is a proof about the exact linear annihilation condition. It is not a classification of all possible observational equivalences of rounded nonlinear programs on a finite input set.

The exact verifier constructs this H and projector and records the zero capacity. The universal conclusion follows from T2, not from the single matrix test alone.

## C2 — Two locally deficient spaces can exhaust a shared matrix

One site receives inputs in V_1=span(e_1), while another site of the **same physical two-column matrix** receives inputs in V_2=span(e_2), in the same column frame. The local complementary projectors are

$$
P_{1,\perp}=\begin{pmatrix}0&0\\0&1\end{pmatrix},\qquad
P_{2,\perp}=\begin{pmatrix}1&0\\0&0\end{pmatrix}.
$$

Each has rank one. However, V_1+V_2=R^2 and the globally valid complementary projector is zero. In particular,

$$
P_{1,\perp}e_2=e_2\ne0.
$$

Using the first site's projector as a global update would interfere at the second site in exact algebra. Numerical equality of coefficients in two independently stored matrices would not make them shared; this counterexample explicitly fixes one shared identity.

The JSON records both local projectors, the global zero projector and the nonzero response at the other site. This is an exact rational counterexample, independent of floating rounding.

## C3 — Thirds are not storable, but this particular rounded kernel survives

Take H=(1,1,1)^T and

$$
P_\perp=I-\frac13\mathbf1\mathbf1^T.
$$

A finite binary rational has a reduced denominator that is a power of two, so neither 1/3 nor 2/3 is exactly representable. The exact projector is therefore not a BF16/FP32 stored matrix.

Nevertheless, this example does **not** exhibit a nonzero protected residual after coefficient rounding. Put s=RNE_F(1/3). For these normal values, RNE_F(2/3)=2s, and the rounded matrix is

$$
Q=s(3I-\mathbf1\mathbf1^T)=3sP_\perp.
$$

Thus QH=0 exactly. Because 3s differs from one, Q is not idempotent and is not the exact orthogonal projector.

Both formats were executed. The records show nonzero exact projector/idempotence error, zero exact decoded QH, and zero ordered FP QH for this specific input. The exact squared Frobenius error of Q-P is 1/131072 in BF16 and 1/562949953421312 in FP32.

The row (1,-1,0) is a nonzero, exactly representable null vector in both formats. Hence an unrepresentable orthogonal projector does not imply absence of representable null directions. Their safe storage and execution are still separate obligations.

### C3b — A genuine quantization-induced kernel failure

Take H=1_6 and P=I-J/6. Every decoded rounded row has the exact residual

$$
\operatorname{RNE}(5/6)-5\operatorname{RNE}(1/6).
$$

The measured exact residual is -3/1024 in BF16 and -3/67108864 in FP32. This is already a failure before matrix-vector reduction rounding is added. The actual ordered results additionally depend on the diagonal position:

| Format | Exact decoded row residual | Actual ordered results for rows 0–5 |
|---|---|---|
| BF16 | -3/1024 | (-3/512, -3/512, -1/512, -1/512, -3/1024, -1/256) |
| FP32 | -3/67108864 | (-3/33554432, -3/33554432, -1/33554432, -1/33554432, -3/67108864, -1/16777216) |

All input coordinates are one. The JSON preserves the coefficient words, exact residuals and separate multiply/add traces. The discrepancy between the two residual columns demonstrates that storage and execution are different error sources.

### C3c — A zero basis probe misses another legal input in the same span

Keep the rounded thirds projector Q from C3. Explicitly declare the accepted activation set to contain two stored vectors:

$$
a_1=(1,1,1)^T,\qquad a_2=\eta(1,1,1)^T,
$$

where eta is the smallest positive subnormal of the chosen format. Both are representable and generate the same protected one-dimensional span. This is an explicit two-input contract; it does not assume that every real linear combination is executable.

In exact algebra Qa_1=Qa_2=0. The first FP result is also zero. On a_2, each diagonal product, approximately (2/3)eta, rounds to eta. Each negative off-diagonal product, approximately -(1/3)eta, rounds to signed zero and is normalized to +0 under the declared policy. The ordered output is therefore (eta,eta,eta), with raw word `0x1` in every row in both formats.

The main verifier confirms both the exact zero residual and the nonzero actual result. It also confirms that the relative-only gamma certificate is inapplicable; the exact local absolute-error bound remains valid. Thus checking floating output on a spanning basis cannot by itself certify floating output for every other legal input in that span.

## C4 — Exact annihilation does not imply ordered floating annihilation

Let p=8 for BF16 and p=24 for FP32. Choose

$$
h=(1,1,1,1)^T,\qquad v=(2^p,1,-2^p,-1).
$$

Every operand and individual product is representable, and vh=0 exactly. Under zero bias, separate products and additions, and left-to-right accumulation:

1. The accumulator becomes 2^p.
2. Adding one is a nearest-even tie and rounds back to 2^p.
3. Adding -2^p produces canonical zero.
4. Adding -1 produces -1.

The recorded result is -1 for both formats, with the accumulator words and all FP32 native dtype/bit checks retained. Replacing 256 with 2^24 is essential for the FP32 instance.

This is a numerical counterexample, not authorization to modify the P1 small-coefficient graph with those weights. The coefficients exceed A4's gate-row contract. The example refutes an attempted implication from algebra alone; a valid execution guarantee needs its own admitted-update and operation-graph conditions.

## C5 — Numerical rank and exact rank can disagree

### Threshold-induced false capacity

Take H=diag(1,2^-30). Its exact rank is two and its exact condition number is 2^30. Both entries are exactly representable in the tested precisions. With the explicit rule

$$
s_i>\max(\mathrm{atol},\mathrm{rtol}s_{\max}),
$$

rtol=10^-6 reports rank one, while rtol=10^-12 reports rank two, in both measured SVD routes. The first threshold reports a complementary direction even though the exact annihilator is zero. A small residual does not repair that exact-rank claim.

For example, Q=diag(0,1) gives a small QH residual of size 2^-30, but Qe_2=e_2. Inferring a uniform action bound from QH requires controlling the representation coefficients or the conditioning of a full-rank basis.

### Input conversion and numerical noise

For

$$
H=\begin{pmatrix}1&1\\1&1+2^{-30}\end{pmatrix},
$$

the original rational rank is two. Conversion to FP32 changes H to the rank-one all-ones matrix. The explicitly single-precision SVD reports a small nonzero second singular value, approximately 1.3491e-8. With the two cutoffs it therefore reports rank one or two; neither a numerical threshold nor a finite condition estimate certifies the exact rank of the original and converted matrices simultaneously.

These tests use true single-real `f->fff` dispatch in the pinned NumPy gufunc. The public NumPy 2.3.5 float32 SVD interface promotes internally to double; output dtype alone would have mislabeled the experiment. FP64, FP32 and BF16-quantized inputs/proposals are distinguished in the record. No native BF16 SVD is claimed.

A further implementation regression uses singular values equal to one and a recorded binary64 cutoff 1-2^-30. Weak scalar casting could round that cutoff to FP32 one and change the comparison. The implementation widens the singular values exactly to binary64 before comparison, and the recorded rank remains two. This is an implementation fix, not a theorem about all SVD software.

## C6 — The actual stored update can violate an ideal null constraint

Let H=(1,1)^T, put a proposed update row v=(1,-1), and use an original stored row W=(2^p,0), with p=8 or 24. The ideal update annihilates H and is itself representable. It can be produced exactly by the complementary projector for this H.

The actual final storage is

$$
W'=\operatorname{RNE}(W+v)=(2^p,-1),\qquad
\Delta W_{\rm eff}=W'-W=(0,-1).
$$

Its protected residual is -1. The old and new ordered executions on H produce 2^p and 2^p-1, respectively. Both formats were executed and the pointwise T3 certificate accounts for the difference as commit error; the ideal projection constraint alone does not authorize this storage operation.

The implementation also distinguishes a final-rounding commit from a separately stored delta. W=-Fmax and an ideal candidate 2Fmax have a finite final sum Fmax even though the candidate alone is not storable. An optional native-addition probe must not incorrectly reject that declared ideal commit solely because it cannot first encode the candidate. The corrected API and a finite regression cover this domain distinction.

## C7 — A nonzero safe direction can be useless for the selected AI input

Three separate failures of an overly broad learning claim are recorded:

1. **The target is protected.** For V=span(1,1,1), the nonzero exact update P_perp annihilates h_A=(1,1,1). In fact every exact annihilator must do so. No protected target can change under that algebraic condition.
2. **An outside target is missed by a particular update.** Let V=span(e_1) in R^3 and choose delta=diag(0,1,0). This is a nonzero annihilator, but it also annihilates h_A=e_3, even though e_3 is outside V. T2 proves that a useful update exists for every outside target; it does not prove that every nonzero candidate is useful.
3. **Stored or executed response vanishes.** In the structural kernel, changing theta from one to two changes A input one from output one to two, while A input zero remains zero. Moreover, the nonzero ideal changes from one to 1025/1024 (BF16) or 67108865/67108864 (FP32) round back to the same stored theta=1, leaving effective change zero.

The first two are exact rational examples. The latter cases are actual finite structural executions and storage checks. The successful theta=1 to theta=2 witness establishes nontrivial changed output in that small system, not learning quality or usefulness for every task.

## C8 — A changed reduction tree or FMA changes the contract

Using the C4 row, the alternate tree

$$
(p_0+p_2)+(p_1+p_3)
$$

gives zero, whereas the specified left-to-right reduction gives -1. The alternate tree is explicitly evaluated in both formats; it is not silently substituted into the protected policy.

For the FMA comparison, set x=1+2^-k, y=1-2^-k, c=-1. Use k=5 in BF16 and k=13 in FP32. The executed separate product/add result is zero, while one rounding of the exact fused expression is -2^(-2k):

| Format | Inputs x,y,c | Separate result | One-round fused reference |
|---|---|---:|---:|
| BF16 | 33/32, 31/32, -1 | 0 | -1/1024 |
| FP32 | 8193/8192, 8191/8192, -1 | 0 | -1/67108864 |

The fused result is computed by an exact rational **software single-RNE reference**. Native FMA was not executed or certified. The fixed executor rejects `pairwise` and `fma` policy requests, and the structural updater separately rejects a changed execution policy. These cases show why a compiler's arithmetic graph must remain part of the safety contract.

## Additional capacity boundary — stored deltas versus stored endpoints

Let a=2^p-1 and

$$
H=\begin{pmatrix}1&0\\a&1\\0&a\end{pmatrix}.
$$

Its row annihilator is the line generated by v=(a^2,-a,1). The squared odd integer a^2 requires more than p significant binary bits. Every nonzero finite binary coefficient t is dyadic; the odd significand of ta^2 cannot fit in p bits. Thus this line contains no nonzero vector that can be represented as three standalone target-format coefficients. This is the separate exact representability lemma in the theorem document, not an inference from testing one vector.

Nevertheless,

$$
W=(-1,0,0),\qquad W'=(a^2-1,-a,1)
$$

are both stored finite rows in BF16 for p=8 and FP32 for p=24, and their exact decoded difference is v. The finite endpoint checks and exact annihilation are recorded under `numerical_bounds.sections.commit_and_capacity.stored_difference_capacity`.

No floating execution invariance is asserted for these endpoint rows. The example shows that three capacities differ: real/rational null directions, standalone representable delta arrays, and exact differences of representable stored weights.

## What these cases do and do not establish

The cases rule out several unconditional interpretations of orthogonality, approximate rank and finite testing. They do not invalidate the exact T1/T2 results, the explicitly bounded pointwise T3 statement, or the restricted structural T4 construction. Nor do they replace those proofs with experiments.

All admissibility constraints remain explicit: global or certified-superspace H rather than sample-only H, fixed physical sharing, accepted stored operands, numerical policy, canonical-zero behavior, and the specified graph/storage/scheduler. The numerical examples do not automatically satisfy the P1 compiler's small-coefficient D-program contract; they are deliberately used to test broader algebra-to-execution implications. Full GPU/native-BF16/concurrency and proof-assistant certification remain outside this round.

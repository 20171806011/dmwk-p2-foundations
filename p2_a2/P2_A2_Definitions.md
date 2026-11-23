# P2-A2 — Definitions and execution contracts

This round separates exact algebra, bounded finite arithmetic, and one structural bit-exact update mechanism. None of those categories is silently promoted to another. The original request and execution plan are preserved beside these files; the existing P1 and P2-A1 artifacts remain read-only dependencies.

## 1. Protected activation evidence

Fix a physical shared matrix W with d input columns, its column ordering, every call site, input preparation, fixed program D, legal initial states, legal input/history contract, state encoding, and scheduler. Unless explicitly stated otherwise, the target matrix is square, W in R^(d by d), with d>=1. A mathematical rectangular extension has k output rows and the same input-space construction, but does not change the reference's advertised shapes.

Let A_D be the union of numeric input activations at all protected calls of this matrix over all admitted finite execution prefixes, using the P2-A1 definitions. All matrices and vectors in exact algorithms have rational entries; accepted finite BF16/FP32 words decode to dyadic rationals. The real vector space is used for Euclidean orthogonality and norm statements. Rational and real ranks agree, but the sets of rational and real vectors are not identical.

Supply H in Q^(d by m) and label its evidence:

- **Exact global space:** col_R(H)=span_R(A_D).
- **Proved superspace:** span_R(A_D) is contained in col_R(H), with a declared containment proof or complete finite model certificate.
- **Samples only:** H contains some observed activations without a proved upper inclusion. Its projector is an algebraic object, but does not justify a global protection claim.

Set V=col_R(H), r=rank_Q(H)=rank_R(H). Duplicate, zero and dependent columns are allowed. An empty column family has r=0. Sharing requires merging all call-site activation generators in the same physical column frame before projection; equal coefficient values alone do not identify shared parameter storage. A larger proved V is conservative: it may reduce available update directions but cannot invalidate annihilation of A_D.

The proof supplied for H remains conditional on the fixed original program and all P2-A1 execution premises. A matrix update may change later activations or control flow. A single-call algebraic relation at original activations does not by itself certify a modified whole program. T4 uses a separate structural argument to avoid that circularity.

## 2. Exact projectors and matrix updates

Select a full-column-rank B in Q^(d by r) spanning V. For 0<r<d define

$$
P_D=B(B^T B)^{-1}B^T,\qquad P=P_\perp=I_d-P_D.
$$

If r=0, define P_D=0 and P=I_d. If r=d, define P_D=I_d and P=0. The formula with B also works for r=d, but the explicit edge case avoids any need to invert an empty matrix at rank zero.

Let N in Q^(d by (d-r)) be a full-column-rank basis for ker(H^T). Its Gram formula N(N^T N)^(-1)N^T gives the same P whenever 0<d-r; a zero-column null basis gives P=0. All exact inverses and products here are rational operations, never FP64 approximations labelled exact.

For a candidate G in R^(d by d), an ideal update is Delta=GP. In the reference exact computations, G is rational so Delta is rational. The algebraic annihilator space is

$$
\mathcal U_V=\{A\in\mathbb R^{d\times d}:Ah=0\text{ for all }h\in V\}.
$$

Its dimension is a dimension of a space of matrices, not the rank of one matrix. An element can have rank smaller than its parameter-space dimension. A nonzero ideal update need not be storable in the target format, affect a chosen A input, obey a compiler coefficient restriction, or preserve a floating execution.

Bias is fixed and stored separately unless a joint affine block has explicitly been declared. Joint bias updates require analyzing augmented activations (h,1) and a correspondingly wider block. Call-specific biases are not one jointly shared parameter. Algebraic homogenization must not reorder a bias-first floating reduction.

## 3. Three different projector/update representations

The following objects are recorded separately:

1. P: the exact rational orthogonal projector determined by H.
2. Q: a finite numerical approximation, decoded exactly from its stored values. It may arise from SVD, a rank cutoff, arithmetic forming I-QQ^T from a numerical basis, or target-format quantization. To avoid overloaded notation, numerical basis matrices are denoted U_r, while Q denotes the resulting approximate projector.
3. D_hat: the actually generated candidate increment. If its intended algebraic value is GQ, define the exact decoded generation error A_gen=D_hat-GQ.
4. W': the actual finite stored replacement matrix produced by the declared commit procedure. Define S=W'-(W+D_hat), and the effective increment Delta_eff=W'-W.
5. y_hat(W,h): the result of the specified execution graph, rather than an unrounded product or a separately computed Delta_eff h.

All differences in this list mean exact rational/real differences of decoded finite values. They are not additional target-format subtraction instructions. When a procedure rounds W+D_hat, it specifies whether the sum is formed exactly and rounded once, or whether an additional intermediate arithmetic format is used. That distinction belongs in S and its certificate. Rejection of overflow is distinct from a finite result with a small residual.

The decomposition is

$$
\Delta_{\rm eff}=GP+G(Q-P)+A_{\rm gen}+S.
$$

This accounting prevents an ideal Delta from being confused with the change actually written to storage. If candidate multiplication is exact rational, A_gen=0. If a target-format product is used, its observed or bounded error must be included.

## 4. Numerical policies

Each format fixes its precision p and exponent range: BF16 has p=8 and FP32 p=24, with the stated binary exponent conventions. The declared reference rounding is nearest, ties to even. Finite normal and subnormal values are admitted by the general arithmetic model; NaN and infinities are rejected. An operation whose correctly rounded result would be nonfinite is rejected rather than covered by a finite-error bound. Gradual underflow is modeled explicitly; flush-to-zero is a different, uncertified policy.

Numeric zero is distinguished from raw-word equality. Any canonicalization of negative zero is an explicit operation/policy. Bounds in R cannot distinguish +0 and -0 and therefore are not bitwise-safety certificates.

For a dot with fixed bias b, the reference order is

$$
s_0=b,\quad p_j=\operatorname{RN}_F(w_jh_j),\quad
s_j=\operatorname{RN}_F(s_{j-1}+p_j),\quad j=1,\ldots,d.
$$

Multiplication and addition are separate. A fused multiply-add, a reordered reduction tree, mixed intermediate precision, a BLAS/GPU kernel, or compiler fusion does not satisfy this contract merely by producing the same real formula. A numerical probe of a fused or alternative-order policy is labeled as a different policy, not as the reference backend.

The BF16 path is software RNE. FP32 claims are limited to actual local scalar operations whose dtype and words are checked against an exact rational rounding reference. A software calculation of a hypothetical FMA is not a native hardware FMA test. No native BF16, GPU, SIMD reduction, concurrency or full compiler certification is presumed.

## 5. Numerical rank and residual evidence

An SVD routine decomposes an explicitly converted finite array, not the exact rational H unless that conversion is lossless. The computation dtype, input conversion, output dtype, numerical library, singular values, absolute and relative cutoff rule, selected effective rank, projection residuals and observed time are recorded. Exact rank remains the rational-elimination result.

Changing singular-vector signs or applying an orthogonal basis change inside the same selected subspace leaves the ideal product U_r U_r^T unchanged. At a cutoff, however, changing the selected subspace changes the projector. Floating evaluation of equivalent bases can also change low bits. Numerical singular values and condition estimates are diagnostics unless an independently justified interval or exact certificate makes them bounds.

Exact rational evaluation of QH, Q-P, Q^2-Q and Q^T-Q certifies those residuals for the particular stored matrices. It does not certify that sampled H includes every protected activation. To turn QH into a bound on a general h in V, one needs a coefficient h=Hc and a bound on c, or a certified inverse/conditioning bound for a full-rank basis B.

## 6. Certificate and commit meanings

A result is labelled with one of the following meanings:

- **Exact algebraic:** exact rational identities or their stated real extension hold for H and the candidate, independently of whether the candidate is target-storable.
- **Numerically bounded:** finite decoded matrices and the declared arithmetic graph satisfy a computed residual/error bound, for a specified input or a proved input family. A pointwise measured certificate is not a universal certificate.
- **Structurally bit-exact:** a fixed layout and dependency graph make permitted writes absent from the protected computation's read dependencies; T4 proves identical protected traces under its exact contract.
- **Refused:** evidence, format, shape, source identity, version, permission, numerical acceptance, or execution-policy checks fail. A refusal is not a successful update and must leave the admitted stored state unchanged.

The safe reference is a trusted local API with complete validation before publication and a bit-preserving single-threaded snapshot/commit model. It is not an operating-system sandbox against arbitrary private-memory mutation. T4's concrete layout and allowed writes are specified alongside its proof and in `safe_update.py`; whole-program protected trace equality additionally fixes the D initial state, protected input sequence and trusted logical schedule.

## 7. Evidence types and stopping boundary

Theorems are handwritten mathematical arguments with explicit hypotheses. Exhaustive checks cover only their declared finite domains; random checks cover only their recorded fixed-seed instances. Any finite SMT or proof-assistant evidence must be separately identified if actually executed. Hashes bind source/result identities but do not prove correctness. No finite run substitutes for the all-finite-time induction in T4.

This round ends after P2-A2 delivery and coordinator handoff. It does not implement P2-A3 or the full historical coordinate migration protocol.

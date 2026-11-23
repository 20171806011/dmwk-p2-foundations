# P2-A2 — Exact projection and executable-safety theorems

All statements use [Definitions](P2_A2_Definitions.md). These are handwritten proofs, not proof-assistant results and not conclusions inferred solely from finite tests. The initial T1/T2 derivation below was saved before numerical experiments; later sections integrate the separately specified numerical and structural contracts.

## T1 — Exact orthogonal projector existence and uniqueness

**Statement.** Let H in Q^(d by m), V=col_R(H), and r=rank(H). The exact projector P defined in the Definitions is rational and satisfies

$$
P^2=P,\quad P^T=P,\quad Ph=0\ (h\in V),\quad
\operatorname{im}P=V^\perp,\quad\operatorname{rank}P=d-r.
$$

It is the unique Euclidean orthogonal projection onto V-perp. If N is any rational full-column basis of ker(H^T), then P=N(N^T N)^(-1)N^T when d-r>0, with the zero-column result interpreted as zero. Repeated or zero columns in H and a different exact basis do not alter P.

**Proof for 0<r<d.** A full-column-rank rational basis B exists by exact elimination. For every nonzero x in R^r,

$$
x^T B^T Bx=\|Bx\|_2^2>0.
$$

Thus K=B^T B is positive definite and invertible; its inverse is rational by exact elimination (or the adjugate/determinant identity). K and K^(-1) are symmetric. Write D=BK^(-1)B^T. Then

$$
D^T=D,\qquad D^2=BK^{-1}(B^TB)K^{-1}B^T=D.
$$

Its image is contained in V because its left factor is B. Conversely D(Bx)=Bx, so its image is V and it is identity on V. A vector z orthogonal to V has B^Tz=0 and hence Dz=0. Every vector y has the decomposition y=Dy+(y-Dy); the first summand belongs to V and the second satisfies B^T(y-Dy)=0. The intersection V intersect V-perp is {0}, since a vector in it has zero squared norm. Therefore this is the unique orthogonal decomposition.

Set P=I-D. Symmetry follows from that of D, and P^2=I-2D+D^2=I-D=P. It is zero on V and identity on V-perp. Consequently its image is V-perp, whose dimension is d-r, establishing its rank. Any Euclidean orthogonal projection onto V-perp sends the unique decomposition v+z to z; it must equal P on every vector, proving uniqueness.

The columns of N span ker(H^T)=V-perp. Applying the same Gram argument to N makes N(N^T N)^(-1)N^T the orthogonal projection onto V-perp, hence it equals P by uniqueness. Different bases and redundant H columns preserve V, so they preserve that same unique projector. ∎

**Degenerate cases.** If r=0 then every column of H is zero (including an empty column set), V={0}, V-perp=R^d and P=I. All identities hold and rank(P)=d. If r=d then V=R^d, V-perp={0}, and P=0; all identities hold and rank(P)=0. When B is square invertible, its Gram formula also gives D=I, consistently with this definition. No inverse of a zero-size Gram matrix is needed for these cases. ∎

**Rational/real agreement.** The projector entries are rational. Its action on Q^d gives the rational annihilator, and extending scalars to R gives the Euclidean orthogonal complement. This is not a claim that all real update entries can be stored as finite binary floats.

## T2 — Complete update parameterization, capacity and response

**Statement.** For any G in R^(d by d), Delta=GP annihilates V. Conversely every A that annihilates V satisfies A=AP. Thus

$$
\mathcal U_V=\{GP:G\in\mathbb R^{d\times d}\},\qquad
\dim\mathcal U_V=d(d-r).
$$

Every such update has rank at most d-r, and if rank(G)<=k then rank(GP)<=min(k,d-r). For any h_A outside V and any prescribed nonzero y in R^d, there is a nonzero rank-one update in this space with Delta h_A=y. If h_A belongs to V, every update in the space instead gives Delta h_A=0.

**Proof.** If h belongs to V, T1 gives Ph=0, so GPh=0. Conversely let A vanish on V. For any x, x=(I-P)x+Px and (I-P)x belongs to V. Applying A gives Ax=APx; since this holds for every x, A=AP.

A row of A annihilates V exactly when its transpose lies in V-perp. Choose any basis of that (d-r)-dimensional space. Each of d rows then has independently d-r scalar coordinates. This is a linear bijection from R^(d by (d-r)) to U_V, proving dimension d(d-r). Equivalently, if N is a full-column basis of V-perp, every A is uniquely C N^T for some C in R^(d by (d-r)); N need not be orthonormal for this parameterization.

For any product GP, image(GP)=G(image(P)) has dimension at most dim(image(P))=d-r and also at most rank(G). This proves both rank bounds. The dimension of U_V is therefore different from the rank bound on each individual element.

For nontrivial response, set z=Ph_A. Since ker(P)=V, h_A outside V implies z is nonzero. By symmetry and idempotence,

$$
z^T h_A=h_A^TPh_A=\|Ph_A\|_2^2=\|z\|_2^2>0.
$$

Define Delta=y z^T/||z||_2^2. Its row factor z belongs to V-perp, so it annihilates V. It gives Delta h_A=y and is nonzero of rank one because y and z are nonzero. If H,h_A,y are rational, this construction is rational. If h_A belongs to V, annihilation directly forces zero response. ∎

**Boundary cases and restrictions.** At r=d, U_V={0}; no nonzero globally linear annihilating update exists. At r=0, U_V is the full d-by-d matrix space. A nonzero update can still be useless on a particular h_A outside V if its kernel happens to contain h_A; existence of an effective update does not mean every candidate is effective. Target storage, masks, bounds, sparsity and execution certificates may shrink the usable set further.

**Conservative H.** If the true protected span V_true is contained in V, then U_V is contained in U_V_true. A proved superspace sacrifices capacity but remains algebraically protective. A sample-only subspace has the reverse containment and permits directions that can affect unseen protected inputs. Local spaces must be summed before applying this statement to a shared matrix.

## T3 — Certified decomposition of numerical perturbation

**Statement.** Fix accepted finite decoded W, G, Q, D_hat and W' and a protected h in V. Let

$$
E=Q-P,\quad A_{\rm gen}=\widehat D-GQ,\quad
S=W'-(W+\widehat D),\quad\Delta_{\rm eff}=W'-W.
$$

With exact products and differences of those decoded values,

$$
\Delta_{\rm eff}h=GEh+A_{\rm gen}h+Sh.
$$

For the specified old and new execution graphs with the same fixed bias, define numerical execution errors e=y_hat(W,h)-(Wh+b) and e'=y_hat(W',h)-(W'h+b). Then

$$
\|\widehat y(W',h)-\widehat y(W,h)\|_2
\le (\|G\|_2\|E\|_2+\|A_{\rm gen}\|_2+\|S\|_2)\|h\|_2
+\|e'\|_2+\|e\|_2.
$$

Any rigorously computed upper bounds for the terms give a valid perturbation certificate for the declared input or proved input family. They do not imply equality of raw bits.

**Proof.** Add and subtract the exact GP and GQ values:

$$
\Delta_{\rm eff}=GP+G(Q-P)+(\widehat D-GQ)+[W'-(W+\widehat D)].
$$

Since h is in V, Ph=0. Multiplying by h gives the stated identity. The executed output difference equals Delta_eff h+e'-e because the fixed bias cancels. Apply the triangle inequality and submultiplicativity of the spectral norm to each term. Every equality precedes the norm estimate, so no independent-error, small-error or statistical assumption is needed. ∎

**Computable certificates without an unproved spectral norm.** For a rational matrix X, its squared Frobenius norm is the exactly computable rational sum of squared entries, and ||X||_2<=||X||_F. One may bound square roots upward by a rational enclosure, or use the looser exact rational bound ||X||_2<=sum_ij |X_ij|. Analogous vector bounds give a completely rational, conservative certificate. A floating SVD estimate of a norm is not itself a rigorous upper bound unless separately enclosed. Recorded exact residuals are statements about the particular decoded finite matrices; the P2-A1 evidence for global coverage of h remains a separate premise.

**Residual-based variant.** If h=Hc, then Qh=QHc, and

$$
\|GQh\|_2\le\|G\|_2\|QH\|_2\|c\|_2.
$$

This expression needs a bound on c, not just a small QH. For a full-column basis B, L=(B^T B)^(-1)B^T satisfies LB=I and h=BLh for h in V. Therefore

$$
\|GQh\|_2\le\|G\|_2\|QB\|_2\|L\|_2\|h\|_2.
$$

Exact rational L with certified norm bounds supplies one explicit alternative to an uncertified smallest-singular-value estimate. Poorly conditioned or rescaled generators can make a tiny raw QH residual misleading without this coefficient control. ∎

**Local rounding-error certificate.** For one admitted dot under the separate bias-first order, let its finite decoded products and sums be p_j and s_j. Define

$$
\rho_j=p_j-w_jh_j,\qquad \sigma_j=s_j-(s_{j-1}+p_j).
$$

Then

$$
s_d-(b+\sum_jw_jh_j)=\sum_j(\rho_j+\sigma_j),\qquad
|e_{\rm row}|\le\sum_j(|\rho_j|+|\sigma_j|).
$$

**Proof.** Substitute p_j=w_jh_j+rho_j into s_j=s_{j-1}+p_j+sigma_j, and sum over j. Adjacent s_j terms telescope, with s_0=b. The triangle inequality gives the bound. All decoded operands are finite rationals, so these residuals can be calculated exactly, including subnormals. No relative-error model is used. With a per-row bound beta_i, ||e||_2<=sqrt(sum_i beta_i^2), or the rational upper bound sum_i beta_i. Overflow/nonfinite rejection leaves this admitted finite theorem's domain; it is not assigned a fictitious finite error bound. ∎

**Optional gamma bound.** Suppose every multiply and add obeys fl(x op y)=(x op y)(1+delta) with |delta|<=u, with the stipulated order and no overflow or underflow invalidating that relative-error model. If 2du<1, define gamma_(2d)=2du/(1-2du). Expanding the recurrence expresses the bias and each exact product with at most 2d rounding factors. For a product of k<=2d factors, its deviation from one is bounded by gamma_k<=gamma_(2d): the bound follows by expanding absolute values and using (1+u)^k<=1/(1-ku). Thus

$$
|e_{\rm row}|\le\gamma_{2d}\left(|b|+\sum_j|w_jh_j|\right).
$$

This is a conservative sufficient bound, not a claim of the sharpest dot-product constant. It is not used across arbitrary subnormal/flush-to-zero behavior. A different reduction tree or FMA graph needs its own operation accounting. A measured per-input local certificate is not a uniform all-time bound unless its coverage or uniform hypotheses are separately proved. ∎

## T4 — Structural bit-exact update theorem

**Fixed construction.** The two tracks use the same immutable-bank representation of a 2-by-2 matrix and fixed bias,

$$
W_\theta=\begin{pmatrix}-1&+0\\+0&\theta\end{pmatrix},\qquad
b=(+1,+0),\qquad M=\begin{pmatrix}0&0\\0&1\end{pmatrix}.
$$

Here M is a write-permission mask enforced by checked indices; it is not an arithmetic mask multiplied against an untrusted update. The only writable word is theta. It must be an accepted finite BF16/FP32 word; the concrete updater rejects negative-zero proposals and admits only canonical +0 for a zero weight. The matrix layout, all other raw words, biases, format and graph/policy identities are protected.

The deterministic track has state q in canonical {+0,+1}, receives a canonical Boolean u, and prepares h_D=(q,+0). Its **fixed sparse graph reads W[0,0] and b[0] only**. On the old-state/input snapshot it forms

$$
n=\operatorname{RN}(b_0+\operatorname{RN}(W_{00}q)),\qquad
\bar u=1-u,\qquad
q'=\operatorname{RN}(\operatorname{RN}(\bar u q)+\operatorname{RN}(u n)).
$$

The occurrence of 1-u is the specified exact Boolean NOT primitive with its declared scalar operations. Products/additions have the stated separate RNE order and canonical Boolean zero outputs. The complete candidate q' is committed once. The A track prepares h_A=(+0,a), for canonical Boolean a, and its fixed sparse graph reads theta and b[1] only, returning the specified RNE evaluation of theta*a+b[1]. It cannot change D inputs, D state or D scheduling.

A permitted transaction validates its complete copied request against the trusted layout/mask, format, protected raw words, expected version and exact numerical-policy identifier before publication. A failed request leaves the current bank/version and protected state unchanged. An accepted request publishes a complete new immutable bank with only theta changed; it does not modify the old snapshot used by an in-progress logical step. Execution and publication are the declared single-threaded/serialized operations, not an unproved concurrent atomic memory protocol.

**Statement.** Under this fixed construction, two executions starting with the same admitted D state and receiving the same protected input sequence and trusted logical schedule have identical D raw-word states and protected outputs after every successfully completed finite number of steps, even if one receives any sequence of accepted theta updates. Each D state remains a canonical Boolean. The construction admits a nonzero stored update with a changed legal A response.

**Proof of one-step D closure.** For q=0 or 1, W00=-1 and b0=1 give n=1-q exactly. Every operand, product and partial sum is one of -1,0,1, all exactly representable in the admitted formats; any sign on an arithmetic zero is handled by the specified canonicalization. Likewise ubar=1-u is exactly Boolean. If u=0, the two selected products are q and 0, so q'=q. If u=1, they are 0 and n, so q'=1-q. Thus all admitted (q,u) pairs yield canonical Boolean next states, and the arithmetic matches the fixed discrete toggle/hold semantics. Both alternatives read the same old q, not a partially updated register.

**Proof of update noninterference.** A permitted write changes none of the words read by the D graph. The graph, numerical policy and input/state snapshot also remain fixed. Induct over the fixed sequence of D scalar instructions: their initial operands have the same bits, each instruction and its rounding/zero policy are identical, and therefore each result has the same bits in the two executions. The complete next-state candidate and its bit-preserving commit consequently agree. A rejected transaction does not publish any candidate and changes no protected state. An accepted theta commit also leaves D state unchanged and preserves the same D read dependencies.

Now induct over any finite interleaving of admitted D steps and serialized update transactions with the same logical D inputs and schedule. Initialization agrees. Either an update preserves the protected projection, or the proved one-step relation preserves equal D states. The induction proves equal D traces for every finite completed prefix; it does not assert fault-free infinite hardware operation, liveness or unconstrained concurrency. ∎

**Nontrivial stored and observable update.** Take theta=1 and replace it with theta'=2. Both values are exactly storable in BF16 and FP32. The decoded update matrix has only Delta[1,1]=1, so it is nonzero. For legal a=1, the A output changes exactly from 1 to 2. For the protected calls, all h_D lie in span{(1,0)^T}, while Delta(1,0)^T=0. Therefore this example also fits the algebraic annihilator, but its bit-exact safety proof uses absence of mutable words from D reads, not a floating cancellation of Delta h_D. A one-word committed change, a nonzero algebraic direction and a changed A response are all present. The algebraic space for d=2,r=1 has dimension two, whereas this structural mask leaves one coordinate direction. The sufficient safe construction deliberately retains less freedom than the unrestricted algebraic parameterization. ∎

**Coverage and limits.** The all-input/all-time coverage for span{(1,0)^T} follows directly from the proved Boolean invariant and declared input preparation; it is not a user-supplied sample label. A outputs for a=0 or 1 are finite when theta is finite under the stated gradual-underflow policy. There is no A-to-D feedback channel, unmodeled timing channel, shared mutable scratch state or arbitrary Python-private-memory adversary in this theorem. It protects the D projection, not A behavior or the entire kernel state/version. The sparse graph intentionally does not read the inactive row/column. A dense GEMV, a changed reduction/fusion policy, or a compiler that introduces extra dependencies requires a new contract/proof. This theorem does not show that general projected updates are bit-exact, and does not formalize the whole Python runtime or an optimized device backend.

## Coordinate covariance and matrix-free formulas

**Proposition.** Let Pi be a permutation matrix on the input coordinates, H'=Pi H, and P' the exact complementary projector for col(H'). Then

$$
P'=\Pi P\Pi^T.
$$

**Proof.** Pi is orthogonal. Pi P Pi^T is symmetric and idempotent. Its image is Pi V-perp=(Pi V)-perp: inner products are preserved by Pi. T1 uniqueness identifies it with P'. ∎

If outputs are not relabeled, h'=Pi h, W'=W Pi^T and G'=G Pi^T yield Delta'=G'P'=GP Pi^T and W'h'=Wh. If both square input/output coordinates are relabeled, W'=Pi W Pi^T, G'=Pi G Pi^T and Delta'=Pi Delta Pi^T; outputs transform by Pi. In neither convention should a projector be permuted alone while its input and patch coordinates stay fixed. These are exact algebra relations, not guarantees that finite reductions with permuted term order preserve original bits. No historical migration protocol is implemented here.

For the nonempty basis cases, without explicitly storing P its action is

$$
Px=x-B(B^TB)^{-1}B^Tx,
$$

or, using a null basis, Px=N(N^TN)^(-1)N^Tx. Correspondingly GP=G-(GB)(B^TB)^(-1)B^T. These identities follow by multiplying the exact formulas; use P=I or P=0 directly for an empty-basis edge case. They do not authorize reassociating a target-format execution without new numerical accounting.

## Complexity and representability boundaries

Exact elimination and Gram inversion use a polynomial number of rational field operations in the explicit d-by-m input size; a dense implementation has the familiar cubic-size elimination/inversion terms, plus matrix products. Rational field operations are not unit-cost bit operations. Clearing denominators, intermediate numerator/denominator growth, gcd reduction and determinant sizes matter. Fraction-free elimination or minor bounds give polynomial bit-complexity in explicit rational input length; a practical implementation should also record observed stored coefficient bit lengths. No fixed numerical condition number is needed to decide exact rational rank, although exact arithmetic cost can grow.

Explicit projectors require d^2 entries. A basis-and-Gram representation instead stores order dr+r^2 entries and applies P without forming it; the complement basis alternative uses d(d-r)+(d-r)^2 entries. A dense G already has d^2 entries, independently of projector storage. Numerical SVD has separate floating-operation and workspace costs and uses threshold-dependent effective rank, not a certified algebraic rank. A structural mask may be implicit and checked in time proportional to the allowed writes, but an actual transaction still has its validation, snapshot and storage costs.

A rational projector need not be binary representable. For V=span(1,1,1), P has diagonal 2/3 and off-diagonal -1/3. Those entries are not finite binary numbers, because a reduced rational has a finite binary expansion only if its denominator is a power of two. This does not prohibit representable null vectors such as (1,-1,0). Particular target rounding may preserve P's annihilation while destroying idempotence; the actual residual must be measured, not guessed from nonrepresentability alone.

A nonzero rational null vector can be scaled to an integer vector algebraically, but fixed exponent/precision ranges, coefficient restrictions and storage addition to W can still prevent an admissible nonzero effective patch. A real dimension count is not a count of all target-format storable updates. Structural admissibility and useful A response require additional premises, supplied only by T4's specific construction in this round.


## Optional capacity proposition — a rational nullspace can lack a nonzero storable increment

This proposition concerns general finite rational/FP input vectors, not the P1 A4 Boolean-only activation fixture. Let p be the significand precision, a=2^p-1, and let H have columns (1,a,0) and (0,1,a). All displayed H entries are exactly representable in the corresponding target format, and H has rank two. Solving H^T v=0 gives

$$
\ker(H^T)=\operatorname{span}\{(a^2,-a,1)\}.
$$

No nonzero vector in this line has all three coordinates individually representable as finite p-bit binary floats. **Proof:** if its last coordinate t is a nonzero finite binary value, write t=n*2^e with odd nonzero integer n. Its first coordinate is a^2*n*2^e, whose odd integer significand has bit length at least that of a^2, greater than p. No multiplication by a power of two removes an odd significand bit, so that coordinate cannot have a p-bit finite binary representation. The exponent-range restrictions can only remove additional candidates. ∎

This is not a theorem that no nonzero *effective* update W'-W exists. A difference of two finite words need not itself be a target-format word. For either p=8 or p=24, choose W=(-1,0,0) and W'=(a^2-1,-a,1). The first replacement word is representable because a^2-1=2^p(2^p-2)=2^(p+1)(2^(p-1)-1), whose odd significand has p-1 bits and whose exponent lies within both formats' ranges. Their exact decoded difference is (a^2,-a,1), the displayed null direction. For BF16 this is the concrete pair W=(-1,0,0), W'=(65024,-255,1), with difference (65025,-255,1). This is an algebraic/storage example, not a bitwise-safe execution update: execution still needs T3 or T4's separate conditions. Standalone increment representability, committed-word representability and executable safety are different questions.

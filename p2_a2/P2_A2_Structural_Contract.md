# Structural safe-update contract and proof checkpoint

This contract was derived before executing structural-update experiments. It is a sufficient construction for P2-A2-T4, not a statement about all algebraically orthogonal updates.

## Layout and observations

The shared stored matrix and fixed bias are

$$
W(\theta)=\begin{pmatrix}-1&+0\\+0&\theta\end{pmatrix},\qquad
b=(+1,+0).
$$

The write mask is the exact Boolean matrix `((0,0),(0,1))`; the implementation validates addresses/words rather than multiplying an arbitrary patch by a numerical zero mask. Only the bottom-right word may change. The other three weight words and both bias words are fixed, including their zero signs. Theta is any finite admitted BF16/FP32 word, with canonical +0 for a zero value. NaNs, infinities and negative-zero weight proposals are rejected; finite subnormals are admitted under gradual-underflow RNE.

The protected state q and input u are canonical +0/+1 words. Every tick snapshots q, u and the immutable weight bank, then follows the fixed sparse schedule:

1. `n = add(+1, multiply(W[0,0], q))`.
2. `ubar = add(+1, multiply(-1, u))`.
3. `keep = multiply(ubar, q)`.
4. `flip = multiply(u, n)`.
5. `q_next = add(keep, flip)`.

The named add and multiply operations are separate correctly rounded RNE operations in the target format, with the fixed zero canonicalization policy. Every intermediate here is in {-1,0,1}. All outputs and state words are canonical Boolean encodings. The complete `q_next` is committed after evaluation; no partial state overwrite is visible through this API.

The logical matrix-call activation is `(q,+0)`, but the protected graph loads only the first row's nonzero protected term. It does not evaluate mutable terms multiplied by zero. The static sparse schedule, input gathers and output selection are part of the contract; conversion to a dense GEMM, FMA, reassociated reduction, dynamically changed mask or different schedule is not silently authorized.

The A call has input `(0,a)` with canonical Boolean a. Its fixed sparse observation loads only theta and evaluates `add(+0, multiply(theta,a))`. It returns the second row's result and does not feed it into the protected input. Multiplication by a=0 or a=1 has a finite result for every admitted theta, including maximal finite values and subnormals, subject to the stipulated backend contract.

## Transaction and trust boundary

An update request contains a complete candidate weight tuple, format, policy identifier and expected version. The implementation validates exact built-in types, dimensions, every finite raw word, canonical zeros, the protected slots and the version before publishing a new immutable bank. A refusal leaves weights, D state, tick count and version unchanged. A public snapshot consists only of immutable tuples, strings and integers; it is not an alias to a mutable dataclass. Reinitializing a live kernel is refused.

This is a trusted local, single-threaded API with fixed implementation/runtime functions. It does not defend against arbitrary access to private Python memory, module monkey-patching, an untrusted interpreter, concurrent calls, hardware faults, process compromise or OS-level interference. A caller's sample residual or claimed certificate does not bypass the independent structural validation. Only this declared structural route is accepted by the updater.

## Proof of T4 for this structure

An accepted update changes theta alone. Consequently every word read by every protected primitive is unchanged. For fixed q and u, the first instruction has the same raw operands before and after any accepted update; determinism of the specified primitive gives the same raw result. Applying that argument in instruction order establishes equality of every protected intermediate and `q_next`. The elementary Boolean identities give `q_next=q` when u=0 and `q_next=1-q` when u=1, so the state invariant is preserved. Every update itself preserves q. Induction on the trusted schedule of ticks and successful updates therefore proves identical D traces for every finite prefix with the same initial q and input sequence. No cancellation involving theta is used.

For the A observation, theta=1 and theta'=2 are distinct exact finite words in both formats. With a=1, the old and new outputs are respectively the exact words 1 and 2, so the nonzero update has a witnessed nonzero learning response while the protected trace is unchanged.

With both legal initial states admitted, the protected activation space is span(e1). Its unrestricted algebraic update space has dimension 2 for a 2-by-2 matrix. The structural mask permits only the theta coordinate and thus has dimension 1: it is a strict sufficient subset, not a maximal-capacity construction. A target A input lying in the protected space or with a=0 need not respond to this update. Nonzero safe parameter freedom is not a claim of useful response on every possible learning input.

The proof is handwritten. Executed finite tests, backend scope and independent review are reported separately. It is not a full machine-checked proof of the Python updater or its arithmetic dependencies.

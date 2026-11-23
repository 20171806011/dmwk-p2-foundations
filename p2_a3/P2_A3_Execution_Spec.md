# P2-A3 executable certificate contract

This specification follows the saved mathematical checkpoint. The implementation is [certificate_kernel.py](certificate_kernel.py). It extends A2's sparse read-exclusion witness with a dense, completely checked finite-domain witness. It does not turn a numerical residual or a caller's claimed global span into permission to commit.

## Three separate meanings

An exact algebra report states that the exact decoded effective difference annihilates a rational generating matrix and hence its rational/real span. A pointwise numerical report bounds a specified actual execution difference. Neither report is accepted as the bitwise certificate below.

The executable claim is `bitwise_complete_registered_domain_v1`. It certifies equality of the full output words for every activation at every protected site in one fixed registry entry, together with the concrete state closure where applicable. It is not a claim over every real linear combination. In particular, exact annihilation is reported separately and is not required for this finite-word claim: real products can differ while each admitted finite execution rounds to the same words. Conversely, exact annihilation does not establish this claim.

## Fixed trusted registry

The caller names a supported model; the checker constructs its complete descriptor independently. The caller cannot provide a sample list and label it exhaustive. Each registry entry fixes one physical shared matrix, shapes, all protected sites, legal raw activations, fixed zero bias, operation graph, format, initial states, input histories, state invariant and schedule. The finite domains are declared inputs to a small program with a proved closure argument; they are not inferred from empirical observations.

| Model | Protected sites/domain | Live state |
|---|---|---|
| `duplicate_feedback_v1` | `state`: `(q,q)`; `input`: `(u,u)`; both bits independently range over canonical zero/one | Boolean q, all finite Boolean input histories |
| `split_feedback_v1` | `state`: `(q,q)`; `input`: `(u,0)` | Same Boolean q and histories; the merged real span is full rank |
| `thirds_two_inputs_v1` | One 3-vector site with exactly `ones(3)` and `eta*ones(3)`, eta the smallest positive subnormal | Stateless local-call certificate only |
| `commit_rounding_v1` | One 2-vector site with exactly `(1,1)` | Stateless local-call certificate only |
| `shared_axis_v1` | One site for e1, another for e2 | Stateless local-call certificate only |

The stateful baseline weights are I2. The thirds baseline is the zero 3-by-3 matrix. The commit-rounding baseline is `((2^p,0),(0,0))`, p=8 or 24. The axis baseline is I2. Stateless entries provide concrete refusal experiments and are not silently promoted to stateful-program certificates. `CertificateKernel` accepts only the two stateful registry entries.

## Arithmetic and dense program graph

BF16 and FP32 finite canonical-zero words are admitted. NaN, infinity and negative-zero storage proposals are refused. Rounding is nearest, ties to even, with gradual underflow and explicit arithmetic-zero canonicalization. Each protected matrix call evaluates every row and every column in ascending column order:

`s=+0; for j: p=RN(W[i,j]*h[j]); s=RN(s+p)`.

No zero term is skipped. Multiply and add remain separate. Neither reassociation, FMA, mixed precision, fused GEMM, flush-to-zero nor a different graph identity is accepted by this policy. A nonfinite result or a failed primitive audit causes refusal before publication.

For a tick, both calls use one old `(weights,q)` snapshot. Their full two-word outputs are protected observations. If their first coordinates are a and b, the state update uses the fixed floating graph

`product=a*b; twice=2*product; negative=(-1)*twice; summed=a+b; q_next=summed+negative`.

For legal bits this is XOR, all intermediates lie in `{-2,-1,0,1,2}`, and the result is canonical zero/one. The complete next state is committed once after both calls and the XOR graph. Runtime guards additionally refuse an invalid Boolean output/state.

The checker does not trust closure from the current state alone. For each stateful certificate it checks all four pairs `(q,u)` and the full outputs at both sites. It also verifies that both old and new endpoints match the registry's baseline output map on all legal activations. Thus an arbitrary old endpoint cannot be used to assert the Boolean program invariant. A live kernel starts at I2 and each accepted update preserves this same invariant.

The A domain of the stateful models is `{e1,e2,0}`. Its full dense output is returned but cannot enter D state or the protected input through this API. A different external feedback controller would require new premises and a new registry/proof.

## Nonzero executable witness

For the duplicate model,

\[
W=I_2,\qquad W'=\begin{pmatrix}0&1\\2&-1\end{pmatrix}.
\]

On each legal protected activation `(t,t)`, both endpoints produce `(t,t)` with exactly representable intermediates. All changed entries are actually evaluated when t=1. The effective difference `[[-1,1],[2,-2]]` also annihilates the global protected line in exact algebra. At A input e1 the output changes from `(1,0)` to `(0,2)` in both formats. This is an observed nonzero output response, not a claim of learned performance or optimization quality.

The split model uses an additional protected input direction. The same strong patch is refused there. Separate subnormal examples may nevertheless be bitwise equivalent on its finite raw inputs despite nonzero exact residual; finite observational equivalence and exact real-span annihilation are different properties.

## Certificate contents and verification

`make_certificate(model_id, format, old_words, new_words, version=0)` is pure with respect to live kernels. It returns a bounded canonical JSON string only after all checks pass. Its payload includes:

- Exact schema and claim identifier; model, physical sharing, format, old/new raw endpoint matrices, and weight version.
- Exact rational effective difference as numerator/denominator pairs, derived from decoded stored endpoints rather than an ideal patch.
- The complete independently generated descriptor, including legal domain, all sites, state/invariant identities, graph, fixed bias, zero/rounding policy, schedule and absence of A-to-D feedback.
- Every protected site/activation old/new output comparison, all state/input closure cases where applicable, and separately computed exact residuals.
- SHA-256 identities of the descriptor, payload, this checker source and the imported P1 execution source.

Hashes identify files and records; they are not signatures, authorities or proofs. `check_certificate(text, model_id, format, old_words, version=0)` reconstructs the complete expected certificate from the trusted registry and actual endpoints and demands canonical byte identity. Recomputing a checksum after omitting a legal input, changing a result or relabeling a sample does not make the altered claim pass.

Only exact built-in primitive input types are allowed. JSON duplicate keys, nonfinite constants, unexpected shape/fields, altered metadata, noncanonical serialization and excessive text length are refused. Versions are nonnegative built-in integers less than 2^63, not booleans or floating values. Caller string/int/container subclasses cannot supply callbacks through validation. No caller audit object is accepted; the implementation creates its own audit containers.

The checker is deliberately incomplete: valid but unknown proof modes or domains are refused. It is not a general theorem prover for arbitrary invariants. The fixed trusted registry and implementation are part of the assumed correctness boundary. A hardware fault or arbitrary modification of private Python state/module code is not covered.

## Transaction, version and schedule

`CertificateKernel.prepare(new_words)` produces evidence against its current endpoint/version without mutation. `commit(text)` reads one immutable bank, checks the certificate against that exact current bank, allocates the receipt and new bank, and then publishes once. The version increments; D state and tick count do not change. Any refusal preserves the complete snapshot: weights, q, version and tick count. A stale certificate cannot be replayed after a successful commit, including a no-op commit.

A certificate may remain valid across a legal D tick when the weight version is unchanged: it covers the complete common state/input domain rather than only the state observed at issuance. No certificate binds or replaces external D inputs. The program theorem compares executions with the same admitted initial state, input sequence and trusted schedule.

`snapshot()` returns `(model_id, format, policy, schedule, version, weights, state_word, ticks)` as immutable primitive tuples. `d_tick(input_word)` returns `(full_state_call_output, full_input_call_output, next_state_word)`. The A observation is separate. Reinitialization of a live kernel is refused. Ticks are diagnostic host integers, not hidden input to D; no claim of unlimited physical counter/storage capacity is made. Version exhaustion explicitly refuses further commits.

The interface is serialized and trusted. It does not implement lock-free atomicity, concurrent proof validation/publication, OS isolation, protection against arbitrary private memory access or protection from process failure between instructions. Those are separate obligations.

## Backend and proof scope

The reused P1 arithmetic interface is read-only. BF16 is software exact-rational RNE. Actual local CPU FP32 scalar operations are checked against exact rational RNE and retain explicit dtype semantics. This does not certify native BF16, GPUs, an arbitrary BLAS/GEMM backend, compiler optimization or all CPUs. No prior-stage suite is launched by this checker.

For the concrete closed domain, the finite case check is exhaustive over its declared local operands and state/input pairs. The arbitrary finite-horizon conclusion uses the separate induction theorem and its premises. The Python checker and mathematical proof have not been verified in Lean/Coq; no finite experiment is labeled a complete machine proof.

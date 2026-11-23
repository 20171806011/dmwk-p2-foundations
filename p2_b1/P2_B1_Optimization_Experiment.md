# P2-B1 fixed optimization experiment

## Scope and outcome

This finite experiment demonstrates a nontrivial accepted optimization path under the selected `ALG_AND_BIT` endpoint contract. It also measures refusal and offline failure modes. It does not prove general optimizer convergence, useful task performance, generalization, optimal speed, or that every mathematically projected step has a representable accepted endpoint.

The actual run has **24 runs, 192 attempted steps, 1,013 main assertions, 75 accepted joint-contract commits, 21 joint-contract refusals, and 96 offline applications**. Sixty-one accepted commits change stored weights. Ninety-six paired authorized protected ticks agree with an unchanged reference peer. Proposal and actual endpoints receive 1,536 complete registered state/input-pair diagnostics in total. All unexpected-failure counters are zero. The run's wall-clock duration is recorded in `training_results.json`; it is not a benchmark. The random seed is **20261114**; every run uses the same input bits `[0,0,1,0,1,0,1,0]`.

The eight-step dense SGD path decreases exact decoded loss from `5/2` to `5/131072` in both BF16 and FP32, with eight accepted nonzero commits each. The reserved-column SGD path reaches zero loss at its first step. These paths establish existence of accepted output-changing optimization in these fixtures, rather than an all-frozen construction.

## Objective, layouts and legal domains

The target is `(0,2)`. Loss is computed with exact rationals **after decoding the actually executed target-format A output**, as `L(y)=((y0-0)^2+(y1-2)^2)/2`. It is not computed with an unconstrained high-precision surrogate output.

The dense shared bank starts at `I_2`, with protected state and input call activations `(q,q)` and `(u,u)` for canonical bits `q,u`. Both full two-component call outputs are protected. Its legal A probe is `e1`, initially producing `(1,0)`. Every diagnostic enumerates all four legal `(q,u)` pairs; this is the complete registered local domain, not an empirical activation sample.

The structural bank starts at `((1,0,1),(0,1,0))`. Its first two columns stay `I_2`; its third column is reserved. The two protected call sites use `(q,q,0)` and `(u,u,0)`. D has an explicitly fixed sparse arithmetic graph reading columns 0 then 1. A uses the full ordered three-column graph at `e3`, initially producing `(1,0)`. Pure admission validation can inspect all words; arithmetic read exclusion starts after that validation. This is not a claim that the entire Python instruction trace is independent of the reserve.

Both models use the inherited fixed XOR of the first outputs, same old-state snapshot and synchronous commit, with no A-to-D feedback. Legal initial state and external inputs are canonical bits. Experiments start at zero. The registered-domain proof and local certificate, not the one sampled input sequence, support the conditional arbitrary-finite-time induction stated in the theorems.

The dense and structural geometries, numbers of parameters and protected graphs differ. Their losses are not a fair performance ranking of two algorithms for an identical parameterization.

## Four routes and proposal arithmetic

1. **Unconstrained offline:** apply the raw staged optimizer increment and quantized endpoint in an isolated diagnostic bank. There is no live authority.
2. **Gradient-only projection offline:** project the gradient first, then run the optimizer including decay; quantize and apply in an isolated bank. There is no live authority.
3. **Final projection plus certificate:** compute the entire increment, project it onto the exact global annihilator, quantize the replacement endpoint, check the effective stored difference and full fixed-graph domain, then publish through the trusted B1 transaction only if both ALG and BIT hold.
4. **Structural final mask plus certificate:** retain only the third column of the final increment, quantize, check exact ALG and the fixed sparse registered execution contract, and publish through the same composite transaction.

The gradient is that of the continuous linear squared-loss extension evaluated at the decoded endpoint: errors occur only in the A probe's column. It is **not** the derivative of BF16/FP32 rounding.

Each optimizer runs for eight attempts with no clipping:

| Optimizer | Configuration |
|---|---|
| SGD | learning rate 1 |
| Momentum | learning rate 1/2; EMA coefficient 1/2; `m_new=(m+g)/2` |
| AdamW | learning rate 1/4; beta1 1/2; beta2 3/4; epsilon 1/1024; decoupled decay 1/8 |

All moments begin at zero. SGD, momentum, decay, exact projection and masks use rational arithmetic. AdamW moments, bias correction, square root, denominator, division and parameter step follow the separately specified host Python binary64 operation sequence, after which each finite result is decoded exactly to a rational. No cross-platform `sqrt`/power certification is inferred. Endpoint sums are computed exactly and rounded once to the target format. Protected execution then uses software BF16 round-to-nearest-even or CPU NumPy scalar FP32, with every primitive result audited against rational round-to-nearest-even; operations are separate multiply/add, use gradual underflow and canonical positive zero, and do not use FMA. The endpoint model is not an in-place BF16 optimizer kernel.

## Actual results

The accept/refuse columns apply to live routes; `0/0` for an offline route means **no authorization was requested**. `All D equal` reports all stored endpoints tested against the initial protected bank on every registered pair. Decimal loss is a convenience display; the full exact rational loss and raw output words are in the JSON.

| Format | Optimizer | Route | Accept/refuse | Final loss (approx.) | All D equal |
|---|---|---|---:|---:|---|
| BF16 | sgd | Unconstrained (offline) | 0/0 | 0 | No |
| BF16 | sgd | Gradient only (offline) | 0/0 | 3.81469727e-05 | Yes |
| BF16 | sgd | Final projection + joint certificate | 8/0 | 3.81469727e-05 | Yes |
| BF16 | sgd | Reserved column + joint certificate | 8/0 | 0 | Yes |
| BF16 | momentum | Unconstrained (offline) | 0/0 | 0.00970506668 | No |
| BF16 | momentum | Gradient only (offline) | 0/0 | 0.00555112958 | No |
| BF16 | momentum | Final projection + joint certificate | 2/6 | 1.23596191 | Yes |
| BF16 | momentum | Reserved column + joint certificate | 8/0 | 0.00970506668 | Yes |
| BF16 | adamw | Unconstrained (offline) | 0/0 | 0.09322837 | No |
| BF16 | adamw | Gradient only (offline) | 0/0 | 0.0932493508 | No |
| BF16 | adamw | Final projection + joint certificate | 1/7 | 2.09790039 | Yes |
| BF16 | adamw | Reserved column + joint certificate | 8/0 | 0.09322837 | Yes |
| FP32 | sgd | Unconstrained (offline) | 0/0 | 0 | No |
| FP32 | sgd | Gradient only (offline) | 0/0 | 3.81469727e-05 | Yes |
| FP32 | sgd | Final projection + joint certificate | 8/0 | 3.81469727e-05 | Yes |
| FP32 | sgd | Reserved column + joint certificate | 8/0 | 0 | Yes |
| FP32 | momentum | Unconstrained (offline) | 0/0 | 0.00954279734 | No |
| FP32 | momentum | Gradient only (offline) | 0/0 | 0.00571515002 | Yes |
| FP32 | momentum | Final projection + joint certificate | 8/0 | 0.00571515002 | Yes |
| FP32 | momentum | Reserved column + joint certificate | 8/0 | 0.00954279734 | Yes |
| FP32 | adamw | Unconstrained (offline) | 0/0 | 0.0932230736 | No |
| FP32 | adamw | Gradient only (offline) | 0/0 | 0.0935953615 | No |
| FP32 | adamw | Final projection + joint certificate | 0/8 | 2.5 | Yes |
| FP32 | adamw | Reserved column + joint certificate | 8/0 | 0.0932230736 | Yes |

All **21 refused candidates passed this registered-domain BIT diagnostic**, but failed the additionally selected exact ALG condition after endpoint rounding. Their effective differences have rank two in this fixture, despite the one-dimensional exact-safe input complement. Refusal is therefore evidence that the joint checker enforces its stricter declared claim; it is not evidence that these 21 candidates corrupted D. In particular, dense FP32 AdamW's frozen result here does not prove that BIT-safe AdamW learning is impossible. No alternate BIT-only route is silently substituted.

BF16 gradient-only momentum loses protected equality during this particular trajectory, while FP32 gradient-only momentum happens to preserve it over eight steps. Gradient-only AdamW loses protected equality in both formats; its decoupled decay is not removed by gradient projection. SGD's gradient-only route is safe in this deliberately exact dyadic fixture, but it remains an uncertified offline experiment.

Offline state feedback stops before applying a Boolean recurrence to non-Boolean protected call outputs. A optimization can continue in the isolated bank after that stop; subsequent records explicitly say that the offline D feedback is stopped. No illegal state is reclassified as reachable or passed to the live API. Offline full-domain probes continue to diagnose all four legal state/input pairs.

## Dyadic SGD derivation and its distinct evidence level

For dense projected SGD with rate one and initial `I_2`, write `t` for accepted steps. The exact recurrence yields rows

`(2^(-t), 1-2^(-t))`, and `(2-2^(1-t), -1+2^(1-t))`.

Each row sum is one. Thus its exact difference annihilates `(1,1)`, and A at `e1` has error `(2^(-t), -2^(1-t))`. Its exact squared loss is `(5/2) * 4^(-t)`. For `0 <= t <= 8`, all listed coefficients are representable in BF16 as well as FP32; the selected order on the protected `(1,1)` sum gives exactly one, and `(0,0)` yields canonical zero. The complete fixed-graph checker confirms these particular endpoints and commits them. This small mathematical derivation supports this eight-step fixture; it does not assert that arbitrarily many repeated halvings stay representable or continue to be accepted.

For the structural rate-one SGD path, only the reserve is changed from `(1,0)` to `(0,2)` in one exact storable step. D's admitted sparse graph excludes this column; A at `e3` exactly returns the new reserve. Remaining steps have zero gradient and may make accepted zero changes. The general structural read-exclusion proof and transaction induction have their own stated assumptions in the theorem file.

## Logged observations and rollback

Every attempt records original weights, proposed rounded weights, actual final weights, exact raw/restricted increments, exact proposed and actual effective differences and ranks, optimizer old/staged/actual moments and step, exact loss and raw A output words. Both candidate and actual endpoints receive complete-domain observations. Safe commits record the certificate digest and receipt; refusals record the reason and exact full-snapshot rollback equality. After each attempt, accepted or refused, the actual safe bank and an unchanged peer each execute the same legal input tick. Their full returned protected traces and next-state words must agree.

A refused step does not advance optimizer time, moments, weight version or weights. A subsequent protected tick may advance q/ticks normally; preparation always precedes that tick. The B1 certificate binds the whole old snapshot, so reuse after a tick is rejected by the transaction verifier. State feedback, optimizer state and weight versions are not interchangeable counters.

The main experiment's local arithmetic diagnostic is separately written, but it uses the same audited primitive runtime; this alone is not independent proof. `verify_independent.py` and its separately derived references supply the independent finite review. The parent evidence map identifies those checks. Neither set of tests constitutes a complete machine proof.

## Reproduction and limits

From a working copy with the declared read-only dependency paths available:

```sh
python /workspace/p2_b1/verify_training.py
```

The script writes `training_results.json` beside itself, independent of the caller's current directory. Run without `-O` or `-OO`. Exact operation counts and environment metadata are recorded; no old stage test suite is imported or rerun. The root aggregate and independent scripts provide their own reproducibility records.

This experiment covers software BF16 and locally audited CPU FP32, two fixed trusted graphs, finite canonical domains, serialized immutable composite publication and eight-step toy optimization. It does not certify GPU, native BF16, general concurrent writers, crash recovery, arbitrary compiler fusion/reassociation, malicious modification of trusted memory or APIs, arbitrary A-to-D feedback, or a globally useful learning objective. Handwritten universal proofs, complete local enumeration, sampled trajectories and independent numerical replay remain distinct evidence classes.

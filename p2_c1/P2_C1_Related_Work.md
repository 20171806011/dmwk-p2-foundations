# P2-C1 — Verified projection-method context

This is a limited original-source check, not a literature survey or a novelty assessment. The actual retrieval record is [literature_sources.json](literature_sources.json). No earlier research artifacts or optimizer experiments were changed or rerun.

## Verified bibliographic records

| Method | Original paper | Authors | Publication verified from the original source |
|---|---|---|---|
| OGD | *Orthogonal Gradient Descent for Continual Learning* | Mehrdad Farajtabar, Navid Azizan, Alex Mott, Ang Li | AISTATS 2020; Proceedings of Machine Learning Research 108, pp. 3762–3773. [Official proceedings page](https://proceedings.mlr.press/v108/farajtabar20a.html), [official PDF](https://proceedings.mlr.press/v108/farajtabar20a/farajtabar20a.pdf). |
| GPM | *Gradient Projection Memory for Continual Learning* | Gobinda Saha, Isha Garg, Kaushik Roy | ICLR 2021. The original arXiv record identifies ICLR 2021 and submission version v1 dated 17 March 2021; the PDF identifies itself as an ICLR 2021 conference paper. [Original author preprint record](https://arxiv.org/abs/2103.09762), [PDF](https://arxiv.org/pdf/2103.09762), [arXiv DOI](https://doi.org/10.48550/arXiv.2103.09762). |

The GPM OpenReview forum request redirected to a challenge page. That response was recorded as unusable paper content; it was not treated as independent verification of the conference record. The arXiv metadata and actual paper PDF supplied the checked GPM evidence. PDF page numbers below count the first PDF page as page 1.

## OGD: projection of parameter gradients with a locality premise

Section 3, PDF pp. 2–4, constructs update directions orthogonal to gradients of the model's output logits on earlier task examples. Equation (7) states the desired current-gradient orthogonality. Because earlier data are unavailable during the next task, the method uses stored output gradients evaluated near the earlier task's learned parameters: the discussion before equation (8), PDF p. 3, explicitly approximates the current output gradients by those stored gradients in a nearby parameter neighborhood.

Equation (9) subtracts projections onto an orthogonal basis of stored directions. OGD-ALL, OGD-AVE and OGD-GTL retain different output-gradient information; the experiments use OGD-GTL and a subset of gradients, including 200 per task for the MNIST experiments. The p. 3 discussion states: “we store only a subset of gradients from each task in our experiments”. Section 4, PDF p. 4, explicitly notes the locality issue with larger learning rates.

Lemma 3.1, PDF pp. 3–4, concerns the projected direction's descent property for the new-task loss. In exact Euclidean algebra, if the projected gradient is g_perp, the negative direction has directional derivative `-||g_perp||^2`; strict first-order decrease requires a nonzero projection, together with the usual differentiability/step-size conditions for a finite step. That fact is not an exact finite-step preservation theorem for all old nonlinear outputs.

For P2-C1, the useful inherited idea is projection away from protected directions. The inspected original construction does not supply proof that a finite stored gradient subset covers every legal execution activation, and current-output preservation cannot be inferred solely from stale/local output-gradient orthogonality. It also does not establish this stage's source-to-graph equivalence, stored-endpoint bitwise checks or serial publication contract. These are differences in the stated verification obligations, not an assertion that OGD lacks value for its own continual-learning objective.

## GPM: activation-derived subspaces and thresholded approximation

Sections 4–5 relate fully connected and convolutional weight gradients to layer inputs. Section 5, PDF p. 5, constructs each layer's representation matrix from forward passes of random training examples, then retains leading singular vectors according to a squared Frobenius-energy threshold. Equation (5) specifies that threshold; equations (6)–(7) project new gradients away from the retained subspace. For a fully connected layer in its stated orientation, equation (6) has the form `G <- G - G M M^T`.

Equations (8)–(9) remove the component of new representations already in memory and append newly selected orthogonal directions. The paper explicitly describes a growing core gradient space and shrinking residual space as new task directions are retained. This supports distinguishing additional independent constraints from the mere number of optimizer steps. A fixed existing protected span need not shrink after each projected step.

Section 7, PDF p. 9, analyzes the layerwise interference term `Delta W x` and relates its size to the representation threshold. The statement `Delta W x = 0` implies unchanged exact linear action at that same input. In the method's practical representation construction, however, random samples and energy truncation are not an all-legal-domain containment proof. Section 7 discusses the stability/plasticity tradeoff as the threshold is raised, rather than supplying a general BF16/FP32 bitwise execution theorem.

Section 6, PDF p. 6, also makes concrete implementation choices: no bias units, batch-normalization parameters learned for the first task and shared thereafter, plain SGD, and unconstrained task-specific classifiers in the multi-head experiments. Those choices should not be silently generalized into protection of arbitrary biases, normalization/state, optimizer transformations or all observation ports.

## Relationship to the bounded C1 compiler contract

The exact identity `(W + Delta) h = W h` under `Delta h = 0`, complementary-space projections, and parameter-space interference arguments are established mathematical ideas reflected in these papers. C1 does not claim to invent projection, orthogonality or the stability/plasticity issue.

The present stage instead makes a bounded, explicitly chosen language and trusted compilation/verification interface responsible for additional obligations:

1. Reconstruct the entire compiled call graph from the admitted source and identify every use of a shared matrix, including state and observation effects.
2. Prove a containing activation space or invariant for all legal inputs and initial states in the claimed language, instead of treating a sampled or truncated representation as global coverage.
3. Reserve writable structural coordinates and report their capacity separately from an unrestricted algebraic annihilator, finite stored endpoints, BIT classes and target-response feasibility.
4. Check actual stored endpoints under a fixed arithmetic graph and numerical policy. Exact real orthogonality or projected-gradient direction alone is not a BF16/FP32 bitwise authorization.
5. Bind source, graph, parameters, domain, versions, optimizer/state and schedule to a trusted serial transaction, preserving the whole owned snapshot on refusal.

These are the goals and stated scope of the local C1 research artifact. This two-paper check does not establish that they are new relative to all prior compilation, verification, isolation or continual-learning work. No comparative performance experiment against OGD or GPM was performed, and no performance advantage is claimed. The papers' reported benchmark results are not imported as evidence for C1.

GPU, native BF16, arbitrary compiler transformations/FMA, general concurrency, full-host machine verification and universal learning performance remain outside this literature check and the C1 guarantees.

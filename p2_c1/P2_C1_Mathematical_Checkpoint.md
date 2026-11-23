# P2-C1 mathematical checkpoint before implementation

This checkpoint fixes the proposed proof obligations before compiler/runtime code is written. The root plan and B4 handoff are read-only context. Concrete parser limits and JSON field spellings will be stated in Definitions and Compiler; they do not enlarge the following language or theorem claims.

## 1. Closed source and compilation boundary

Use a finite synchronous Boolean state-machine IR with named state and input bits, a nonempty explicit allowed-initial-state set, Boolean expression trees for every next-state coordinate and named Boolean outputs. The expression constructors are constants/references, NOT, AND and fixed eager Boolean macros OR/XOR/MUX. Outputs and all next expressions read the same old state and common input; no source expression reads a partially written next state. All bit combinations are legal inputs. The invariant domain includes every Boolean state, even if only a subset is initially allowed.

Only deterministic traversal, fresh ordered temporary/site assignment and the specified Boolean macro lowering are allowed. Leaves are wires/constants. Every primitive site is recovered from the entire canonical source by the trusted compiler/checker. There is no acceptance of an arbitrary external graph based merely on checking that its listed sites look locally valid. No CSE, fusion, reassociation, hidden external effects, arbitrary branch, rotation or user-supplied graph optimization is included.

## 2. One physical bank with structural reserve

For a_rows=m>=1 and a_cols=c>=1 use one stored matrix

    W = [[B, 0_(2 by c)], [0_(m by 3), A]],
    B = [[1,1,-1],[-1,0,1]].

Rows/columns, fixed zero cross blocks, the B block and the editable A block have compiler-defined identities. Bias is an explicit fixed zero; the constant third input coordinate is the affine lift. A D primitive prepares h=(a,b,1,0,...,0), evaluates only the fixed B block in ascending column order with separate correctly rounded multiply/add, then applies coordinate ReLU and selects its declared AND or NOT result. NOT sites set b=0. A calls prepare only c A coordinates and evaluate A rows/columns with identity activation, separately from D state evolution. The proposed legal A domain is zero and each canonical coordinate vector e_j; no arbitrary dense A input is silently admitted.

For Boolean a,b, all D coefficients, products and partial sums are small exactly representable integers. Thus the two row outputs are a AND b and NOT a exactly in canonical BF16/FP32 words. The result stays Boolean. This is not a claim of arbitrary-weight floating exactness.

## 3. Source correspondence and activation coverage

Structural induction on source expressions, followed by induction on the primitive-site order, proves every compiled result wire equals its source Boolean value. Simultaneous publication then gives the source next state and outputs exactly. A further induction over ticks proves equality for every finite legal input sequence and every admitted initial state, assuming exact gates, fixed graph, bit-preserving storage and trusted scheduling.

Every D call at every tick lies in

    H_D = {(a,b,1,0_c): a,b in {0,1}},
    V_* = span_K H_D = K^3 x {0_c}, K=Q or R.

Indeed (0,0,1),(1,0,1),(0,1,1) span the first three coordinates. The containing rank is three even if a particular program uses fewer directions or no primitive call. Enumerating all Boolean state/input pairs and all generated sites can give a tighter containing span V_enum. With a proper initial-state subset, this is not automatically the exact reachable span. Neither space is inferred from samples.

## 4. Capacity and response obligations

The actual structural update family has Delta only in the m-by-c A block, so its unrestricted exact scalar dimension is mc, single-update rank is at most min(m,c), and a freely chosen rank-q generator caps it by min(q,m,c). This is distinct from the full-output annihilator of V_*, whose dimension is (2+m)c, and from the still different family protecting only selected D observations. The compiler may deliberately freeze additional safe coordinates for structural simplicity.

For target input matrix Z in K^(c by p), structural responses are UZ. Their image dimension is m rank Z, prescribed R is feasible iff ker Z is contained in ker R, and the minimum implementing rank when feasible is rank R. Under homogeneous full coordinates X, the general inherited condition X alpha in V implies R alpha=0 still applies; the structural mask can impose stronger restrictions. Storage and actual finite-graph execution remain separate obligations.

A resource budget is accepted only when this concrete construction fits the requested row/column/cell/site limits and its certified capacity/response claims satisfy the requested minima. Failure of this construction is not impossibility for every conceivable compiler. Theorems will distinguish universal linear-algebra necessary conditions, sufficient construction and implementation resource refusals.

On the proposed A domain {0,e_1,...,e_c}, every row has at most one nonzero product, so every canonical finite A endpoint is total and returns an exact coefficient column or zero. If N_F counts admitted finite canonical words, there are exactly N_F^(mc) structural endpoints and full-basis A response signatures. This is a finite-set cardinality theorem, not a vector-space dimension or an exhaustive experiment; N_BF16=65279 and N_FP32=4278190079 under the fixed finite/canonical-zero policy.

## 5. Exact endpoint publication

Only actual stored endpoint differences count. A proposed A update may round away or be unrepresentable. A valid compiler certificate binds the complete canonical source, initial/input domain, derived graph, every site/sharing/layout identity, numerical policy and fixed weights/mask. A live update additionally binds the current full owned snapshot: endpoint/version, D state and tick, optimizer state, counters, schedule and ledger. Full canonical reconstruction/checking runs on an unexposed copy; publication occurs once after all checks and receipt construction. Refusal publishes nothing.

Every accepted structural endpoint preserves the entire D gate graph and its state/input/effect interfaces, hence every finite serial update/tick history preserves the original source D trajectory under equal initial state, inputs and trusted tick schedule. Weight/optimizer/version/ledger metadata may legitimately differ; only rejection requires equality of the entire owned snapshot. No A-to-D feedback is allowed outside the specified source interface.

## 6. Explicit boundaries

Geometric projection can be studied in exact algebra, but a real zero product is not BIT authorization. General rotations do not commute with coordinate ReLU; the checker does not silently accept them. Numerical diagnostics stay read-only. The actual endpoint difference already contains upstream optimizer/projection/storage effects; bounds comparing two numeric executions still require both rounding errors.

Fixed V_* does not shrink with update count. New independent cumulative constraints, conflicting anchors, finite storage saturation and local quantization stalls are different mechanisms. Repeated rank-q increments need not have cumulative rank q. Nonzero target change or a toy loss decrease is not universal learning benefit.

All universal statements here are conditional handwritten proofs to be expanded in Theorems. Complete finite program/domain enumeration and independent numeric/source references are evidence of the bounded implementation, not full-machine proof. GPU, native BF16, general concurrency/crash safety, arbitrary compiler/FMA transformations and C2/C3/C4 are outside this checkpoint.

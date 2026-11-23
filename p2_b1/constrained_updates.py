"""B1 exact constraints and explicitly staged optimizer proposals.

These helpers never authorize a stored endpoint or mutate protected state.
SGD/momentum are rational. Adam moment arithmetic is finite host binary64;
its decoded result becomes an exact rational before endpoint restriction.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import sys

from b1_runtime import load_a2

xp = load_a2("exact_projection")
Matrix = xp.Matrix
LIMIT = (1 << 63) - 1


def require(ok, message):
    if not ok:
        raise ValueError(message)


def _matrix(a):
    require(type(a) is Matrix, "Exact immutable A2 Matrix required")
    return a


def _rat(x):
    require(type(x) in (int, Fraction), "Only exact int/Fraction scalars are admitted")
    return Fraction(x)


def matrix_record(a):
    _matrix(a)
    return {"shape": [a.nrows, a.ncols],
            "rows": [[[v.numerator, v.denominator] for v in row] for row in a.rows]}


def matrix_from_record(record):
    require(type(record) is dict and set(record) == {"shape", "rows"}, "Matrix schema mismatch")
    shape = record["shape"]
    require(type(shape) is list and len(shape) == 2 and
            all(type(v) is int and 0 <= v <= 64 for v in shape), "Matrix dimensions outside reference bound")
    rows = record["rows"]
    require(type(rows) is list and len(rows) == shape[0], "Matrix row count mismatch")
    data = []
    for row in rows:
        require(type(row) is list and len(row) == shape[1], "Matrix column count mismatch")
        decoded = []
        for pair in row:
            require(type(pair) is list and len(pair) == 2 and
                    all(type(v) is int for v in pair) and pair[1] > 0,
                    "Rational pair must use integer numerator and positive denominator")
            value = Fraction(*pair)
            require([value.numerator, value.denominator] == pair, "Rational pair must be reduced/canonical")
            decoded.append(value)
        data.append(tuple(decoded))
    return Matrix(tuple(data), shape[1])


def project_direction(G, H):
    _matrix(G); _matrix(H)
    require(G.ncols == H.nrows, "Projection input dimension mismatch")
    return xp.project_update(G, xp.projection(H))


def nullspace_update(Z, H):
    _matrix(Z); _matrix(H)
    N = xp.nullspace(xp.transpose(H))
    require(Z.ncols == N.ncols, "Nullspace coefficient width mismatch")
    return xp.matmul(Z, xp.transpose(N))


def lowrank_update(L, R, H):
    _matrix(L); _matrix(R); _matrix(H)
    require(L.ncols == R.nrows and R.ncols == H.nrows, "Low-rank factor shape mismatch")
    return project_direction(xp.matmul(L, R), H)


def mask_direction(G, free_columns):
    _matrix(G)
    require(type(free_columns) in (tuple, list), "Column mask must be a sequence")
    require(all(type(j) is int and 0 <= j < G.ncols for j in free_columns), "Invalid free column")
    require(len(set(free_columns)) == len(free_columns), "Duplicate mask column")
    return Matrix(tuple(tuple(v if j in free_columns else Fraction(0)
                              for j, v in enumerate(row)) for row in G.rows), G.ncols)


def _float(x):
    require(sys.float_info.mant_dig == 53 and sys.float_info.radix == 2,
            "The declared host binary64 proposal path is unavailable")
    try:
        out = float(x)
    except (OverflowError, ValueError):
        raise ValueError("Optimizer host conversion is nonfinite") from None
    require(math.isfinite(out), "Optimizer host result is nonfinite")
    return out


def _from_float(x):
    return Fraction.from_float(_float(x))


def clip_direction(G, mode="none", bound=None):
    _matrix(G)
    require(type(mode) is str and mode in ("none", "element", "global_norm"), "Unknown clipping mode")
    if mode == "none":
        require(bound is None, "Unused clip bound must be absent")
        return G, {"mode": "none"}
    limit = _rat(bound)
    require(limit > 0, "Clip bound must be positive")
    if mode == "element":
        clipped = Matrix(tuple(tuple(max(-limit, min(limit, v)) for v in row)
                               for row in G.rows), G.ncols)
        return clipped, {"mode": mode, "arithmetic": "exact rational coordinate clipping"}
    norm = _float(math.sqrt(_float(xp.frobenius_squared(G))))
    factor = 1.0 if norm == 0.0 else min(1.0, _float(limit) / norm)
    scalar = _from_float(factor)
    return xp.scale(G, scalar), {"mode": mode, "host_norm_hex": norm.hex(),
                                "common_scalar": [scalar.numerator, scalar.denominator],
                                "arithmetic": "host binary64 norm, exact common rational scaling"}


@dataclass(frozen=True)
class OptimizerConfig:
    kind: str
    learning_rate: Fraction
    momentum: Fraction = Fraction(9, 10)
    beta1: Fraction = Fraction(9, 10)
    beta2: Fraction = Fraction(999, 1000)
    epsilon: Fraction = Fraction(1, 100000000)
    weight_decay: Fraction = Fraction(0)
    clip_mode: str = "none"
    clip_bound: Fraction | None = None

    def __post_init__(self):
        require(type(self.kind) is str and self.kind in ("sgd", "momentum", "adamw"), "Unknown optimizer")
        for name in ("learning_rate", "momentum", "beta1", "beta2", "epsilon", "weight_decay"):
            object.__setattr__(self, name, _rat(getattr(self, name)))
        require(self.learning_rate > 0 and self.epsilon > 0 and self.weight_decay >= 0,
                "Positive learning rate/epsilon and nonnegative decay required")
        require(all(0 <= v < 1 for v in (self.momentum, self.beta1, self.beta2)), "Moment coefficients must be in [0,1)")
        require(type(self.clip_mode) is str and self.clip_mode in ("none", "element", "global_norm"), "Unknown clip mode")
        if self.clip_mode == "none":
            require(self.clip_bound is None, "Unused clip bound must be absent")
        else:
            object.__setattr__(self, "clip_bound", _rat(self.clip_bound))
            require(self.clip_bound > 0, "Clip bound must be positive")


def config_record(config):
    require(type(config) is OptimizerConfig, "Pinned optimizer config required")
    out = {"kind": config.kind, "clip_mode": config.clip_mode}
    for name in ("learning_rate", "momentum", "beta1", "beta2", "epsilon", "weight_decay", "clip_bound"):
        v = getattr(config, name)
        out[name] = None if v is None else [v.numerator, v.denominator]
    return out


@dataclass(frozen=True)
class OptimizerState:
    step: int
    m: Matrix
    v: Matrix

    def __post_init__(self):
        require(type(self.step) is int and 0 <= self.step <= LIMIT, "Invalid bounded optimizer step")
        _matrix(self.m); _matrix(self.v)
        require(self.m.shape == self.v.shape, "Optimizer state shape mismatch")
        require(all(v >= 0 for row in self.v.rows for v in row), "Second moment cannot be negative")


def initial_optimizer_state(n, d):
    return OptimizerState(0, xp.zeros(n, d), xp.zeros(n, d))


def state_record(state):
    require(type(state) is OptimizerState, "Immutable optimizer state required")
    return {"step": state.step, "m": matrix_record(state.m), "v": matrix_record(state.v)}


@dataclass(frozen=True)
class Stage:
    raw_increment: Matrix
    increment: Matrix
    next_state: OptimizerState
    audit: dict


def optimizer_proposal(W, gradient, state, config):
    _matrix(W); _matrix(gradient)
    require(type(state) is OptimizerState and type(config) is OptimizerConfig, "Optimizer state/config type mismatch")
    require(W.shape == gradient.shape == state.m.shape, "Optimizer matrix shape mismatch")
    require(state.step < LIMIT, "Optimizer step counter exhausted")
    step = state.step + 1
    if config.kind == "sgd":
        m, v = state.m, state.v
        parameter_step = xp.scale(gradient, -config.learning_rate)
        arithmetic = "exact rational SGD"
    elif config.kind == "momentum":
        m = xp.add(xp.scale(state.m, config.momentum), xp.scale(gradient, 1-config.momentum))
        v = state.v
        parameter_step = xp.scale(m, -config.learning_rate)
        arithmetic = "exact rational EMA momentum"
    else:
        b1, b2, lr, eps = map(_float, (config.beta1, config.beta2, config.learning_rate, config.epsilon))
        denom1 = _float(1.0 - _float(b1 ** step))
        denom2 = _float(1.0 - _float(b2 ** step))
        require(denom1 > 0 and denom2 > 0 and eps > 0,
                "Rounded Adam coefficients/epsilon make bias correction invalid")
        ms, vs, ds = [], [], []
        for grow, mrow, vrow in zip(gradient.rows, state.m.rows, state.v.rows):
            mr, vr, dr = [], [], []
            for g, old_m, old_v in zip(grow, mrow, vrow):
                gf = _float(g)
                mf = _float(_float(b1 * _float(old_m)) + _float(_float(1.0-b1) * gf))
                vf = _float(_float(b2 * _float(old_v)) + _float(_float(1.0-b2) * _float(gf * gf)))
                mh, vh = _float(mf / denom1), _float(vf / denom2)
                require(vh >= 0, "Negative rounded second moment")
                denominator = _float(_float(math.sqrt(vh)) + eps)
                require(denominator > 0, "Invalid Adam denominator")
                delta = _float(-_float(lr * _float(mh / denominator)))
                mr.append(_from_float(mf)); vr.append(_from_float(vf)); dr.append(_from_float(delta))
            ms.append(tuple(mr)); vs.append(tuple(vr)); ds.append(tuple(dr))
        m, v, parameter_step = Matrix(tuple(ms), W.ncols), Matrix(tuple(vs), W.ncols), Matrix(tuple(ds), W.ncols)
        arithmetic = "finite host binary64 ordered Adam with Python pow/math.sqrt, exact Fraction decoding; no universal RNE pow/sqrt certification"
    decay = xp.scale(W, -config.learning_rate * config.weight_decay)
    raw = xp.add(parameter_step, decay)
    clipped, clip_audit = clip_direction(raw, config.clip_mode, config.clip_bound)
    return Stage(raw, clipped, OptimizerState(step, m, v),
                 {"optimizer": config.kind, "proposal_arithmetic": arithmetic,
                  "decay_arithmetic": "exact rational decoupled increment",
                  "order": ["moments", "parameter_step", "decoupled_decay", "increment_clip"],
                  "clip": clip_audit, "authorizes_endpoint": False})


def stage_optimizer(W, gradient, state, config, mode="none", H=None, free_columns=()):
    require(type(mode) is str and mode in ("none", "gradient_only", "projected", "structural"), "Unknown restriction mode")
    if mode in ("gradient_only", "projected"):
        _matrix(H)
    actual_gradient = project_direction(gradient, H) if mode == "gradient_only" else gradient
    staged = optimizer_proposal(W, actual_gradient, state, config)
    increment = staged.increment
    if mode == "projected":
        increment = project_direction(increment, H)
    elif mode == "structural":
        increment = mask_direction(increment, free_columns)
    audit = dict(staged.audit)
    audit.update({"restriction": mode, "original_gradient": matrix_record(gradient),
                  "optimizer_gradient": matrix_record(actual_gradient),
                  "final_increment": matrix_record(increment)})
    return Stage(staged.raw_increment, increment, staged.next_state, audit)

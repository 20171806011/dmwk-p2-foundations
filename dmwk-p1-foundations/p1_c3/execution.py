"""C3 reference policies on the frozen B2 raw-word dense-network model.

``ordered`` is bias-first, separate rounded multiply/add in column order.
``canonical`` first obtains the complete B2 canonical representative.
``exactacc`` rounds every product, sums those finite products and the bias
as Fractions, and rounds once. It does not compute an unrounded real dot.

BF16 operations are software RNE. FP32 multiply/add are actual NumPy CPU
scalar operations with explicit dtype, individually checked against exact
rational RNE; the exact accumulator and its last rounding are software.
No GPU, BLAS reduction, FMA, JIT, or parallel execution is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import sys
from types import MappingProxyType
from typing import Any, NamedTuple

# Frozen dependencies are imported read-only, including their cache files.
sys.dont_write_bytecode = True

import numpy as np

from p1_b2.canonicalize import Model, canonicalize, validate


class ExecutionError(ValueError):
    """Invalid execution-domain value, model, format, or policy."""


class ArithmeticRejected(ExecutionError):
    """An arithmetic result would be nonfinite under RNE."""


class BackendMismatch(ExecutionError):
    """A native FP32 operation did not satisfy the checked RNE contract."""


class Format(NamedTuple):
    """Deeply immutable format descriptor; public views cannot redefine RNE."""
    name: str
    p: int
    exponent_bits: int = 8

    @property
    def fraction_bits(self) -> int:
        return self.p - 1

    @property
    def total_bits(self) -> int:
        return self.p + self.exponent_bits

    @property
    def bias(self) -> int:
        return (1 << (self.exponent_bits - 1)) - 1

    @property
    def emin(self) -> int:
        return 1 - self.bias

    @property
    def emax(self) -> int:
        return self.bias

    @property
    def sign_mask(self) -> int:
        return 1 << (self.total_bits - 1)

    @property
    def fraction_mask(self) -> int:
        return (1 << self.fraction_bits) - 1

    @property
    def exponent_mask(self) -> int:
        return (1 << self.exponent_bits) - 1

    @property
    def max_finite_word(self) -> int:
        return ((self.exponent_mask - 1) << self.fraction_bits) | self.fraction_mask

    @property
    def min_subnormal_exponent(self) -> int:
        return self.emin - self.fraction_bits


FORMATS = MappingProxyType({"BF16": Format("BF16", 8), "FP32": Format("FP32", 24)})


def get_format(format_name: str | Format) -> Format:
    """Return one of the two supported e=8 formats, rejecting extensions."""
    if type(format_name) is str and format_name in FORMATS:
        return FORMATS[format_name]
    if type(format_name) is Format:
        if (type(format_name.name) is not str or type(format_name.p) is not int
                or type(format_name.exponent_bits) is not int):
            raise ExecutionError("format fields must have the exact built-in types")
        expected = FORMATS.get(format_name.name)
        if expected is not None and format_name == expected:
            return expected
    raise ExecutionError("format must be BF16 or FP32 with its fixed p,e")


def _scale_two(value: int, exponent: int) -> Fraction:
    if exponent >= 0:
        return Fraction(value << exponent)
    return Fraction(value, 1 << -exponent)


def decode_word(raw: int, format_name: str | Format) -> Fraction:
    """Decode a finite exact built-in unsigned raw word to its exact value.

    Both zero signs are accepted and decode to the same rational zero.
    NaN/infinity, wrong widths, bools, and host floating values are rejected.
    """
    fmt = get_format(format_name)
    if type(raw) is not int or not 0 <= raw < 1 << fmt.total_bits:
        raise ExecutionError(f"{fmt.name} requires an in-range built-in raw int")
    exponent = (raw >> fmt.fraction_bits) & fmt.exponent_mask
    fraction = raw & fmt.fraction_mask
    if exponent == fmt.exponent_mask:
        raise ExecutionError(f"{fmt.name} NaN/infinity raw word rejected: {raw:#x}")
    if exponent == 0:
        value = _scale_two(fraction, fmt.min_subnormal_exponent)
    else:
        value = _scale_two((1 << fmt.fraction_bits) | fraction,
                           exponent - fmt.bias - fmt.fraction_bits)
    return -value if raw & fmt.sign_mask else value


def _floor_log2_ratio(numerator: int, denominator: int) -> int:
    """floor(log2(numerator/denominator)), using only positive integers."""
    exponent = numerator.bit_length() - denominator.bit_length()
    if exponent >= 0:
        if numerator < denominator << exponent:
            exponent -= 1
    elif numerator << -exponent < denominator:
        exponent -= 1
    return exponent


def round_fraction(value: Fraction | int, format_name: str | Format) -> int:
    """Correct RNE for an arbitrary rational; all rounded zeros become +0.

    The lattice spacing is 2**max(emin-(p-1), floor(log2(abs(value)))-(p-1)).
    Quotient/remainder comparison implements ties-to-even without a host
    float conversion. A carry is normalized before the exponent check.
    Values at/above the RNE infinity threshold are explicitly rejected.
    """
    fmt = get_format(format_name)
    if type(value) is int:
        value = Fraction(value)
    if type(value) is not Fraction:
        raise ExecutionError("rounding accepts only Fraction or built-in int")
    if not value:
        return 0
    negative = value < 0
    numerator, denominator = abs(value.numerator), value.denominator
    exponent = _floor_log2_ratio(numerator, denominator)
    spacing = max(fmt.min_subnormal_exponent, exponent - fmt.fraction_bits)
    if spacing >= 0:
        quotient, remainder = divmod(numerator, denominator << spacing)
        divisor = denominator << spacing
    else:
        quotient, remainder = divmod(numerator << -spacing, denominator)
        divisor = denominator
    twice_remainder = remainder << 1
    if twice_remainder > divisor or (twice_remainder == divisor and quotient & 1):
        quotient += 1
    if quotient == 0:
        return 0
    if quotient == 1 << fmt.p:
        quotient >>= 1
        spacing += 1
    top_exponent = quotient.bit_length() - 1 + spacing
    if top_exponent > fmt.emax:
        raise ArithmeticRejected(f"{fmt.name} RNE overflow")
    if top_exponent < fmt.emin:
        # Here spacing is exactly the fixed subnormal quantum.
        magnitude = quotient
    else:
        significand = quotient << (fmt.p - quotient.bit_length())
        magnitude = ((top_exponent + fmt.bias) << fmt.fraction_bits) | (
            significand - (1 << fmt.fraction_bits))
    return magnitude | (fmt.sign_mask if negative else 0)


def encode_constant(value: Fraction | int, format_name: str | Format) -> int:
    """Encode a rational test/model constant without implicit binary64 input.

    Use Fraction(n,d), integers, or explicit raw words for constants. Host
    float input is deliberately rejected because it can hide double rounding.
    """
    return round_fraction(value, format_name)


@dataclass
class Audit:
    """Per-operation evidence; FP32 native events contain dtype and raw words."""
    native_multiply: int = 0
    native_add: int = 0
    software_multiply: int = 0
    software_add: int = 0
    exact_sums: int = 0
    native_oracle_checks: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)


def _canonical_zero(raw: int, fmt: Format) -> int:
    return 0 if raw & (fmt.sign_mask - 1) == 0 else raw


def _native_binary(a: int, b: int, fmt: Format, kind: str,
                   audit: Audit | None) -> int:
    left_exact, right_exact = decode_word(a, fmt), decode_word(b, fmt)
    exact = left_exact * right_exact if kind == "multiply" else left_exact + right_exact
    # Scalar reinterpretation preserves the input raw words, including -0.
    left = np.asarray(a, dtype=np.uint32).view(np.float32)[()]
    right = np.asarray(b, dtype=np.uint32).view(np.float32)[()]
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        if kind == "multiply":
            result = np.multiply(left, right, dtype=np.float32)
        else:
            result = np.add(left, right, dtype=np.float32)
    if type(left) is not np.float32 or type(right) is not np.float32 or type(result) is not np.float32:
        raise BackendMismatch("native operation did not preserve np.float32 scalar dtype")
    raw_native = int(np.asarray(result).view(np.uint32)[()])
    raw_normalized = _canonical_zero(raw_native, fmt)
    event = {"operation": kind, "left_raw": a, "right_raw": b,
             "left_dtype": str(left.dtype), "right_dtype": str(right.dtype),
             "result_dtype": str(result.dtype), "native_result_raw": raw_native,
             "normalized_result_raw": raw_normalized}
    if audit is not None:
        if kind == "multiply":
            audit.native_multiply += 1
        else:
            audit.native_add += 1
    try:
        expected = round_fraction(exact, fmt)
    except ArithmeticRejected:
        native_nonfinite = ((raw_native >> fmt.fraction_bits) & fmt.exponent_mask) == fmt.exponent_mask
        expected_infinity = (fmt.exponent_mask << fmt.fraction_bits) | (
            fmt.sign_mask if exact < 0 else 0)
        matches = raw_native == expected_infinity
        event.update(status="overflow_rejected" if matches else "backend_mismatch",
                     native_nonfinite=native_nonfinite, expected_raw=expected_infinity)
        if audit is not None:
            audit.native_oracle_checks += 1
            audit.events.append(event)
        if not matches:
            raise BackendMismatch("native result disagrees with correctly signed RNE infinity")
        raise ArithmeticRejected(f"FP32 {kind} overflow") from None
    if raw_normalized != expected:
        event.update(status="backend_mismatch", expected_raw=expected)
        if audit is not None:
            audit.native_oracle_checks += 1
            audit.events.append(event)
        raise BackendMismatch(f"FP32 {kind} failed exact RNE audit")
    event.update(status="finite", expected_raw=expected)
    if audit is not None:
        audit.native_oracle_checks += 1
        audit.events.append(event)
    return raw_normalized


def _binary(a: int, b: int, format_name: str | Format, kind: str,
            audit: Audit | None) -> int:
    fmt = get_format(format_name)
    if fmt.name == "FP32":
        return _native_binary(a, b, fmt, kind, audit)
    left, right = decode_word(a, fmt), decode_word(b, fmt)
    if audit is not None:
        if kind == "multiply":
            audit.software_multiply += 1
        else:
            audit.software_add += 1
    return round_fraction(left * right if kind == "multiply" else left + right, fmt)


def mul_words(a: int, b: int, format_name: str | Format,
              audit: Audit | None = None) -> int:
    """Separate RNE multiply; rejects nonfinite inputs or rounded overflow."""
    return _binary(a, b, format_name, "multiply", audit)


def add_words(a: int, b: int, format_name: str | Format,
              audit: Audit | None = None) -> int:
    """Separate RNE add; rejects nonfinite inputs or rounded overflow."""
    return _binary(a, b, format_name, "add", audit)


def final_sum_words(words: tuple[int, ...], format_name: str | Format,
                    audit: Audit | None = None) -> int:
    """Exact rational sum of already rounded finite words, followed by RNE."""
    fmt = get_format(format_name)
    if type(words) is not tuple:
        raise ExecutionError("exact sum requires a tuple of finite raw words")
    total = sum((decode_word(word, fmt) for word in words), Fraction(0))
    if audit is not None:
        audit.exact_sums += 1
    return round_fraction(total, fmt)


def _validate_input(model: Model, inputs: tuple[int, ...]) -> Format:
    validate(model)
    if len(model.widths) < 3:
        raise ExecutionError("C3 requires at least two affine layers and one hidden layer")
    fmt = get_format(model.format)
    if type(inputs) is not tuple or len(inputs) != model.widths[0]:
        raise ExecutionError("inputs must be a raw-word tuple of the input width")
    for raw in inputs:
        decode_word(raw, fmt)
    return fmt


@dataclass(frozen=True)
class Evaluation:
    outputs: tuple[int, ...]
    layers: tuple[tuple[int, ...], ...]
    policy: str
    backend: str
    audit: Audit
    canonical_witness: tuple[tuple[int, ...], ...] | None = None
    canonical_serialized: bytes | None = None


def evaluate(model: Model, inputs: tuple[int, ...], policy: str = "ordered",
             audit: Audit | None = None,
             max_group_size: int | None = 100000) -> Evaluation:
    """Evaluate hidden-ReLU/output-affine B2 models on finite raw inputs.

    Canonical policies use the acceptance domain of C(model), not that of the
    original representation. Exactacc rejects any product overflow or final
    rounded-sum overflow, and has no rounded intermediate-addition step.
    ``canonical_exactacc`` composes canonicalization with exactacc explicitly.
    """
    fmt = _validate_input(model, inputs)
    if type(policy) is not str or policy not in ("ordered", "canonical", "exactacc", "canonical_exactacc"):
        raise ExecutionError("unknown execution policy")
    if audit is None:
        audit = Audit()
    if type(audit) is not Audit:
        raise ExecutionError("audit must be an Audit instance")
    witness, serialized = None, None
    if policy in ("canonical", "canonical_exactacc"):
        canonical = canonicalize(model, max_group_size=max_group_size)
        model = canonical.model
        witness, serialized = canonical.witness, canonical.serialized
    exact_accumulation = policy in ("exactacc", "canonical_exactacc")
    values = inputs
    layer_outputs = []
    for layer_index, (weights, biases) in enumerate(model.layers):
        outputs = []
        for row, bias in zip(weights, biases):
            if exact_accumulation:
                products = tuple(mul_words(weight, value, fmt, audit)
                                 for weight, value in zip(row, values))
                result = final_sum_words((bias,) + products, fmt, audit)
            else:
                result = bias
                for weight, value in zip(row, values):
                    product = mul_words(weight, value, fmt, audit)
                    result = add_words(result, product, fmt, audit)
            if layer_index + 1 < len(model.layers):
                # Relu maps negatives and both zero signs to positive zero.
                if result & fmt.sign_mask or decode_word(result, fmt) == 0:
                    result = 0
            outputs.append(_canonical_zero(result, fmt))
        values = tuple(outputs)
        layer_outputs.append(values)
    if fmt.name == "BF16":
        backend = "software BF16 rational RNE; software exact sum" if exact_accumulation else "software BF16 rational RNE"
    else:
        backend = ("CPU NumPy FP32 scalar multiply (per-op rational audit); software exact sum/RNE"
                   if exact_accumulation else
                   "CPU NumPy FP32 scalar multiply/add (per-op rational audit); separate operations")
    return Evaluation(values, tuple(layer_outputs), policy, backend, audit, witness, serialized)


def ordered_execute(model: Model, inputs: tuple[int, ...], **kwargs) -> Evaluation:
    return evaluate(model, inputs, policy="ordered", **kwargs)


def canonical_execute(model: Model, inputs: tuple[int, ...], **kwargs) -> Evaluation:
    return evaluate(model, inputs, policy="canonical", **kwargs)


def exactacc_execute(model: Model, inputs: tuple[int, ...], **kwargs) -> Evaluation:
    return evaluate(model, inputs, policy="exactacc", **kwargs)


def exact_real_execute(model: Model, inputs: tuple[int, ...]) -> tuple[Fraction, ...]:
    """Full exact-real affine/ReLU oracle, with no floating-point rounding."""
    fmt = _validate_input(model, inputs)
    values = tuple(decode_word(raw, fmt) for raw in inputs)
    for layer_index, (weights, biases) in enumerate(model.layers):
        next_values = []
        for row, bias in zip(weights, biases):
            total = decode_word(bias, fmt) + sum(
                (decode_word(weight, fmt) * value for weight, value in zip(row, values)), Fraction(0))
            if layer_index + 1 < len(model.layers):
                total = max(Fraction(0), total)
            next_values.append(total)
        values = tuple(next_values)
    return values


def backend_metadata() -> dict[str, Any]:
    """Describe actual implementations without claiming untested devices."""
    return {
        "numpy_version": np.__version__,
        "BF16": "software Fraction RNE multiply/add; exact Fraction accumulator",
        "FP32": "CPU NumPy scalar multiply/add, dtype=float32, every result audited by rational RNE",
        "FP32_exactacc_final_round": "software rational RNE (hybrid backend)",
        "rounding": "nearest, ties to even; gradual underflow; every arithmetic zero becomes +0",
        "fma": False,
        "gpu": "not executed or certified",
    }

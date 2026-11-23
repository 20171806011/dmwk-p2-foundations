"""A fixed sparse 2x2 structural safe-update reference for P2-A2.

This is a trusted local, single-threaded API. It does not accept a numerical
projector or a caller's orthogonality claim as a permission certificate.
Only the declared theta word is writable. No mutable term is evaluated on
the protected path, including terms that would be multiplied by zero.
"""
from __future__ import annotations

from fractions import Fraction

from p1_runtime import get_fp


POLICY = "p2-a2-sparse-separate-rne-canonical-zero-v1"
ROUTE = "structural_mask_v1"
WRITE_MASK = ((0, 0), (0, 1))


class UpdateRejected(ValueError):
    """A candidate or call does not meet the fixed structural contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UpdateRejected(message)


def policy_id() -> str:
    # A fresh return of this literal prevents public constant rebinding from
    # accidentally changing the policy accepted by a live kernel.
    return "p2-a2-sparse-separate-rne-canonical-zero-v1"


def _finite_word(raw: int, format_name: str) -> int:
    require(type(raw) is int, "Every word must be an exact built-in int")
    fp = get_fp()
    fmt = fp.get_format(format_name)
    require(0 <= raw < (1 << fmt.total_bits), "Raw word is out of format range")
    require(((raw >> fmt.fraction_bits) & fmt.exponent_mask) != fmt.exponent_mask,
            "Nonfinite proposed weight is rejected")
    require(raw != fmt.sign_mask, "Zero weights must use canonical +0")
    # This checks the imported format's finite decoder without a host float.
    fp.decode_word(raw, format_name)
    return raw


def _matrix_words(value, format_name: str) -> tuple:
    require(type(value) is tuple and len(value) == 2,
            "Candidate weights must be an exact 2x2 tuple")
    require(all(type(row) is tuple and len(row) == 2 for row in value),
            "Candidate rows must be exact two-word tuples")
    return tuple(tuple(_finite_word(raw, format_name) for raw in row)
                 for row in value)


def _checked_audit(audit) -> None:
    if audit is None:
        return
    fp = get_fp()
    require(type(audit) is fp.Audit, "Audit instrumentation must use the declared value container")
    for name in ("native_multiply", "native_add", "software_multiply", "software_add",
                 "exact_sums", "native_oracle_checks"):
        value = getattr(audit, name)
        require(type(value) is int and value >= 0, "Audit counters must be plain nonnegative integers")
    require(type(audit.events) is list, "Audit event storage must be a plain list")


class StructuralKernel:
    """Fixed D toggle/hold transition and A scalar readout of one shared bank.

    Public snapshots and receipts contain only immutable primitive values.
    Private memory/runtime mutation and concurrent invocation are outside the
    trust boundary, as are changes to compilation, FMA, reduction or zero rules.
    """

    __slots__ = ("_initialized", "_format", "_one", "_minus_one", "_bank")

    def __init__(self, format_name: str, initial_bit: int = 0,
                 theta_word: int | None = None):
        require(not getattr(self, "_initialized", False),
                "A live structural kernel cannot be reinitialized")
        require(type(format_name) is str and format_name in ("BF16", "FP32"),
                "Declared BF16 or FP32 format required")
        require(type(initial_bit) is int and initial_bit in (0, 1),
                "Initial D state must be a Boolean bit")
        fp = get_fp()
        one = fp.encode_constant(1, format_name)
        minus_one = fp.encode_constant(-1, format_name)
        theta = one if theta_word is None else _finite_word(theta_word, format_name)
        weights = ((minus_one, 0), (0, theta))
        state = one if initial_bit else 0
        bank = (0, weights, state, 0)  # model version, W words, D word, ticks
        self._format = format_name
        self._one = one
        self._minus_one = minus_one
        self._bank = bank
        self._initialized = True

    @property
    def format_name(self) -> str:
        return self._format

    @property
    def version(self) -> int:
        return self._bank[0]

    @property
    def weights(self) -> tuple:
        return self._bank[1]

    @property
    def state_word(self) -> int:
        return self._bank[2]

    @property
    def ticks(self) -> int:
        return self._bank[3]

    def snapshot(self) -> tuple:
        version, weights, state, ticks = self._bank
        return (self._format, policy_id(), version, weights,
                (self._one, 0), state, ticks)

    def _check_policy(self, policy: str) -> None:
        require(type(policy) is str and policy == policy_id(),
                "Unknown or changed execution policy")

    def _boolean_word(self, raw: int) -> int:
        require(type(raw) is int and raw in (0, self._one),
                "D/A inputs require canonical +0/+1 words")
        return raw

    def d_tick(self, input_word: int, *, policy: str = POLICY, audit=None) -> int:
        self._check_policy(policy)
        _checked_audit(audit)
        u = self._boolean_word(input_word)
        version, weights, old, ticks = self._bank
        # All reads use this one immutable snapshot. Mutable theta is never
        # loaded, multiplied, or included in a protected reduction.
        fp = get_fp()
        n = fp.add_words(self._one,
                         fp.mul_words(weights[0][0], old, self._format, audit),
                         self._format, audit)
        ubar = fp.add_words(self._one,
                            fp.mul_words(self._minus_one, u, self._format, audit),
                            self._format, audit)
        keep = fp.mul_words(ubar, old, self._format, audit)
        flip = fp.mul_words(u, n, self._format, audit)
        candidate = fp.add_words(keep, flip, self._format, audit)
        self._boolean_word(candidate)
        new_bank = (version, weights, candidate, ticks + 1)
        self._bank = new_bank
        return candidate

    def a_output(self, input_word: int, *, policy: str = POLICY, audit=None) -> int:
        self._check_policy(policy)
        _checked_audit(audit)
        a = self._boolean_word(input_word)
        weights = self._bank[1]
        fp = get_fp()
        return fp.add_words(0, fp.mul_words(weights[1][1], a, self._format, audit),
                            self._format, audit)

    def commit_words(self, candidate_weights, *, expected_version: int,
                     format_name: str, policy: str = POLICY,
                     route: str = ROUTE) -> tuple:
        """Validate a full raw-word candidate, then publish it once.

        Receipt: (new version, old immutable W, new immutable W).
        The route name is not a trusted external certificate: all fixed
        structural conditions are independently revalidated on every request.
        """
        self._check_policy(policy)
        require(type(route) is str and route == "structural_mask_v1",
                "Only the independently checked structural route may commit")
        require(type(format_name) is str and format_name == self._format,
                "Patch format does not match the live kernel")
        require(type(expected_version) is int and expected_version >= 0,
                "Expected version must be a nonnegative built-in int")
        version, old_weights, old_state, ticks = self._bank
        require(expected_version == version, "Stale weight version")
        candidate = _matrix_words(candidate_weights, self._format)
        require(candidate[0][0] == self._minus_one and candidate[0][1] == 0
                and candidate[1][0] == 0,
                "Protected weight words may not change")
        # Allocate every published/returned object before publication. Nothing
        # in these values retains caller-owned mutable containers or callbacks.
        new_version = version + 1
        new_bank = (new_version, candidate, old_state, ticks)
        receipt = (new_version, old_weights, candidate)
        self._bank = new_bank
        return receipt

    def commit_theta_ideal(self, ideal_theta: Fraction | int, *,
                           expected_version: int, policy: str = POLICY) -> tuple:
        """Quantize a proposed new theta value, then use the same validator.

        Receipt adds the exact effective theta change as numerator/denominator.
        It is the difference between stored new and old words, not a claim that
        the proposed ideal change was representable or effective.
        """
        self._check_policy(policy)
        require(type(ideal_theta) in (int, Fraction),
                "Ideal theta must be an exact rational, not a host float")
        require(type(expected_version) is int and expected_version == self.version,
                "Expected version mismatch")
        fp = get_fp()
        old = self.weights
        try:
            raw = fp.round_fraction(ideal_theta, self._format)
        except fp.ArithmeticRejected:
            raise UpdateRejected("Ideal theta rounds to a nonfinite value") from None
        effective = fp.decode_word(raw, self._format) - fp.decode_word(old[1][1], self._format)
        # These receipt fields are allocated before the nested commit mutates.
        delta_pair = (effective.numerator, effective.denominator)
        candidate = (old[0], (old[1][0], raw))
        result = (expected_version + 1, old, candidate, delta_pair)
        self.commit_words(candidate, expected_version=expected_version,
                          format_name=self._format, policy=policy)
        return result


def decoded_weights(snapshot: tuple) -> tuple:
    """Observer helper for valid snapshots; not an execution or commit path."""
    require(type(snapshot) is tuple and len(snapshot) == 7, "Snapshot shape mismatch")
    format_name, _, _, weights, _, _, _ = snapshot
    require(type(format_name) is str and format_name in ("BF16", "FP32"), "Format mismatch")
    value = _matrix_words(weights, format_name)
    fp = get_fp()
    return tuple(tuple(fp.decode_word(x, format_name) for x in row) for row in value)

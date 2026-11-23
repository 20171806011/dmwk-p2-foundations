"""DMWK P1-B2 reference canonicalization, wire version 1.

This independent module reads no prior-stage files. Parameters are unsigned
BF16/FP32 bit patterns, not host floating values. Signed zeros are distinct;
all finite values (including subnormals) are accepted. NaN/Inf are rejected.
Only the complete finite hidden-layer permutation group is searched.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from math import factorial, prod
import struct
from typing import Iterator


MAGIC = b'DMWKB2\x00\x00'
VERSION = 1
PROFILE = 1  # Dense chain, hidden ReLU, affine output, fixed port labels.
U32_MAX = (1 << 32) - 1
FORMATS = {'BF16': (1, 2, 7), 'FP32': (2, 4, 23)}
FORMAT_BY_TAG = {value[0]: name for name, value in FORMATS.items()}

Permutation = tuple[int, ...]
GroupElement = tuple[Permutation, ...]
Layer = tuple[tuple[tuple[int, ...], ...], tuple[int, ...]]


class ValidationError(ValueError):
    """Malformed model, permutation, or unsupported/noncanonical wire syntax."""


class ResourceLimit(RuntimeError):
    """Enumeration refused before searching; no approximate result returned."""


@dataclass(frozen=True, slots=True)
class Model:
    format: str
    widths: tuple[int, ...]
    input_labels: tuple[bytes, ...]
    output_labels: tuple[bytes, ...]
    layers: tuple[Layer, ...]


@dataclass(frozen=True, slots=True)
class CanonicalResult:
    model: Model
    serialized: bytes
    witness: GroupElement
    minimizing_witness_count: int
    group_size: int
    candidates_examined: int


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _tuple(value: object, name: str) -> None:
    _require(type(value) is tuple, f'{name} must be an immutable tuple')


def _positive_u32(value: object, name: str) -> None:
    _require(type(value) is int and 1 <= value <= U32_MAX,
             f'{name} must be a positive unsigned 32-bit integer')


def _labels(labels: object, width: int, name: str) -> None:
    _tuple(labels, name)
    _require(len(labels) == width, f'{name} count must match the port width')
    for label in labels:
        _require(type(label) is bytes and 1 <= len(label) <= U32_MAX,
                 f'{name} must contain nonempty opaque byte strings')
    _require(len(set(labels)) == len(labels), f'{name} must be distinct within the interface')


def validate(model: Model) -> None:
    """Validate the precise mathematical domain; perform no normalization."""
    _require(type(model) is Model, 'Expected Model')
    _require(type(model.format) is str and model.format in FORMATS,
             'Unsupported format; expected BF16 or FP32')
    _tuple(model.widths, 'widths')
    _require(3 <= len(model.widths) <= U32_MAX + 1,
             'A version-1 network has 2..2^32-1 affine layers')
    for width in model.widths:
        _positive_u32(width, 'width')
    _labels(model.input_labels, model.widths[0], 'input labels')
    _labels(model.output_labels, model.widths[-1], 'output labels')
    _tuple(model.layers, 'layers')
    _require(len(model.layers) == len(model.widths) - 1,
             'Layer count does not match architecture')
    _, byte_count, fraction_bits = FORMATS[model.format]
    word_limit = 1 << (8 * byte_count)

    def check_word(value: object) -> None:
        _require(type(value) is int and 0 <= value < word_limit,
                 'Parameter must be an unsigned raw word of the declared format')
        _require(((value >> fraction_bits) & 255) != 255,
                 'NaN and infinity are outside the accepted parameter domain')

    for index, layer in enumerate(model.layers):
        _tuple(layer, 'layer')
        _require(len(layer) == 2, 'Each layer must contain (matrix, bias)')
        matrix, bias = layer
        _tuple(matrix, 'matrix')
        _tuple(bias, 'bias')
        before, after = model.widths[index:index + 2]
        _require(len(matrix) == after and len(bias) == after,
                 'Matrix rows and bias length must match destination width')
        for row in matrix:
            _tuple(row, 'matrix row')
            _require(len(row) == before, 'Matrix columns must match source width')
            for value in row:
                check_word(value)
        for value in bias:
            check_word(value)


def serialize(model: Model) -> bytes:
    """Unique version-1 syntax; lex order is unsigned byte lexicographic order."""
    validate(model)
    format_tag, byte_count, _ = FORMATS[model.format]
    output = bytearray(MAGIC)
    output.extend(struct.pack('>HBBI', VERSION, format_tag, PROFILE, len(model.layers)))
    for width in model.widths:
        output.extend(struct.pack('>I', width))
    for label in model.input_labels + model.output_labels:
        output.extend(struct.pack('>I', len(label)))
        output.extend(label)
    for matrix, bias in model.layers:
        for row in matrix:
            for value in row:
                output.extend(value.to_bytes(byte_count, 'big'))
        for value in bias:
            output.extend(value.to_bytes(byte_count, 'big'))
    return bytes(output)


def deserialize(data: bytes) -> Model:
    """Strict parser: rejects trailing bytes and all unsupported syntax.

    Length lower bounds precede loops/allocations controlled by decoded fields,
    so a tiny malformed input cannot request a huge architecture allocation.
    """
    _require(type(data) is bytes, 'Serialized model must be immutable bytes')
    _require(len(data) >= 16, 'Truncated fixed header')
    _require(data[:8] == MAGIC, 'Wrong magic')
    version, format_tag, profile, layer_count = struct.unpack('>HBBI', data[8:16])
    _require(version == VERSION, 'Unsupported serialization version')
    _require(format_tag in FORMAT_BY_TAG, 'Unsupported format tag')
    _require(profile == PROFILE, 'Unsupported architecture profile')
    _require(layer_count >= 2, 'At least two affine layers are required')
    offset = 16
    shape_bytes = 4 * (layer_count + 1)
    _require(len(data) - offset >= shape_bytes, 'Truncated architecture widths')
    widths = tuple(struct.unpack_from('>I', data, offset + 4 * i)[0]
                   for i in range(layer_count + 1))
    offset += shape_bytes
    _require(all(width > 0 for width in widths), 'All widths must be positive')
    format_name = FORMAT_BY_TAG[format_tag]
    byte_count = FORMATS[format_name][1]
    parameter_count = sum(after * (before + 1)
                          for before, after in zip(widths, widths[1:]))
    tensor_bytes = byte_count * parameter_count
    label_count = widths[0] + widths[-1]
    _require(len(data) - offset >= 5 * label_count + tensor_bytes,
             'Insufficient bytes for labels and declared tensors')
    labels = []
    for label_index in range(label_count):
        _require(len(data) - offset >= 4, 'Truncated label length')
        label_size = struct.unpack_from('>I', data, offset)[0]
        offset += 4
        _require(label_size > 0, 'Port labels must be nonempty')
        remaining_minimum = 5 * (label_count - label_index - 1) + tensor_bytes
        _require(len(data) - offset >= label_size + remaining_minimum,
                 'Truncated label or inconsistent payload length')
        labels.append(data[offset:offset + label_size])
        offset += label_size
    _require(len(data) - offset == tensor_bytes,
             'Truncated tensor payload or forbidden trailing bytes')

    def read_word() -> int:
        nonlocal offset
        result = int.from_bytes(data[offset:offset + byte_count], 'big')
        offset += byte_count
        return result

    layers = []
    for before, after in zip(widths, widths[1:]):
        matrix = tuple(tuple(read_word() for _ in range(before)) for _ in range(after))
        bias = tuple(read_word() for _ in range(after))
        layers.append((matrix, bias))
    model = Model(format_name, widths, tuple(labels[:widths[0]]),
                  tuple(labels[widths[0]:]), tuple(layers))
    validate(model)
    _require(offset == len(data), 'Parser did not consume the full payload')
    return model


def _validate_permutation(p: Permutation, width: int | None = None) -> None:
    _tuple(p, 'permutation')
    _require(all(type(value) is int for value in p), 'Permutation entries must be integers')
    if width is not None:
        _require(len(p) == width, 'Permutation width does not match hidden layer')
    _require(len(p) > 0 and set(p) == set(range(len(p))),
             'Permutation must bijectively map 0..d-1 to 0..d-1')


def _validate_group(g: GroupElement, shape: tuple[int, ...] | None = None) -> None:
    _tuple(g, 'group element')
    if shape is not None:
        _require(len(g) == len(shape) - 2, 'Wrong number of hidden-layer permutations')
    for index, p in enumerate(g):
        _validate_permutation(p, shape[index + 1] if shape is not None else None)


def identity(model: Model) -> GroupElement:
    validate(model)
    return tuple(tuple(range(width)) for width in model.widths[1:-1])


def _inverse_permutation(p: Permutation) -> Permutation:
    result = [0] * len(p)
    for old, new in enumerate(p):
        result[new] = old
    return tuple(result)


def inverse(g: GroupElement) -> GroupElement:
    _validate_group(g)
    return tuple(_inverse_permutation(p) for p in g)


def compose(g: GroupElement, h: GroupElement) -> GroupElement:
    """Apply h first, then g: composite old j -> g[h[j]]."""
    _validate_group(g)
    _validate_group(h)
    _require(len(g) == len(h) and all(len(p) == len(q) for p, q in zip(g, h)),
             'Group elements must have the same layer shapes')
    return tuple(tuple(p[q[j]] for j in range(len(p))) for p, q in zip(g, h))


def action(model: Model, g: GroupElement) -> Model:
    """Complete coupled transformation; moves raw words without arithmetic."""
    validate(model)
    _validate_group(g, model.widths)
    inverse_hidden = tuple(_inverse_permutation(p) for p in g)
    inverse_all = ((tuple(range(model.widths[0])),) + inverse_hidden +
                   (tuple(range(model.widths[-1])),))
    layers = []
    for index, (matrix, bias) in enumerate(model.layers, 1):
        source, target = inverse_all[index - 1:index + 1]
        moved_matrix = tuple(tuple(matrix[old_i][old_j] for old_j in source)
                             for old_i in target)
        moved_bias = tuple(bias[old_i] for old_i in target)
        layers.append((moved_matrix, moved_bias))
    return Model(model.format, model.widths, model.input_labels,
                 model.output_labels, tuple(layers))


def group_size(model: Model) -> int:
    validate(model)
    return prod(factorial(width) for width in model.widths[1:-1])


def iter_group(model: Model) -> Iterator[GroupElement]:
    """Lexicographic complete group enumeration using O(sum hidden widths) state.

    Unlike itertools.product(permutations(...), ...), this implementation does
    not cache each layer's factorial-size pool of permutations.
    """
    validate(model)
    hidden = model.widths[1:-1]
    iterators = [None] * len(hidden)
    current = [None] * len(hidden)
    level = 0
    iterators[level] = permutations(range(hidden[level]))
    while level >= 0:
        try:
            current[level] = next(iterators[level])
        except StopIteration:
            iterators[level] = None
            level -= 1
            continue
        if level == len(hidden) - 1:
            yield tuple(current)
        else:
            level += 1
            iterators[level] = permutations(range(hidden[level]))


def _bounded_group_size(model: Model, limit: int | None) -> int:
    if limit is not None:
        _require(type(limit) is int and limit >= 1,
                 'max_group_size must be a positive integer or None')
    total = 1
    for width in model.widths[1:-1]:
        for factor in range(2, width + 1):
            total *= factor
            if limit is not None and total > limit:
                raise ResourceLimit(f'Complete group exceeds max_group_size={limit}; '
                                    'no canonical representative was returned')
    return total


def canonicalize(model: Model, max_group_size: int | None = 100_000) -> CanonicalResult:
    """Global lexicographic minimum over the full finite permutation orbit.

    Ties choose the lexicographically smallest permutation witness. That
    deterministic choice does not recover historical neuron identity.
    If the group is too large, refuse before enumerating any candidates.
    """
    validate(model)
    expected = _bounded_group_size(model, max_group_size)
    best_model = best_bytes = best_witness = None
    ties = examined = 0
    for g in iter_group(model):
        moved = action(model, g)
        candidate = serialize(moved)
        examined += 1
        if best_bytes is None or candidate < best_bytes:
            best_model, best_bytes, best_witness = moved, candidate, g
            ties = 1
        elif candidate == best_bytes:
            ties += 1
            if g < best_witness:
                best_witness = g
    _require(examined == expected, 'Internal error: incomplete group enumeration')
    _require(best_model is not None, 'Internal error: finite group had no identity')
    return CanonicalResult(best_model, best_bytes, best_witness, ties, expected, examined)

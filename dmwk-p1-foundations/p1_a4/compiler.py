"""P1-A4 typed CFG -> fixed sparse affine/ReLU weight program.

Independent implementation: no previous-stage files are accessed. The source
interpreter uses integers only as an oracle. Executor.tick evaluates every
compiled node and never dispatches on a decoded program counter.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
import numpy as np


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


@dataclass(frozen=True)
class Type:
    kind: str
    width: int

    def __post_init__(self):
        require(type(self.width) is int and self.width >= 1, 'Positive type width required')
        require(self.kind == 'U' or (self.kind == 'Bool' and self.width == 1),
                'Type must be Bool or U(w)')


BOOL = Type('Bool', 1)


def U(width):
    return Type('U', width)


@dataclass(frozen=True)
class Expr:
    op: str
    args: tuple = ()
    value: int | None = None
    name: str | None = None
    typ: Type | None = None


def C(value, typ):
    return Expr('const', value=value, typ=typ)


def R(name):
    return Expr('reg', name=name)


def I(name):
    return Expr('input', name=name)


def NOT(a):
    return Expr('not', (a,))


def AND(a, b):
    return Expr('and', (a, b))


def OR(a, b):
    return Expr('or', (a, b))


def XOR(a, b):
    return Expr('xor', (a, b))


def EQ(a, b):
    return Expr('eq', (a, b))


def ADD(a, b):
    return Expr('add', (a, b))


def MUX(c, a, b):
    return Expr('mux', (c, a, b))


@dataclass(frozen=True)
class Assign:
    bindings: tuple
    next: int


@dataclass(frozen=True)
class Branch:
    cond: Expr
    yes: int
    no: int


@dataclass(frozen=True)
class Jump:
    next: int


@dataclass(frozen=True)
class Halt:
    pass


@dataclass(frozen=True)
class Program:
    registers: tuple
    inputs: tuple
    blocks: tuple
    entry: int = 0


@dataclass(frozen=True)
class State:
    values: tuple
    pc: int


def _declarations(declarations, label):
    require(type(declarations) is tuple, label + ' declarations must be a tuple')
    names = []
    for declaration in declarations:
        require(type(declaration) is tuple and len(declaration) == 2, 'Invalid declaration')
        name, typ = declaration
        require(type(name) is str and name != '', 'Nonempty variable name required')
        require(type(typ) is Type, 'Variable declaration needs a Type')
        names.append(name)
    require(len(names) == len(set(names)), 'Duplicate ' + label + ' name')
    return dict(declarations)


def _infer(expr, regs, inputs):
    require(type(expr) is Expr and type(expr.args) is tuple, 'Expression must be immutable Expr')
    if expr.op == 'const':
        require(not expr.args and expr.name is None and type(expr.typ) is Type,
                'Malformed typed constant')
        require(type(expr.value) is int and 0 <= expr.value < 2**expr.typ.width,
                'Constant outside its explicit unsigned/Boolean width')
        return expr.typ
    if expr.op in ('reg', 'input'):
        require(not expr.args and expr.value is None and expr.typ is None,
                'Malformed variable reference')
        namespace = regs if expr.op == 'reg' else inputs
        require(type(expr.name) is str and expr.name in namespace, 'Unknown variable')
        return namespace[expr.name]
    arity = {'not': 1, 'and': 2, 'or': 2, 'xor': 2, 'eq': 2, 'add': 2, 'mux': 3}
    require(expr.op in arity and len(expr.args) == arity[expr.op], 'Unknown operator or arity')
    require(expr.value is None and expr.name is None and expr.typ is None,
            'Operator carries unexpected metadata')
    types = tuple(_infer(arg, regs, inputs) for arg in expr.args)
    if expr.op in ('not', 'and', 'or', 'xor'):
        require(all(t == BOOL for t in types), 'Boolean operator requires Bool operands')
        return BOOL
    if expr.op == 'eq':
        require(types[0] == types[1], 'EQ requires identical operand types')
        return BOOL
    if expr.op == 'add':
        require(types[0] == types[1] and types[0].kind == 'U',
                'ADD requires matching U(w) operands')
        return types[0]
    require(types[0] == BOOL and types[1] == types[2], 'MUX type mismatch')
    return types[1]


def infer(program, expr):
    return _infer(expr, _declarations(program.registers, 'register'),
                  _declarations(program.inputs, 'input'))


def validate_program(program):
    require(type(program) is Program, 'Expected Program')
    regs = _declarations(program.registers, 'register')
    inputs = _declarations(program.inputs, 'input')
    require(type(program.blocks) is tuple and len(program.blocks) >= 1,
            'Program requires a nonempty immutable block tuple')
    count = len(program.blocks)

    def address(target):
        require(type(target) is int and 0 <= target < count, 'Invalid CFG target')

    address(program.entry)
    for instruction in program.blocks:
        if type(instruction) is Assign:
            require(type(instruction.bindings) is tuple and len(instruction.bindings) >= 1,
                    'Parallel assignment requires immutable nonempty bindings')
            names = []
            for binding in instruction.bindings:
                require(type(binding) is tuple and len(binding) == 2, 'Malformed assignment binding')
                name, expr = binding
                require(type(name) is str and name in regs, 'Unknown assignment target')
                require(_infer(expr, regs, inputs) == regs[name], 'Assignment type mismatch')
                names.append(name)
            require(len(names) == len(set(names)), 'Duplicate parallel assignment target')
            address(instruction.next)
        elif type(instruction) is Branch:
            require(_infer(instruction.cond, regs, inputs) == BOOL, 'Branch requires Bool')
            address(instruction.yes)
            address(instruction.no)
        elif type(instruction) is Jump:
            address(instruction.next)
        else:
            require(type(instruction) is Halt, 'Unsupported source instruction')


def _typed_values(declarations, values, label):
    require(type(values) is tuple and len(values) == len(declarations), label + ' arity mismatch')
    for (_, typ), value in zip(declarations, values):
        require(type(value) is int and 0 <= value < 2**typ.width, label + ' out of range')


def _eval(expr, regs, inputs, reg_types, input_types):
    if expr.op == 'const':
        return expr.value
    if expr.op == 'reg':
        return regs[expr.name]
    if expr.op == 'input':
        return inputs[expr.name]
    values = tuple(_eval(a, regs, inputs, reg_types, input_types) for a in expr.args)
    if expr.op == 'not':
        return 1 - values[0]
    if expr.op == 'and':
        return values[0] & values[1]
    if expr.op == 'or':
        return values[0] | values[1]
    if expr.op == 'xor':
        return values[0] ^ values[1]
    if expr.op == 'eq':
        return int(values[0] == values[1])
    if expr.op == 'add':
        width = _infer(expr, reg_types, input_types).width
        return (values[0] + values[1]) % (2**width)
    return values[1] if values[0] else values[2]


def source_step(program, state, inputs):
    """Integer reference interpreter. Never called by Executor.tick."""
    validate_program(program)
    require(type(state) is State, 'Source state must be State')
    _typed_values(program.registers, state.values, 'Source registers')
    _typed_values(program.inputs, inputs, 'Source inputs')
    require(type(state.pc) is int and 0 <= state.pc < len(program.blocks), 'Source PC out of range')
    old = dict(zip((name for name, _ in program.registers), state.values))
    incoming = dict(zip((name for name, _ in program.inputs), inputs))
    reg_types, input_types = dict(program.registers), dict(program.inputs)
    evaluate = lambda expr: _eval(expr, old, incoming, reg_types, input_types)
    instruction = program.blocks[state.pc]
    if type(instruction) is Assign:
        updated = old.copy()
        for name, expr in instruction.bindings:
            updated[name] = evaluate(expr)
        return State(tuple(updated[name] for name, _ in program.registers), instruction.next)
    if type(instruction) is Branch:
        return State(state.values, instruction.yes if evaluate(instruction.cond) else instruction.no)
    if type(instruction) is Jump:
        return State(state.values, instruction.next)
    return state


@dataclass(frozen=True)
class Node:
    terms: tuple
    bias: int
    activation: str


@dataclass(frozen=True)
class Compiled:
    registers: tuple
    inputs: tuple
    block_count: int
    entry: int
    halt_pcs: tuple
    nodes: tuple
    outputs: tuple

    @property
    def register_bit_count(self):
        return sum(typ.width for _, typ in self.registers)

    @property
    def state_count(self):
        return self.register_bit_count + self.block_count

    @property
    def input_count(self):
        # Total DAG input wires, including the old state snapshot.
        return self.state_count + sum(typ.width for _, typ in self.inputs)

    def __post_init__(self):
        _declarations(self.registers, 'register')
        _declarations(self.inputs, 'input')
        require(type(self.block_count) is int and self.block_count >= 1, 'Invalid block count')
        require(type(self.entry) is int and 0 <= self.entry < self.block_count, 'Invalid entry')
        require(type(self.halt_pcs) is tuple and all(type(p) is int and 0 <= p < self.block_count
                for p in self.halt_pcs), 'Invalid halt metadata')
        require(type(self.nodes) is tuple and type(self.outputs) is tuple, 'Mutable target graph')
        for index, node in enumerate(self.nodes):
            require(type(node) is Node and type(node.terms) is tuple, 'Invalid target node')
            require(node.activation in ('linear', 'relu'), 'Unknown target activation')
            require(type(node.bias) is int, 'Bias must be exact integer')
            for term in node.terms:
                require(type(term) is tuple and len(term) == 2, 'Invalid weighted edge')
                wire, coefficient = term
                require(type(wire) is int and 0 <= wire < self.input_count + index,
                        'Target graph must have backward-only dependencies')
                require(type(coefficient) is int and coefficient in (-2, -1, 0, 1, 2),
                        'Unsupported target coefficient')
            require(abs(node.bias) + sum(abs(c) for _, c in node.terms) <= 4,
                    'Target affine small-integer certificate exceeds 4')
        require(len(self.outputs) == self.state_count and all(type(i) is int and
                0 <= i < self.input_count + len(self.nodes) for i in self.outputs),
                'Target outputs must write exactly the complete next state')


class Builder:
    def __init__(self, input_count):
        self.input_count = input_count
        self.nodes = []
        self.constants = {}

    def affine(self, terms, bias=0, activation='linear'):
        wire = self.input_count + len(self.nodes)
        self.nodes.append(Node(tuple(terms), bias, activation))
        return wire

    def const(self, bit):
        if bit not in self.constants:
            self.constants[bit] = self.affine((), bit)
        return self.constants[bit]

    def NOT(self, a):
        return self.affine(((a, -1),), 1)

    def AND(self, a, b):
        return self.affine(((a, 1), (b, 1)), -1, 'relu')

    def OR(self, a, b):
        h = self.AND(a, b)
        return self.affine(((a, 1), (b, 1), (h, -1)))

    def XOR(self, a, b):
        h = self.AND(a, b)
        return self.affine(((a, 1), (b, 1), (h, -2)))

    def MUX(self, s, a, b):
        first, second = self.AND(s, a), self.AND(self.NOT(s), b)
        return self.affine(((first, 1), (second, 1)))


def compile_program(program):
    validate_program(program)
    register_offsets, input_offsets = {}, {}
    offset = 0
    for name, typ in program.registers:
        register_offsets[name] = tuple(range(offset, offset + typ.width))
        offset += typ.width
    reg_bits, block_count = offset, len(program.blocks)
    offset += block_count
    for name, typ in program.inputs:
        input_offsets[name] = tuple(range(offset, offset + typ.width))
        offset += typ.width
    builder = Builder(offset)

    def expression(expr):
        if expr.op == 'const':
            return tuple(builder.const((expr.value >> bit) & 1) for bit in range(expr.typ.width))
        if expr.op == 'reg':
            return register_offsets[expr.name]
        if expr.op == 'input':
            return input_offsets[expr.name]
        args = tuple(expression(arg) for arg in expr.args)
        if expr.op == 'not':
            return (builder.NOT(args[0][0]),)
        if expr.op in ('and', 'or', 'xor'):
            return (getattr(builder, expr.op.upper())(args[0][0], args[1][0]),)
        if expr.op == 'eq':
            equal = builder.const(1)
            for a, b in zip(*args):
                equal = builder.AND(equal, builder.NOT(builder.XOR(a, b)))
            return (equal,)
        if expr.op == 'add':
            carry, result = builder.const(0), []
            for a, b in zip(*args):
                pair_xor = builder.XOR(a, b)
                result.append(builder.XOR(pair_xor, carry))
                carry = builder.OR(builder.AND(a, b), builder.AND(pair_xor, carry))
            return tuple(result)
        return tuple(builder.MUX(args[0][0], a, b) for a, b in zip(args[1], args[2]))

    next_regs = {name: list(wires) for name, wires in register_offsets.items()}
    next_pc = [builder.const(0) for _ in program.blocks]
    halt_pcs = []

    def destination(target, guard):
        # Pairwise OR gates keep the local arithmetic certificate independent of CFG size.
        next_pc[target] = builder.OR(next_pc[target], guard)

    for pc, instruction in enumerate(program.blocks):
        guard = reg_bits + pc
        if type(instruction) is Assign:
            for name, expr in instruction.bindings:
                candidate = expression(expr)  # references old register wires only
                next_regs[name] = [builder.MUX(guard, value, old)
                                   for value, old in zip(candidate, next_regs[name])]
            destination(instruction.next, guard)
        elif type(instruction) is Branch:
            condition = expression(instruction.cond)[0]
            destination(instruction.yes, builder.AND(guard, condition))
            destination(instruction.no, builder.AND(guard, builder.NOT(condition)))
        elif type(instruction) is Jump:
            destination(instruction.next, guard)
        else:
            halt_pcs.append(pc)
            destination(pc, guard)
    outputs = tuple(wire for name, _ in program.registers for wire in next_regs[name]) + tuple(next_pc)
    return Compiled(program.registers, program.inputs, block_count, program.entry,
                    tuple(halt_pcs), tuple(builder.nodes), outputs)


def graph_to_dict(compiled):
    return {'schema': 'DMWK-A4-sparse-affine-relu-v1',
            'registers': [{'name': n, 'type': t.kind, 'width': t.width} for n, t in compiled.registers],
            'inputs': [{'name': n, 'type': t.kind, 'width': t.width} for n, t in compiled.inputs],
            'block_count': compiled.block_count, 'entry': compiled.entry,
            'halt_pcs': compiled.halt_pcs, 'state_count': compiled.state_count,
            'dag_input_count': compiled.input_count,
            'wire_order': 'register bits LSB-first, one-hot PC, external input bits LSB-first',
            'nodes': [{'output_wire': compiled.input_count+i, 'weights': node.terms,
                       'bias': node.bias, 'activation': node.activation}
                      for i, node in enumerate(compiled.nodes)],
            'next_state_output_wires': compiled.outputs,
            'affine_absolute_weight_plus_bias_bound': 4,
            'execution_order': 'all nodes in listed topological order; bias then listed weighted terms'}


def source_to_dict(program):
    def expr(e):
        result = {'op': e.op}
        if e.args:
            result['args'] = [expr(a) for a in e.args]
        if e.value is not None:
            result.update(value=e.value, type=e.typ.kind, width=e.typ.width)
        if e.name is not None:
            result['name'] = e.name
        return result
    blocks = []
    for instruction in program.blocks:
        if type(instruction) is Assign:
            blocks.append({'op': 'parallel_assign', 'bindings': [(n, expr(e)) for n, e in instruction.bindings],
                           'next': instruction.next})
        elif type(instruction) is Branch:
            blocks.append({'op': 'branch', 'cond': expr(instruction.cond),
                           'yes': instruction.yes, 'no': instruction.no})
        elif type(instruction) is Jump:
            blocks.append({'op': 'jump', 'next': instruction.next})
        else:
            blocks.append({'op': 'halt'})
    return {'registers': [(n, t.kind, t.width) for n, t in program.registers],
            'inputs': [(n, t.kind, t.width) for n, t in program.inputs],
            'entry': program.entry, 'blocks': blocks}


class Executor:
    """Actual FP32 or exact small-integer BF16 reference operations.

    Raw BF16 words represent scalar floating values; they never contain packed
    source integers. Signed arithmetic zero is tracked; gate outputs normalize
    zero. Every fixed graph node is evaluated on every tick.
    """

    def __init__(self, format_name):
        require(format_name in ('BF16', 'FP32'), 'Unsupported arithmetic format')
        self.format = format_name
        self.native = format_name == 'FP32'
        self.dtype = np.dtype(np.float32 if self.native else np.uint16)
        self.uint_dtype = np.dtype(np.uint32 if self.native else np.uint16)
        self.scalar_type = np.float32 if self.native else np.uint16
        self.sign = 0x80000000 if self.native else 0x8000
        self.encoded = {}
        for value in range(-4, 5):
            word = struct.unpack('>I', struct.pack('>f', value))[0]
            self.encoded[value] = word if self.native else word >> 16
        self.decoded = {word: value for value, word in self.encoded.items()}
        self.decoded[self.sign] = 0
        self.operations = {'multiply': 0, 'add': 0, 'relu': 0, 'linear': 0}
        self.arithmetic_checks = 0
        self.state_bit_checks = 0
        self.ticks = 0
        self.node_evaluations = 0
        self.observed_intermediate_values = set()

    def _from_bits(self, bits):
        return np.uint32(bits).view(np.float32) if self.native else np.uint16(bits)

    def const(self, value):
        require(type(value) is int and value in self.encoded, 'Non-small target constant')
        return self._from_bits(self.encoded[value])

    def scalar_bits(self, value):
        require(type(value) is self.scalar_type, 'Implicit arithmetic dtype promotion')
        return int(value.view(np.uint32)) if self.native else int(value)

    def _value(self, value):
        bits = self.scalar_bits(value)
        require(bits in self.decoded, 'Out-of-certificate intermediate operand')
        return self.decoded[bits]

    def _op(self, kind, a, b):
        av, bv = self._value(a), self._value(b)
        exact = av * bv if kind == 'multiply' else av + bv
        require(exact in self.encoded, 'Affine intermediate exceeded exact integer certificate')
        expected = self.encoded[exact]
        abits, bbits = self.scalar_bits(a), self.scalar_bits(b)
        if exact == 0:
            negative = ((bool(abits & self.sign) != bool(bbits & self.sign))
                        if kind == 'multiply' else (abits == self.sign and bbits == self.sign))
            expected = self.sign if negative else 0
        result = ((np.multiply if kind == 'multiply' else np.add)(a, b)
                  if self.native else self._from_bits(expected))
        require(self.scalar_bits(result) == expected, 'Target operation did not equal exact result bits')
        self.arithmetic_checks += 1
        self.operations[kind] += 1
        self.observed_intermediate_values.add(exact)
        return result

    def words(self, array):
        require(type(array) is np.ndarray and array.dtype == self.dtype,
                'State/input must have the actual target dtype')
        require(array.ndim == 1, 'State/input must be a one-dimensional vector')
        return array.view(self.uint_dtype)

    def _boolean_array(self, array, width):
        bits = self.words(array)
        require(array.shape == (width,), 'State/input vector width mismatch')
        require(np.all((bits == self.encoded[0]) | (bits == self.encoded[1])),
                'Illegal Boolean port encoding (including negative zero)')
        self.state_bit_checks += width

    def _validate_state(self, compiled, array):
        self._boolean_array(array, compiled.state_count)
        pc = self.words(array)[compiled.register_bit_count:]
        require(np.count_nonzero(pc == self.encoded[1]) == 1, 'PC must be one-hot')

    def encode_state(self, compiled, state):
        require(type(state) is State, 'Expected typed source State for encoding')
        _typed_values(compiled.registers, state.values, 'Encoded registers')
        require(type(state.pc) is int and 0 <= state.pc < compiled.block_count, 'Encoded PC out of range')
        bits = []
        for (_, typ), value in zip(compiled.registers, state.values):
            bits.extend((value >> i) & 1 for i in range(typ.width))
        bits.extend(int(i == state.pc) for i in range(compiled.block_count))
        return np.array([self.const(b) for b in bits], dtype=self.dtype)

    def encode_inputs(self, compiled, values):
        _typed_values(compiled.inputs, values, 'Encoded inputs')
        bits = [((value >> i) & 1) for (_, typ), value in zip(compiled.inputs, values)
                for i in range(typ.width)]
        return np.array([self.const(b) for b in bits], dtype=self.dtype)

    def decode_state(self, compiled, array):
        """Observer/oracle helper; not used by tick or graph evaluation."""
        self._validate_state(compiled, array)
        bits = tuple(int(v == self.encoded[1]) for v in self.words(array))
        values, offset = [], 0
        for _, typ in compiled.registers:
            values.append(sum(bits[offset+i] << i for i in range(typ.width)))
            offset += typ.width
        return State(tuple(values), bits[offset:].index(1))

    def check_state(self, compiled, actual, expected):
        self._validate_state(compiled, actual)
        reference = self.encode_state(compiled, expected)
        require(np.array_equal(self.words(actual), self.words(reference)), 'Source/target state bits differ')

    def tick(self, compiled, state, inputs):
        require(type(compiled) is Compiled, 'Expected validated compiled weight program')
        self._validate_state(compiled, state)
        external_width = compiled.input_count - compiled.state_count
        self._boolean_array(inputs, external_width)
        old, incoming = state.copy(), inputs.copy()
        old.flags.writeable = incoming.flags.writeable = False
        wires = list(old) + list(incoming)
        for node in compiled.nodes:
            accumulator = self.const(node.bias)
            for wire, coefficient in node.terms:
                product = self._op('multiply', self.const(coefficient), wires[wire])
                accumulator = self._op('add', accumulator, product)
            value = self._value(accumulator)
            if node.activation == 'relu' and value <= 0:
                accumulator = self.const(0)
            elif value == 0:
                accumulator = self.const(0)
            require(self._value(accumulator) in (0, 1), 'Compiled logical node violated Boolean closure')
            wires.append(accumulator)
            self.operations[node.activation] += 1
            self.node_evaluations += 1
        candidate = np.array([wires[index] for index in compiled.outputs], dtype=self.dtype)
        self._validate_state(compiled, candidate)
        require(not np.shares_memory(candidate, state) and not np.shares_memory(candidate, inputs),
                'Next state aliases old state or inputs')
        self.ticks += 1
        return candidate


def counter_program(width=6, target=37):
    typ = U(width)
    return Program((('counter', typ),), (),
        (Branch(EQ(R('counter'), C(target, typ)), 2, 1),
         Assign((('counter', ADD(R('counter'), C(1, typ))),), 0), Halt()))

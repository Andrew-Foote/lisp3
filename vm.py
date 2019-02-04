import typing as t
from functools import reduce
import operator
from base import LispError
from scanner import Symbol, Token
from compiler import Instruction, Operator

def product(iterable):
    return reduce(operator.mul, iterable, 1)

def exec_(instructions: t.Iterable[Instruction]):
    stack = []
    env = {
        '+': lambda *args: sum(args),
        '-': lambda x, y: x - y,
        '*': lambda *args: product(args),
    }

    for instruction in instructions:
        operator = instruction.operator
        location = instruction.location

        if operator == Operator.push:
            content, = instruction.args

            if not isinstance(content, Symbol):
                stack.append(content)
                continue

            symbol_content = content.content

            try:
                value = env[symbol_content]
            except KeyError:
                raise LispError(
                    f'undefined symbol "{symbol_content}"',
                    location
                )
                
            stack.append(value)
            continue

        if operator == Operator.call:
            proc = stack.pop()

            if not callable(proc):
                raise LispError(
                    f'head of procedure call expression is not a procedure',
                    location
                )

            arg_count, = instruction.args
            assert arg_count <= len(stack), "The virtual machine encountered a"\
            "stack underflow."
            args = [stack.pop() for _ in range(arg_count)]
            args.reverse()
            stack.append(proc(*args))
            continue

        if operator == Operator.def_:
            name, = instruction.args
            assert stack, "The virtual machine encountered a stack underflow."
            value = stack.pop()
            env[name] = value
            continue

        assert False, "The virtual machine encountered an invalid operator."

    return stack[-1]

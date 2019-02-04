import typing as t
from functools import reduce
import operator
from base import LispError
from scanner import Symbol, Token
from compiler import Instruction, Operator

def product(iterable):
    return reduce(operator.mul, iterable, 1)

class Machine:
    def __init__(self):
        self.env = {
            '+': lambda *args: sum(args),
            '-': lambda x, y: x - y,
            '*': lambda *args: product(args),
        }

    def exec_(self, instructions: t.Iterable[Instruction]):
        stack = []

        for instruction in instructions:
            operator = instruction.operator
            location = instruction.location
            args = instruction.args

            if operator == Operator.push:
                value, = args

                if not isinstance(value, Symbol):
                    stack.append(value)
                    continue

                content = value.content

                try:
                    bound_value = self.env[content]
                except KeyError:
                    raise LispError(f'undefined symbol "{content}"', location)
                    
                stack.append(bound_value)
            elif operator == Operator.call:
                proc = stack.pop()

                if not callable(proc):
                    raise LispError(
                        f'head of procedure call expression is not a procedure',
                        location
                    )

                arg_count, = args
                assert arg_count <= len(stack), "The virtual machine "\
                "encountered a stack underflow."
                args = [stack.pop() for _ in range(arg_count)]
                args.reverse()
                stack.append(proc(*args))
            elif operator == Operator.def_:
                symbol, = args
                assert stack, "The virtual machine encountered a stack "\
                "underflow."
                value = stack.pop()
                self.env[symbol.content] = value
            else:
                assert False, "The virtual machine encountered an invalid operator."

        return stack

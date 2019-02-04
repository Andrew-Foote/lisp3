import typing as t
from base import LispError
from scanner import Symbol, Token
from compiler import Instruction

def exec_(instructions: t.Iterable[Instruction]):
    stack = []
    env = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
    }

    for instruction in instructions:
        expr = instruction.expr

        if isinstance(expr, Token):
            content = expr.content

            if isinstance(content, Symbol):
                symbol_content = content.content

                try:
                    value = env[symbol_content]
                except KeyError:
                    raise LispError(
                        f'undefined symbol "{symbol_content}"',
                        expr.location
                    )
                
                stack.append(value)
            else:
                stack.append(content)
        else:
            proc = stack.pop()

            if not callable(proc):
                raise LispError(
                    f'head of procedure call expression is not a procedure',
                    expr.location
                )

            arg_count = len(expr.subexprs) - 1

            assert arg_count <= len(stack), "The virtual machine encountered a"\
            "stack underflow."

            args = [stack.pop() for _ in range(arg_count)]
            args.reverse()
            stack.append(proc(*args))

    return stack[-1]

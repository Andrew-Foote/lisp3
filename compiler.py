import typing as t
from enum import Enum
from base import LispError
from scanner import Token
from parser_ import Expr

# Compile the Lisp program into bytecode for a virtual stack machine.

# E.g.
# (+ (* 2 3) 4)
#
# PUSH 2 ON TOP OF STACK
# PUSH 3 ON TOP OF STACK
# PUSH * ON TOP OF STACK (NARGS 2)
# APPLY FUNCTION ON TOP OF STACK TO VALUES BELOW IT
# PUSH 4 ON TOP OF STACK
# PUSH + ON TOP OF STACK (NARGS 2)
# APPLY FUNCTION ON TOP OF STACK TO VALUES BELOW IT

# MULTIPLY TOP TWO ON STACK
# PUSH 4 ON TOP OF STACK
# ADD TOP TWO ON STACK
# RETURN VALUE ON TOP OF STACK
#
# (def pi 3.14) pi
# 
# BIND 3.14 TO PI
# PUSH PI ON TOP OF STACK
# RETURN VALUE ON TOP OF STACK
#
# (map square (list 1 2 3))
#
# PUSH SQUARE ON TOP OF STACK
# PUSH 1 ON TOP OF STACK
# PUSH 2 ON TOP OF STACK
# PUSH 3 ON TOP OF STACK
# PUSH LIST ON TOP OF STACK
# APPLY FUNCTION ON TOP OF STACK TO NEXT 3 VALUES BELOW
# PUSH MAP ON TOP OF STACK
# APPLY FUNCTION ON TOP OF STACK TO NEXT 2 VALUES BELOW IT
#
#
# ((iterate square 2) 4)
#
# PUSH 4 ON TOP OF STACK
# PUSH SQUARE ON TOP OF STACK
# PUSH 2 ON TOP OF STACK
# PUSH ITERATE ON TOP OF STACK
# APPLY FUNCTION ON TOP OF STACK TO NEXT 2 VALUES BELOW IT
# APPLY FUNCTION ON TOP OF STACK TO VALUE BELOW IT

class Operator(Enum):
    push = 0
    call = 1
    def_ = 2

Instruction = t.NamedTuple('Instruction', [
    ('op', Operator),
    ('expr', Expr),
    ('args', t.List),
])

def compile_expr(expr: Expr) -> t.Iterator[Instruction]:
    expr_stack = [expr]

    while expr_stack:
        expr = expr_stack.pop()

        if isinstance(expr, Instruction):
            yield expr
        elif isinstance(expr, Token):
            yield Instruction(Operator.push, expr)
        else:
            if not expr.subexprs:
                raise LispError(
                    'empty procedure call expression',
                    expr.location
                )

            head = expr.subexprs[0]
            tail = expr.subexprs[1:]

            if isinstance(head, Symbol):
                if head.content == 'def':
                    expr_stack.append(Instruction, (expr.subexprs[1]))
                    expr_stack.append(expr.subexprs[2])
            
            expr_stack.append(Instruction(expr))
            expr_stack.append(head)
            expr_stack.extend(reversed(expr.subexprs[1:]))

def compile_(expr: Expr) -> t.Iterator[Instruction]:
    for subexpr in expr.subexprs:
        yield from compile_expr(subexpr)

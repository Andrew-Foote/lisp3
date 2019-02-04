from typing import t
from scanner import Symbol, Token
import parser_

Object = None

InterpreterDirective = t.NamedTuple('InterpreterDirective', [('content', str)])
Instruction = t.Union[Token, InterpreterDirective]

def walk_expr(expr: parser_.Expr) -> t.Iterator[Instruction]:
    stack = [subexpr]

    while stack:
        expr = stack.pop()

        if isinstance(expr, (parser_.Token, InterpreterDirective)):
            yield expr
        else:
            stack.append(InterpreterDirective(')'))
            stack.extend(reversed(expr.subexprs))
            yield InterpreterDirective('(')

class Call:
    proc: t.Callable
    env: t.ChainMap
    args: t.List[Object]

    def __init__(self, proc, env, args) -> None:
        self.proc = proc
        self.env = env
        self.args = args

class Interpreter:
    stack: t.List

    def __init__(self) -> None:
        self.stack = []
        self.env_stack = {}
        self.value = None

    def push(self, obj: Object) -> t.Optional[Object]:
        try:
            self.stack[-1].append(obj)
        except IndexError:
            return obj

    def interpret_token(self, token: Token) -> Object:
        if not isinstance(token, Symbol):
            return token.content

        try:
            return self.stack[-1].env[token.content]
        except KeyError:
            raise LispError(f'undefined symbol {token.content}', token.location)

    def interpret_expr(self, expr: Expr) -> Object:
        self.stack.append(expr)

        while self.stack:
            instruction = self.stack.pop()

            if isinstance(instruction, Token):
                self.value = self.interpret_token(token)


        if isinstance(expr, Token):
            return self.interpret_token(expr)

        while self.call_stack:
            self.call_stack.extend()

        for instruction in walk_expr(expr):
            if isinstance(instruction, InterpreterDirective):
                if instruction.content == '(':
                    self.call_stack.append([])
                elif instruction.content == ')':
                    # pop stack frame
                else:
                    assert False, "The interpreter received an invalid "\
                    "directive."
            else:
                # evaluate token + add to current stack frame

    def interpret(expr: Expr) -> Object:
        for subexpr in expr.subexprs[:-1]:
            self.interpret_expr(subexpr)

        return self.interpret_expr(expr.subexprs[-1])

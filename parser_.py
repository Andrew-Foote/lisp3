import typing as t
from base import Location, LispError
from scanner import ParserDirective, Token

ComplexExpr = t.NamedTuple('ComplexExpr', [
    ('location', Location),
    ('subexprs', t.Tuple['Expr', ...]),
])

Expr = t.Union[Token, ComplexExpr]

ExprFragment = t.NamedTuple('ExprFragment', [
    ('location', Location),
    ('subexprs', t.List[Expr]),
])

class Parser:
    expr_stack: t.List[ExprFragment]

    def __init__(self) -> None:
        self.expr_stack = [ExprFragment(None, [])]

    def parse(self, tokens: t.Iterable[Token]) -> None:
        for token in tokens:
            content = token.content

            if isinstance(content, ParserDirective):
                if content.content == '(':
                    self.expr_stack.append(ExprFragment(token.location, []))
                elif content.content == ')':
                    if len(self.expr_stack) <= 1:
                        raise LispError(
                            'Unmatched closing parenthesis',
                            token.location
                        )

                    fragment = self.expr_stack.pop()
                    expr = ComplexExpr(fragment.location, tuple(fragment.subexprs))
                    self.expr_stack[-1].subexprs.append(expr)
                else:
                    assert False, "The parser received an invalid directive."
            else:
                self.expr_stack[-1].subexprs.append(token)

    def end(self) -> Expr:
        fragment = self.expr_stack.pop()

        if self.expr_stack:
            raise LispError(
                'Unmatched opening parentheses',
                self.expr_stack[-1].location,
            )

        return ComplexExpr(fragment.location, tuple(fragment.subexprs))

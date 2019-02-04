import typing as t
from functools import partial
from fractions import Fraction
from base import basedigit, Location, LispError
from scanner import Lexeme, Symbol, Token, ScannerYield

def enumerate_lexeme_with_locations(lexeme):
    for i, c in enumerate(lexeme.content):
        yield Location(
            lexeme.location.filename,
            lexeme.location.line_number,
            lexeme.location.line,
            lexeme.location.col + i
        ), c

def eval_lexeme(lexeme: Lexeme) -> Token:
    def eval_first_c(location: Location, c: str):
        assert c is not None, "The evaluator received an empty lexeme."

        if c.isdigit():
            return partial(eval_integer_literal,
                sign=1,
                value=ord(c) - ord('0'),
            )
        elif c == '+':
            return eval_plus
        elif c == '-':
            return eval_minus

        return partial(eval_symbol, content=[c])

    def eval_integer_literal(location: Location, c: str,
    *, sign: int, value: int):
        if c is None:
            return sign * value

        if c.isdigit():
            return partial(eval_integer_literal,
                sign=sign,
                value=10 * value + (ord(c) - ord('0')),
            )

        if c == '_':
            return partial(eval_integer_literal, sign=sign, value=value)

        if c == '#':
            return partial(eval_integer_literal_with_base,
                sign=sign,
                value=0,
                base=value,
            )
                
        if c == '.':
            return partial(eval_real_literal,
                sign=sign,
                value=Fraction(value),
                base=10,
                denominator=10,
            )

        raise LispError(
            'Invalid character in base 10 integer literal',
            location,
        )

    def eval_integer_literal_with_base(location: Location, c: str,
    *, sign: int, value: int, base: int):
        if c is None:
            return sign * value

        try:
            digit = basedigit(c, base)
        except ValueError:
            pass
        else:
            return partial(eval_integer_literal_with_base,
                sign=sign,
                value=base * value + digit,
                base=base,
            )

        if c == '_':
            return partial(eval_integer_literal_with_base,
                sign=sign,
                value=value,
                base=base,
            )

        if c == '.':
            return partial(eval_real_literal,
                sign=sign,
                value=Fraction(value),
                base=base,
                denominator=base,
            )

        raise LispError(
            f'Invalid character in base {base} integer literal',
            location,
        )

    def eval_real_literal(location: Location, c: str, *,
    sign, value, base, denominator):
        if c is None:
            return sign * value

        try:
            digit = basedigit(c, base)
        except ValueError:
            pass
        else:
            return partial(eval_real_literal,
                sign=sign,
                value=value + Fraction(digit, denominator),
                base=base,
                denominator=denominator * base,
            )

        if c == '_':
            return partial(eval_real_literal,
                sign=sign,
                value=value,
                base=base,
                denominator=denominator,
            )

        raise LispError(
            f'Invalid character in base {base} real literal',
            location,
        )

    def eval_plus(location: Location, c: str):
        if c is None:
            return Symbol('+')

        if c.isdigit():
            return partial(eval_integer_literal,
                sign=1,
                value=ord(c) - ord('0'),
            )
        
        return partial(eval_symbol, content=[f'+{c}'])

    def eval_minus(location: Location, c: str):
        if c is None:
            return Symbol('-')

        if c.isdigit():
            return partial(eval_integer_literal,
                sign=-1,
                value=ord(c) - ord('0'),
            )

        return partial(eval_symbol, content=[f'-{c}'])

    def eval_symbol(location: Location, c: str,
    *, content: t.List[str]):
        if c is None:
            return Symbol(''.join(content))

        content.append(c)
        return partial(eval_symbol, content=content)

    state = eval_first_c

    for location, c in enumerate_lexeme_with_locations(lexeme):
        state = state(location, c)
        
    return Token(lexeme.location, state(None, None))

def eval_lexemes(lexemes: t.Iterator[ScannerYield]) -> t.Iterator[Token]:
    for lexeme in lexemes:
        if isinstance(lexeme, Token):
            yield lexeme
        else:
            yield eval_lexeme(lexeme)

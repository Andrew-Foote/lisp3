import typing as t
from functools import partial
from fractions import Fraction
from base import basedigit, Location, LispError

def enumerate_file_with_locations(filename: str, f: t.TextIO)\
-> t.Iterator[t.Tuple[Location, str]]:
    """Iterate over the `Locations` within the given file, yielding pairs
    consisting of the `Location` and the character at that location."""
    for line_number, line in enumerate(f, start=1):
        for col, c in enumerate(line):
            yield Location(filename, line_number, line[:-1], col), c

Lexeme = t.NamedTuple('Lexeme', [('location', Location), ('content', str)])

class LexemeFragment:
    """A mutable `Lexeme`. The characters of its `content` are stored within a
    list rather than a string, for fast appending."""
    location: Location
    content: t.List[str]

    def __init__(self, location: Location, content: t.List[str]) -> None:
        self.location = location
        self.content = content

ParserDirective = t.NamedTuple('ParserDirective', [('content', str)])
Symbol = t.NamedTuple('Symbol', [('content', str)])

Token = t.NamedTuple('Token', [
    ('location', Location),
    ('content', t.Union[ParserDirective, Symbol, str, int, Fraction]),
])

ScannerYield = t.Union[Lexeme, Token]

class Scanner:
    """A scanner of Lisp source code. The scanner exists independently of any
    input stream, and its state is preserved after an input stream is exhausted,
    so that it can be hooked to a new stream and resume scanning. This
    functionality is used by the interpreter to allow for multi-line inputs."""
    SIMPLE_ESCAPE_SEQUENCES = {
        'a': '\a',
        'b': '\b',
        't': '\t',
        'n': '\n',
        'v': '\v',
        'f': '\f',
        'r': '\r',
        'e': '\x1b',
        '"': '"',
        "'": "'",
        '\\': '\\',
        '(': '(',
        '\n': '',
    }

    state: t.Callable[['Scanner', Location, str], t.Iterator[ScannerYield]]

    def __init__(self) -> None:
        self.state = self.scan_whitespace

    def scan(self, filename: str, f: t.TextIO) -> t.Iterator[ScannerYield]:
        """Scan an input stream and yield its tokens."""
        for location, c in enumerate_file_with_locations(filename, f):
            self.state = yield from self.state(location, c)

    def scan_whitespace(self, location: Location, c: str)\
    -> t.Iterator[ScannerYield]:
        if c.isspace():
            return self.scan_whitespace
        elif c in '()':
            yield Token(location, ParserDirective(c))
            return self.scan_whitespace
        elif c == ';':
            return self.scan_comment
        elif c in '\'"':
            return partial(self.scan_string,
                fragment=LexemeFragment(location, []),
                delimiter=c,
            )
        
        return partial(self.scan_lexeme,
            fragment=LexemeFragment(location, [c]),
        )

    def scan_comment(self, location: Location, c: str)\
        -> t.Iterator[ScannerYield]:
        yield from ()

        if c == ':':
            return partial(self.scan_block_comment, level=0)
        elif c == '\n':
            return self.scan_whitespace
        
        return self.scan_line_comment

    def scan_block_comment(self, location: Location, c: str,
    *, level: int) -> t.Iterator[ScannerYield]:
        yield from ()

        if c == ':':
            return partial(self.scan_block_comment_colon, level=level)
        elif c == ';':
            return partial(self.scan_block_comment_semicolon, level=level)

        return partial(self.scan_block_comment, level=level)

    def scan_block_comment_colon(self, location: Location, c: str,
    *, level: int) -> t.Iterator[ScannerYield]:
        yield from ()    

        if c == ';':
            if not level:
               return self.scan_whitespace
            
            return partial(self.scan_block_comment, level=level - 1)
        
        return partial(self.scan_block_comment, level=level)

    def scan_block_comment_semicolon(self, location: Location, c: str,
    *, level: int) -> t.Iterator[ScannerYield]:
        yield from ()

        if c == ':':
            return partial(self.scan_block_comment, level=level + 1)
        
        return partial(self.scan_block_comment, level=level)

    def scan_line_comment(self, location: Location, c: str)\
    -> t.Iterator[ScannerYield]:
        yield from ()

        if c == '\n':
            return self.scan_whitespace

        return self.scan_line_comment
            
    def scan_string(self, location: Location, c: str,
    *, fragment: LexemeFragment, delimiter: str) -> t.Iterator[ScannerYield]:
        if c == '\\':
            return partial(
                self.scan_escape_sequence,
                fragment=fragment,
                delimiter=delimiter,
            )
        elif c == delimiter:
            yield Token(fragment.location, ''.join(fragment.content))
            return self.scan_whitespace
        
        fragment.content.append(c)
        return partial(self.scan_string,
            fragment=fragment,
            delimiter=delimiter
        )
                    
    def scan_escape_sequence(self, location: Location, c: str,
    *, fragment: LexemeFragment, delimiter: str) -> t.Iterator[ScannerYield]:
        yield from ()

        if c == '(':
            return partial(self.scan_char_code,
                fragment=fragment,
                delimiter=delimiter,
                code=0,
            )

        try:
            escaped_c = self.SIMPLE_ESCAPE_SEQUENCES[c]
        except KeyError:
            raise LispError('Invalid escape sequence', location)
        
        fragment.content.append(escaped_c)
        return partial(self.scan_string,
            fragment=fragment,
            delimiter=delimiter,
        )

    def scan_char_code(self, location: Location, c: str,
    *, fragment: LexemeFragment, delimiter: str, code: int)\
    -> t.Iterator[ScannerYield]:
        yield from ()

        if c.isdigit():
            return partial(self.scan_char_code,
                fragment=fragment,
                delimiter=delimiter,
                code=10 * code + (ord(c) - ord('0')),
            )
        elif c == '#':
            return partial(self.scan_char_code_with_base,
                fragment=fragment,
                delimiter=delimiter,
                base=code,
                code=0,
            )
        elif c == ')':
            fragment.content.append(chr(code))
            return partial(self.scan_string,
                fragment=fragment,
                delimiter=delimiter,
            )
        else:
            raise LispError('Invalid character code', location)

    def scan_char_code_with_base(self, location: Location, c: str,
    *, fragment: LexemeFragment, delimiter: str, base: int, code: int)\
    -> t.Iterator[ScannerYield]:
        yield from ()

        try:
            digit = basedigit(c, base)
        except ValueError:
            pass
        else:
            return partial(
                self.scan_char_code_with_base,
                fragment=fragment,
                delimiter=delimiter,
                base=base,
                code=base * code + digit,
            )

        if c == ')':
            fragment.content.append(chr(code))
            return partial(self.scan_string,
                fragment=fragment,
                delimiter=delimiter,
            )
        else:
            raise LispError('Invalid character in character code', location)

    def scan_lexeme(self, location: Location, c: str,
    *, fragment: LexemeFragment) -> t.Iterator[ScannerYield]:
        def flush():
            yield Lexeme(fragment.location, ''.join(fragment.content))
        
        if c.isspace():
            yield from flush()
            return self.scan_whitespace
        elif c in '()':
            yield from flush()
            yield Token(location, ParserDirective(c))
            return self.scan_whitespace
        elif c in '\'"':
            yield from flush()
            return partial(self.scan_string,
                fragment=[],
                delimiter=c,
            )
        else:
            fragment.content.append(c)
            return partial(self.scan_lexeme,
                fragment=fragment,
            )

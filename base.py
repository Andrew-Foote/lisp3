import typing as t

def basedigit(c: str, base: int) -> int:
    """Interpret a character as a single-digit integer in the given
    base."""
    if len(c) != 1:
        raise TypeError(
            f'basedigit() expected a character, but string of length {len(c)}'
            'found'
        )

    if base <= 10:
        digit = ord(c) - ord('0')

        if 0 <= digit < 10:
            return digit

        raise ValueError(
            f'invalid character for basedigit() with base {base}: {repr(c)}'
        )
    elif base <= 36:
        digit = ord(c) - ord('0')

        if 0 <= digit < 10:
            return digit
        
        digit = ord(c) - ord('a')

        if 0 <= digit < base:
            return 10 + digit

        raise ValueError(
            f'invalid character for basedigit() with base {base}: {repr(c)}'
        )

    raise ValueError(f'invalid base for basedigit(): {base}')

class Location(t.NamedTuple('Location', [
    ('filename', str),
    ('line_number', int),
    ('line', str),
    ('col', int),
])):
    """The location of a character within the file system. These are kept track
    of for error logging."""

class LispError(Exception):
    """A compile-time error in a Lisp program."""
    def __init__(self, msg: str, location: Location) -> None:
        super().__init__(msg)
        self.location = location

    def fullstr(self) -> str:
        return f"""\
Error in "{self.location.filename}" at line {self.location.line}, column {self.location.col}
  {self.location.line}
  {' ' * self.location.col}^
{str(self)}"""

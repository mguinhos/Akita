from functools import cache
from typing import Iterator
from enum import Enum

from io import TextIOBase
from io import IOBase

class Token(Enum):
    Eof=                '\0'

    Colon=              ':'
    Semicolon=          ';'
    Comma=              ','
    Dot=                '.'
    Ellipsis=           '...'

    Not=                '!'
    Equal=              '='
    GreaterThan=        '>'
    LessThan=           '<'
    Plus=               '+'
    Minus=              '-'
    Star=               '*'
    Slash=              '/'
    Percent=            '%'

    NotEqual=           '!='
    EqualEqual=         '=='
    GreaterThanEqual=   '>='
    LessThanEqual=      '<='
    PlusEqual=          '+='
    MinusEqual=         '-='
    StarEqual=          '*='
    SlashEqual=         '/='
    PercentEqual=       '%='

    Arrow=              '->'

    LeftParenthesis=    '('
    RightParenthesis=   ')'
    LeftBracket=        '['
    RightBracket=       ']'

    def __bool__(self):
        return self.value != '\0'

    def __hash__(self):
        return hash(self.value)

    def __len__(self):
        return len(self.value)
    
    def __eq__(self, value: str):
        return self.value == value

TOKENS_SORTED = sorted(Token, key=len, reverse=True)
LONGEST_TOKEN = TOKENS_SORTED[0]
LEN_LONGEST_TOKEN = len(LONGEST_TOKEN)

class Keyword(Enum):
    Pass=               'pass'
    From=               'from'
    Import=             'import'
    Class=              'class'
    Def=                'def'
    Return=             'return'
    While=              'while'
    For=                'for'
    In=                 'in'
    If=                 'if'
    Elif=               'elif'
    Else=               'else'
    Break=              'break'
    Continue=           'continue'

    def __hash__(self):
        return hash(self.value)

    def __len__(self):
        return len(self.value)
    
    def __eq__(self, value: str):
        return self.value == value

KEYWORDS_SORTED = sorted(Keyword, key=len, reverse=True)
LONGEST_KEYWORD = KEYWORDS_SORTED[0]
LEN_LONGEST_KEYWORD = len(LONGEST_KEYWORD)

class Name:
    def __init__(self, value: str, hint: "Name"=None):
        self.value = value
        self.hint = hint
    
    def __repr__(self):
        if self.hint is None:
            return f'Name({self.value})'
            
        return f'Name({self.value}, {self.hint})'
    
    def __hash__(self):
        return hash(self.value)

    def __len__(self):
        return len(self.value)
    
    def __eq__(self, value: str):
        if type(value) is type(self):
            return self.value == value.value
            
        return self.value == value

class Literal:
    def __init__(self, value: str | bool | int | float, fstring=False):
        self.value = value
        self.fstring = fstring
    
    def __repr__(self):
        if self.fstring:
            return f'Literal(f{self.value!r})'

        return f'Literal({self.value!r})'
    
    def __hash__(self):
        return hash(self.value)

    def __len__(self):
        return len(self.value)
    
    def __eq__(self, value: str):
        return self.value == value
    
    @property
    def hint(self):
        return Name(type(self.value).__name__, hint=Name('type'))

class Comment:
    def __init__(self, value: str):
        self.value = value
    
    def __repr__(self):
        return f'Comment({self.value})'

class Indent:
    def __init__(self, value: int):
        self.value = value
    
    def __repr__(self):
        return f'Indent({self.value})'
    
    def __eq__(self, value: str):
        return self.value == value

AnyToken = Keyword | Token | Name | Literal | Comment | Indent


def drop(stream: TextIOBase, decrement=1) -> int:
    return stream.seek(stream.tell() - decrement)

def take(stream: TextIOBase) -> str:
    return stream.read(1)


def scan_token(stream: TextIOBase) -> Token:
    position = stream.tell()

    for token in TOKENS_SORTED:
        chunk = stream.read(len(token))

        if chunk.startswith(token.value):
            return token
        
        stream.seek(position)

    raise SyntaxError(f'invalid token {stream.read(1)!r}')

def scan_name(stream: TextIOBase, name: str) -> Name:
    while char := take(stream):
        if char >= 'a' and char <= 'z' or char >= 'A' and char <= 'Z':
            name += char
        elif char == '_' or char >= '0' and char <= '9':
            name += char
        else:
            break
    
    if char:
        drop(stream)
    
    return Name(name)

def scan_number(stream: TextIOBase, value: str) -> Literal:
    while char := take(stream):
        if char == '_' or char >= '0' and char <= '9':
            value += char
        else:
            break
    
    if char != '.':
        if char:
            drop(stream)
        
        return Literal(int(value))
    
    value += char
    
    while char := take(stream):
        if char == '_' or char >= '0' and char <= '9':
            value += char
        else:
            break
    
    if char:
        drop(stream)
    
    return Literal(float(value))

def scan_hex_number(stream: TextIOBase, value: str) -> Literal:
    while char := take(stream):
        if char >= '0' and char <= '9' or char >= 'a' and char <= 'f':
            value += char
        elif char == '_' or char >= 'A' and char <= 'f':
            value += char
        else:
            break
    
    if char:
        drop(stream)
    
    return Literal(int(value, 16))

def scan_bin_number(stream: TextIOBase, value: str) -> Literal:
    while char := take(stream):
        if char == '_' or char == '0' or char == '1':
            value += char
        else:
            break
    
    if char:
        drop(stream)
    
    return Literal(int(value, 2))

def scan_string(stream: TextIOBase, quote: str) -> Literal:
    value = str()

    while char := take(stream):
        if char == quote:
            break
        
        if char == '\\':
            char = take(stream)

            if char == quote:
                value += char
            else:
                value += '\\' + char
        else:
            value += char
    
    return Literal(value)

def scan_comment(stream: TextIOBase) -> Comment:
    value = str()

    while char := take(stream):
        if char == '\n':
            break
        else:
            value += char 
    
    if char:
        drop(stream)
    
    return Comment(value.strip())

def scan_indent(stream: TextIOBase) -> Indent:
    value = 0

    while char := take(stream):
        if char == ' ':
            value += 1
        else:
            break
    
    if char:
        drop(stream)
    
    if char == '\n':
        return Indent(0)
    
    return Indent(value)

class TokenHook:
    def __init__(self, iterator: Iterator[AnyToken], position=0):
        self.iterator = iterator
        self.position = position
        self.cache = []
    
    def __iter__(self):
        try:
            while (token := self.take()) is not Token.Eof:
                yield token
            
        except StopIteration:
            pass
        
        yield Token.Eof
    
    def take(self) -> AnyToken:
        if self.position < len(self.cache):
            token = self.cache[self.position]
            self.position += 1

            return token
        
        token = next(self.iterator)
        self.cache.append(token)
        self.position += 1

        return token
    
    def drop(self):
        self.position -= 1

        return

def tokenize(stream: TextIOBase) -> TokenHook:
    def iterator() -> Iterator[AnyToken]:
        while char := take(stream):
            if char == ' ' or char == '\t':
                continue
            
            if char == '\n':
                yield scan_indent(stream)
            
            elif char == 'f':
                pref = take(stream)

                if pref == '"' or pref == "'":
                    yield Literal(scan_string(stream, pref).value, fstring=True)
                else:
                    drop(stream)

                    name = scan_name(stream, char)

                    if name in KEYWORDS_SORTED:
                        yield Keyword(name)
                    else:
                        yield name
            
            elif char >= 'a' and char <= 'z':
                name = scan_name(stream, char)

                if name in KEYWORDS_SORTED:
                    yield Keyword(name)
                else:
                    yield name
            
            elif char == '_' or char >= 'A' and char <= 'Z':
                yield scan_name(stream, char)
            elif char >= '0' and char <= '9':
                fmt = take(stream)

                if fmt == 'x':
                    yield scan_hex_number(stream, take(stream))
                elif fmt == 'b':
                    yield scan_bin_number(stream, take(stream))
                else:
                    if fmt:
                        drop(stream)

                    yield scan_number(stream, char)

            elif char == '"' or char == "'":
                yield scan_string(stream, char)
            elif char == '#':
                yield scan_comment(stream)
            else:
                drop(stream)
                yield scan_token(stream)
        
        yield Token.Eof
    
    return TokenHook(iterator())
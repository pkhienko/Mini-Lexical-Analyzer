"""Token rules and output formatting for the assignment's miniature language."""

from sly import Lexer


class LexicalError(Exception):
    """The first invalid lexeme; analysis must stop at this exception."""

    def __init__(self, character, lineno, index, detail=None):
        self.character = character
        self.lineno = lineno
        self.index = index
        message = f"Lexical error: unexpected character {character}"
        if detail:
            message += f" ({detail})"
        super().__init__(message)


class MiniLexer(Lexer):
    tokens = {
        ID, INTEGER, STRING, KEYWORD,
        PLUS, MINUS, TIMES, DIVIDE, ASSIGN, GT, GE, LT, LE, EQ,
        INCREMENT, DECREMENT, LPAREN, RPAREN, SEMICOLON,
    }
    ignore = " \t\r"

    # Rules are ordered: comments precede division, and long operators
    # precede their one-character prefixes.
    @_(r'//[^\n]*')
    def ignore_line_comment(self, token):
        pass

    @_(r'/\*(?:[^*]|\*(?!/))*(?:\*/|\Z)')
    def ignore_block_comment(self, token):
        if len(token.value) < 4 or not token.value.endswith("*/"):
            raise LexicalError("/", token.lineno, token.index,
                               "unterminated block comment")
        self.lineno += token.value.count("\n")

    GE = r'>='
    LE = r'<='
    EQ = r'=='
    INCREMENT = r'\+\+'
    DECREMENT = r'--'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    ASSIGN = r'='
    GT = r'>'
    LT = r'<'
    LPAREN = r'\('
    RPAREN = r'\)'
    SEMICOLON = r';'
    STRING = r'"[^"\n\r]*"'

    # Reject 1score as a whole rather than silently emitting INTEGER + ID.
    @_(r'[0-9]+[a-zA-Z_][a-zA-Z0-9_]*')
    def ignore_invalid_identifier(self, token):
        raise LexicalError(token.value[0], token.lineno, token.index,
                           f"invalid identifier {token.value}")

    INTEGER = r'[0-9]+'
    ID = r'[a-zA-Z][a-zA-Z0-9]*'
    ID['if'] = KEYWORD
    ID['then'] = KEYWORD
    ID['else'] = KEYWORD
    ID['endif'] = KEYWORD
    ID['while'] = KEYWORD
    ID['do'] = KEYWORD
    ID['endwhile'] = KEYWORD
    ID['print'] = KEYWORD
    ID['newline'] = KEYWORD
    ID['read'] = KEYWORD

    @_(r'\n+')
    def ignore_newline(self, token):
        self.lineno += len(token.value)

    def error(self, token):
        detail = "unterminated string" if token.value[0] == '"' else None
        raise LexicalError(token.value[0], token.lineno, token.index, detail)


class Analyzer:
    """One fresh symbol table per input; output is yielded in source order."""

    def __init__(self):
        self.symbol_table = set()

    def analyze(self, source):
        self.symbol_table.clear()
        for token in MiniLexer().tokenize(source):
            if token.type == "ID":
                if token.value in self.symbol_table:
                    yield f'identifier "{token.value}" already in symbol table'
                else:
                    self.symbol_table.add(token.value)
                    yield f"new identifier: {token.value}"
            else:
                label = {
                    "INTEGER": "integer", "STRING": "string",
                    "KEYWORD": "keyword", "LPAREN": "left parenthesis",
                    "RPAREN": "right parenthesis", "SEMICOLON": "semicolon",
                }.get(token.type, "operator")
                yield f"{label}: {token.value}"

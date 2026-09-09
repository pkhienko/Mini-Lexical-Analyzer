from sly import Lexer


def token_rule(pattern):
    def decorate(function):
        setattr(function, "pattern", pattern)
        return function
    return decorate


class LexicalError(Exception):
    def __init__(self, character, lineno, index, detail=None):
        self.character = character
        self.lineno = lineno
        self.index = index
        message = f"Lexical error: unexpected character {character}"
        if detail:
            message += f" ({detail})"
        super().__init__(message)


class MiniLexer(Lexer):
    tokens = {"ID", "INTEGER", "STRING", "KEYWORD", "PLUS", "MINUS", "TIMES", "DIVIDE", "ASSIGN", "GT", "GE", "LT", "LE", "EQ", "INCREMENT", "DECREMENT", "LPAREN", "RPAREN", "SEMICOLON"}
    keywords = {"if", "then", "else", "endif", "while", "do", "endwhile", "print", "newline", "read"}
    ignore = " \t\r"

    @token_rule(r'//[^\n]*')
    def ignore_line_comment(self, token):
        pass

    @token_rule(r'/\*(?:[^*]|\*(?!/))*(?:\*/|\Z)')
    def ignore_block_comment(self, token):
        if len(token.value) < 4 or not token.value.endswith("*/"):
            raise LexicalError("/", token.lineno, token.index, "unterminated block comment")
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

    @token_rule(r'[0-9]+[a-zA-Z_][a-zA-Z0-9_]*')
    def ignore_invalid_identifier(self, token):
        raise LexicalError(token.value[0], token.lineno, token.index, f"invalid identifier {token.value}")

    INTEGER = r'[0-9]+'

    @token_rule(r'[a-zA-Z][a-zA-Z0-9]*')
    def ID(self, token):
        token.type = "KEYWORD" if token.value in self.keywords else "ID"
        return token

    @token_rule(r'\n+')
    def ignore_newline(self, token):
        self.lineno += len(token.value)

    def error(self, token):
        detail = "unterminated string" if token.value[0] == '"' else None
        raise LexicalError(token.value[0], token.lineno, token.index, detail)


class Analyzer:
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
                label = { "INTEGER": "integer", "STRING": "string", "KEYWORD": "keyword", "LPAREN": "left parenthesis", "RPAREN": "right parenthesis", "SEMICOLON": "semicolon", }.get(token.type, "operator")
                yield f"{label}: {token.value}"

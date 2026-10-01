from sly import Lexer

TOKEN_LABELS = {"INTEGER": "integer", "STRING": "string", "KEYWORD": "keyword", "LPAREN": "left parenthesis", "RPAREN": "right parenthesis", "SEMICOLON": "semicolon"}

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


    @token_rule(r'/\*[\s\S]*?\*/')
    def ignore_block_comment(self, token):
        self.lineno += token.value.count("\n")


    @token_rule(r'/\*')
    def ignore_unclosed_comment(self, token):
        raise LexicalError("/", token.lineno, token.index, "unterminated block comment")


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
        if token.value in self.keywords:
            token.type = "KEYWORD"
        return token


    @token_rule(r'\n+')
    def ignore_newline(self, token):
        self.lineno += len(token.value)


    def error(self, token):
        detail = None
        if token.value[0] == '"':
            detail = "unterminated string"
        raise LexicalError(token.value[0], token.lineno, token.index, detail)


def format_token(token, symbol_table):
    if token.type == "ID":
        if token.value in symbol_table:
            return f'identifier "{token.value}" already in symbol table'
        symbol_table.add(token.value)
        return f"new identifier: {token.value}"
    label = TOKEN_LABELS.get(token.type, "operator")
    return f"{label}: {token.value}"


def analyze(source):
    symbol_table = set()
    lexer = MiniLexer()
    for token in lexer.tokenize(source):
        print(format_token(token, symbol_table))
    return symbol_table

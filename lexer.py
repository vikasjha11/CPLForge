<<<<<<< HEAD
=======
# M1: Full lexer — tokenise CPL, define all token types (INT, ID, PLUS...)
# M2: Extended lexer for new CPL keywords (string, array, print, input)
>>>>>>> 35f1492d35f2c5706a6f1004b84e92afbfc194d2

import re

# ─────────────────────────────────────────────
#  TOKEN TYPES
# ─────────────────────────────────────────────

# Literals
TT_INT       = 'INT'      
TT_FLOAT     = 'FLOAT'     
TT_STRING    = 'STRING'    

# Identifiers & Keywords
TT_ID        = 'ID'        # variable / function name
TT_KEYWORD   = 'KEYWORD'   

# Arithmetic operators
TT_PLUS      = 'PLUS'      
TT_MINUS     = 'MINUS'    
TT_MUL       = 'MUL'      
TT_DIV       = 'DIV'      
TT_MOD       = 'MOD'       

# Comparison operators
TT_EQ        = 'EQ'        # ==
TT_NEQ       = 'NEQ'       # !=
TT_LT        = 'LT'        # <
TT_GT        = 'GT'        # >
TT_LTE       = 'LTE'       # <=
TT_GTE       = 'GTE'       # >=

# Assignment
TT_ASSIGN    = 'ASSIGN'    # =

# Logical operators
TT_AND       = 'AND'       # &&
TT_OR        = 'OR'        # ||
TT_NOT       = 'NOT'       # !

# Delimiters
TT_LPAREN    = 'LPAREN'    # (
TT_RPAREN    = 'RPAREN'    # )
TT_LBRACE    = 'LBRACE'    # {
TT_RBRACE    = 'RBRACE'    # }
TT_LBRACKET  = 'LBRACKET'  # [   
TT_RBRACKET  = 'RBRACKET'  # ]   
TT_SEMICOLON = 'SEMICOLON' # ;
TT_COMMA     = 'COMMA'     # ,

# Special
TT_EOF       = 'EOF'       # end of file

# ─────────────────────────────────────────────
#  KEYWORDS (M1 base + M2 extensions)
# ─────────────────────────────────────────────

KEYWORDS = {
    # M1 — base CPL keywords
    'int',
    'float',
    'if',
    'else',
    'while',
    'return',
    'true',
    'false',

    # M2 — new CPL keywords (bootstrapping prep)
    'string',    # string data type
    'array',     # array declaration
    'print',     # built-in output
    'input',     # built-in input
    'func',      # function declaration (M2 extension)
}

# ─────────────────────────────────────────────
#  TOKEN CLASS
# ─────────────────────────────────────────────

class Token:
    """Represents a single token with type, value, and source position."""

    def __init__(self, type_, value, line=None, col=None):
        self.type  = type_
        self.value = value
        self.line  = line
        self.col   = col

    def __repr__(self):
        if self.value is not None:
            return f'Token({self.type}, {self.value!r}, L{self.line}:C{self.col})'
        return f'Token({self.type}, L{self.line}:C{self.col})'


# ─────────────────────────────────────────────
#  LEXER ERROR
# ─────────────────────────────────────────────

class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"LexerError at L{line}:C{col} — {message}")
        self.line = line
        self.col  = col


# ─────────────────────────────────────────────
#  LEXER CLASS
# ─────────────────────────────────────────────

class Lexer:
    """
    Converts a CPL source string into a flat list of Tokens.
    Usage:
        lexer  = Lexer(source_code)
        tokens = lexer.tokenize()
    """

    def __init__(self, source: str):
        self.source = source
        self.pos    = 0          # current character index
        self.line   = 1
        self.col    = 1
        self.tokens = []

    # ── helpers ──────────────────────────────

    def current(self):
        """Return current character or None if past end."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def peek(self, offset=1):
        """Look ahead without consuming."""
        idx = self.pos + offset
        if idx < len(self.source):
            return self.source[idx]
        return None

    def advance(self):
        """Consume current character and update position counters."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col   = 1
        else:
            self.col  += 1
        return ch

    def skip_whitespace(self):
        while self.current() in (' ', '\t', '\r', '\n'):
            self.advance()

    def skip_comment(self):
        """Skip // single-line and /* */ multi-line comments."""
        if self.current() == '/' and self.peek() == '/':
            while self.current() and self.current() != '\n':
                self.advance()
        elif self.current() == '/' and self.peek() == '*':
            self.advance(); self.advance()          # consume /*
            while self.current():
                if self.current() == '*' and self.peek() == '/':
                    self.advance(); self.advance()  # consume */
                    return
                self.advance()
            raise LexerError("Unterminated block comment", self.line, self.col)

    # ── token readers ────────────────────────

    def read_number(self):
        """Read INT or FLOAT literal."""
        start_line, start_col = self.line, self.col
        num_str = ''
        is_float = False

        while self.current() and self.current().isdigit():
            num_str += self.advance()

        if self.current() == '.' and self.peek() and self.peek().isdigit():
            is_float = True
            num_str += self.advance()               # consume '.'
            while self.current() and self.current().isdigit():
                num_str += self.advance()

        if is_float:
            return Token(TT_FLOAT, float(num_str), start_line, start_col)
        return Token(TT_INT, int(num_str), start_line, start_col)

    def read_identifier_or_keyword(self):
        """Read identifier; classify as KEYWORD if in KEYWORDS set."""
        start_line, start_col = self.line, self.col
        word = ''

        while self.current() and (self.current().isalnum() or self.current() == '_'):
            word += self.advance()

        if word in KEYWORDS:
            return Token(TT_KEYWORD, word, start_line, start_col)
        return Token(TT_ID, word, start_line, start_col)

    def read_string(self):
        """
        M2: Read a double-quoted string literal.
        Supports escape sequences: \\n  \\t  \\\\ \\"
        """
        start_line, start_col = self.line, self.col
        self.advance()          # consume opening "
        result = ''

        while self.current() and self.current() != '"':
            if self.current() == '\\':
                self.advance()  # consume backslash
                esc = self.advance()
                escape_map = {'n': '\n', 't': '\t', '\\': '\\', '"': '"'}
                if esc in escape_map:
                    result += escape_map[esc]
                else:
                    raise LexerError(f"Unknown escape sequence '\\{esc}'",
                                     self.line, self.col)
            else:
                result += self.advance()

        if self.current() != '"':
            raise LexerError("Unterminated string literal", start_line, start_col)
        self.advance()          # consume closing "
        return Token(TT_STRING, result, start_line, start_col)

    # ── main tokenise loop ───────────────────

    def tokenize(self) -> list:
        """
        Main entry point.
        Returns a list of Token objects ending with TT_EOF.
        """
        while self.pos < len(self.source):
            self.skip_whitespace()
            if self.pos >= len(self.source):
                break

            ch = self.current()
            line, col = self.line, self.col

            # ── comments ──────────────────────
            if ch == '/' and self.peek() in ('/', '*'):
                self.skip_comment()
                continue

            # ── number literals ───────────────
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue

            # ── identifiers / keywords ────────
            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier_or_keyword())
                continue

            # ── string literals (M2) ──────────
            if ch == '"':
                self.tokens.append(self.read_string())
                continue

            # ── two-character operators ────────
            two = ch + (self.peek() or '')
            two_char_map = {
                '==': TT_EQ,
                '!=': TT_NEQ,
                '<=': TT_LTE,
                '>=': TT_GTE,
                '&&': TT_AND,
                '||': TT_OR,
            }
            if two in two_char_map:
                self.advance(); self.advance()
                self.tokens.append(Token(two_char_map[two], two, line, col))
                continue

            # ── single-character tokens ────────
            one_char_map = {
                '+': TT_PLUS,
                '-': TT_MINUS,
                '*': TT_MUL,
                '/': TT_DIV,
                '%': TT_MOD,
                '=': TT_ASSIGN,
                '<': TT_LT,
                '>': TT_GT,
                '!': TT_NOT,
                '(': TT_LPAREN,
                ')': TT_RPAREN,
                '{': TT_LBRACE,
                '}': TT_RBRACE,
                '[': TT_LBRACKET,
                ']': TT_RBRACKET,
                ';': TT_SEMICOLON,
                ',': TT_COMMA,
            }
            if ch in one_char_map:
                self.advance()
                self.tokens.append(Token(one_char_map[ch], ch, line, col))
                continue

            # ── unknown character ──────────────
            raise LexerError(f"Unexpected character '{ch}'", line, col)

        self.tokens.append(Token(TT_EOF, None, self.line, self.col))
        return self.tokens


# ─────────────────────────────────────────────
#  QUICK TEST  (run: python lexer.py)
# ─────────────────────────────────────────────

if __name__ == '__main__':
    sample = """
    int x = 10;
    float y = 3.14;
    string name = "CPL";
    array nums[5];

    if (x > 5) {
        print(name);
    } else {
        while (x != 0) {
            x = x - 1;
        }
    }
    """

    lexer  = Lexer(sample)
    tokens = lexer.tokenize()

    for tok in tokens:
        print(tok)
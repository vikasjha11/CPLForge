# parser.py
# Member C's file — Recursive Descent Parser for CPL
#
# WHAT IS PARSING?
# We have a flat token list from the lexer. Parsing reads those tokens
# left-to-right and builds the AST defined in ast.py.
#
# WHY RECURSIVE DESCENT?
# The problem statement says LL(1). Recursive descent IS an LL(1) parser
# written by hand. Each grammar rule becomes one Python function.
# It's easy to write, easy to debug, and easy to extend.
#
# GRAMMAR OVERVIEW (simplified):
#   program        → statement*  EOF
#   statement      → varDecl | assignment | if | while | return | print | input | exprStmt
#   varDecl        → TYPE ID ('=' expr)? ';'
#   assignment     → ID '=' expr ';'
#   if             → 'if' '(' expr ')' block ('else' block)?
#   while          → 'while' '(' expr ')' block
#   block          → '{' statement* '}'
#   expr           → comparison (('&&' | '||') comparison)*
#   comparison     → additive (('=='|'!='|'<'|'>'|'<='|'>=') additive)*
#   additive       → multiplicative (('+' | '-') multiplicative)*
#   multiplicative → unary (('*' | '/' | '%') unary)*
#   unary          → ('-' | '!') unary | primary
#   primary        → INT | FLOAT | STRING | 'true' | 'false' | ID | ID'['expr']' | ID'('args')' | '('expr')'

from lexer import (
    Token,
    TT_INT, TT_FLOAT, TT_STRING, TT_ID, TT_KEYWORD, TT_EOF,
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_MOD,
    TT_EQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE,
    TT_ASSIGN, TT_AND, TT_OR, TT_NOT,
    TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
    TT_LBRACKET, TT_RBRACKET, TT_SEMICOLON, TT_COMMA,
)
from ast import (
    Program, VarDecl, Assignment, IfStatement, WhileStatement,
    ReturnStatement, PrintStatement, InputStatement, ExpressionStatement,
    BinaryOp, UnaryOp, Literal, Identifier, ArrayAccess,
    FunctionCall, FunctionDecl,
)


# ─────────────────────────────────────────────────────────
#  PARSER ERROR
# ─────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, message, token):
        pos = f"L{token.line}:C{token.col}"
        super().__init__(f"ParseError at {pos} — {message} (got {token.type} '{token.value}')")


# ─────────────────────────────────────────────────────────
#  TYPE KEYWORDS  (used to identify variable declarations)
# ─────────────────────────────────────────────────────────

TYPE_KEYWORDS = {'int', 'float', 'string', 'array'}


# ─────────────────────────────────────────────────────────
#  PARSER CLASS
# ─────────────────────────────────────────────────────────

class Parser:
    """
    Recursive descent parser.
    Takes a token list (from Lexer.tokenize()) and returns a Program AST node.

    Usage:
        parser = Parser(tokens)
        tree   = parser.parse()
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos    = 0

    # ── token navigation ─────────────────────────────────

    def current(self) -> Token:
        """Current token without consuming it."""
        return self.tokens[self.pos]

    def peek(self, offset=1) -> Token:
        """Look ahead without consuming."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]  # EOF

    def advance(self) -> Token:
        """Consume and return current token."""
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, type_: str, value: str = None) -> Token:
        """
        Consume token if it matches; raise ParseError otherwise.
        WHY: Most grammar rules say "there MUST be a ';' here".
        expect() enforces that contract cleanly.
        """
        tok = self.current()
        if tok.type != type_:
            exp = f"'{value}'" if value else type_
            raise ParseError(f"Expected {exp}", tok)
        if value is not None and tok.value != value:
            raise ParseError(f"Expected '{value}'", tok)
        return self.advance()

    def match(self, type_: str, value: str = None) -> bool:
        """
        Returns True (and DOES NOT consume) if current token matches.
        WHY: Used for lookahead decisions without committing.
        """
        tok = self.current()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def match_keyword(self, kw: str) -> bool:
        return self.match(TT_KEYWORD, kw)

    # ─────────────────────────────────────────────────────
    #  TOP LEVEL
    # ─────────────────────────────────────────────────────

    def parse(self) -> Program:
        """
        Entry point.
        program → statement* EOF

        We keep parsing statements until we hit EOF.
        """
        stmts = []
        while not self.match(TT_EOF):
            stmts.append(self.parse_statement())
        return Program(statements=stmts)

    # ─────────────────────────────────────────────────────
    #  STATEMENT DISPATCHER
    # ─────────────────────────────────────────────────────

    def parse_statement(self):
        """
        Decides WHICH kind of statement to parse based on lookahead.

        WHY lookahead?
        We can't know if "x = ..." is an assignment until we see 'x'.
        But we CAN know "int" means a variable declaration immediately.
        This is the LL(1) "one token of lookahead" principle.
        """
        tok = self.current()

        # ── type keyword → variable declaration ──────────
        if tok.type == TT_KEYWORD and tok.value in TYPE_KEYWORDS:
            return self.parse_var_decl()

        # ── func keyword (M2) ────────────────────────────
        if self.match_keyword('func'):
            return self.parse_function_decl()

        # ── if statement ──────────────────────────────────
        if self.match_keyword('if'):
            return self.parse_if()

        # ── while statement ───────────────────────────────
        if self.match_keyword('while'):
            return self.parse_while()

        # ── return ────────────────────────────────────────
        if self.match_keyword('return'):
            return self.parse_return()

        # ── print (M2) ────────────────────────────────────
        if self.match_keyword('print'):
            return self.parse_print()

        # ── input (M2) ────────────────────────────────────
        if self.match_keyword('input'):
            return self.parse_input()

        # ── ID followed by '=' → assignment ──────────────
        # WHY check peek? Because 'x = 5' and 'x + 5' both start with ID.
        # The '=' on peek tells us it's assignment, not an expression stmt.
        if tok.type == TT_ID and self.peek().type == TT_ASSIGN:
            return self.parse_assignment()

        # ── fallthrough: expression statement ─────────────
        # e.g.  foo(x);   or   x + 1;  (rare but legal)
        return self.parse_expression_statement()

    # ─────────────────────────────────────────────────────
    #  VARIABLE DECLARATION
    # ─────────────────────────────────────────────────────

    def parse_var_decl(self):
        """
        varDecl → TYPE ID ('=' expr)? ';'
                | 'array' ID '[' INT ']' ';'     (M2)

        Examples:
            int x = 5;
            float y;          ← init is optional
            array nums[10];   ← M2 syntax
        """
        type_tok  = self.advance()          # consume TYPE keyword
        var_type  = type_tok.value
        line, col = type_tok.line, type_tok.col

        name_tok = self.expect(TT_ID)       # must be followed by a name
        name     = name_tok.value

        # M2 array declaration:  array nums[10];
        if var_type == 'array':
            self.expect(TT_LBRACKET)
            size_tok = self.expect(TT_INT)
            self.expect(TT_RBRACKET)
            self.expect(TT_SEMICOLON)
            return VarDecl(var_type='array', name=name,
                           array_size=size_tok.value, line=line, col=col)

        # Optional initialiser:  int x = 5;
        init_value = None
        if self.match(TT_ASSIGN):
            self.advance()                  # consume '='
            init_value = self.parse_expr()

        self.expect(TT_SEMICOLON)
        return VarDecl(var_type=var_type, name=name,
                       init_value=init_value, line=line, col=col)

    # ─────────────────────────────────────────────────────
    #  ASSIGNMENT
    # ─────────────────────────────────────────────────────

    def parse_assignment(self):
        """
        assignment → ID '=' expr ';'
        Example: x = x + 1;

        WHY not handle  x[i] = v  here?
        Array element assignment is out of scope for M1.
        We keep it simple — only scalar variable assignment.
        """
        id_tok = self.advance()             # consume ID
        self.expect(TT_ASSIGN)             # consume '='
        value = self.parse_expr()
        self.expect(TT_SEMICOLON)
        return Assignment(name=id_tok.value, value=value,
                          line=id_tok.line, col=id_tok.col)

    # ─────────────────────────────────────────────────────
    #  IF STATEMENT
    # ─────────────────────────────────────────────────────

    def parse_if(self):
        """
        if → 'if' '(' expr ')' block ('else' block)?

        WHY parse_block() instead of parse_statement()?
        CPL requires braces around if/while bodies (like Java, not Python).
        parse_block handles the { } and collects the statements inside.
        """
        tok = self.advance()                # consume 'if'
        self.expect(TT_LPAREN)
        condition = self.parse_expr()
        self.expect(TT_RPAREN)
        then_body = self.parse_block()

        else_body = []
        if self.match_keyword('else'):
            self.advance()                  # consume 'else'
            else_body = self.parse_block()

        return IfStatement(condition=condition, then_body=then_body,
                           else_body=else_body, line=tok.line, col=tok.col)

    # ─────────────────────────────────────────────────────
    #  WHILE STATEMENT
    # ─────────────────────────────────────────────────────

    def parse_while(self):
        """
        while → 'while' '(' expr ')' block
        """
        tok = self.advance()                # consume 'while'
        self.expect(TT_LPAREN)
        condition = self.parse_expr()
        self.expect(TT_RPAREN)
        body = self.parse_block()
        return WhileStatement(condition=condition, body=body,
                              line=tok.line, col=tok.col)

    # ─────────────────────────────────────────────────────
    #  BLOCK  { statement* }
    # ─────────────────────────────────────────────────────

    def parse_block(self) -> list:
        """
        block → '{' statement* '}'

        Returns a list of statements (not an ASTNode itself).
        WHY a list and not a node?
        A block isn't a value — it's just a container.
        IfStatement and WhileStatement store the list directly.
        """
        self.expect(TT_LBRACE)
        stmts = []
        while not self.match(TT_RBRACE) and not self.match(TT_EOF):
            stmts.append(self.parse_statement())
        self.expect(TT_RBRACE)
        return stmts

    # ─────────────────────────────────────────────────────
    #  RETURN, PRINT, INPUT
    # ─────────────────────────────────────────────────────

    def parse_return(self):
        tok = self.advance()                # consume 'return'
        value = None
        if not self.match(TT_SEMICOLON):   # bare return; is allowed
            value = self.parse_expr()
        self.expect(TT_SEMICOLON)
        return ReturnStatement(value=value, line=tok.line, col=tok.col)

    def parse_print(self):
        """
        M2:  print(expr);
        """
        tok = self.advance()                # consume 'print'
        self.expect(TT_LPAREN)
        value = self.parse_expr()
        self.expect(TT_RPAREN)
        self.expect(TT_SEMICOLON)
        return PrintStatement(value=value, line=tok.line, col=tok.col)

    def parse_input(self):
        """
        M2:  input(varName);
        WHY only an identifier inside?
        input() writes INTO a variable — it doesn't make sense to input
        into an expression like  input(x+1).
        """
        tok = self.advance()                # consume 'input'
        self.expect(TT_LPAREN)
        id_tok = self.expect(TT_ID)
        self.expect(TT_RPAREN)
        self.expect(TT_SEMICOLON)
        return InputStatement(var_name=id_tok.value, line=tok.line, col=tok.col)

    def parse_expression_statement(self):
        line, col = self.current().line, self.current().col
        expr = self.parse_expr()
        self.expect(TT_SEMICOLON)
        return ExpressionStatement(expression=expr, line=line, col=col)

    # ─────────────────────────────────────────────────────
    #  FUNCTION DECLARATION (M2)
    # ─────────────────────────────────────────────────────

    def parse_function_decl(self):
        """
        M2:  func TYPE NAME '(' params ')' block

        Example:
            func int add(int a, int b) {
                return a + b;
            }

        WHY store params as list of tuples (type, name)?
        Simple and matches how C function signatures work.
        The semantic analyser can easily iterate over them.
        """
        self.advance()                      # consume 'func'
        ret_type_tok = self.expect(TT_KEYWORD)
        name_tok     = self.expect(TT_ID)

        self.expect(TT_LPAREN)
        params = []
        while not self.match(TT_RPAREN):
            ptype = self.expect(TT_KEYWORD).value
            pname = self.expect(TT_ID).value
            params.append((ptype, pname))
            if self.match(TT_COMMA):
                self.advance()
        self.expect(TT_RPAREN)

        body = self.parse_block()
        return FunctionDecl(
            name=name_tok.value,
            return_type=ret_type_tok.value,
            params=params,
            body=body,
            line=name_tok.line, col=name_tok.col
        )

    # ─────────────────────────────────────────────────────
    #  EXPRESSION PARSING  (operator precedence)
    #
    #  WHY this chain of functions?
    #  Operator precedence is encoded in the CALL CHAIN.
    #  parse_expr calls parse_logical, which calls parse_comparison,
    #  which calls parse_additive, etc.
    #  Lower precedence = higher up in the chain = parsed LAST.
    #  This is the standard "Pratt/descent" trick.
    #
    #  Precedence (low → high):
    #    || &&        ← parse_expr (logical)
    #    == != < > <= >=  ← parse_comparison
    #    + -          ← parse_additive
    #    * / %        ← parse_multiplicative
    #    - !          ← parse_unary
    #    literals, IDs, ()  ← parse_primary
    # ─────────────────────────────────────────────────────

    def parse_expr(self):
        return self.parse_logical()

    def parse_logical(self):
        """
        logical → comparison (('&&' | '||') comparison)*

        WHY left-associative loop?
        a && b && c should parse as (a && b) && c, not a && (b && c).
        The while loop naturally builds left-leaning trees.
        """
        left = self.parse_comparison()
        while self.match(TT_AND) or self.match(TT_OR):
            op  = self.advance().value
            right = self.parse_comparison()
            left = BinaryOp(left=left, op=op, right=right,
                            line=left.line, col=left.col)
        return left

    def parse_comparison(self):
        """comparison → additive (('==' | '!=' | '<' | '>' | '<=' | '>=') additive)*"""
        COMP_OPS = {TT_EQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE}
        left = self.parse_additive()
        while self.current().type in COMP_OPS:
            op    = self.advance().value
            right = self.parse_additive()
            left  = BinaryOp(left=left, op=op, right=right,
                             line=left.line, col=left.col)
        return left

    def parse_additive(self):
        """additive → multiplicative (('+' | '-') multiplicative)*"""
        left = self.parse_multiplicative()
        while self.match(TT_PLUS) or self.match(TT_MINUS):
            op    = self.advance().value
            right = self.parse_multiplicative()
            left  = BinaryOp(left=left, op=op, right=right,
                             line=left.line, col=left.col)
        return left

    def parse_multiplicative(self):
        """multiplicative → unary (('*' | '/' | '%') unary)*"""
        left = self.parse_unary()
        while self.match(TT_MUL) or self.match(TT_DIV) or self.match(TT_MOD):
            op    = self.advance().value
            right = self.parse_unary()
            left  = BinaryOp(left=left, op=op, right=right,
                             line=left.line, col=left.col)
        return left

    def parse_unary(self):
        """
        unary → ('-' | '!') unary | primary

        WHY recursive?
        !!x is valid (double negation). Recursion handles arbitrary depth.
        """
        if self.match(TT_MINUS) or self.match(TT_NOT):
            op_tok  = self.advance()
            operand = self.parse_unary()
            return UnaryOp(op=op_tok.value, operand=operand,
                           line=op_tok.line, col=op_tok.col)
        return self.parse_primary()

    def parse_primary(self):
        """
        primary → INT | FLOAT | STRING | 'true' | 'false'
                | ID '[' expr ']'     (array access)
                | ID '(' args ')'     (function call)
                | ID                  (variable reference)
                | '(' expr ')'        (parenthesised expression)

        WHY is this the longest function?
        Primary is the "leaf" of every expression — it handles all the
        specific terminal cases that don't recurse further upward.
        """
        tok = self.current()

        # ── integer literal ───────────────────────────────
        if tok.type == TT_INT:
            self.advance()
            return Literal(value=tok.value, type_='int',
                           line=tok.line, col=tok.col)

        # ── float literal ─────────────────────────────────
        if tok.type == TT_FLOAT:
            self.advance()
            return Literal(value=tok.value, type_='float',
                           line=tok.line, col=tok.col)

        # ── string literal (M2) ───────────────────────────
        if tok.type == TT_STRING:
            self.advance()
            return Literal(value=tok.value, type_='string',
                           line=tok.line, col=tok.col)

        # ── boolean keywords ──────────────────────────────
        if tok.type == TT_KEYWORD and tok.value in ('true', 'false'):
            self.advance()
            return Literal(value=(tok.value == 'true'), type_='bool',
                           line=tok.line, col=tok.col)

        # ── identifier: could be variable, array access, or function call ──
        if tok.type == TT_ID:
            self.advance()                  # consume the ID

            # Array access:  nums[i]
            if self.match(TT_LBRACKET):
                self.advance()
                index = self.parse_expr()
                self.expect(TT_RBRACKET)
                return ArrayAccess(array_name=tok.value, index=index,
                                   line=tok.line, col=tok.col)

            # Function call:  foo(a, b)
            if self.match(TT_LPAREN):
                self.advance()
                args = []
                while not self.match(TT_RPAREN):
                    args.append(self.parse_expr())
                    if self.match(TT_COMMA):
                        self.advance()
                self.expect(TT_RPAREN)
                return FunctionCall(name=tok.value, args=args,
                                    line=tok.line, col=tok.col)

            # Plain variable reference
            return Identifier(name=tok.value, line=tok.line, col=tok.col)

        # ── parenthesised expression  (expr) ─────────────
        if tok.type == TT_LPAREN:
            self.advance()                  # consume '('
            expr = self.parse_expr()
            self.expect(TT_RPAREN)
            return expr

        raise ParseError("Expected an expression", tok)
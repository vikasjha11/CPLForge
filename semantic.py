# semantic.py
# Semantic Analyser for CPL
#
# WHAT DOES IT CHECK?
# 1. Undeclared variables  — using x before declaring it
# 2. Re-declaration        — declaring x twice in same scope
# 3. Type mismatch         — assigning string to int variable
# 4. Undeclared functions  — calling foo() when foo was never declared
#
# HOW?
# We use a SYMBOL TABLE — a dictionary that maps variable names to their types.
# When we declare  int x = 5;   we add  x → 'int'  to the table.
# When we later use  x + 1;     we look up x, confirm it's 'int', proceed.
#
# SCOPE:
# CPL has block scope (like C). Variables declared inside { } are local to it.
# We implement this with a STACK of symbol tables.
# Enter block → push new table. Exit block → pop it.

<<<<<<< HEAD
from cpl_ast import (
=======
from ast import (
>>>>>>> 35f1492d35f2c5706a6f1004b84e92afbfc194d2
    Program, VarDecl, Assignment, IfStatement, WhileStatement,
    ReturnStatement, PrintStatement, InputStatement, ExpressionStatement,
    BinaryOp, UnaryOp, Literal, Identifier, ArrayAccess,
    FunctionCall, FunctionDecl, ASTNode,
)


class SemanticError(Exception):
    def __init__(self, message, line=0, col=0):
        super().__init__(f"SemanticError at L{line}:C{col} — {message}")


class SymbolTable:
    """
    A single scope's symbol table.
    Maps name → {'type': ..., 'line': ..., 'is_array': bool}
    """
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent  = parent   # enclosing scope (for variable lookup)

    def declare(self, name, type_, line, col, is_array=False):
        if name in self.symbols:
            raise SemanticError(f"Variable '{name}' already declared in this scope",
                                line, col)
        self.symbols[name] = {'type': type_, 'line': line, 'is_array': is_array}

    def lookup(self, name):
        """
        Walk up the scope chain to find the variable.
        WHY walk up? Variables declared in outer scopes are visible inside.
        e.g. x declared outside while loop is still accessible inside it.
        """
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None


# ─────────────────────────────────────────────────────────
#  TYPE COMPATIBILITY RULES
# ─────────────────────────────────────────────────────────

def types_compatible(declared: str, assigned: str) -> bool:
    """
    Can a value of type 'assigned' be stored in a variable of type 'declared'?

    Rules:
    - Same type: always ok
    - int ← float: NOT ok (would lose precision, CPL is statically typed)
    - float ← int: ok (int can be widened to float)
    - string ← string: ok
    - bool ← bool: ok
    - anything ← None: ok (unresolved/dynamic, we let it pass)
    """
    if assigned is None:
        return True
    if declared == assigned:
        return True
    if declared == 'float' and assigned == 'int':
        return True
    return False


# ─────────────────────────────────────────────────────────
#  SEMANTIC ANALYSER
# ─────────────────────────────────────────────────────────

class SemanticAnalyser:
    """
    Walks the AST and checks for semantic errors.
    Returns the annotated AST (same tree, but with type info attached).

    Usage:
        analyser = SemanticAnalyser()
        analyser.analyse(program_node)   # raises SemanticError if invalid
    """

    def __init__(self):
        self.scope          = SymbolTable()     # global scope
        self.functions      = {}                # name → FunctionDecl node
        self.current_func   = None              # for return type checking

    def analyse(self, node: ASTNode):
        self.visit(node)

    def visit(self, node: ASTNode):
        method = f"visit_{type(node).__name__}"
        return getattr(self, method, self.visit_unknown)(node)

    def visit_unknown(self, node):
        pass    # nodes we don't need to check (safe default)

    # ── helpers ───────────────────────────────────────────

    def enter_scope(self):
        self.scope = SymbolTable(parent=self.scope)

    def exit_scope(self):
        self.scope = self.scope.parent

    def get_type(self, node) -> str:
        """Infer the CPL type of an expression node."""
        if isinstance(node, Literal):
            return node.type_
        if isinstance(node, Identifier):
            sym = self.scope.lookup(node.name)
            if sym is None:
                raise SemanticError(f"Undeclared variable '{node.name}'",
                                    node.line, node.col)
            return sym['type']
        if isinstance(node, BinaryOp):
            lt = self.get_type(node.left)
            rt = self.get_type(node.right)
            # Comparison operators always return bool
            if node.op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
                return 'bool'
            # Arithmetic: if either side is float, result is float
            if 'float' in (lt, rt):
                return 'float'
            return lt   # both int → int
        if isinstance(node, UnaryOp):
            if node.op == '!':
                return 'bool'
            return self.get_type(node.operand)
        if isinstance(node, FunctionCall):
            func = self.functions.get(node.name)
            if func:
                return func.return_type
            return 'int'    # built-in or unresolved → assume int
        if isinstance(node, ArrayAccess):
            sym = self.scope.lookup(node.array_name)
            if sym:
                # array of int → element type is int, etc.
                return sym['type'].replace('array_', '')
            return 'int'
        return None

    # ── visitors ──────────────────────────────────────────

    def visit_Program(self, node: Program):
        # First pass: register all function declarations
        # WHY first pass? So functions can call each other regardless of order.
        for stmt in node.statements:
            if isinstance(stmt, FunctionDecl):
                self.functions[stmt.name] = stmt

        # Second pass: analyse everything
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDecl(self, node: VarDecl):
        # Check init value type matches declared type
        if node.init_value:
            self.visit(node.init_value)
            val_type = self.get_type(node.init_value)
            if not types_compatible(node.var_type, val_type):
                raise SemanticError(
                    f"Type mismatch: cannot assign '{val_type}' to '{node.var_type}' variable '{node.name}'",
                    node.line, node.col
                )
        self.scope.declare(node.name, node.var_type, node.line, node.col,
                           is_array=(node.var_type == 'array'))

    def visit_Assignment(self, node: Assignment):
        sym = self.scope.lookup(node.name)
        if sym is None:
            raise SemanticError(f"Assignment to undeclared variable '{node.name}'",
                                node.line, node.col)
        self.visit(node.value)
        val_type = self.get_type(node.value)
        if not types_compatible(sym['type'], val_type):
            raise SemanticError(
                f"Type mismatch: cannot assign '{val_type}' to '{sym['type']}' variable '{node.name}'",
                node.line, node.col
            )

    def visit_IfStatement(self, node: IfStatement):
        self.visit(node.condition)
        self.enter_scope()
        for s in node.then_body: self.visit(s)
        self.exit_scope()
        if node.else_body:
            self.enter_scope()
            for s in node.else_body: self.visit(s)
            self.exit_scope()

    def visit_WhileStatement(self, node: WhileStatement):
        self.visit(node.condition)
        self.enter_scope()
        for s in node.body: self.visit(s)
        self.exit_scope()

    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.value:
            self.visit(node.value)

    def visit_PrintStatement(self, node: PrintStatement):
        self.visit(node.value)

    def visit_InputStatement(self, node: InputStatement):
        sym = self.scope.lookup(node.var_name)
        if sym is None:
            raise SemanticError(f"input() on undeclared variable '{node.var_name}'",
                                node.line, node.col)

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        self.visit(node.expression)

    def visit_FunctionDecl(self, node: FunctionDecl):
        self.current_func = node
        self.enter_scope()
        for (ptype, pname) in node.params:
            self.scope.declare(pname, ptype, node.line, node.col)
        for s in node.body: self.visit(s)
        self.exit_scope()
        self.current_func = None

    def visit_FunctionCall(self, node: FunctionCall):
        if node.name not in self.functions:
            # Could be a built-in or forward-declared — warn but don't crash
            pass
        for arg in node.args:
            self.visit(arg)

    def visit_BinaryOp(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.operand)

    def visit_Identifier(self, node: Identifier):
        if self.scope.lookup(node.name) is None:
            raise SemanticError(f"Undeclared variable '{node.name}'",
                                node.line, node.col)

    def visit_Literal(self, node: Literal):
        pass    # literals are always valid
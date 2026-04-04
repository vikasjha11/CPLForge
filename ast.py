# ast.py
# Defines all AST (Abstract Syntax Tree) node types for CPL.
#
# WHY AST?
# After lexing, we have a flat list of tokens like:
#   [INT, x, =, 10, ;]
# That's still just a sequence. An AST gives it STRUCTURE — it captures
# that "x = 10" is an assignment, where the LEFT side is a variable
# and the RIGHT side is a number. The tree shape encodes grammar.
#
# Every node is a Python dataclass — clean, no boilerplate, printable.

from dataclasses import dataclass, field
from typing import List, Optional, Any


# ─────────────────────────────────────────────────────────
#  BASE NODE
# ─────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    """
    Base class for all AST nodes.
    Every node stores line/col so error messages can say WHERE things went wrong.
    """
    line: int = field(default=0, repr=False)
    col:  int = field(default=0, repr=False)

    def tree_str(self, indent=0):
        """Pretty-print the AST as an indented tree (for debugging)."""
        pad = "  " * indent
        name = self.__class__.__name__
        # collect non-position fields
        parts = []
        for k, v in self.__dict__.items():
            if k in ('line', 'col'):
                continue
            if isinstance(v, ASTNode):
                parts.append(f"\n{pad}  {k}:\n{v.tree_str(indent+2)}")
            elif isinstance(v, list):
                items = "\n".join(
                    n.tree_str(indent+2) if isinstance(n, ASTNode) else f"{pad}    {n}"
                    for n in v
                )
                parts.append(f"\n{pad}  {k}:\n{items}")
            else:
                parts.append(f"{k}={v!r}")
        inline = ", ".join(p for p in parts if not p.startswith("\n"))
        block  = "".join(p for p in parts if p.startswith("\n"))
        return f"{pad}{name}({inline}){block}"


# ─────────────────────────────────────────────────────────
#  PROGRAM (root node)
# ─────────────────────────────────────────────────────────

@dataclass
class Program(ASTNode):
    """
    Root of every CPL program.
    A program is just a list of statements — nothing fancy.
    WHY: The parser's job is to produce exactly one Program node.
    """
    statements: List[ASTNode] = field(default_factory=list)


# ─────────────────────────────────────────────────────────
#  STATEMENTS
#  A statement is a "complete action" — it doesn't produce a value.
#  e.g.  int x = 5;   if (...) {...}   while (...) {...}
# ─────────────────────────────────────────────────────────

@dataclass
class VarDecl(ASTNode):
    """
    Variable declaration.
    Examples:  int x = 10;
               float y = 3.14;
               string name = "CPL";   (M2)

    WHY separate from Assignment?
    Declaration INTRODUCES a new name into the symbol table.
    Assignment UPDATES an already-existing name.
    The semantic analyser needs to tell them apart.
    """
    var_type:   str           = ''          # 'int', 'float', 'string', 'array'
    name:       str           = ''          # variable name
    init_value: Optional[ASTNode] = None   # right-hand side (can be None for arrays)
    array_size: Optional[int] = None       # M2: for  array nums[5];


@dataclass
class Assignment(ASTNode):
    """
    Re-assignment to existing variable.
    Example:  x = x + 1;

    WHY: Kept separate from VarDecl so the semantic analyser can check
    "does this variable exist?" before allowing the assignment.
    """
    name:  str     = ''
    value: ASTNode = None


@dataclass
class IfStatement(ASTNode):
    """
    if (condition) { then_body } else { else_body }
    else_body is Optional — plain if without else is valid.
    """
    condition: ASTNode       = None
    then_body: List[ASTNode] = field(default_factory=list)
    else_body: List[ASTNode] = field(default_factory=list)


@dataclass
class WhileStatement(ASTNode):
    """
    while (condition) { body }

    WHY no for-loop? The problem statement says only 'while'.
    Keep scope tight — you can always extend later.
    """
    condition: ASTNode       = None
    body:      List[ASTNode] = field(default_factory=list)


@dataclass
class ReturnStatement(ASTNode):
    """
    return expr;
    value can be None for bare  return;
    """
    value: Optional[ASTNode] = None


@dataclass
class PrintStatement(ASTNode):
    """
    M2:  print(expr);
    WHY a dedicated node instead of a function call?
    print is a BUILT-IN keyword in CPL, not a user-defined function.
    Treating it separately keeps codegen simple.
    """
    value: ASTNode = None


@dataclass
class InputStatement(ASTNode):
    """
    M2:  input(var_name);
    Reads from stdin into a variable.
    """
    var_name: str = ''


@dataclass
class ExpressionStatement(ASTNode):
    """
    A statement that is just an expression followed by ;
    Example:  foo(x);   (calling a function but not using return value)
    WHY: In CPL, expressions CAN appear as statements (like in C).
    """
    expression: ASTNode = None


# ─────────────────────────────────────────────────────────
#  EXPRESSIONS
#  An expression PRODUCES A VALUE.
#  e.g.  x + 5   true   "hello"   foo(x)
# ─────────────────────────────────────────────────────────

@dataclass
class BinaryOp(ASTNode):
    """
    Two operands connected by an operator.
    Examples:  x + y    a * b    x == 10    x && y

    WHY store operator as a string?
    It's the simplest representation. The IR generator will pattern-match
    on op to decide which TAC instruction to emit.
    """
    left:  ASTNode = None
    op:    str     = ''    # '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>='
    right: ASTNode = None


@dataclass
class UnaryOp(ASTNode):
    """
    Single operand with a prefix operator.
    Examples:  -x    !flag

    WHY: Unary minus and logical NOT are grammatically different from
    binary ops — they only have ONE child.
    """
    op:    str     = ''    # '-' or '!'
    operand: ASTNode = None


@dataclass
class Literal(ASTNode):
    """
    A hardcoded value in source code.
    Examples:  42   3.14   "hello"   true   false

    value holds the PYTHON value (int, float, str, bool).
    type_  tells us which CPL type it is.
    WHY store type_? The IR generator needs to know whether to emit
    an int register or a float register.
    """
    value:  Any = None
    type_:  str = ''    # 'int', 'float', 'string', 'bool'


@dataclass
class Identifier(ASTNode):
    """
    A reference to a variable by name.
    Example:  x    myVar    result

    WHY separate from Literal?
    An identifier is a NAME that must be LOOKED UP in the symbol table.
    A literal is a VALUE that is known at compile time.
    """
    name: str = ''


@dataclass
class ArrayAccess(ASTNode):
    """
    M2:  nums[i]   — read element at index
    array_name: the array variable
    index: expression for the index (can be any expr, e.g. i+1)
    """
    array_name: str     = ''
    index:      ASTNode = None


@dataclass
class FunctionCall(ASTNode):
    """
    Calling a user-defined or built-in function.
    Example:  add(x, y)

    WHY args is a list?
    Functions can have zero or more arguments.
    """
    name: str              = ''
    args: List[ASTNode]    = field(default_factory=list)


@dataclass
class FunctionDecl(ASTNode):
    """
    M2:  func add(int a, int b) { ... return a + b; }

    params: list of (type, name) tuples
    body:   list of statements inside the function
    """
    name:        str              = ''
    return_type: str              = 'int'
    params:      List[tuple]      = field(default_factory=list)
    body:        List[ASTNode]    = field(default_factory=list)
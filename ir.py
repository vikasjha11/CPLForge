# ir.py
# Intermediate Representation — Three Address Code (TAC) Generator
#
# WHAT IS TAC?
# Three Address Code is the compiler's "assembly language for math".
# Every instruction has at most 3 operands: result = left op right
#
# WHY TAC and not directly generate assembly?
# 1. TAC is target-INDEPENDENT — same TAC works for x86 and VM targets.
# 2. TAC is easy to OPTIMIZE (constant folding, dead code elimination).
# 3. TAC maps directly to registers — codegen becomes mechanical.
#
# Example: CPL source  →  AST  →  TAC
#   int x = (a + b) * 2;
#   →
#   t0 = a + b
#   t1 = t0 * 2
#   x  = t1
#
# TAC INSTRUCTION TYPES we support:
#   ASSIGN     x = y
#   BINOP      x = y op z
#   UNARY      x = op y
#   LABEL      LABEL_n:          (for if/while jumps)
#   JUMP       goto LABEL_n
#   JUMPIF     if x goto LABEL_n
#   JUMPIFNOT  ifnot x goto LABEL_n
#   PARAM      param x           (push function argument)
#   CALL       x = call f n      (call function f with n args)
#   RETURN     return x
#   PRINT      print x           (built-in)
#   INPUT      input x           (built-in, M2)
#   ARRAY_SET  a[i] = x          (M2)
#   ARRAY_GET  x = a[i]          (M2)

from dataclasses import dataclass, field
from typing import Optional, Any
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

<<<<<<< HEAD
=======

# ─────────────────────────────────────────────────────────
#  TAC INSTRUCTION
# ─────────────────────────────────────────────────────────

>>>>>>> 35f1492d35f2c5706a6f1004b84e92afbfc194d2
@dataclass
class TACInstruction:
    """
    A single Three Address Code instruction.

    op     : instruction type (string, see list above)
    result : where the result goes (variable name or temp)
    arg1   : first operand
    arg2   : second operand (None for unary/assign)

    Examples:
        TACInstruction('BINOP', 't0', 'a', '+', 'b')   → t0 = a + b
        TACInstruction('ASSIGN', 'x', 't0')             → x  = t0
        TACInstruction('LABEL', 'L0')                   → L0:
        TACInstruction('JUMPIFNOT', None, 't1', 'L2')  → ifnot t1 goto L2
    """
    op:     str
    result: Optional[str] = None
    arg1:   Optional[Any] = None
    op_sym: Optional[str] = None    # the operator symbol for BINOP/UNARY
    arg2:   Optional[Any] = None

    def __str__(self):
        """Human-readable TAC (useful for debugging and the report)."""
        if self.op == 'LABEL':
            return f"{self.result}:"
        if self.op == 'JUMP':
            return f"    goto {self.result}"
        if self.op == 'JUMPIF':
            return f"    if {self.arg1} goto {self.result}"
        if self.op == 'JUMPIFNOT':
            return f"    ifnot {self.arg1} goto {self.result}"
        if self.op == 'ASSIGN':
            return f"    {self.result} = {self.arg1}"
        if self.op == 'BINOP':
            return f"    {self.result} = {self.arg1} {self.op_sym} {self.arg2}"
        if self.op == 'UNARY':
            return f"    {self.result} = {self.op_sym}{self.arg1}"
        if self.op == 'PARAM':
            return f"    param {self.arg1}"
        if self.op == 'CALL':
            return f"    {self.result} = call {self.arg1} {self.arg2}"
        if self.op == 'RETURN':
            return f"    return {self.arg1}" if self.arg1 else "    return"
        if self.op == 'PRINT':
            return f"    print {self.arg1}"
        if self.op == 'INPUT':
            return f"    input {self.arg1}"
        if self.op == 'ARRAY_SET':
            return f"    {self.result}[{self.arg1}] = {self.arg2}"
        if self.op == 'ARRAY_GET':
            return f"    {self.result} = {self.arg1}[{self.arg2}]"
        if self.op == 'FUNC_BEGIN':
            return f"\nFUNC {self.result}:"
        if self.op == 'FUNC_END':
            return f"END FUNC {self.result}"
        return f"    {self.op} {self.result} {self.arg1} {self.arg2}"


# ─────────────────────────────────────────────────────────
#  IR GENERATOR
# ─────────────────────────────────────────────────────────

class IRGenerator:
    """
    Walks the AST (visitor pattern) and emits TAC instructions.

    Usage:
        gen  = IRGenerator()
        tac  = gen.generate(ast_program)
        # tac is a list of TACInstruction objects
    """

    def __init__(self):
        self.instructions: list  = []
        self._temp_count:  int   = 0    # counter for temp variables: t0, t1, ...
        self._label_count: int   = 0    # counter for labels: L0, L1, ...

    # ── helpers ───────────────────────────────────────────

    def new_temp(self) -> str:
        """
        Create a fresh temporary variable name.
        WHY? When we compute  a + b * c, we need  t0 = b * c  then  t1 = a + t0.
        Each sub-expression gets its own temp so nothing overwrites anything else.
        """
        name = f"t{self._temp_count}"
        self._temp_count += 1
        return name

    def new_label(self) -> str:
        """Create a fresh jump label (L0, L1, ...) for if/while control flow."""
        name = f"L{self._label_count}"
        self._label_count += 1
        return name

    def emit(self, *args, **kwargs):
        """Append one TAC instruction to the output list."""
        self.instructions.append(TACInstruction(*args, **kwargs))

    # ── entry point ───────────────────────────────────────

    def generate(self, node: ASTNode) -> list:
        """
        Main entry. Call this with the root Program node.
        Returns the flat list of TACInstruction objects.
        """
        self.visit(node)
        return self.instructions

    # ── visitor dispatcher ────────────────────────────────

    def visit(self, node: ASTNode):
        """
        WHY visitor pattern?
        Instead of one giant if-elif chain, we dispatch to a method named
        visit_<NodeType>. Adding a new node type = adding one new method.
        Clean, extensible, standard in compiler design.
        """
        method_name = f"visit_{type(node).__name__}"
        visitor     = getattr(self, method_name, self.visit_unknown)
        return visitor(node)

    def visit_unknown(self, node):
        raise NotImplementedError(f"IRGenerator: no visitor for {type(node).__name__}")

    # ── statement visitors ────────────────────────────────

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDecl(self, node: VarDecl):
        """
        int x = expr;
        →  [evaluate expr → temp]  then  x = temp

        If there's no initialiser (e.g. float y;), we emit nothing.
        The variable is just "declared" — it gets a slot when codegen runs.
        """
        if node.init_value:
            val = self.visit(node.init_value)   # evaluate RHS, get temp name
            self.emit('ASSIGN', result=node.name, arg1=val)
        # array with no init: nothing to emit at this stage

    def visit_Assignment(self, node: Assignment):
        """
        x = expr;  →  evaluate expr → temp, then  x = temp
        """
        val = self.visit(node.value)
        self.emit('ASSIGN', result=node.name, arg1=val)

    def visit_IfStatement(self, node: IfStatement):
        """
        WHY so many labels?
        if/else requires CONDITIONAL JUMPS in TAC.

        Pattern with else:
            ifnot cond goto L_else
            [then body]
            goto L_end
          L_else:
            [else body]
          L_end:

        Pattern without else:
            ifnot cond goto L_end
            [then body]
          L_end:
        """
        cond     = self.visit(node.condition)
        l_else   = self.new_label()
        l_end    = self.new_label()

        self.emit('JUMPIFNOT', result=l_else, arg1=cond)

        for stmt in node.then_body:
            self.visit(stmt)

        if node.else_body:
            self.emit('JUMP', result=l_end)
            self.emit('LABEL', result=l_else)
            for stmt in node.else_body:
                self.visit(stmt)
            self.emit('LABEL', result=l_end)
        else:
            self.emit('LABEL', result=l_else)

    def visit_WhileStatement(self, node: WhileStatement):
        """
        While loop TAC pattern:
          L_start:
            [evaluate condition → temp]
            ifnot temp goto L_end
            [body]
            goto L_start
          L_end:

        WHY goto L_start at the end?
        That's what makes it a LOOP — we jump back to re-check the condition.
        """
        l_start = self.new_label()
        l_end   = self.new_label()

        self.emit('LABEL', result=l_start)
        cond = self.visit(node.condition)
        self.emit('JUMPIFNOT', result=l_end, arg1=cond)

        for stmt in node.body:
            self.visit(stmt)

        self.emit('JUMP', result=l_start)
        self.emit('LABEL', result=l_end)

    def visit_ReturnStatement(self, node: ReturnStatement):
        val = self.visit(node.value) if node.value else None
        self.emit('RETURN', arg1=val)

    def visit_PrintStatement(self, node: PrintStatement):
        val = self.visit(node.value)
        self.emit('PRINT', arg1=val)

    def visit_InputStatement(self, node: InputStatement):
        self.emit('INPUT', arg1=node.var_name)

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        self.visit(node.expression)     # evaluate but discard result

    def visit_FunctionDecl(self, node: FunctionDecl):
        """
        M2 function:
          FUNC_BEGIN  funcname
            [body instructions]
          FUNC_END    funcname
        """
        self.emit('FUNC_BEGIN', result=node.name)
        for stmt in node.body:
            self.visit(stmt)
        self.emit('FUNC_END', result=node.name)

    # ── expression visitors (return temp variable name) ───

    def visit_Literal(self, node: Literal):
        """
        A literal like 42 or 3.14 gets stored in a fresh temp.
        WHY not use the value directly?
        TAC instructions always reference NAMES, not inline values.
        This keeps the format uniform — codegen never has to special-case it.
        """
        temp = self.new_temp()
        self.emit('ASSIGN', result=temp, arg1=node.value)
        return temp

    def visit_Identifier(self, node: Identifier):
        """
        A variable reference: just return its name.
        WHY no emit? The variable already HAS a name — no temp needed.
        The variable name itself IS the TAC operand.
        """
        return node.name

    def visit_BinaryOp(self, node: BinaryOp):
        """
        a + b  →
            t0 = [evaluate a]
            t1 = [evaluate b]
            t2 = t0 + t1
        returns t2
        """
        left  = self.visit(node.left)
        right = self.visit(node.right)
        temp  = self.new_temp()
        self.emit('BINOP', result=temp, arg1=left, op_sym=node.op, arg2=right)
        return temp

    def visit_UnaryOp(self, node: UnaryOp):
        """
        -x  →  t0 = -x
        !b  →  t0 = !b
        """
        operand = self.visit(node.operand)
        temp    = self.new_temp()
        self.emit('UNARY', result=temp, op_sym=node.op, arg1=operand)
        return temp

    def visit_FunctionCall(self, node: FunctionCall):
        """
        foo(a, b)  →
            param a
            param b
            t0 = call foo 2
        returns t0

        WHY PARAM instructions before CALL?
        This mirrors actual calling conventions. The callee will pop
        arguments in order. Standard in all real compilers.
        """
        for arg in node.args:
            val = self.visit(arg)
            self.emit('PARAM', arg1=val)
        temp = self.new_temp()
        self.emit('CALL', result=temp, arg1=node.name, arg2=len(node.args))
        return temp

    def visit_ArrayAccess(self, node: ArrayAccess):
        """
        M2:  nums[i]  →  t0 = nums[i]
        """
        idx  = self.visit(node.index)
        temp = self.new_temp()
        self.emit('ARRAY_GET', result=temp, arg1=node.array_name, arg2=idx)
        return temp
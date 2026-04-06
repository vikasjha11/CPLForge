# cplc.py — Extraordinary CPL Cross Compiler
# Full 6-stage pipeline + symbol table + dual targets + rich errors

import sys
import os
import time
from lexer               import Lexer,            LexerError
from parser              import Parser,           ParseError
from semantic            import SemanticAnalyser, SemanticError
from ir                  import IRGenerator
from optimizer           import Optimizer
from codegen             import CodeGenerator
from codegen_c           import CCodeGenerator
from symbol_table_printer import print_symbol_table

# ── ANSI colours ──────────────────────────────────────────
BOLD   = '\033[1m'
GREEN  = '\033[92m'
CYAN   = '\033[96m'
YELLOW = '\033[93m'
RED    = '\033[91m'
DIM    = '\033[2m'
RESET  = '\033[0m'

def banner():
    print(f"""
{CYAN}{BOLD}
 ██████╗██████╗ ██╗      ██████╗ ██████╗ ███╗   ███╗██████╗
██╔════╝██╔══██╗██║     ██╔════╝██╔═══██╗████╗ ████║██╔══██╗
██║     ██████╔╝██║     ██║     ██║   ██║██╔████╔██║██████╔╝
██║     ██╔═══╝ ██║     ██║     ██║   ██║██║╚██╔╝██║██╔═══╝
╚██████╗██║     ███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║██║
 ╚═════╝╚═╝     ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝
{RESET}
{BOLD}  Bootstrap-Enabled Cross Compiler for CPL (Custom Programming Language){RESET}
{DIM}  Targets: x86 AT&T Assembly  |  C99
  Phases:  Lexer → Parser → Semantic → TAC IR → Optimizer → Codegen{RESET}
""")

def stage(n, name):
    print(f"{CYAN}{BOLD}[Stage {n}]{RESET} {BOLD}{name}{RESET}")

def ok(msg):
    print(f"         {GREEN}✓{RESET} {msg}")

def info(msg):
    print(f"         {DIM}{msg}{RESET}")

def compile_cpl(source: str,
                filename: str = "<stdin>",
                target: str   = "both",
                show_tokens   = False,
                show_ast      = True,
                show_ir       = True,
                show_opt      = True,
                show_symtable = True):

    banner()
    source_lines = source.splitlines()
    t_total = time.time()

    # ═══════════════════════════════════════════════════
    #  STAGE 1 — LEXICAL ANALYSIS
    # ═══════════════════════════════════════════════════
    stage(1, "Lexical Analysis")
    t = time.time()
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        ok(f"{len(tokens)-1} tokens produced in {(time.time()-t)*1000:.1f}ms")
    except LexerError as e:
        print(f"{RED}{BOLD}[Lex Error]{RESET} {e}")
        return

    if show_tokens:
        print(f"\n{DIM}  {'TYPE':<14} {'VALUE':<20} POSITION{RESET}")
        print(f"  {'─'*50}")
        for tok in tokens[:-1]:
            print(f"  {CYAN}{tok.type:<14}{RESET} {str(tok.value):<20} L{tok.line}:C{tok.col}")
        print()

    # ═══════════════════════════════════════════════════
    #  STAGE 2 — SYNTAX ANALYSIS
    # ═══════════════════════════════════════════════════
    stage(2, "Syntax Analysis  (LL(1) Recursive Descent Parser)")
    t = time.time()
    try:
        parser = Parser(tokens)
        tree   = parser.parse()
        # Count AST nodes
        node_count = _count_nodes(tree)
        ok(f"AST built — {node_count} nodes in {(time.time()-t)*1000:.1f}ms")
    except ParseError as e:
        print(f"{RED}{BOLD}[Parse Error]{RESET} {e}")
        return

    if show_ast:
        print(f"\n{YELLOW}{BOLD}  Abstract Syntax Tree:{RESET}")
        _print_ast_colored(tree)
        print()

    # ═══════════════════════════════════════════════════
    #  STAGE 3 — SEMANTIC ANALYSIS
    # ═══════════════════════════════════════════════════
    stage(3, "Semantic Analysis  (Symbol Table + Type Checking)")
    t = time.time()
    try:
        analyser = SemanticAnalyser()
        analyser.analyse(tree)
        ok(f"No semantic errors — {(time.time()-t)*1000:.1f}ms")
    except SemanticError as e:
        print(f"{RED}{BOLD}[Semantic Error]{RESET} {e}")
        return

    if show_symtable:
        print_symbol_table(analyser)

    # ═══════════════════════════════════════════════════
    #  STAGE 4 — IR GENERATION (TAC)
    # ═══════════════════════════════════════════════════
    stage(4, "Intermediate Code Generation  (Three Address Code)")
    t = time.time()
    gen = IRGenerator()
    tac = gen.generate(tree)
    ok(f"{len(tac)} TAC instructions generated in {(time.time()-t)*1000:.1f}ms")

    if show_ir:
        print(f"\n{YELLOW}{BOLD}  TAC (before optimization):{RESET}")
        _print_tac_colored(tac)
        print()

    # ═══════════════════════════════════════════════════
    #  STAGE 5 — OPTIMIZATION
    # ═══════════════════════════════════════════════════
    stage(5, "Optimization  (4-Pass: Folding → Propagation → Copy → DCE)")
    t = time.time()
    opt     = Optimizer()
    opt_tac = opt.optimize(tac)
    removed = len(tac) - len(opt_tac)
    pct     = (removed / len(tac) * 100) if tac else 0
    ok(f"{removed} instructions eliminated ({pct:.0f}% reduction) in {(time.time()-t)*1000:.1f}ms")

    if show_opt:
        print(f"\n{YELLOW}{BOLD}  TAC (after optimization):{RESET}")
        _print_tac_colored(opt_tac)
        print()

    # ═══════════════════════════════════════════════════
    #  STAGE 6 — CODE GENERATION (dual targets)
    # ═══════════════════════════════════════════════════
    stage(6, "Target Code Generation  (Cross-Compilation)")

    results = {}

    if target in ('x86', 'both'):
        t   = time.time()
        cg  = CodeGenerator()
        asm = cg.generate(opt_tac)
        with open("output.asm", 'w') as f: f.write(asm)
        ok(f"x86 AT&T Assembly → output.asm  ({len(asm.splitlines())} lines, {(time.time()-t)*1000:.1f}ms)")
        results['asm'] = asm

    if target in ('c', 'both'):
        t    = time.time()
        ccg  = CCodeGenerator()
        csrc = ccg.generate(opt_tac)
        with open("output.c", 'w') as f: f.write(csrc)
        ok(f"C99 Source Code   → output.c    ({len(csrc.splitlines())} lines, {(time.time()-t)*1000:.1f}ms)")
        results['c'] = csrc

    # ═══════════════════════════════════════════════════
    #  SUMMARY
    # ═══════════════════════════════════════════════════
    total_ms = (time.time() - t_total) * 1000
    print(f"\n{GREEN}{BOLD}{'═'*52}{RESET}")
    print(f"{GREEN}{BOLD}  ✓ Compilation successful in {total_ms:.1f}ms{RESET}")
    print(f"{GREEN}{BOLD}{'═'*52}{RESET}\n")

    if 'asm' in results:
        print(f"{YELLOW}{BOLD}  ── x86 Assembly Output ──────────────────────{RESET}")
        for line in results['asm'].splitlines():
            if line.strip().startswith('#'):
                print(f"  {DIM}{line}{RESET}")
            elif line.strip().endswith(':') and not line.strip().startswith('.'):
                print(f"  {CYAN}{BOLD}{line}{RESET}")
            elif line.strip().startswith('.'):
                print(f"  {YELLOW}{line}{RESET}")
            else:
                print(f"  {line}")

    if 'c' in results:
        print(f"\n{YELLOW}{BOLD}  ── C Output ─────────────────────────────────{RESET}")
        for line in results['c'].splitlines():
            if line.strip().startswith('//') or line.strip().startswith('/*'):
                print(f"  {DIM}{line}{RESET}")
            elif any(kw in line for kw in ('int ', 'double ', 'void ', 'return', '#include')):
                print(f"  {CYAN}{line}{RESET}")
            else:
                print(f"  {line}")

    return results


# ── helpers ───────────────────────────────────────────────

def _count_nodes(node) -> int:
    from ast import ASTNode
    if not isinstance(node, ASTNode): return 0
    count = 1
    for v in node.__dict__.values():
        if isinstance(v, ASTNode):
            count += _count_nodes(v)
        elif isinstance(v, list):
            count += sum(_count_nodes(i) for i in v)
    return count

def _print_ast_colored(node, indent=0):
    from ast import ASTNode
    if not isinstance(node, ASTNode): return
    pad  = "  " * indent
    name = type(node).__name__
    # Color node types
    color = {
        'Program': BOLD, 'VarDecl': GREEN, 'Assignment': GREEN,
        'IfStatement': CYAN, 'WhileStatement': CYAN,
        'BinaryOp': YELLOW, 'Literal': DIM, 'Identifier': '',
        'PrintStatement': GREEN, 'FunctionDecl': CYAN,
    }.get(name, '')
    attrs = {k: v for k, v in node.__dict__.items()
             if k not in ('line', 'col') and not isinstance(v, (ASTNode, list))}
    attr_str = ', '.join(f"{k}={v!r}" for k, v in attrs.items() if v not in (None, '', 0))
    print(f"{pad}{color}{name}{RESET}({attr_str})")
    for k, v in node.__dict__.items():
        if k in ('line', 'col'): continue
        if isinstance(v, ASTNode):
            print(f"{pad}  {DIM}{k}:{RESET}")
            _print_ast_colored(v, indent + 2)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, ASTNode):
                    _print_ast_colored(item, indent + 1)

def _print_tac_colored(instructions):
    for instr in instructions:
        line = str(instr)
        if instr.op == 'LABEL':
            print(f"  {CYAN}{BOLD}{line}{RESET}")
        elif instr.op in ('JUMP', 'JUMPIF', 'JUMPIFNOT'):
            print(f"  {YELLOW}{line}{RESET}")
        elif instr.op == 'PRINT':
            print(f"  {GREEN}{line}{RESET}")
        elif instr.op in ('FUNC_BEGIN', 'FUNC_END'):
            print(f"  {CYAN}{BOLD}{line}{RESET}")
        else:
            print(f"  {DIM}{line}{RESET}")


# ═══════════════════════════════════════════════════════════
#  DEMO — run with:  python cplc.py
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    # This demo shows ALL features:
    # - int, float, string types
    # - if/else, while
    # - arithmetic with operator precedence
    # - constant folding opportunity (100 + 200)
    # - dead variable (unused temp)
    # - print, input

    sample = """
    int a = 5;
    int b = 3;
    int folded = 100 + 200;
    int result = a + b * 2;

    if (result > 10) {
        print(result);
    } else {
        int x = 0;
        while (x < result) {
            x = x + 1;
        }
        print(x);
    }
    """

    compile_cpl(
        sample,
        show_tokens   = False,
        show_ast      = True,
        show_ir       = True,
        show_opt      = True,
        show_symtable = True,
        target        = 'both',
    )
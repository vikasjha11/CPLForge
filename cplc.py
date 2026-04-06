# cplc.py — Full compiler driver
# Wires all 6 stages together.

import sys
from lexer     import Lexer,     LexerError
from parser    import Parser,    ParseError
from semantic  import SemanticAnalyser, SemanticError
from ir        import IRGenerator
from optimizer import Optimizer
from codegen   import CodeGenerator


def compile_cpl(source: str,
                dump_tokens=False,
                dump_ast=False,
                dump_ir=False,
                dump_opt=False,
                output_file=None):

    print("=" * 50)
    print("  CPL Cross Compiler — Bootstrap Edition")
    print("=" * 50)

    # ── Stage 1: Lexical Analysis ─────────────────────────
    print("\n[Stage 1] Lexical Analysis...")
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        print(f"          {len(tokens)-1} tokens produced.")
    except LexerError as e:
        print(f"  [LEXER ERROR] {e}"); return None

    if dump_tokens:
        print("\n=== TOKENS ===")
        for t in tokens: print(" ", t)

    # ── Stage 2: Syntax Analysis (Parsing) ───────────────
    print("\n[Stage 2] Syntax Analysis (Parsing)...")
    try:
        parser = Parser(tokens)
        tree   = parser.parse()
        print(f"          AST built successfully.")
    except ParseError as e:
        print(f"  [PARSE ERROR] {e}"); return None

    if dump_ast:
        print("\n=== AST ===")
        print(tree.tree_str())

    # ── Stage 3: Semantic Analysis ───────────────────────
    print("\n[Stage 3] Semantic Analysis...")
    try:
        analyser = SemanticAnalyser()
        analyser.analyse(tree)
        print(f"          No semantic errors found.")
    except SemanticError as e:
        print(f"  [SEMANTIC ERROR] {e}"); return None

    # ── Stage 4: IR Generation (TAC) ─────────────────────
    print("\n[Stage 4] Intermediate Code Generation (TAC)...")
    gen = IRGenerator()
    tac = gen.generate(tree)
    print(f"          {len(tac)} TAC instructions generated.")

    if dump_ir:
        print("\n=== THREE ADDRESS CODE (before optimization) ===")
        for instr in tac: print(instr)

    # ── Stage 5: Optimization ─────────────────────────────
    print("\n[Stage 5] Optimization...")
    opt     = Optimizer()
    opt_tac = opt.optimize(tac)
    removed = len(tac) - len(opt_tac)
    print(f"          {removed} instructions eliminated.")

    if dump_opt:
        print("\n=== THREE ADDRESS CODE (after optimization) ===")
        for instr in opt_tac: print(instr)

    # ── Stage 6: Code Generation ──────────────────────────
    print("\n[Stage 6] Target Code Generation (x86 Assembly)...")
    cg  = CodeGenerator()
    asm = cg.generate(opt_tac)
    print(f"          Assembly generated.")

    # Output
    out_file = output_file or "output.asm"
    with open(out_file, 'w') as f:
        f.write(asm)
    print(f"\n✓ Output written to: {out_file}")
    print("\n=== ASSEMBLY OUTPUT ===")
    print(asm)

    return asm


if __name__ == '__main__':
    sample = """
int a = 5;
int b = 3;
int result = a + b * 2;
int dead = 100 + 200;
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
        dump_tokens=False,
        dump_ast=True,
        dump_ir=True,
        dump_opt=True,
        output_file="output.asm"
    )
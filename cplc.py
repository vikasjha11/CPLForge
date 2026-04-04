# cplc.py  — main compiler driver (Member A owns this fully)
# This is a MINIMAL version so the team can test lexer + parser + IR together.

import sys
from lexer  import Lexer,  LexerError
from parser import Parser, ParseError
from ir     import IRGenerator

def compile_cpl(source: str, dump_tokens=False, dump_ast=False, dump_ir=True):
    # ── Stage 1: Lex ─────────────────────────────────────
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[LEXER ERROR] {e}"); return

    if dump_tokens:
        print("=== TOKENS ===")
        for t in tokens: print(" ", t)

    # ── Stage 2: Parse ────────────────────────────────────
    try:
        parser = Parser(tokens)
        tree   = parser.parse()
    except ParseError as e:
        print(f"[PARSE ERROR] {e}"); return

    if dump_ast:
        print("=== AST ===")
        print(tree.tree_str())

    # ── Stage 3: Generate IR ──────────────────────────────
    gen  = IRGenerator()
    tac  = gen.generate(tree)

    if dump_ir:
        print("=== THREE ADDRESS CODE ===")
        for instr in tac: print(instr)

    return tac


if __name__ == '__main__':
    sample = """
    int a = 5;
    int b = 3;
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
    compile_cpl(sample, dump_tokens=False, dump_ast=True, dump_ir=True)
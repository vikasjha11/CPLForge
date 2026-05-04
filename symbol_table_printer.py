# symbol_table_printer.py
# Dumps the symbol table in a beautiful format for demo purposes.
#
# WHY show this?
# The symbol table is one of the core data structures in any compiler.
# Printing it visually proves you understand scope and type management.

def print_symbol_table(analyser):
    """
    Takes a SemanticAnalyser after it has run and prints its symbol table.
    """
    BOLD  = '\033[1m'
    CYAN  = '\033[96m'
    GREEN = '\033[92m'
    RESET = '\033[0m'

    print(f"\n{BOLD}{CYAN}{'='*52}{RESET}")
    print(f"{BOLD}{CYAN}  SYMBOL TABLE — CPL Compiler{RESET}")
    print(f"{BOLD}{CYAN}{'='*52}{RESET}")

    def dump_scope(scope, depth=0):
        pad = "  " * depth
        label = "Global Scope" if depth == 0 else f"Block Scope (depth {depth})"
        print(f"\n{pad}{BOLD}{label}{RESET}")
        print(f"{pad}{'─'*40}")

        if not scope.symbols:
            print(f"{pad}  (empty)")
        else:
            print(f"{pad}  {'Name':<15} {'Type':<10} {'Array?':<8} {'Line'}")
            print(f"{pad}  {'─'*35}")
            for name, info in scope.symbols.items():
                arr = '✓' if info.get('is_array') else '–'
                print(f"{pad}  {GREEN}{name:<15}{RESET} {info['type']:<10} {arr:<8} {info['line']}")

        if scope.parent:
            # We can't walk children directly, but global scope has all globals
            pass

    dump_scope(analyser.scope)

    if analyser.functions:
        print(f"\n{BOLD}  Functions Declared:{RESET}")
        print(f"  {'─'*35}")
        for fname, fdecl in analyser.functions.items():
            params = ', '.join(f"{t} {n}" for t, n in fdecl.params)
            print(f"  {GREEN}{fname}{RESET}({params}) → {fdecl.return_type}")

    print(f"\n{BOLD}{CYAN}{'='*52}{RESET}\n")
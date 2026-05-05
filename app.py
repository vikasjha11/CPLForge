from flask import Flask, render_template, request, jsonify
import sys, os, time

sys.path.insert(0, os.path.dirname(__file__))

from lexer      import Lexer,            LexerError
from parser     import Parser,           ParseError
from semantic   import SemanticAnalyser, SemanticError
from ir         import IRGenerator
from optimizer  import Optimizer
from codegen    import CodeGenerator
from codegen_c  import CCodeGenerator

app = Flask(__name__)

def count_nodes(node):
    from cpl_ast import ASTNode
    if not isinstance(node, ASTNode): return 0
    count = 1
    for v in node.__dict__.values():
        if isinstance(v, ASTNode): count += count_nodes(v)
        elif isinstance(v, list): count += sum(count_nodes(i) for i in v)
    return count

def ast_to_text(node, indent=0):
    from cpl_ast import ASTNode
    if not isinstance(node, ASTNode): return ""
    lines = []
    pad  = "  " * indent
    name = type(node).__name__
    attrs = {k: v for k, v in node.__dict__.items()
             if k not in ('line','col') and not isinstance(v, (ASTNode, list))}
    attr_str = ', '.join(f"{k}={v!r}" for k, v in attrs.items() if v not in (None,'',0))
    lines.append(f"{pad}{name}({attr_str})")
    for k, v in node.__dict__.items():
        if k in ('line','col'): continue
        if isinstance(v, ASTNode): lines.append(ast_to_text(v, indent+1))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, ASTNode): lines.append(ast_to_text(item, indent+1))
    return "\n".join(l for l in lines if l)

@app.route("/compile", methods=["POST"])
def compile_code():
    data   = request.get_json()
    source = data.get("code", "").strip()
    if not source:
        return jsonify({"success": False, "error": "Source code is empty.", "error_stage": 1})

    stages = {}

    # Stage 1: Lexer
    t = time.time()
    try:
        lexer  = Lexer(source)
        tokens = lexer.tokenize()
        tok_list = [{"type": tok.type, "value": str(tok.value), "line": tok.line, "col": tok.col}
                    for tok in tokens if tok.type != "EOF"]
        ms = round((time.time()-t)*1000, 1)
        stages["1"] = {"status":"success","summary":f"{len(tok_list)} tokens in {ms}ms","tokens":tok_list}
    except LexerError as e:
        stages["1"] = {"status":"error","summary":str(e)}
        return jsonify({"success":False,"error":str(e),"error_stage":1,"stages":stages})

    # Stage 2: Parser
    t = time.time()
    try:
        parser = Parser(tokens)
        tree   = parser.parse()
        nodes  = count_nodes(tree)
        ms     = round((time.time()-t)*1000, 1)
        preview_lines = ast_to_text(tree).splitlines()
        preview = "\n".join(preview_lines[:20])
        if len(preview_lines) > 20: preview += f"\n  ... ({len(preview_lines)-20} more nodes)"
        stages["2"] = {"status":"success","summary":f"AST built — {nodes} nodes in {ms}ms","ast_nodes":nodes,"ast_preview":preview}
    except ParseError as e:
        stages["2"] = {"status":"error","summary":str(e)}
        return jsonify({"success":False,"error":str(e),"error_stage":2,"stages":stages})

    # Stage 3: Semantic
    t = time.time()
    try:
        analyser = SemanticAnalyser()
        analyser.analyse(tree)
        ms = round((time.time()-t)*1000, 1)
        symbols = []
        # Walk the scope chain and collect all declared symbols
        def collect_scope(scope, scope_label):
            if scope is None: return
            for name, info in scope.symbols.items():
                symbols.append({"name":name,"type":str(info.get("type","?")),"value":str(info.get("value","-")),"scope":scope_label})
            if scope.parent:
                collect_scope(scope.parent, "parent")
        collect_scope(analyser.scope, "global")
        stages["3"] = {"status":"success","summary":f"No semantic errors · {ms}ms","symbols":symbols}
    except SemanticError as e:
        stages["3"] = {"status":"error","summary":str(e)}
        return jsonify({"success":False,"error":str(e),"error_stage":3,"stages":stages})

    # Stage 4: IR
    t = time.time()
    gen = IRGenerator()
    tac = gen.generate(tree)
    ms  = round((time.time()-t)*1000, 1)
    tac_strs = [str(i) for i in tac]
    stages["4"] = {"status":"success","summary":f"{len(tac_strs)} TAC instructions · {ms}ms","tac":tac_strs}

    # Stage 5: Optimizer
    t = time.time()
    opt     = Optimizer()
    opt_tac = opt.optimize(tac)
    ms      = round((time.time()-t)*1000, 1)
    removed = len(tac) - len(opt_tac)
    stages["5"] = {"status":"success","summary":f"{removed} instructions eliminated · {ms}ms","optimized_tac":[str(i) for i in opt_tac],"eliminated":removed}

    # Stage 6: Codegen
    t   = time.time()
    asm = CodeGenerator().generate(opt_tac)
    c   = CCodeGenerator().generate(opt_tac)
    with open("output.asm", "w", encoding="utf-8") as f:
        f.write(asm)
    with open("output.c", "w", encoding="utf-8") as f:
        f.write(c)
    ms  = round((time.time()-t)*1000, 1)
    stages["6"] = {"status":"success","summary":f"x86 + C99 generated · {ms}ms","asm":asm,"c_code":c}

    return jsonify({"success":True,"error":None,"error_stage":None,"stages":stages})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    print("=" * 52)
    print("  CPL Cross Compiler — Local (No API needed!)")
    print("  Open in browser: http://localhost:5000")
    print("=" * 52)
    app.run(debug=True, port=5000)

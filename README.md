<div align="center">

```
 ██████╗██████╗ ██╗            ██████╗ ██████╗ ███╗   ███╗██████╗ ██╗██╗     ███████╗██████╗
██╔════╝██╔══██╗██║           ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██║██║     ██╔════╝██╔══██╗
██║     ██████╔╝██║           ██║     ██║   ██║██╔████╔██║██████╔╝██║██║     █████╗  ██████╔╝
██║     ██╔═══╝ ██║           ██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██║██║     ██╔══╝  ██╔══██╗
╚██████╗██║     ███████╗      ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║███████╗███████╗██║  ██║
 ╚═════╝╚═╝     ╚══════╝       ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
```

# CPL Cross Compiler

### A full-pipeline compiler for the CPL language — from source to x86 Assembly & C99

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web%20UI-black?style=flat-square&logo=flask)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)

</div>

---

## ✨ What is CPL Compiler?

CPL Compiler is a **6-stage cross compiler** built with Python and Flask. It takes CPL source code and walks it through the complete compilation pipeline — right in your browser. No heavyweight IDE, no cloud dependency, no Node.js. Just Python.

### 🔁 Compilation Pipeline

```
Source Code
    │
    ▼
┌──────────────┐
│  1. Lexer    │  → Tokenizes source into typed tokens
└──────┬───────┘
       ▼
┌──────────────┐
│  2. Parser   │  → Builds Abstract Syntax Tree (AST)
└──────┬───────┘
       ▼
┌──────────────┐
│  3. Semantic │  → Type checking, scope & symbol resolution
└──────┬───────┘
       ▼
┌──────────────┐
│  4. IR Gen   │  → Generates Three-Address Code (TAC)
└──────┬───────┘
       ▼
┌──────────────┐
│  5. Optimizer│  → Dead code elimination & instruction reduction
└──────┬───────┘
       ▼
┌──────────────┐
│  6. Codegen  │  → Outputs x86 Assembly + C99 code
└──────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** → [Download here](https://python.org)

Verify: `python --version`

---

### Step 1 — Clone or Download the Project

```bash
git clone https://github.com/vikasjha11/Cross_Compiler_Project.git
cd cpl-compiler/CPL_Flask
```

Or download the ZIP and extract it.

---

### Step 2 — Install Dependencies

```bash
pip install flask
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

---

### Step 3 — Run the Compiler

```bash
python app.py
```

Then open your browser at:

```
http://localhost:5000
```

That's it. The full UI loads instantly.

---

## 🗂️ Project Structure

```
CPL_Flask/
│
├── app.py                  ← Flask server — the only file you need to run
├── requirements.txt        ← Python dependencies
│
├── lexer.py                ← Stage 1: Tokenizer / Lexical Analyser
├── parser.py               ← Stage 2: Recursive Descent Parser
├── cpl_ast.py              ← AST Node definitions
├── semantic.py             ← Stage 3: Semantic Analyser
├── ir.py                   ← Stage 4: Intermediate Representation (TAC) Generator
├── optimizer.py            ← Stage 5: TAC Optimizer
├── codegen.py              ← Stage 6: x86 Assembly Code Generator
├── codegen_c.py            ← Stage 6: C99 Code Generator
├── symbol_table_printer.py ← Symbol table display utility
├── error_handler.py        ← Centralised error handling
│
└── templates/
    └── index.html          ← Complete web UI (single file)
```

---

## 🎯 Features

| Feature | Description |
|---|---|
| 🔍 **Lexical Analysis** | Full tokenizer with line & column tracking |
| 🌳 **AST Visualization** | Human-readable AST preview in the browser |
| 🔎 **Semantic Checking** | Type checking, undeclared variable detection, scope analysis |
| 📋 **Symbol Table** | Inspect all declared symbols, their types & values |
| ⚙️ **IR Generation** | Three-address code (TAC) intermediate representation |
| ⚡ **Optimization** | Dead code elimination & instruction count reduction |
| 💻 **x86 Assembly** | Full x86 assembly output |
| 🇨 **C99 Output** | Portable C99 code generation |
| ⏱️ **Stage Timing** | Each stage reports its execution time in milliseconds |
| 🖥️ **Browser UI** | Clean, interactive web interface — no IDE needed |

---

## 🧪 Example

Write CPL code in the browser editor and click **Compile**. The UI shows each pipeline stage separately — tokens, AST, symbol table, TAC, optimized TAC, and final assembly/C output — all at once.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web server & template rendering |

> All compiler stages are written in **pure Python** — no external compiler tools required.



## 👨‍💻 Built With

- **Python 3** — Core language
- **Flask** — Lightweight web framework
- **Vanilla HTML/CSS/JS** — Zero frontend dependencies

---



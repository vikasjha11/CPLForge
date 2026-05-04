# optimizer.py — Full Optimizer (4 passes)
#
# PASS 1: Constant Folding    — compute 3+4 at compile time → 7
# PASS 2: Constant Propagation — if x=5 always, replace uses of x with 5
# PASS 3: Copy Propagation    — if t1=t0, replace uses of t1 with t0
# PASS 4: Dead Code Elimination — remove writes to temps never read
#
# WHY THIS ORDER?
# Each pass exposes opportunities for the next:
# Folding creates constants → propagation spreads them → more dead code appears → eliminate it.
# Running them in sequence is called an "optimization pipeline".

from ir import TACInstruction


class Optimizer:

    def optimize(self, instructions: list) -> list:
        result = instructions
        # Run 2 full cycles — second cycle catches cascading opportunities
        for _ in range(2):
            result = self.constant_folding(result)
            result = self.constant_propagation(result)
            result = self.copy_propagation(result)
            result = self.dead_code_elimination(result)
        return result

    # ── PASS 1: Constant Folding ──────────────────────────

    def constant_folding(self, instructions):
        """
        t0 = 3         }
        t1 = 4         }  →  t2 = 7   (folded at compile time)
        t2 = t0 + t1   }
        """
        const_map = {}
        result    = []

        for instr in instructions:
            if instr.op == 'ASSIGN':
                if isinstance(instr.arg1, (int, float, bool)):
                    const_map[instr.result] = instr.arg1
                elif isinstance(instr.arg1, str) and instr.arg1 in const_map:
                    const_map[instr.result] = const_map[instr.arg1]
                else:
                    const_map.pop(instr.result, None)
                result.append(instr)

            elif instr.op == 'BINOP':
                lv = const_map.get(instr.arg1, instr.arg1)
                rv = const_map.get(instr.arg2, instr.arg2)
                if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
                    folded = self._apply_op(instr.op_sym, lv, rv)
                    if folded is not None:
                        const_map[instr.result] = folded
                        result.append(TACInstruction('ASSIGN',
                                      result=instr.result, arg1=folded))
                        continue
                const_map.pop(instr.result, None)
                result.append(instr)
            else:
                if instr.result:
                    const_map.pop(instr.result, None)
                result.append(instr)
        return result

    # ── PASS 2: Constant Propagation ─────────────────────

    def constant_propagation(self, instructions):
        """
        x = 5
        t0 = x + 1   →   t0 = 5 + 1   (x replaced by its known value 5)

        WHY different from folding?
        Folding works on TEMPS. Propagation works on USER VARIABLES.
        Together they cover all constant cases.
        """
        const_map = {}
        result    = []

        for instr in instructions:
            # Replace known constants in operands
            arg1 = const_map.get(instr.arg1, instr.arg1) if isinstance(instr.arg1, str) else instr.arg1
            arg2 = const_map.get(instr.arg2, instr.arg2) if isinstance(instr.arg2, str) else instr.arg2

            new_instr = TACInstruction(instr.op, instr.result, arg1, instr.op_sym, arg2)

            if instr.op == 'ASSIGN' and isinstance(arg1, (int, float, bool)):
                const_map[instr.result] = arg1
            elif instr.result:
                # If variable is reassigned to non-constant, forget its value
                const_map.pop(instr.result, None)

            result.append(new_instr)
        return result

    # ── PASS 3: Copy Propagation ──────────────────────────

    def copy_propagation(self, instructions):
        """
        t1 = t0       }
        t2 = t1 + x   }  →  t2 = t0 + x   (t1 eliminated, use t0 directly)

        WHY? Removes unnecessary variable copies.
        This often triggers dead code elimination on the copy instruction.
        """
        copy_map = {}   # t1 → t0 (t1 is just a copy of t0)
        result   = []

        for instr in instructions:
            # Resolve operands through copy chain
            arg1 = copy_map.get(instr.arg1, instr.arg1) if isinstance(instr.arg1, str) else instr.arg1
            arg2 = copy_map.get(instr.arg2, instr.arg2) if isinstance(instr.arg2, str) else instr.arg2

            # Record copy relationship
            if instr.op == 'ASSIGN' and isinstance(instr.arg1, str) \
               and isinstance(instr.result, str):
                copy_map[instr.result] = arg1
            elif instr.result:
                copy_map.pop(instr.result, None)

            result.append(TACInstruction(instr.op, instr.result, arg1, instr.op_sym, arg2))
        return result

    # ── PASS 4: Dead Code Elimination ────────────────────

    def dead_code_elimination(self, instructions):
        """
        Remove any temp write that is never read.
        """
        read_set = set()
        for instr in instructions:
            for val in (instr.arg1, instr.arg2):
                if isinstance(val, str) and not val.startswith('L'):
                    read_set.add(val)

        result = []
        for instr in instructions:
            is_dead = (
                instr.op in ('ASSIGN', 'BINOP', 'UNARY', 'CALL', 'ARRAY_GET')
                and isinstance(instr.result, str)
                and instr.result.startswith('t')
                and instr.result not in read_set
            )
            if not is_dead:
                result.append(instr)
        return result

    def _apply_op(self, op, l, r):
        try:
            ops = {'+': l+r, '-': l-r, '*': l*r,
                   '/': (l//r if isinstance(l,int) and isinstance(r,int) else l/r) if r!=0 else None,
                   '%': l%r if r!=0 else None,
                   '==': l==r, '!=': l!=r,
                   '<': l<r, '>': l>r, '<=': l<=r, '>=': l>=r}
            return ops.get(op)
        except: return None
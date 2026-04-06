# optimizer.py
# TAC Optimizer for CPL
#
# TWO OPTIMIZATIONS (as required by problem statement):
#
# 1. CONSTANT FOLDING
#    If both operands of a BINOP are known constants at compile time,
#    compute the result NOW instead of emitting a runtime instruction.
#
#    Before:  t0 = 3
#             t1 = 4
#             t2 = t0 + t1      ← both temps hold constants
#    After:   t2 = 7            ← computed at compile time, 2 instructions gone
#
# 2. DEAD CODE ELIMINATION
#    A temp variable that is assigned but NEVER READ afterward is "dead".
#    Remove its assignment — it contributes nothing.
#
#    Before:  t0 = 5            ← t0 is never used again
#             t1 = x + 1
#    After:   t1 = x + 1        ← t0 line removed

from ir import TACInstruction


class Optimizer:
    """
    Takes a list of TACInstructions, returns an optimized list.

    Usage:
        opt = Optimizer()
        optimized_tac = opt.optimize(tac_list)
    """

    def optimize(self, instructions: list) -> list:
        # Run multiple passes — each pass enables the next
        # WHY multiple passes? Constant folding may expose new dead code.
        result = instructions
        result = self.constant_folding(result)
        result = self.dead_code_elimination(result)
        return result

    # ─────────────────────────────────────────────────────
    #  PASS 1: CONSTANT FOLDING
    # ─────────────────────────────────────────────────────

    def constant_folding(self, instructions: list) -> list:
        """
        Track which temps hold constant values.
        When a BINOP has both operands as known constants → fold it.

        We maintain a dict:  const_map = { 't0': 5, 't1': 3, ... }
        When we see  t2 = t0 + t1  and both are in const_map,
        we compute t2's value and add it to const_map too.
        Then we REPLACE the BINOP with a simple ASSIGN of the folded value.
        """
        const_map = {}   # temp_name → constant Python value
        result    = []

        for instr in instructions:
            if instr.op == 'ASSIGN':
                # If RHS is a Python literal → record it as constant
                if isinstance(instr.arg1, (int, float, bool)):
                    const_map[instr.result] = instr.arg1
                elif isinstance(instr.arg1, str) and instr.arg1 in const_map:
                    # Propagating:  x = t0  where t0 is known constant
                    const_map[instr.result] = const_map[instr.arg1]
                else:
                    # RHS is a non-constant variable → result is not constant
                    const_map.pop(instr.result, None)
                result.append(instr)

            elif instr.op == 'BINOP':
                left_val  = const_map.get(instr.arg1,  instr.arg1)
                right_val = const_map.get(instr.arg2, instr.arg2)

                # Both sides are concrete Python values → fold now
                if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
                    folded = self._apply_op(instr.op_sym, left_val, right_val)
                    if folded is not None:
                        const_map[instr.result] = folded
                        # Replace BINOP with a simple ASSIGN of the folded value
                        result.append(TACInstruction('ASSIGN',
                                                     result=instr.result,
                                                     arg1=folded))
                        continue    # skip appending original BINOP

                # Can't fold → propagate as non-constant
                const_map.pop(instr.result, None)
                result.append(instr)

            else:
                # Non-arithmetic instruction — pass through unchanged
                # But if it WRITES to a temp, invalidate that temp's const status
                if instr.result and instr.result in const_map:
                    const_map.pop(instr.result, None)
                result.append(instr)

        return result

    def _apply_op(self, op: str, left, right):
        """Evaluate a binary operation on two Python values."""
        try:
            if op == '+':  return left + right
            if op == '-':  return left - right
            if op == '*':  return left * right
            if op == '/':
                if right == 0: return None   # don't fold division by zero
                return left // right if isinstance(left, int) and isinstance(right, int) else left / right
            if op == '%':
                if right == 0: return None
                return left % right
            if op == '==': return left == right
            if op == '!=': return left != right
            if op == '<':  return left < right
            if op == '>':  return left > right
            if op == '<=': return left <= right
            if op == '>=': return left >= right
        except Exception:
            return None
        return None

    # ─────────────────────────────────────────────────────
    #  PASS 2: DEAD CODE ELIMINATION
    # ─────────────────────────────────────────────────────

    def dead_code_elimination(self, instructions: list) -> list:
        """
        Remove ASSIGN/BINOP/UNARY instructions whose result is NEVER READ.

        Step 1: Find all temps that are READ anywhere (used as arg1 or arg2).
        Step 2: Any temp that is written but NEVER appears as a read → dead.
        Step 3: Remove its write instruction.

        WHY only temps (t0, t1, ...)?
        We only eliminate TEMPORARIES. We never remove writes to user-named
        variables (x, result, etc.) because the user might read them later
        or they might be printed/returned.
        """
        # Collect all values that are READ (appear as an operand)
        read_set = set()
        for instr in instructions:
            for val in (instr.arg1, instr.arg2, instr.op_sym):
                if isinstance(val, str) and not val.startswith('L'):
                    read_set.add(val)

        result = []
        for instr in instructions:
            # Only consider eliminating temp writes (t0, t1, ...)
            is_temp_write = (
                instr.op in ('ASSIGN', 'BINOP', 'UNARY', 'CALL', 'ARRAY_GET')
                and isinstance(instr.result, str)
                and instr.result.startswith('t')
                and instr.result not in read_set
            )
            if is_temp_write:
                continue    # skip — this temp is never used
            result.append(instr)

        return result
---
name: re-decompilation
description: Reverse engineering decompilation with radare2 and Ghidra: recover logic from disassembly, rename symbols, reconstruct functions. Use after binary analysis when recovering code logic.
---

# Decompilation

Recover readable logic from machine code. The goal is reconstructing what a function
does, precisely, with addresses and evidence. Never guess what code does from its name.

## Toolchain

- **radare2 (`r2`)**: core, always available. Static + dynamic.
- **Ghidra**: upgrade for precision, its decompiler produces C-like output. Optional but
  strongly preferred for complex logic.
- If Ghidra is missing, radare2 + `r2dec` or manual disassembly still works. Degrade
  gracefully (see anti-delirium: only claim what the tool showed).

## Workflow

### 1. Analyze and list functions

```bash
r2 -A <binary>
r2 -qc "afl" <binary>          # functions (stripped: fewer)
r2 -qc "aflt" <binary>         # functions by size
```

### 2. Pick a target function

Start where behavior is visible: the entry, the functions called by imports of interest,
or the strings you found. Go from observable to internal.

### 3. Disassemble and decompile

```bash
# disassembly of a function
r2 -qc "s <addr>; pdf" <binary>

# decompile (if r2dec/ghidra decompiler installed)
r2 -qc "s <addr>; pdd" <binary>

# Ghidra: File → Import → Analyze → Decompile (F5 on a function)
```

### 4. Rename and annotate as you understand

- Rename `fcn.00401000` → `verify_license` once you understand it. This is the work.
- Track arguments, return values, and what each branch means.
- Every rename must be justified by evidence (what the code does), not vibes.

### 5. Reconstruct the algorithm

Produce a readable description: what the function takes, what it does, what it returns,
which branch does what. This feeds re-algorithm-recovery.

## Unpacking (when packed)

```bash
# UPX
upx -d <binary> -o <unpacked>

# Generic: dump after unpacking in a debugger (see re-dynamic-analysis)
# or use Ghidra's auto-analysis which often handles packed sections partially
```

Never analyze a packed binary as if it were the real code. Unpack first.

## Precision rules (the core of RE)

1. **Address + evidence for everything.** Every claim about a function is tied to an
   address and the disassembly that supports it.
2. **Name only what you understand.** An unconfirmed function stays `fcn.xxxx`, it does
   not become `decrypt_data` on a hunch.
3. **Reconstruct, don't invent.** If a branch is unreachable or a call is obfuscated, say
   so. Recovered logic must trace back to instructions you read.
4. **Strings guide, code proves.** A string "invalid key" hints at a check; the comparison
   instruction proves where it is.

## Output contract

```
### RECOVERED FUNCTION
- address / name: [0x401000] verify_license
- signature: [int verify_license(char *key)]
- logic:
  - [what it does, step by step, each step tied to an address]
  - [branches and what they mean]
  - [calls and what they return]
- evidence: [pdf output / decompiler output referenced]

### UNCONFIRMED
- [functions/parts not yet understood, marked as such]

### NEXT STEP
- [trace the crypto / confirm the branch / move to dynamic]
```

## Anti-delirium

- Never say a function "does X" without the instructions that show it.
- `fcn.xxxx` is not `decrypt_data` until you traced the bytes.
- If the decompiler output is wrong or partial, say so and fall back to disassembly.
- Every address in your output was read, not recalled.

---
name: re-binary-analysis
description: "Reverse engineering binary analysis: identify file format, architecture, sections, imports, exports, strings, packing. Use when analyzing an ELF, PE, Mach-O, or firmware binary first time."
---

# Binary Analysis

The first step of any reverse engineering task. Identify what the binary is before
touching logic. Precise identification drives every later decision.

## 1. Identify the file (always first)

```bash
file <binary>                 # format, architecture, endianness, stripped?
strings -n 6 <binary> | head  # readable strings, hints
xxd <binary> | head -3        # magic bytes
```

Key signals:
- **ELF** (Linux): `\x7fELF`, 32/64-bit, x86/ARM/RISC-V
- **PE** (Windows): `MZ` + `PE\0\0`, subsystem, DLL imports
- **Mach-O** (macOS/iOS): `\xfe\xed\xfa`, LC_LOAD commands
- **Firmware**: custom magic, often compressed/encrypted (see re-firmware-analysis)

## 2. Sections and symbols

```bash
# ELF
readelf -h -S -l <binary>     # headers, sections, program headers
readelf -s <binary> | head    # symbols (if not stripped)
objdump -T <binary>           # dynamic symbols

# General (radare2)
r2 -A <binary>                # analyze
r2 -qc "iI; iS; is~FUNC" <binary>  # info, sections, functions
```

- **Stripped vs unstripped**: `file` says "stripped" or symbol table present. Unstripped
  gives you function names free. Stripped means you reconstruct them.
- **Packed/obfuscated**: high entropy (see step 3), few symbols, sections like `.UPX`.

## 3. Entropy and packing detection

```bash
# entropy per section (radare2)
r2 -qc "iS~.text; iS~.data; iS~UPX" <binary>
```

| Signal | Meaning |
|--------|---------|
| All sections ~8.0 entropy | packed or encrypted |
| `.UPX` / "UPX!" string | UPX packed |
| Tiny .text, huge .data | data hidden in .data |
| Few exports + no imports | obfuscated |

If packed, unpack first (see re-decompilation: unpacking).

## 4. Imports and exports

```bash
objdump -T <binary> | head -30    # what it calls (imports)
objdump -p <binary> | grep -A20 "DLL Name"  # PE DLLs
r2 -qc "ii" <binary>              # imports
```

Imports reveal behavior before you read code: `crypto`, `socket`, `WriteFile`,
`fork`, `exec` are strong hints.

## 5. Strings as intelligence

```bash
strings -n 8 <binary> | grep -iE "http|https|key|secret|password|token|/bin/|flag|config"
```

- URLs → endpoints, C2, update servers
- `key`/`secret` → hardcoded credentials (a finding)
- `/bin/sh`, `exec` → command execution
- Error messages → logic hints, format strings

## 6. Environment

Record: arch, OS, endianness, compiler (via `file` + section names like `.comment`),
linker version. This matters for every later phase.

## Output contract (before deeper phases)

```
### BINARY PROFILE
- format / arch / endian / bits: [ELF 64-bit x86-64, little]
- compiler / stripped: [GCC, stripped]
- packed: [no] | [UPX] | [high-entropy .text]
- imports of interest: [crypto, socket]
- strings of interest: [url, key paths]
- entry point: [0x401000]

### NEXT STEP
- [decompile / trace crypto / unpack / dynamic]
```

## Anti-delirium

- Every claim about format/arch/imports comes from a command you ran. `file` output is
  evidence; "it looks like" is not.
- If a section is high-entropy, say "high entropy, possibly packed", never "it's
  encrypted" without entropy measurement.
- No invention: every address and symbol must come from tool output.

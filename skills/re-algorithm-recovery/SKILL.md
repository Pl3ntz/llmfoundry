---
name: re-algorithm-recovery
description: Reverse engineering algorithm recovery, detect and reconstruct crypto, checksums, serial validation, and custom algorithms from binary logic with proof. Use after decompilation when a function computes something important.
---

# Algorithm Recovery

Reconstruct what a function computes: crypto, checksums, serial keys, license
validation, custom encodings. This is where precision matters most, because getting it
wrong means reproducing a false algorithm.

## 1. Recognize known crypto/checksums

Signatures in disassembly:

| Algorithm | Tell |
|-----------|------|
| AES | S-box in .rodata (256 bytes), 10/12/14 rounds, `aesenc`/`aeskeygenassist` |
| SHA-1/2 | constants 0x67452301, 0xEFCDAB89 (SHA-1); 0x428a2f98 (SHA-256) |
| MD5 | constants 0x67452301, 0x98badcfe, rotations |
| CRC | table in .rodata (256x4), or bitwise loop |
| Base64 | alphabet table `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef...` |
| RSA | big number constants, exponentiation (modpow) |
| XTEA/TEA | delta 0x9E3779B9 |
| RC4 | KSA loop, 256-byte S-box swap |

```bash
# find the tables
r2 -qc "/x 67452301" <binary>   # sha1 init
r2 -qc "/x 9e3779b9" <binary>   # tea delta
strings -n 8 <binary> | grep -i "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
```

A constant match is strong evidence. Cross-check it actually gets used (xrefs), not just
present as data.

## 2. Trace the data flow

Follow the input through the function:
1. Input → transformations → output. Where does each transformation happen?
2. Is there a key? Where does it come from (hardcoded, argument, file)?
3. What is the output compared against (a known hash, a serial)?

```bash
# xrefs to a function/constant
r2 -qc "axt @ <addr>" <binary>
# or in Ghidra: right-click → References
```

## 3. Reconstruct the algorithm step by step

For each stage, map to a precise description:
- Initialization (constants, tables)
- Per-block/per-byte loop (the core)
- Finalization (padding, digest)
- Comparison (what the result is checked against)

Produce a **reference implementation** in the target language, derived instruction by
instruction, not from memory of "how AES works". If it matches known crypto, name it and
confirm params (mode, key size, IV). If it is custom, describe it so it can be reimplemented.

## 4. Verify against the binary (the precision gate)

- Your reconstruction must produce the same output as the binary for the same input.
- If you have a known input/output pair (e.g. a valid serial), run your implementation
  and check it matches.
- Dynamic confirmation (re-dynamic-analysis) is the strongest proof: hook the function,
  feed input, compare.

## Output contract

```
### ALGORITHM
- type: [AES-256-CBC | custom | CRC32 | ...]
- evidence: [constant/table found at addr, xrefs, decompiled excerpt]
- params: [key size, mode, IV, rounds, table]
- reconstruction: [reference implementation or exact description]

### VERIFICATION
- [known pair reproduced? dynamic hook result? or UNVERIFIED + what would confirm]

### NEXT STEP
- [feed to dynamic analysis for confirmation]
```

## Anti-delirium

- A constant in .rodata is evidence only if xrefs show it is used. "It's probably AES"
  is not an algorithm.
- If you name AES, show the S-box/rounds/params you found. If you cannot confirm params,
  say "AES-like, params unconfirmed".
- Custom algorithms get a precise description, never "it's some kind of hash".
- Reproduction is the proof. Unreproduced = UNVERIFIED.

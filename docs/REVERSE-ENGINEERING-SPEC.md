# Reverse Engineering Specialist: SPEC

**Status:** Implemented
**Author:** vplentz
**Date:** 2026-08-01
**Complexity:** Complex

---

## What

A **reverse engineering specialist agent** in LLMFoundry, with dedicated skills, focused
on **maximum precision** for binary analysis (ELF/PE/Mach-O), logic extraction, algorithm
recovery, and vulnerability identification.

## Why

The user works in security and has an Android/APK pipeline. What was missing is a general
binary specialist for firmware, executables, malware, and libraries, at a professional
level of precision (the way the deep-researcher is for research).

## Scope: Skills

| # | Skill | Description |
|---|-------|-----------|
| 1 | `re-binary-analysis` | Identify format (ELF/PE/Mach-O), architecture, sections, imports/exports, strings, entropy, packing detection |
| 2 | `re-decompilation` | radare2/Ghidra workflow: analysis, disassembly, decompilation, renaming, types, xrefs |
| 3 | `re-algorithm-recovery` | Recover logic: crypto (detect AES/RSA/hash), checksums, serial/custom algorithms, deobfuscation |
| 4 | `re-dynamic-analysis` | Controlled execution: gdb/radare2 debug, tracing (strace/ltrace), Frida hooking, sandbox |
| 5 | `re-malware-analysis` | Malware triage: YARA, behavior, IOC extraction, safe detonation, anti-analysis bypass |
| 6 | `re-firmware-analysis` | Firmware extraction, filesystem (binwalk), kernel modules, U-Boot, updater logic |

## Scope: Agent

`agents/reverse-engineer.md` (subagent)

```
description: Reverse engineering specialist, binary analysis, decompilation,
  algorithm recovery, dynamic analysis, malware/firmware triage with maximum precision.
model: opencode-go/deepseek-v4-pro
mode: subagent
```

**Method (precision first):**
1. **INTAKE**, identify format/architecture before any analysis
2. **STATIC**, sections, symbols, strings, imports → function hypothesis
3. **DECOMPILE**, decompile with r2/Ghidra, rename, reconstruct logic
4. **DYNAMIC** (optional), confirm behavior under controlled execution
5. **SYNTHESIZE**, report: mapped functions, recovered algorithms, vulns, confidence

**Output contract:**
```
### FINDINGS (ordered by severity)
- [severity] [description] at [address/symbol], evidence: [hexdump/decompiled excerpt]

### RECOVERED LOGIC
- [recovered algorithm/function with explanation]

### VULNERABILITIES (if any)
- [type + address + impact]

### UNVERIFIED
- [what could not be confirmed, never invented]

### NEXT STEP
```

## Tool dependencies

| Tool | Status | Needed for |
|-----------|--------|-----------------|
| radare2 (`r2`) | installed | static + dynamic analysis |
| objdump/strings/file/nm | installed | initial analysis |
| Ghidra | install | precision decompilation |
| readelf | install (binutils) | detailed ELF headers |
| gdb / lldb | install | debugging |
| capstone + pyelftools + r2pipe | pip install | programmatic analysis |
| binwalk | install | firmware |

> Skills degrade gracefully when a tool is missing (like deep-researcher without
> fastembed): radare2 is enough for the core, Ghidra is a precision upgrade.

## Out of scope

- Do not duplicate the APK/Android pipeline, cross-reference it instead
- No offensive reverse engineering of third-party products without authorization (ethics)
- No evasion techniques meant to avoid detection on other people's systems

## Success criteria

1. `re-binary-analysis` identifies format/architecture accurately on real binaries
2. `re-decompilation` produces verifiable recovered logic (address + evidence)
3. `re-algorithm-recovery` detects real crypto/checksum (not "looks like AES")
4. `re-dynamic-analysis` confirms behavior under controlled execution
5. Output never invents an address/symbol, everything points to evidence
6. Degrades gracefully with only radare2 available
7. Eval harness with one golden test binary

## Kit integration

| Component | Role |
|-----------|-------|
| `agents/reverse-engineer.md` | RE specialist (subagent) |
| `skills/re-*` (6) | methodologies |
| `commands/ai-re.md` | `/ai-re <file>`, binary analysis |
| `evals/reverse-engineer/` | golden binary + rubric |
| Orchestrator | routes "analyze this binary/firmware" → reverse-engineer |
| Memory | RE findings feed the loop (analysis gotchas) |

---

## Implementation plan

1. Install tools: Ghidra, readelf (binutils), gdb, binwalk; pip: capstone, pyelftools, r2pipe
2. Create the 6 `re-*` skills
3. Create `agents/reverse-engineer.md` + `commands/ai-re.md`
4. Register in the orchestrator (routing table) + SKILLS.md
5. Eval: compile a golden test binary with known crypto+logic → validate precision
6. Commit + push

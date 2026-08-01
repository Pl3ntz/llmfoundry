---
description: Reverse engineer a binary, firmware, or sample with maximum precision
model: opencode-go/deepseek-v4-pro
agent: reverse-engineer
---

Reverse engineering analysis using the re-* skills.

**Target:** {{argument}}

Run the 5-phase method: INTAKE → STATIC → DECOMPILE → RECOVER ALGORITHMS → DYNAMIC (sandbox).

1. Identify format/arch/stripped/packed first (re-binary-analysis)
2. Recover logic with radare2/Ghidra (re-decompilation)
3. Reconstruct algorithms with proof (re-algorithm-recovery)
4. Confirm dynamically in a sandbox (re-dynamic-analysis / re-malware-analysis)
5. Output the contract: FINDINGS, BINARY PROFILE, RECOVERED LOGIC, VULNERABILITIES, UNVERIFIED, NEXT STEP

Precision rules: every claim has address + evidence. Never guess code from a name.
Sandbox untrusted samples. UNVERIFIED stated honestly.

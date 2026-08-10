---
name: re-dynamic-analysis
description: "Reverse engineering dynamic analysis: run the binary under control, trace execution, breakpoints, hook functions with a debugger or Frida. Use to confirm static findings or observe runtime behavior."
---

# Dynamic Analysis

Confirm and observe behavior by running the binary under control. Dynamic analysis
proves what static analysis suggests. It is the strongest evidence in reverse engineering.

## Safety first

- **Run in a sandbox/VM** if the binary is untrusted (malware, unknown source). Never
  execute unknown binaries on your main machine without isolation.
- Prefer `--headless`, containers, or throwaway VMs. See re-malware-analysis.
- Only run what you need to observe. No unnecessary execution.

## Debugger (gdb/lldb)

```bash
# start with args, break on a function, step
gdb -q ./binary
(gdb) break <addr_or_func>
(gdb) run <args>
(gdb) x/20i $pc          # disassemble at instruction pointer
(gdb) info registers
(gdb) bt                 # backtrace
(gdb) continue
```

- Break at the entry, at imports you care about, at the comparison instructions found
  statically.
- Inspect arguments and return values at each point.
- Confirm an algorithm by observing its inputs/outputs.

## radare2 dynamic

```bash
r2 -d ./binary            # debug mode
r2 -qc "db <addr>; dc; dr; pd 10" -d ./binary
```

## Frida (hooking, when available)

```js
// hook a function, log args and return
Interceptor.attach(Module.findExportByName(null, "strcmp"), {
  onEnter(args) { console.log("strcmp:", args[0].readCString(), args[1].readCString()); },
  onLeave(retval) { console.log("→", retval.toInt32()); }
});
```

```bash
frida -n <process> -l hook.js
```

Frida is ideal for confirming crypto (capture plaintext/key/ciphertext) and serial
checks (observe the comparison) without running blind.

## Observation patterns

| What you want | Technique |
|---------------|-----------|
| Function args/return | breakpoint + registers |
| Algorithm input/output | hook the function, capture args + ret |
| Is a branch taken | break at both branch targets |
| Hardcoded data used? | break on xref, inspect |
| Anti-debug/anti-VM | observe `ptrace`, `rdtsc`, timing (see re-malware-analysis) |
| Packed code | dump memory after unpacking |

## Confirm static findings

Take each static claim (this function does X) and confirm dynamically:
- Set breakpoint, run, observe.
- If it does what static said, the finding is VERIFIED.
- If not, the static analysis was wrong, fix it and note the correction.

## Output contract

```
### DYNAMIC CONFIRMATION
- observation: [what you ran, what you observed, with register/memory/return evidence]
- confirms/contradicts: [which static finding]
- verdict: [VERIFIED | CONTRADICTED | PARTIAL]

### NEXT STEP
- [further observation or conclusion]
```

## Anti-delirium

- Every observation is what you actually saw (registers, memory, output), not what you
  expected.
- "The function returned 1" requires the observed return value, not an assumption.
- If the binary crashed or refused to run, report that, don't infer behavior.
- Sandbox every untrusted binary; never run blind on the host.

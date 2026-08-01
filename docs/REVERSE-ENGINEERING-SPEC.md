# Reverse Engineering Specialist: SPEC

**Status:** Rascunho para implementação futura
**Autor:** vplentz
**Data:** 2026-08-01
**Complexidade:** Complexo
**Fase:** Após concluir os itens atuais do roadmap (gates, routing eval, baselines, CI)

---

## O que

Criar um **agente especialista em engenharia reversa** no LLMFoundry, com skills dedicadas,
focado em **máxima precisão** de análise de binários (ELF/PE/Mach-O), extração de lógica,
recuperação de algoritmos e identificação de vulnerabilidades.

## Por que

O usuário trabalha com security e tem o `apk-redteam-pipeline` (Android/APK apenas). Falta
um especialista para **análise de binários em geral**, firmware, executáveis, malware,
libraries, com precisão de nível profissional (como o deep-researcher é para pesquisa).

## Escopo: Skills

| # | Skill | Descrição |
|---|-------|-----------|
| 1 | `re-binary-analysis` | Identificar formato (ELF/PE/Mach-O), arquitetura, sections, imports/exports, strings, entropia, packing detection |
| 2 | `re-decompilation` | Uso de radare2/Ghidra: analysis, disassembly, decompilation, renaming, tipos, xrefs |
| 3 | `re-algorithm-recovery` | Recuperar lógica: crypto (detectar AES/RSA/hash), checksums, serial/algoritmos custom, deobfuscation |
| 4 | `re-dynamic-analysis` | Execução controlada: gdb/radare2 debug, tracing (strace/ltrace), Frida hooking, sandbox |
| 5 | `re-malware-analysis` | Triage de malware: YARA, comportamento, IOC extraction, detonation segura, anti-analysis bypass |
| 6 | `re-firmware-analysis` | Extração de firmware, filesystem (binwalk), kernel modules, U-Boot, updater logic |

## Escopo: Agente

`agents/reverse-engineer.md` (subagent)

```
description: Reverse engineering specialist, binary analysis, decompilation,
  algorithm recovery, dynamic analysis, malware/firmware triage with maximum precision.
model: opencode-go/deepseek-v4-pro
mode: subagent
```

**Método (precisão primeiro):**
1. **INTAKE**, identificar formato/arquitetura antes de qualquer análise
2. **STATIC**, sections, symbols, strings, imports → hipótese de função
3. **DECOMPILE**, descompilar com r2/Ghidra, renomear, reconstruir lógica
4. **DYNAMIC** (opcional), confirmar comportamento sob execução controlada
5. **SYNTHESIZE**, relatório: funções mapeadas, algoritmos recuperados, vulns, confidence

**Output contract:**
```
### FINDINGS (ordenado por severidade)
- [severity] [descrição], endereço/símbolo, [evidência, ex. hexdump/decompiled excerpt]

### RECOVERED LOGIC
- [algoritmo/função recuperada com explicação]

### VULNERABILITIES (se aplicável)
- [tipo + endereço + impacto]

### UNVERIFIED
- [o que não pôde ser confirmado, nunca inventar]

### NEXT STEP
```

## Dependências de ferramentas

| Ferramenta | Estado | Necessário para |
|-----------|--------|-----------------|
| radare2 (`r2`) | ✅ instalado | static + dynamic analysis |
| objdump/strings/file/nm | ✅ instalado | análise inicial |
| Ghidra | ❌ instalar | decompilação de precisão |
| readelf | ❌ instalar (binutils) | ELF headers detalhados |
| gdb / lldb | ❌ instalar | debugging |
| capstone + pyelftools + r2pipe | ❌ pip | análise programática |
| binwalk | ❌ instalar | firmware |

> Skills devem degradar graciosamente quando uma ferramenta falta (como o deep-researcher
> degrada sem fastembed): radare2 é suficiente para o núcleo; Ghidra é upgrade de precisão.

## Fora de escopo

- Não duplicar `apk-redteam-pipeline` (Android/APK), cross-ref a ele
- Não fazer engenharia reversa ofensiva de produtos de terceiros sem autorização (ética)
- Não incluir técnicas de evasão para evitar detecção em sistemas alheios

## Critérios de sucesso

1. `re-binary-analysis` identifica formato/arquitetura com precisão em binários reais
2. `re-decompilation` produz lógica recuperada verificável (address + evidence)
3. `re-algorithm-recovery` detecta crypto/checksum real (não "parece AES")
4. `re-dynamic-analysis` confirma comportamento sob execução controlada
5. Output nunca inventa endereço/símbolo, tudo aponta para evidência
6. Degrada graciosamente com apenas radare2 disponível
7. Eval harness com 1 binário golden de teste

## Integração com o kit

| Componente | Papel |
|-----------|-------|
| `agents/reverse-engineer.md` | Especialista RE (subagent) |
| `skills/re-*` (6) | Metodologias |
| `commands/ai-re.md` | `/ai-re <arquivo>`, análise de binário |
| `evals/reverse-engineer/` | golden binário + rubric |
| Orquestrador | Roteia "analisa esse binário/firmware" → reverse-engineer |
| Memória | Findings de RE alimentam o loop (gotchas de análise) |

---

## Plano de implementação

1. Instalar ferramentas: Ghidra, readelf (binutils), gdb, binwalk; pip: capstone, pyelftools, r2pipe
2. Criar as 6 skills `re-*`
3. Criar `agents/reverse-engineer.md` + `commands/ai-re.md`
4. Registrar no orquestrador (routing table) + SKILLS.md
5. Eval: compilar um binário golden de teste com crypto+logic conhecida → validar precisão
6. Commit + push

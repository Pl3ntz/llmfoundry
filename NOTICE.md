# Third-Party Notices

LLMFoundry bundles or depends on third-party components under their original licenses.

## Runtime dependencies

| Component | License | Purpose |
|-----------|---------|---------|
| [fastembed](https://github.com/qdrant/fastembed) | Apache 2.0 | Local semantic embeddings (ONNX) |
| [numpy](https://numpy.org) | BSD-3-Clause | Vector math for semantic search |

## Design references (no code vendored)

| Project | Relation |
|---------|----------|
| [Quarterdeck](https://github.com/Pl3ntz/quarterdeck) | Author's prior Claude Code orchestration kit. Patterns reused: evidence discipline, output discipline, routing table, gates philosophy, deep-researcher protocol. Reimplemented for opencode + DeepSeek, not copied verbatim. |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | Design patterns for skill anatomy (verification gates, anti-rationalization). Conceptual inspiration only. |

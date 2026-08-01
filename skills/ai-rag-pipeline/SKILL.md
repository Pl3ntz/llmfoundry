---
name: ai-rag-pipeline
description: Build and evaluate RAG systems — embedding, chunking, retrieval, reranking, and RAG evaluation. Use when designing retrieval-augmented generation for LLM apps.
---

# AI RAG Pipeline

Design, build, and evaluate retrieval-augmented generation.

## Pipeline

```
DOCS → chunk → embed → index → query → retrieve → rerank → prompt → generate → evaluate
```

## Chunking

- Chunk by semantic boundaries (paragraphs, sections, markdown headers), not fixed byte counts.
- Keep context: chunk + metadata (source, section, date). Overlap or parent-child for recall.
- Chunk size tracks the retrieval unit, not the model input. Smaller chunks retrieve
  better, more context around them helps the answer.
- Preserve structure (headers, tables, lists) so the model can navigate.

## Embeddings

- Choose a model matching content language and type.
- Store vectors in a vector DB or index with the metadata payload.
- Normalize + batch for cost. Cache embeddings.

## Retrieval

- Hybrid beats pure vector: vector (semantic) + keyword/BM25 (exact terms) fused.
- Query transformation: rewrite, expand, sub-query decomposition for hard questions.
- Metadata filters: date, source, type. Reject out-of-scope chunks early.
- Top-K by task: K=3-5 for factual, more for synthesis.

## Reranking

- Retrieve 20-50 candidates, rerank to top 3-10 with a cross-encoder.
- Rerank on relevance to the QUESTION, not the query string.

## Grounding (the part that matters)

- The generated answer must be traceable to retrieved chunks. No answer from parametric memory.
- Provide citations: `[source:file:section]` per claim.
- Hallucination guard: if no chunk supports the answer, say "not in the provided material".

## RAG evaluation

| Dimension | Metric |
|-----------|--------|
| Retrieval recall | fraction of relevant chunks retrieved |
| Retrieval precision | fraction of retrieved chunks that are relevant |
| Faithfulness | fraction of claims supported by chunks |
| Answer relevance | does the answer address the question |

Evaluate with a golden set of {question, expected_chunks, expected_answer}. Run regressions
on every chunking/embedding/retrieval change.

## Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| Vector-only retrieval | Hybrid with BM25 |
| Fixed byte chunks | Semantic boundaries + metadata |
| Answer from memory | Ground in chunks, cite |
| No evaluation | Golden set + faithfulness metric |
| No metadata filter | Filter by date/source/type |

## Verification

- Faithfulness ≥ threshold on the golden set (no unsupported claims)
- Retrieved chunks actually relevant (precision/recall measured)
- Citations resolve to real chunks
- Empty/edge queries degrade gracefully, don't hallucinate

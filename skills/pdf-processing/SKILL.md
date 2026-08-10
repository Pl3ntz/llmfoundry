---
name: pdf-processing
description: "Process PDFs fast and locally with pdf-inspector, no OCR service needed. Use when extracting text, tables, or Markdown from PDFs, or for scanned documents."
---

# PDF Processing

Extract text, tables, and Markdown from PDFs locally and fast, using `pdf-inspector`
(firecrawl, MIT, free). No OCR service, no API cost.

## Why pdf-inspector

Best-in-class on the opendataloader benchmark (200 PDFs):

| Engine | Overall | Speed (200 docs) |
|--------|---------|------------------|
| **pdf-inspector** | **0.875** | **0.470s** |
| pymupdf4llm | 0.735 | 17.1s |
| markitdown | 0.589 | 16.1s |

Local, <200ms per PDF, detects scanned vs text-based, converts to clean Markdown with
tables and headings.

## Install (once)

```bash
# Python binding (recommended)
pip install pdf-inspector

# or Node
npm install @firecrawl/pdf-inspector
```

## Usage

### Python

```python
from pdf_inspector import process_pdf, classify_pdf

# Classify first: is it text-based or scanned?
kind = classify_pdf("document.pdf")  # TextBased | Scanned | ImageBased | Mixed

# Extract to Markdown (text-based PDFs, no OCR)
result = process_pdf("document.pdf", pages="1-10")
print(result["markdown"])  # clean markdown with headings, tables, code blocks
```

### CLI

```bash
pdf-inspector classify document.pdf
pdf-inspector extract document.pdf -o output.md
```

## Workflow for documents

1. **Classify** the PDF first. If Scanned/ImageBased, pdf-inspector still extracts what it
   can but flag the OCR-required pages for the user.
2. **Extract to Markdown** for text-based PDFs. Fast, accurate, local.
3. **Use the Markdown** as context for the agent (docs, CVs, contracts, reports).

## Anti-delirium

- Never claim a PDF is text-based without running the classifier.
- If a PDF is scanned/image-based, say so and note which pages need OCR. Do not pretend
  the extraction is complete.
- Every extraction claim is what the tool actually returned, not what you assume.

## Output contract

```
### PDF PROFILE
- file / pages / classification: [TextBased|Scanned|ImageBased|Mixed, with confidence]

### EXTRACTED
- [Markdown or the key sections, with page references]

### OCR NEEDED (if any)
- [which pages are scanned and need OCR]

### NEXT STEP
- [1 sentence]
```

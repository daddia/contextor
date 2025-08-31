---
title: Contextor — Design Principles
description: Principles and architectural guardrails for Contextor
version: 1.0.0
last_reviewed: 2025-08-31
phases:
  - Phase 1: directory → .mdc (repo-based docs only)
  - Phase 2: add MCP server (read-only over sourcedocs/{source-slug})
  - Phase 3: optional polite scraping for non-repo docs
---

# Design Principles for Contextor

These principles guide the design and development of **Contextor**, adapting the earlier, broader scraper principles to our new **directory-first** scope while keeping MCP as the primary contract. :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1}

1. **Directory-First Ingestion**: Phase 1 processes existing Markdown/MDX trees checked out from public repos—no network calls during optimisation. This maximises reliability and reproducibility.

2. **MCP-First Output**: Emit **Model Context Protocol** files (`.mdc`) as the single, stable interchange format for downstream tools and agents.

3. **LLM-Optimised, Lossless-by-Default**: Normalise headings, code fences, tables and links; remove obvious boilerplate. Any compression (e.g., large code elision) is opt-in and clearly marked.

4. **Deterministic & Idempotent**: The same inputs must yield the same outputs. Only write when the `content_hash` changes to keep diffs clean and history meaningful.

5. **Strong Provenance**: Every `.mdc` includes repo, ref (branch/commit), source path and canonical URL so reviewers can trace claims back to their origins quickly.

6. **Config over Code**: Include/exclude globs, topic tags and per-source tweaks live in YAML. Routine coverage changes shouldn’t require code edits.

7. **Separation of Concerns**: **Contextor** writes to the separate **`sourcedocs/{source-slug}/`** repository; consumers (e.g., Promptman) read from there. Content creation and consumption remain decoupled.

8. **Popular Libraries, Minimal Fuss**: Prefer well-maintained libraries for parsing/formatting and manage them with Poetry. Keep dependencies focused and portable.

9. **Git-Native History**: Rely on Git for versioning of emitted context. Avoid external databases or bespoke state.

10. **Testable Transforms**: Implement MDX cleaning, Markdown normalisation, link hygiene and size control as small, unit-testable functions with clear interfaces.

11. **Cross-Platform & CI-Friendly**: Work consistently on Linux, macOS and Windows. Ensure CI runs are deterministic on GitHub runners.

12. **Security & Licensing**: Operate on local files only in Phase 1; never embed secrets. Preserve licence notices and attribution in front-matter.

13. **Performance Budgets**: Aim for fast end-to-end runs on typical docs trees; avoid quadratic passes and unnecessary reparsing.

14. **Observability by Design**: Maintain `{source-slug}/index.jsonl` and lightweight per-run metrics to aid debugging and auditing.

15. **Forward-Compatible Roadmap**: Phase 2 adds a read-only **MCP server** over `sourcedocs/{source-slug}/`. Phase 3 may add **polite scraping** for non-repo sources—using the same `.mdc` contract to keep the pipeline uniform.

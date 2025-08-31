# Leading Practices to writing Markdown for LLMs

## Goals

* **Clarity:** minimise ambiguity; prefer explicit over clever.
* **Chunkability:** clean section boundaries so retrievers can split safely.
* **Determinism:** stable wording, IDs, and metadata for consistent answers.
* **Token efficiency:** dense facts, little fluff.

## Structure & Metadata

* Start with **YAML front-matter**:

  * `title`, `version`, `updated` (ISO 8601), `owner`, `status`, `tags`, `canonical_id`, `source_url`.
* Use **ATX headings** (`#`…`####`), never setext. One `# H1` per file.
* Put a **Summary** (3–6 bullets) at the top with the key answers/figures.
* Keep each **H2/H3 section self-contained** (200–500 tokens ideal).
* Add a **Glossary** and **Assumptions & Constraints** section if terms are loaded.

## Writing style

* Short paragraphs (≤4 lines), **bulleted lists** for facts, numbered lists for procedures.
* **One concept per section**; avoid cross-referencing with pronouns (“it”, “they”).
* Use **consistent terminology**; include an “Also known as / synonyms” line once.
* Prefer **ISO formats** (dates `YYYY-MM-DD`, times `HH:MMZ`, units with SI symbols).
* Mark voice clearly: “**Do**”, “**Don’t**”, “**Must**”, “**Should**”.

## Formatting

* Avoid inline HTML, footnotes, multi-column layouts, and decorative ASCII.
* Use **plain characters** (straight quotes), UTF-8; avoid soft hyphens/nbsp.
* Keep **tables** small and simple; for anything complex, use lists.
* Use **inline code** for literal identifiers (`ClassName`, `ENV_VAR`) and **fenced code** with language hints for blocks.

## Code & data blocks

* Fenced blocks must be **valid and runnable** (no `...` placeholders).
* Prefer **JSON/YAML** for schemas/config; one top-level object/array; small examples.
* Provide **I/O examples** (inputs, outputs) and at least one **negative example**.
* Label special blocks with custom info strings the tooling can spot:

  * `instruction, `policy, `facts, `prompt, \`\`\`qna (common patterns many pipelines key on).

## Linking & references

* Use **descriptive link text**; include a **stable ID** nearby if the target might move.
* For external sources, add a **“Sources”** section with `title — publisher — date`.
* Where relevant, embed **document IDs** or ticket keys in text (`[ID: ARCH-123]`) for deterministic mapping.

## Chunking & retrieval

* Keep sections **semantic and atomic**; avoid ping-ponging between topics.
* Put **keywords and synonyms in the section body once** (don’t keyword-stuff).
* Duplicate **critical definitions once** across related docs via a **canonical glossary** file and link to it.

## Versioning & governance

* Include a **Change log** (date, summary, author). Avoid repeating the full doc in history.
* Add a **Status** badge in front-matter: `draft | review | approved | deprecated`.
* Prefer **stable filenames** and a `canonical_id` that never changes across versions.

## Anti-patterns (avoid)

* Giant unbroken walls of text; mixed topics in one section.
* Screenshots without alt-text; images instead of text tables.
* “Smart” formatting (footnotes, collapsible sections) that may be stripped.
* Ambiguous placeholders (`TBD`, `???`); use explicit markers like `[REDACTED]` or `{{PLACEHOLDER}}`.

---

## Minimal LLM-friendly Markdown template

```md
---
title: "<Document Title>"
canonical_id: "DOC-001"
version: "1.3.0"
updated: "2025-08-31"
owner: "Team Name"
status: "approved"
tags: ["architecture", "api", "security"]
source_url: "https://example.com/docs/doc-001"
---

# <Document Title>

## Summary
- Purpose:
- Scope:
- Key decisions:
- Out of scope:
- Risks:

## Assumptions & Constraints
- Assumptions:
- Constraints:

## Definitions (see also: /glossary)
- Term — definition.
- Synonyms — …

## Procedure
1. Step…
2. Step…

## Examples
### Input
```json
{ "customer_id": "C123", "country": "AU" }
```

### Output

```json
{ "eligible": true, "limit": 2500 }
```

### Negative example

```json
{ "customer_id": "", "country": "??" }
```

## Policies

```policy
Must: PII is never logged.
Should: Use ISO country codes.
```

## Q\&A

```qna
Q: What happens on failure?
A: We return HTTP 429 with `retry_after` seconds.
```

## Change log

* 2025-08-31 — v1.3.0 — Clarified rate limits. (JD)

```


## Extra tips for prompts in Markdown

- Put **normative instructions** in a fenced `instruction` block at top.
- Separate **facts/context** from **tasks** (`facts` vs `task` sections).
- Keep **evaluation criteria** explicit: success conditions, constraints, forbidden actions.

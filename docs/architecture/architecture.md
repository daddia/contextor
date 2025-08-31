---
title: Contextor — Architecture Overview
description: System architecture for Contextor (directory → .mdc with MCP server)
version: 1.0.0
last_reviewed: 2025-08-31
---

# Architecture Overview

## Introduction
This document describes the architecture of **Contextor**, a lightweight tool that converts Markdown/MDX documentation trees from public repositories into **Model Context Protocol** (`.mdc`) files optimised for LLMs, stores them in a separate repository called **`sourcedocs`**, and (Phase 2) serves them via a read-only MCP server.

The goals are **determinism**, **simplicity**, and **GitHub-native operations**: same inputs produce the same outputs; no database; CI-friendly; and clear provenance for every emitted file. This overview follows the project’s standard architecture template. :contentReference[oaicite:0]{index=0}

## System Overview
- **High-Level Diagram**

```mermaid
flowchart LR
  subgraph Source Repos (read-only)
    A1[Repo A<br/>docs/]:::src
    A2[Repo B<br/>docs/]:::src
  end

  subgraph Contextor (Phase 1)
    B1[Loader<br/>discover files] --> B2[Transforms<br/>MDX clean / markdown normalise / link hygiene / size control]
    B2 --> B3[Emitter<br/>.mdc + index.jsonl + hashing]
  end

  subgraph sourcedocs repo (output)
    C1[{source-slug}/<source>/pages/*.mdc]:::out
    C2[{source-slug}/index.jsonl]:::out
  end

  subgraph MCP Server (Phase 2)
    D1[Read-only API<br/>(list, get, search, stats)]
  end

  A1 --> B1
  A2 --> B1
  B3 --> C1
  B3 --> C2
  C1 --> D1
  C2 --> D1

  classDef src fill:#eef,stroke:#88a;
  classDef out fill:#efe,stroke:#6a6;
````

* **Summary**
  Contextor runs as a CLI (Poetry script) that points at a **local checkout** of upstream docs. It performs a **pure filesystem pipeline** (no network in Phase 1): discover files → apply content transforms → emit `.mdc` + `index.jsonl` into **`sourcedocs/{source-slug}/`**. Phase 2 adds a small Python MCP server that exposes read-only endpoints over this directory. Phase 3 (optional) adds a plugin to collect docs from sites without public repos, reusing the same emitter.

## Components and Responsibilities

* **CLI (`contextor optimize`)**

  * Orchestrates a single run; accepts `--src`, `--out`, `--repo`, `--ref`, `--topics`, `--profile (lossless|balanced|compact)`.

* **Loader (`loader.py`)**

  * Walks `--src`, applies include/exclude globs, collects **provenance** (repo/ref/path), and yields file units (`.md`, `.mdx`).

* **Transforms (`transforms/*`)**

  * **mdx\_clean**: strip `import`/`export` blocks; unwrap common JSX wrappers; keep content semantics.
  * **markdown\_norm**: normalise headings, tables, code fences, spacing via `mdformat` (+GFM).
  * **links**: remove boilerplate (“edit this page”), fix relative links to canonical repo URLs where feasible.
  * **size** (opt-in): elide or summarise very large code/JSON blocks with clear markers.

* **Emitter (`emit.py`)**

  * Builds **front-matter**: `schema`, `source.repo/ref/path/url`, `title`, `topics`, `content_hash`, `fetched_at`, `slug`, `tags`, `license`.
  * Writes `.mdc` deterministically; appends a line to `{source-slug}/index.jsonl`; **writes only when hash changes**.

* **MCP Server (Phase 2, `mcp_server/*`)**

  * Read-only endpoints: `list{source-slug}`, `get_file`, `search`, `stats`.
  * Loads the index for quick enumeration and provides simple full-text/metadata search.

* **Optional Scraper Plugin (Phase 3)**

  * Polite fetching for non-repo sources; produces the same `.mdc` outputs via the emitter.

## Data Flow and Interactions

* **Data Flow Diagram**

```mermaid
sequenceDiagram
  participant Dev as Developer/CI
  participant Up as Upstream Repos (local checkout)
  participant CX as Contextor CLI
  participant SD as sourcedocs/{source-slug}
  participant SV as MCP Server (Phase 2)

  Dev->>CX: contextor optimize --src <path> --out <sourcedocs/{source-slug}> ...
  CX->>Up: Read files (.md / .mdx)
  CX->>CX: MDX clean → markdown normalise → link hygiene → size (opt)
  CX->>SD: Write *.mdc and update index.jsonl (if content_hash changed)
  Dev->>SD: git add/commit/push (sourcedocs)
  SV->>SD: Serve read-only (list/get/search/stats)
```

* **Interaction Patterns**

  * **In-process** function calls between loader, transforms, and emitter.
  * **File I/O** to `sourcedocs/{source-slug}`.
  * **HTTP (Phase 2)** for MCP server clients; server itself performs **no writes**.

## Technologies and Tools

* **Language/Framework:** Python 3.11; CLI via **Typer** (or argparse).
* **Parsing/Formatting:** `markdown-it-py`, **mdformat** (+`mdformat-gfm`), `python-frontmatter`.
* **YAML/Metadata:** `pyyaml` (or `ruamel.yaml`).
* **Search/Index (server):** simple JSONL index; optional `rapidfuzz`/`whoosh` for lightweight search.
* **Web (server):** FastAPI/Starlette + Uvicorn (SSE or simple HTTP endpoints).
* **Build/Deps:** **Poetry**; **Makefile** targets for `install`, `fmt`, `lint`, `optimize`, `serve`, `test`.
* **CI/CD:** GitHub Actions in `sourcedocs` to run optimise and commit outputs; optional container image for the server.

## Deployment Architecture

* **Deployment Diagram**

```mermaid
graph TD
  A[Developer / CI] -->|runs| B[contextor optimize]
  B -->|writes| C[sourcedocs/{source-slug}]
  C -->|git push| D[GitHub remote: sourcedocs]
  E[MCP Server] -->|reads| C
  E --> F[Agents / Clients]
```

* **Environment Considerations**

  * **Local dev:** Run optimise against a vendor checkout; inspect `.mdc`; commit to `sourcedocs`.
  * **CI (sourcedocs):** Scheduled or on-demand workflow that checks out upstream repos, runs optimise, and commits `{source-slug}/` changes.
  * **Server:** Containerised FastAPI/Uvicorn (read-only) mounted on `sourcedocs/{source-slug}`.

## Scalability and Performance Considerations

* **Scaling Strategies**

  * **O(N) traversal:** Process files sequentially or with bounded concurrency per directory tree.
  * **Idempotent writes:** Hash-gate to avoid unnecessary churn.
  * **Profiles:** `balanced`/`compact` to reduce tokens for large code-heavy trees.
  * **Server:** Stateless; scale horizontally behind a simple HTTP load balancer; cache hot responses.

* **Performance Metrics**

  * Files processed/written/skipped; wall-clock runtime; mean/95p transform time; errors by type; estimated token savings (if size pass enabled).

## Security Considerations

* **Authentication and Authorisation**

  * **Phase 1:** Local filesystem only (no secrets required).
  * **Phase 2 Server:** Optional bearer token or allow-list; CORS controls for known clients; rate limiting.

* **Data Protection**

  * `.mdc` includes provenance and licence attribution; no PII expected.
  * Server is **read-only**; no file uploads or writes.

* **Compliance**

  * Honour upstream licences; retain attribution and links; keep `.mdc` body faithful except when compression is explicitly enabled and marked.

## Future Enhancements and Roadmap

* **Planned Features**

  * Phase 2: MCP server endpoints (`list{source-slug}`, `get_file`, `search`, `stats`), container image, basic search.
  * Phase 3: Optional scraping plugin (sitemap + polite fetch + extraction) that reuses the emitter.

* **Technical Debt**

  * MDX edge cases across frameworks (e.g., custom JSX docs components).
  * Link rewriting coverage and canonical URL detection.
  * Search quality in the server (ranking, fuzzy match) if needed at scale.

---

*This document is a living document and will evolve with the system.*

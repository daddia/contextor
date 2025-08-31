---
title: Project Structure for `contextor`
description: Project organisation and folder structure (with MCP server)
version: 1.0.0
---

# Project Structure for `contextor`

This document outlines the project structure and organisation patterns used in `contextor`.

## Project Structure

```sh
contextor/
├─ config/
│  ├─ optimize.example.yaml        # Example rules: include/exclude globs, topics, output scope
│  └─ server.example.yaml          # Example MCP server config (root path, auth, ports)
│
├─ contextor/                      # Source code
│  ├─ __init__.py
│  ├─ __main__.py                  # CLI: `contextor optimize --src ... --out <sourcedocs/{source-slug}>`
│  ├─ loader.py                    # Discover files under --src, apply globs, resolve repo/ref metadata
│  ├─ emit.py                      # Write .mdc files + index.jsonl, slug & hashing
│  ├─ utils.py                     # Slugify, hashing, timing, small helpers
│  ├─ transforms/                  # Small, testable content passes
│  │  ├─ __init__.py
│  │  ├─ mdx_clean.py              # Strip MDX imports/exports; unwrap common JSX
│  │  ├─ markdown_norm.py          # mdformat (GFM), fence/table normalisation
│  │  ├─ links.py                  # Fix relative links; drop “edit this page” boilerplate
│  │  └─ size.py                   # (opt-in) elide huge blocks with markers for token savings
│  └─ mcp_server/                  # Phase 2: read-only MCP server (serves from sourcedocs/{source-slug})
│     ├─ __init__.py
│     ├─ __main__.py               # CLI: `contextor-server --root <sourcedocs/{source-slug}> --port 8080`
│     ├─ server.py                 # ASGI app (e.g., Starlette/FastAPI), SSE/Web endpoints
│     ├─ routes.py                 # list{source-slug}, get_file, search, stats
│     ├─ index.py                  # Manifest loading, simple full-text/metadata search
│     ├─ auth.py                   # Optional: token/allow-list middleware
│     └─ schema.py                 # Pydantic models for tool responses
│
├─ tests/
│  ├─ test_loader.py
│  ├─ test_transforms.py
│  ├─ test_emit.py
│  └─ mcp/
│     ├─ test_server.py
│     └─ fixtures/
│
├─ docs/
│  ├─ index.md                    # Docs index
│  ├─ getting-started.md
│  ├─ model-context-protocol/     # Leading practices for Model Context Protocol (MCP)
│  ├─ mcp-server/ 
│  └─ architecture/
│     ├─ decisions/               # ADRs (register.md)
│     ├─ architecture.md
│     ├─ principles.md
│     └─ structure.md
│
├─ scripts/
│  ├─ deploy.sh
│  └─ sync_sourcedocs.sh           # Optional helper: run optimise and commit to sourcedocs
│
├─ deploy/
│  ├─ Dockerfile.server            # Container image for MCP server
│  └─ compose.yaml                 # Local run of server (if handy)
│
├─ pyproject.toml                  # Poetry: deps, scripts (`contextor`, `contextor-server`)
├─ Makefile                        # install | fmt | lint | optimize | test | serve
├─ .github/workflows/
│  ├─ ci.yml                       # Lint, tests
│  └─ release.yml                  # (Optional) Build & publish package/container
└─ README.md
````

## Directory Descriptions

### `config/`

**Purpose:** Example configurations for both the optimiser and server.
**Contains:**

* `optimize.example.yaml` – per-source globs (include/exclude), topics, profile (`lossless|balanced|compact`).
* `server.example.yaml` – MCP server root (`sourcedocs/{source-slug}`), bind address/port, optional tokens, CORS.

### `contextor/` (source code)

**Purpose:** Main application code.
**Organisation:**

* **CLI & core:** `__main__.py`, `loader.py`, `emit.py`, `utils.py`.
* **Transforms:** Small, composable passes under `transforms/` for MDX cleaning, markdown normalisation, link hygiene, and size trimming.
* **MCP server:** `mcp_server/` provides a read-only API over `{source-slug}/` for agents/tools.

### `tests/`

**Purpose:** Unit tests for transforms, loader, emitter; server contract tests.
**Structure:** Mirrors module layout; fixtures for sample docs trees and MDC outputs.

### `docs/`

**Purpose:** Project documentation (getting started, principles, architecture, roadmap).
**Structure:** Simple markdown files consumable on GitHub; can later be published via MkDocs if needed.

### `scripts/`

**Purpose:** Optional automation helpers for local/dev usage (e.g., push to `sourcedocs`).
**Usage:** Not required in CI; CI should call Poetry scripts directly.

### `deploy/`

**Purpose:** Containerisation for the MCP server (Phase 2).
**Contents:** `Dockerfile.server`, optional `compose.yaml` for local runs.

---

## Conventions

### Naming Conventions

* **Directories:** `kebab-case` for top-level folders; Python packages follow module naming.
* **Files:** Python modules in `snake_case.py`; markdown `.md`/`.mdc` use `kebab-case`.
* **Slugs:** Deterministic: `<source>__<path-with-__-separators>` (query hashed if present).

### Organisation Principles

* **By feature:** Optimiser (Phase 1) and `mcp_server` (Phase 2) are first-class sub-areas inside one package.
* **Small, testable units:** Each transform is a pure function where possible.
* **Separation of concerns:** Emission targets **`sourcedocs/{source-slug}/`**; serving is read-only over that same path.

---

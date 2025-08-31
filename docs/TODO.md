# TODO - Contextor

*Last updated: 31 Aug 2025*  

---

## Conventions

- **Priority:** P1 (urgent/critical), P2 (high), P3 (normal), P4 (low)
- **Status:** Not started · In progress · Blocked · In review · Done
- **Estimates:** Story points
- **DoD (Definition of Done):** Tests updated · Docs updated · Review approved · Deployed/Released (as applicable)

---

## Current Sprint

### Sprint 2 — **`sourcedocs` Integration & CI** → Release v0.1.1

- [x] **Matrix GitHub Action in `sourcedocs`** (P1 · S · Status: Done)  
  Checkout upstream repos (e.g., Next.js, Tailwind) → run `contextor optimize` → commit `{source-slug}/` when changed.

- [x] **Run metrics artefact** (P3 · S · Status: Done)  
  Emit simple JSON (`processed`, `written`, `skipped`, `errors`) per run for observability.

- [x] **Samples & profiles** (P3 · S · Status: Done)  
  Provide sample `optimize.yaml` and recommended include/exclude rules for common projects.

---

## Current Sprint

### Sprint 3 — **MCP Server (Read-only)** → Release v0.2.0

- [ ] **`contextor-server` (Python, SSE)** (P1 · M · Status: Not started)  
  Serve from `sourcedocs/{source-slug}`; read-only by default.

- [ ] **Tools / endpoints** (P1 · S · Status: Not started)  
  `list{source-slug}(since?)`, `get_file(path|slug)`, `search(query, limit)`, `stats()`.

- [ ] **Packaging & runner** (P2 · S · Status: Not started)  
  Poetry script entrypoint; optional Dockerfile; health endpoint.

- [ ] **Tests & docs** (P2 · M · Status: Not started)  
  Contract tests for tool responses; quickstart guide.

---

## Backlog

### Sprint 4 — **Quality & Performance** → Release v0.2.1

- [ ] **Performance budget** (P2 · S · Status: Not started)  
  Bench directory sizes vs runtime; aim ≤10–15 min on GH runners for reference sets.

- [ ] **Logging & error handling** (P2 · S · Status: Not started)  
  Structured logs (json) with file path, duration, and outcome; graceful failures.

- [ ] **Pre-commit, lint, format** (P2 · S · Status: Not started)  
  `ruff` checks & `ruff format`; enforce in CI.

---

### Sprint 5 — **Advanced Content Intelligence** → Release v0.3.0

- [ ] **Advanced Topic** Automatic topic extraction 
  - [ ] **Topic Extraction**: from content using keywords, headings, and metadata.
  - [ ] **Topic tagging helpers**: Derive topics from path/headings; merge with provided `--topics`.
  - [ ] **Semantic analysis**: Extract key concepts, relationships between pages

- [ ] **Cross-linking**: Suggest “related pages” in front-matter.
  - [ ] **Duplicate detection**: Flag near-duplicate pages across sources.
  - [ ] **Content similarity**: Detect duplicate or highly similar content

- [ ] **Quality scoring**: Rate content quality, completeness, freshness

---

## Continuous Items (Track Throughout)

- [ ] **Performance**: Monitor and optimize resource usage; keep under target budgets.
- [ ] **Quality**: Maintain fast unit tests; expand cases for MDX and link rules.
- [ ] **Dependencies**: Keep Poetry lock updated; scan for vulnerabilities.
- [ ] **Security**: Security scanning; no secrets in files; license attribution preserved; read-only server.
- [ ] **Documentation**: Keep docs updated with new features and configuration options
- [ ] **Monitoring**: Record run metrics and failures; surface in PR comments if useful.
- [ ] **Compatibility**: Test against different Python versions, operating systems.
- [ ] **Community**: Respond to issues, review PRs, maintain examples.

---

## Future Enhancement Candidates

### Advanced Content & Extraction  
- [ ] **PDF extraction**: Extract content from linked PDF documents
- [ ] **Image OCR**: Extract text from images using OCR
- [ ] **Video transcription**: Extract transcripts from embedded videos
- [ ] **API content**: Fetch content from REST APIs, GraphQL endpoints
- [ ] **Multi-language support**: Handle international sites, language detection

### Workflow Integration
- [ ] **GitHub Actions**: Pre-built actions for CI/CD integration
- [ ] **Docker images**: Containerized deployment options
- [ ] **Kubernetes operators**: Manage contextor deployments in K8s
- [ ] **Webhook notifications**: Alert on content changes

### Analytics & Insights
- [ ] **Content analytics**: Track content freshness, update frequency
- [ ] **Site health monitoring**: Monitor site availability, response times  
- [ ] **Change impact analysis**: Analyze significance of content changes
- [ ] **Usage analytics**: Track which content is accessed most

### **Developer Experience**
- [ ] **Dry-run mode**: Show proposed writes without touching disk.
- [ ] **Selective optimise**: Only process changed files since last ref.
- [ ] **Profile presets**: `lossless | balanced | compact` with sensible defaults.

### **Distribution**
- [ ] **Homebrew / pipx recipe**: Easier local installs.
- [ ] **GitHub Action**: Reusable action for `contextor optimize`.

---

## Completed
> Pre-pivot work retained for later phases (do not include in active backlog).


### **Core Pipeline: Directory → MDC** - *COMPLETE*

- [x] **Discovery / File selection** (P1 · S · Status: Done)  
  Walk `--src`, honour include/exclude globs; support `.md` and `.mdx`.
- [x] **MDX cleaner** (P1 · M · Status: Done)  
  Strip `import`/`export` blocks and common JSX wrappers; preserve content semantics.
- [x] **Markdown normalisation** (P1 · S · Status: Done)  
  `mdformat` (+GFM): headings, code fences, tables; unify line endings and spacing.
- [x] **Link hygiene** (P1 · S · Status: Done)  
  Convert relative links to canonical repo URLs where possible; remove "edit this page" boilerplate.
- [x] **Token-aware compression (opt-in)** (P2 · M · Status: Done)  
  Elide/compact very large code/JSON blocks with clear markers; preserve summaries.
- [x] **Emitter: `.mdc` + `index.jsonl`** (P1 · S · Status: Done)  
  Write MDC with front-matter (`schema`, `source.repo/ref/path/url`, `title`, `topics`, `content_hash`, `fetched_at`, `slug`); append manifest.
- [x] **Deterministic slug & hashing** (P1 · S · Status: Done)  
  Stable slug from repo + path; `sha256` over normalised content to gate writes.
- [x] **Unit tests (pipeline)** (P2 · M · Status: Done)  
  MDX strip cases, link rewrite, slug/hash stability, emitter idempotency.

### Pivot & Bootstrap - *COMPLETE*

- [x] **Poetry & Makefile baseline**
  Initialise Poetry project, lock dependencies, and add Make targets (`install`, `lint`, `fmt`, `optimize`, `test`).
- [x] **CLI scaffold (`optimize`) with Typer**
  `contextor optimize --src <docs_dir> --out <sourcedocs> --repo <owner/name> --ref <sha|branch> --topics …`.
- [x] **Config file (optional) & defaults**
  Support `config/optimize.yaml` for include/exclude globs, per-source topics, and output scope.
- [x] **Repo metadata capture**
  Resolve canonical GitHub URL for each file (repo, ref, path) for front-matter provenance.

### Legacy assets available — *Reusable in Later Phases* — **ARCHIVED**

- [x] **Early MCP server scaffolding**  
  Prior server modules and handlers can accelerate the Phase-2 read-only server.
- [x] **Serverless deployment stubs**  
  Lambda/Vercel handlers exist and can be adapted for the read-only server.
- [x] **Crawler prototypes**  
  Early HTTP/sitemap/Playwright code remains useful if Phase-3 scraping is enabled.

---

## Archive Roadmap - **IGNORE THIS SECTION**

### Sprint 1 — **Core Extraction Engine** → Release v0.1.0

- [ ] **HTTP requests extractor** (P1 · M · Status: Not started)  
  Implement `RequestsExtractor` with session management, headers, rate limiting using `requests`.

- [ ] **HTML processing with BeautifulSoup** (P1 · M · Status: Not started)  
  Content extraction, selector-based parsing, content cleaning with `beautifulsoup4`.

- [ ] **Markdown conversion** (P1 · S · Status: Not started)  
  Convert extracted HTML to clean Markdown using `html2text`.

- [ ] **Content hashing and deduplication** (P1 · S · Status: Not started)  
  SHA-256 content hashing for change detection, avoid re-processing unchanged content.

- [ ] **Robots.txt respect** (P1 · S · Status: Not started)  
  Check and honor robots.txt using `urllib.robotparser`.

- [ ] **Rate limiting implementation** (P1 · S · Status: Not started)  
  Per-site rate limiting with configurable requests/second and concurrent limits.

- [ ] **MCP file generation** (P1 · M · Status: Not started)  
  Generate structured `.mdc` files with metadata, content sections, and context information.

---

### Sprint 2 — **Advanced Extraction** → Release v0.1.1

- [ ] **Playwright integration** (P2 · M · Status: Not started)  
  Dynamic content extraction for JavaScript-heavy sites using Playwright.

- [ ] **Sitemap discovery** (P2 · M · Status: Not started)  
  Automatic page discovery via `sitemap.xml` parsing with filtering capabilities.

- [ ] **Site-specific extractors** (P2 · S · Status: Not started)  
  Configurable extractors per site with custom selectors and cleanup rules.

- [ ] **Content validation** (P2 · S · Status: Not started)  
  Validate extracted content quality, detect extraction failures.

- [ ] **Error handling and retries** (P2 · S · Status: Not started)  
  Graceful error handling, exponential backoff, retry logic.

---

### Sprint 3 — **MCP Format & Validation** → Release v0.2.0

- [ ] **MCP schema definition** (P1 · S · Status: Not started)  
  Define and validate MCP file schema, ensure consistency across generated files.

- [ ] **Manifest generation** (P1 · S · Status: Not started)  
  Generate site and global manifest files with metadata and indexes.

- [ ] **Content structure analysis** (P2 · M · Status: Not started)  
  Parse content into structured sections, headings, subsections.

- [ ] **Validation commands** (P2 · S · Status: Not started)  
  CLI commands to validate MCP files and directory structure.

---

### Sprint 4 — **CLI Polish & Usability** → Release v0.3.0

- [ ] **Rich CLI interface** (P2 · S · Status: Not started)  
  Improve CLI with progress bars, colored output, better error messages.

- [ ] **Configuration validation** (P1 · S · Status: Not started)  
  Validate target configuration files, provide helpful error messages.

- [ ] **Dry-run mode** (P2 · S · Status: Not started)  
  Show what would be fetched without actually fetching content.

- [ ] **Search and query commands** (P3 · M · Status: Not started)  
  CLI commands to search content by topic, site, keywords.

- [ ] **Export capabilities** (P3 · M · Status: Not started)  
  Export MCP content to different formats (JSON, Markdown, etc.).

---

### Sprint 5 — **Testing & Quality** → Release v0.4.0

- [ ] **Unit test suite** (P1 · L · Status: Not started)  
  Comprehensive tests for extractors, processors, MCP generation.
- [ ] **Integration tests** (P2 · M · Status: Not started)  
  End-to-end tests with mock HTTP responses.
- [ ] **Performance optimization** (P2 · M · Status: Not started)  
  Optimize concurrent processing, memory usage for large sites.
- [ ] **Code quality tools** (P2 · S · Status: Not started)  
  Set up ruff, black, mypy, pre-commit hooks.

---

### Sprint 6 — **Advanced Features** → Release v0.5.0

- [ ] **Content change detection** (P3 · M · Status: Not started)  
  Track content changes over time, generate change reports.

- [ ] **Incremental updates** (P2 · M · Status: Not started)  
  Only fetch and process changed content, efficient updates.

- [ ] **Custom transforms** (P3 · M · Status: Not started)  
  Pluggable content transformation system.

- [ ] **Vector database integration** (P4 · L · Status: Not started)  
  Optional integration with ChromaDB, Pinecone for semantic search.

---

### Sprint 7 — **Enterprise Features** → Release v0.6.0

- [ ] **Authentication support** (P3 · M · Status: Not started)  
  Support for sites requiring login, API keys, OAuth.

- [ ] **Proxy support** (P3 · S · Status: Not started)  
  HTTP/HTTPS proxy support for corporate environments.

- [ ] **Large site optimization** (P3 · M · Status: Not started)  
  Efficient handling of sites with thousands of pages.

- [ ] **Monitoring and metrics** (P3 · S · Status: Not started)  
  Optional telemetry, performance metrics, health checks.

---

### Sprint 8 — **Ecosystem Integration** → Release v0.7.0

- [ ] **LangChain integration** (P3 · M · Status: Not started)  
  Direct integration with LangChain document loaders.

- [ ] **API endpoints** (P4 · L · Status: Not started)  
  Optional REST API for remote content fetching.

- [ ] **Database backends** (P4 · L · Status: Not started)  
  Support for PostgreSQL, SQLite for metadata storage.

- [ ] **Cloud storage backends** (P4 · M · Status: Not started)  
  Support for S3, GCS for storing MCP files.

---

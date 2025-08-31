# Contextor

Contextor converts existing documentation trees (e.g. Next.js, Tailwind CSS) into **Model Context Protocol** (`.mdc`) files optimised for LLMs. 

In **Phase 1**, it walks a target docs directory from another repo, cleans and normalises Markdown/MDX, performs optional token-saving compression, and writes results to a separate repository named **`sourcedocs`** under `{source-slug}/`. **Phase 2** adds a Python MCP server to serve from `sourcedocs`. **Phase 3** (future) may add polite web scraping for docs that aren’t hosted in public repos.

## Key Features

- **Repo docs → `.mdc`** – Recurses through Markdown/MDX docs, adds rich front-matter (repo, ref, path, canonical URL), and outputs `.mdc` files ready for agents.
- **MD/MDX aware normalisation** – Strips MDX imports/exports & common JSX wrappers; fixes headings, code fences, tables, and links.
- **Token-saving compression (optional)** – Compact large code/JSON blocks with safe elision for lower token costs while preserving meaning.
- **Deterministic & idempotent** – Stable slugs and content hashes; writes only when content changes. Git holds the history.
- **Indexing for fast lookup** – Appends a manifest entry to `{source-slug}/index.jsonl` for each emitted `.mdc`.
- **Roadmap ready** – Phase 2 MCP server that serves from `sourcedocs/{source-slug}/`; Phase 3 optional scraping for non-repo docs.

---

## Quick Start

**Get running in under 5 minutes:**

1. Clone the repositories

```bash
# Tooling
git clone <contextor-repository-url>
cd contextor

# Storage target (holds emitted .mdc files)
git clone <sourcedocs-repository-url> ../sourcedocs
````

2. Install dependencies

```bash
# Using Poetry
poetry install
```

3. Configure the environment

```bash
# No .env is required for Phase 1.
# (Optional) Create config/optimize.yaml for include/exclude rules and topics.
```

4. Start the application

```bash
# Convert a docs directory from another repo into .mdc files inside sourcedocs/{source-slug}
poetry run contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/{source-slug} \
  --repo vercel/next.js --ref main \
  --topics "framework,nextjs,prompt-engineering"

# Commit results to sourcedocs
cd ../sourcedocs
git add {source-slug}
git diff --cached --quiet || git commit -m "chore(context): refresh MDC" && git push
```

**You're ready to go!** The `.mdc` files now live in `sourcedocs/{source-slug}/` and can be consumed by agents (e.g. Promptman).
*In Phase 2 you’ll run the MCP server to serve these files; in Phase 3 you may add optional scraping.*

---

## Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

* **[Getting Started](docs/GETTING_STARTED.md)** – Detailed setup and first steps
* **[Architecture](docs/architecture/)** – System design and technical decisions
* **[FAQ](docs/FAQ.md)** – Common questions and answers
* **[Troubleshooting](docs/TROUBLESHOOTING.md)** – Solutions to common issues

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:

* Development workflow and guidelines
* Code standards and quality requirements
* How to submit changes and get them reviewed

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.

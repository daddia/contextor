# Architecture Decision Records (ADRs) for Contextor

This document maintains an index of all architectural decisions made for the Contextor project.

## What is an Architecture Decision Record?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. Each ADR describes:

- The architectural issue or problem
- The decision taken to address it
- The status of the decision (proposed, accepted, deprecated, superseded)
- The context and factors that influenced the decision  
- The consequences of the decision (positive and negative)

## ADR Index

| ID | Title | Status | Date | Context |
|----|-------|--------|------|---------|
| [ADR-001](ADR-001-mcp-file-format.md) | MCP File Format Choice | Accepted | 2025-01-15 | Standard format for content output |
| [ADR-002](ADR-002-popular-libraries.md) | Popular Library Selection | Accepted | 2025-01-15 | Foundation library choices |
| [ADR-003](ADR-003-context-directory.md) | {source-slug} Directory Convention | Accepted | 2025-01-15 | Output directory structure |

## Creating New ADRs

Use the template at [../../templates/adr-template.md](../../templates/adr-template.md) to create new ADRs.

1. Copy the template to a new file: `ADR-{number}-{brief-title}.md`
2. Fill in all sections of the template
3. Add an entry to this index
4. Submit for review via pull request

## Status Values

- **Proposed** - The decision is proposed and under discussion
- **Accepted** - The decision is accepted and implemented
- **Deprecated** - The decision is no longer valid but still exists in legacy systems  
- **Superseded** - The decision has been replaced by a newer decision

---

*For more information about ADRs, see [Michael Nygard's article](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).*

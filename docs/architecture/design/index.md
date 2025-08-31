# Feature Design Document Index

Below are all the Feature Design Documents. Feature Design Documents capture detailed technical designs for specific features, systems, or platform components that implement business or technical requirements.

## What is a Feature Design Document?

A Feature Design Document captures the comprehensive technical design for a feature or system component. Each design document describes:

- The problem being solved and requirements
- Goals and non-goals of the implementation
- Architecture and data flow design
- Security, performance, and observability considerations
- Testing strategy and rollout plan
- Risks, alternatives, and open questions

---

| ID                                             | Title                         | Status   | Date       | Owner        |
|------------------------------------------------|-------------------------------|----------|------------|--------------|
| [FDD-001](FDD-001-configuration-management.md) | Configuration Management      | Accepted | 2025-01-15 | —            |

---

### Status Legend

- **Draft** — Work in progress, not yet ready for review.
- **Review** — Under review, feedback being incorporated.
- **Approved** — Design approved, ready for implementation.
- **Complete** — Feature implemented and design finalized.
- **Deprecated** — No longer applicable or superseded.

---

## Creating a New Feature Design Document

Use the template provided at [../templates/feature-design-doc.md](../templates/feature-design-doc.md) to create new Feature Design Documents.

1. Copy the template to a new file with a descriptive name:

   ```bash
   cp docs/templates/feature-design-doc.md docs/design/{feature-name}.md
   ```

2. The filename should follow the pattern `FDD-{000}-{feature-name}.md`:
   - Use lowercase with hyphens for readability
   - Keep names concise but descriptive
   - Examples: `FDD-123-user-authentication.md`, `FDD-457-payment-processing.md`, `FDD-345-api-versioning.md`

3. Complete all sections of the template:
   - **Summary**: One paragraph explaining what you're building and why
   - **Goals**: Concrete, measurable objectives
   - **Non-goals**: What's explicitly out of scope
   - **Requirements**: Functional and non-functional requirements
   - **Architecture & Data Flow**: High-level design and request flow
   - **Security & Privacy**: Threat model and mitigations
   - **Testing & Quality**: Testing strategy and quality gates
   - **Rollout Plan**: Deployment and feature flag strategy
   - **Risks & Alternatives**: Key risks and options considered

4. Submit for review via pull request (PR). Start with **Draft** status.

5. Upon approval:
   - Update status to **Approved**
   - Add entry to this Feature Design Document Index
   - Begin implementation following the approved design

6. Mark as **Complete** when feature is fully implemented and deployed.

---

## Resources

- [Design Doc Template](../templates/feature-design-doc.md)
- [Google's Design Doc Guide](https://www.industrialempathy.com/posts/design-doc-a-design-doc/)
- [Architecture Decision Records](../decisions/register.md)

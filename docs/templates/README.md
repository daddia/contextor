---
title: Documentation Templates
description: Collection of reusable documentation templates for project setup
version: 1.0.0
---

# Documentation Templates

This directory contains reusable templates to help teams create consistent, high-quality documentation across all projects.

## Available Templates

### Core Project Templates (\_projectroot)
Copy these to your project root directory:

- **[README.md](../_projectroot/README.md)** - Main project overview and introduction
- **[CONTRIBUTING.md](../_projectroot/CONTRIBUTING.md)** - Development workflow and contribution guidelines  
- **[CHANGELOG.md](../_projectroot/CHANGELOG.md)** - Record of notable changes and version history
- **[TODO.md](../_projectroot/TODO.md)** - Task tracking and project roadmap

### Documentation Templates (docs/)
Copy these to your `docs/` directory:

- **[index.md](../index.md)** - Documentation hub and navigation
- **[GETTING_STARTED.md](../GETTING_STARTED.md)** - Comprehensive setup guide
- **[FAQ.md](../FAQ.md)** - Frequently asked questions
- **[TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Common issues and solutions
- **[RELEASE_NOTES.md](../RELEASE_NOTES.md)** - Release information and highlights

### Architecture Templates (docs/architecture/)
Copy these to your `docs/architecture/` directory:

- **[ARCHITECTURE.md](../architecture/ARCHITECTURE.md)** - System architecture overview
- **[PRINCIPLES.md](../architecture/PRINCIPLES.md)** - Design principles and guidelines
- **[STRUCTURE.md](../architecture/STRUCTURE.md)** - Project structure documentation

### Specialized Templates (docs/templates/)
Copy these as needed for your specific project requirements:

- **[security-policy.md](./security-policy.md)** - Security policy and vulnerability reporting
- **[api-documentation.md](./api-documentation.md)** - REST API documentation template
- **[deployment-guide.md](./deployment-guide.md)** - Deployment procedures and environments
- **[monitoring-guide.md](./monitoring-guide.md)** - Monitoring and observability setup
- **[runbook.md](./runbook.md)** - Operational procedures and incident response

### Process Templates (existing)
These templates are already available for architectural and design processes:

- **[adr-template.md](./adr-template.md)** - Architecture Decision Record template
- **[feature-design-doc.md](./feature-design-doc.md)** - Feature design documentation template

---

## Quick Setup

Use the **[project-template.md](./project-template.md)** guide for step-by-step instructions on setting up documentation for a new project.

### Basic Setup
1. Copy root templates to project root
2. Create `docs/` directory structure  
3. Copy appropriate documentation templates
4. Update all placeholder values with project-specific information

### Template Customization
All templates include placeholder values in brackets like `[Project Name]` and `[Description]`. Replace these with your actual project information.

---

## Template Standards

### Frontmatter
All templates include YAML frontmatter with:
```yaml
---
title: [Document Title]
description: [Brief description]
version: 1.0.0
# Additional metadata as needed
---
```

### Formatting Conventions
- **Headings**: Use sentence case for headings
- **Lists**: Use consistent bullet point styling  
- **Code Blocks**: Include language specification for syntax highlighting
- **Links**: Use descriptive link text, not "click here"
- **Placeholders**: Use `[Placeholder Text]` format for values to replace

### Content Guidelines
- **Clarity**: Write for your audience - be clear and concise
- **Actionability**: Include specific steps and examples
- **Completeness**: Cover the essential information users need
- **Maintainability**: Include update instructions and version information

---

## Using Templates

### For New Projects
1. Follow the [project-template.md](./project-template.md) setup guide
2. Copy all relevant templates to your project
3. Replace placeholder values with project-specific information
4. Remove sections that don't apply to your project
5. Add project-specific sections as needed

### For Existing Projects
1. Review your current documentation against these templates
2. Identify gaps or inconsistencies
3. Gradually migrate to the standard template structure
4. Update documentation to match the standard format

---

## Maintenance

### Template Updates
- Templates are versioned using the `version` field in frontmatter
- When templates are updated, increment the version number
- Communicate template changes to teams using them
- Consider backward compatibility when making changes

### Feedback and Improvements
- Gather feedback from teams using the templates
- Regular reviews to identify improvement opportunities
- Update templates based on evolving best practices
- Maintain consistency across all templates

---

## Resources

- **[Writing Style Guide](../../.cursor/rules/writing-style.md)** - Tone and voice guidelines
- **[Project Template Setup](./project-template.md)** - Detailed setup instructions
- **[Architecture Decisions](../architecture/decisions/register.md)** - Record of architectural decisions
- **[Design Documents](../architecture/design/index.md)** - Feature design specifications

---

*These templates are living documents. Please contribute improvements and report issues to help make them better for everyone.*

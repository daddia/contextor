---
title: Project Template Guide
description: Template for setting up a new project with standard documentation structure
version: 1.0.0
---

# Project Template Guide

This guide helps you set up a new project with our standard documentation structure.

## Template Structure

When creating a new project, copy these files to establish consistent documentation:

### Root Directory Files
Copy these files to your project root:

```
├── README.md              # Main project overview (use _projectroot/README.md template)  
├── CONTRIBUTING.md         # Contribution guidelines (use _projectroot/CONTRIBUTING.md template)
├── CHANGELOG.md            # Change history (use _projectroot/CHANGELOG.md template)
├── TODO.md                # Task tracking (use _projectroot/TODO.md template)
├── LICENSE                # Project license
└── .env.example           # Environment variable template
```

### Documentation Directory
Create a `docs/` directory with this structure:

```
docs/
├── index.md               # Documentation hub (use docs/index.md template)
├── GETTING_STARTED.md     # Setup guide (use docs/GETTING_STARTED.md template)
├── FAQ.md                 # Common questions (use docs/FAQ.md template)
├── TROUBLESHOOTING.md     # Problem solving (use docs/TROUBLESHOOTING.md template)
├── RELEASE_NOTES.md       # Release information (use docs/RELEASE_NOTES.md template)
├── architecture/
│   ├── ARCHITECTURE.md    # System overview (use architecture/ARCHITECTURE.md template)
│   ├── PRINCIPLES.md      # Design principles (use architecture/PRINCIPLES.md template)
│   ├── STRUCTURE.md       # Project structure (use architecture/STRUCTURE.md template)
│   ├── decisions/
│   │   ├── register.md    # ADR index (use existing template)
│   │   └── adr-template.md # ADR template (use existing template)
│   └── design/
│       ├── index.md       # Design doc index (use existing template)
│       └── feature-design-doc.md # Design doc template (use existing template)
└── templates/
    ├── security-policy.md # Security policy (optional, for public projects)
    ├── api-documentation.md # API docs template (for API projects)
    ├── deployment-guide.md # Deployment procedures (for complex deployments)
    ├── monitoring-guide.md # Monitoring setup (for production services)
    └── runbook.md         # Operational procedures (for production services)
```

---

## Setup Checklist

Use this checklist when setting up a new project:

### Basic Setup
- [ ] Copy root directory templates to project root
- [ ] Create `docs/` directory structure
- [ ] Copy appropriate template files to `docs/`
- [ ] Update project name and description in all templates
- [ ] Configure appropriate frontmatter fields

### Customization
- [ ] Update README.md with project-specific information
- [ ] Customize CONTRIBUTING.md for project workflow
- [ ] Set up initial TODO.md with project milestones
- [ ] Update architecture documentation with system design
- [ ] Configure appropriate templates in `docs/templates/`

### Optional Enhancements
- [ ] Add security policy if project will be public
- [ ] Set up API documentation if building an API
- [ ] Create deployment guide for complex deployments
- [ ] Add monitoring guide for production services
- [ ] Create runbooks for operational procedures

---

## Template Customization

### Required Updates

For each template file, update these placeholder values:

- `[Project Name]` → Your actual project name
- `[Brief description]` → Actual project description  
- `[Team Name]` → Your team or organization name
- `[Contact Information]` → Actual contact details
- `[Version]` → Current version numbers
- `[Date]` → Current dates
- `[URL/Link]` → Actual URLs and links

### Frontmatter Fields

Each template includes frontmatter with these fields:

```yaml
---
title: [Document Title]
description: [Brief description of the document]
version: 1.0.0
# Additional fields based on document type
---
```

Update these fields appropriately for your project.

### Content Adaptation

- **Remove sections** that don't apply to your project
- **Add sections** for project-specific requirements  
- **Update examples** with project-relevant information
- **Modify procedures** to match your team's workflow

---

## Best Practices

### Documentation Standards

- **Keep it Simple**: Start with basic templates and add complexity as needed
- **Stay Current**: Update documentation as the project evolves
- **Be Consistent**: Use the same structure and style across all documents
- **Link Effectively**: Cross-reference related documents appropriately

### Team Adoption

- **Training**: Ensure team members understand the documentation structure
- **Review Process**: Include documentation review in your PR process
- **Regular Updates**: Schedule regular documentation reviews and updates
- **Feedback Loop**: Gather feedback and improve templates over time

---

## Template Maintenance

### When to Update Templates

- **New Project Requirements**: When project needs evolve
- **Process Changes**: When team workflow or tools change
- **Best Practice Updates**: When industry standards evolve
- **Feedback Integration**: Based on team feedback and usage

### Version Management

- Track template versions using the frontmatter `version` field
- Document template changes in this guide
- Communicate template updates to all teams using them

---

## Resources

### Template Sources
- **Root Templates**: `.horizon/docs/_projectroot/`
- **Doc Templates**: `.horizon/docs/`  
- **Architecture Templates**: `.horizon/docs/architecture/`
- **Additional Templates**: `.horizon/docs/templates/`

### Related Guides
- **[Writing Style Guide](../.cursor/rules/writing-style.md)** - Consistency in tone and voice
- **[Architecture Decision Records](./architecture/decisions/register.md)** - Recording architectural decisions
- **[Feature Design Documents](./architecture/design/index.md)** - Detailed feature specifications

---

*This template guide should be updated when new templates are added or existing ones are modified. Last updated: [Date]*

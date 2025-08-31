# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/), and this project adheres to [Semantic Versioning](http://semver.org/).

---

## [Unreleased]

### Added

- **Matrix GitHub Action** for automated sourcedocs integration
  - Multi-source repository processing with change detection
  - Automatic commit and push of updated MDC files
  - Support for manual workflow dispatch with filtering options
  - Comprehensive run summary with metrics visualization
- **Run metrics artifact** with JSON output
  - New `--metrics-output` CLI option for observability
  - Detailed metrics including processed, written, skipped, and error counts
  - Timestamp and source metadata for tracking runs
- **Sample configurations and profiles** for popular frameworks
  - Pre-configured profiles for Next.js, React, Tailwind CSS, VS Code, and Vite
  - Comprehensive `optimize.sample.yaml` with multi-source configuration
  - Profile documentation and usage guidelines
- **Advanced project configurations** aligned with Context7 structure
  - JSON-based project configurations in `config/projects/` directory
  - Context7-compatible metadata including trust scores, approval status, and VIP flags
  - New `--project-config` CLI option for simplified usage
  - `contextor list-projects` command to view available configurations
  - Automatic parameter inference from project configurations (repo, branch, topics, profile)
  - Enhanced GitHub Actions integration with dynamic configuration loading

### Changed

- Enhanced Makefile with metrics support and improved examples
- Updated CLI help text to include new metrics option
- Simplified GitHub Actions matrix configuration (project details now in JSON configs)
- Updated DocumentLoader to support project configuration integration

## [0.0.1] - 2025-08-31

### Added

- Initial repo and scaffold for Contextor
- Basic CLI with `contextor optimize` command
- Markdown/MDX processing pipeline
- Content transformation system
- MDC file emission with frontmatter

---

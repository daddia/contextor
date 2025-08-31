# Contextor Configuration Profiles

This directory contains pre-configured optimization profiles for popular documentation sources. These profiles are optimized for the specific structure, content patterns, and MDX components used by each project.

## Available Profiles

### Framework Documentation

- **`nextjs.yaml`** - Next.js framework documentation
  - Optimized for Next.js docs structure and React/JSX examples
  - Handles Next.js specific MDX components (Callout, Card, Tabs, etc.)
  - Preserves important code examples while compressing large blocks

- **`react.yaml`** - React library documentation  
  - Configured for React's docs and beta docs structure
  - Handles React-specific components (YouWillLearn, Recap, Sandpack, etc.)
  - Emphasizes preserving component and hook examples

- **`vite.yaml`** - Vite build tool documentation
  - Optimized for build tool configuration examples
  - Preserves complex config files and build scripts
  - Handles Vite's minimal MDX component set

### CSS & Styling

- **`tailwindcss.yaml`** - Tailwind CSS framework documentation
  - Optimized for utility-first CSS documentation
  - Preserves CSS examples and HTML snippets
  - Handles Tailwind's design system components

### Developer Tools

- **`vscode.yaml`** - VS Code editor documentation
  - Configured for editor and extension documentation
  - Preserves configuration examples and API references
  - Handles VS Code's minimal component structure

## Using Profiles

### Option 1: Direct Profile Usage (Future Feature)

```bash
# Use a pre-built profile directly
poetry run contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --repo vercel/next.js --ref main \
  --profile-config config/profiles/nextjs.yaml
```

### Option 2: Copy and Customize

```bash
# Copy a profile as starting point
cp config/profiles/nextjs.yaml config/my-nextjs-config.yaml

# Customize the copied file
# Then use with --config flag
poetry run contextor optimize \
  --config config/my-nextjs-config.yaml \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --repo vercel/next.js --ref main
```

### Option 3: Matrix CI/CD Integration

The GitHub Action at `.github/workflows/sourcedocs-matrix.yml` automatically uses appropriate settings for each source repository. The configuration is embedded in the workflow matrix.

## Profile Structure

Each profile contains:

- **File patterns** - Include/exclude rules optimized for the project structure
- **Topics** - Relevant topic tags for the content type
- **Optimization settings** - Balance between content preservation and token efficiency
- **Transform rules** - Handling of MDX components and content patterns
- **Link rules** - Base URL and link rewriting configuration

## Creating Custom Profiles

To create a new profile:

1. Copy an existing profile that's similar to your target documentation
2. Update the file patterns to match your source structure
3. Adjust topics to reflect your content domain
4. Customize MDX component handling for your specific components
5. Set appropriate link rewriting rules

## Profile Validation

Profiles follow the same schema as the main `optimize.yaml` configuration. See `optimize.sample.yaml` for the complete configuration reference and available options.

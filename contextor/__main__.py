"""CLI entry point for Contextor."""

import json
from datetime import datetime
from pathlib import Path

import click
import structlog

from .emit import MDCEmitter
from .loader import DocumentLoader
from .project_config import ProjectConfigManager
from .transforms import apply_transforms

logger = structlog.get_logger()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Convert documentation trees to Model Context Protocol files."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def list_projects():
    """List available project configurations."""
    config_manager = ProjectConfigManager()
    projects = config_manager.list_available_projects()
    
    if not projects:
        click.echo("No project configurations found.")
        return
    
    click.echo("Available project configurations:")
    for project_name in projects:
        config = config_manager.load_project_config(project_name)
        if config:
            click.echo(f"  {project_name}: {config.title} ({config.repo_url})")
        else:
            click.echo(f"  {project_name}: (failed to load)")


@cli.command()
@click.option(
    "--src", required=True, help="Source directory containing Markdown/MDX files"
)
@click.option("--out", required=True, help="Output directory for .mdc files")
@click.option(
    "--repo", default="", help="Repository identifier (e.g., 'vercel/next.js') - optional if using project config"
)
@click.option("--ref", default="", help="Git reference (branch or commit SHA) - optional if using project config")
@click.option("--topics", default="", help="Comma-separated list of topics")
@click.option(
    "--profile",
    default="balanced",
    help="Optimization profile: lossless, balanced, or compact",
)
@click.option("--project-config", default="", help="Project configuration name (e.g., 'nextjs', 'react')")
@click.option("--auto-detect-config", is_flag=True, default=True, help="Automatically detect and use standards-based config files from target repo")
@click.option("--metrics-output", default="", help="Output path for run metrics JSON")
def optimize(src, out, repo, ref, topics, profile, project_config, auto_detect_config, metrics_output):
    """Convert a documentation directory to .mdc files.

    This command processes Markdown/MDX files from a source directory,
    applies content transforms, and outputs .mdc files with rich metadata.
    """
    # Convert string paths to Path objects
    src_path = Path(src)
    out_path = Path(out)

    # Validate source directory exists
    if not src_path.exists() or not src_path.is_dir():
        logger.error("Source directory does not exist or is not a directory", src=src)
        raise click.Abort()

    # Initialize config manager
    config_manager = ProjectConfigManager()
    
    # Load project configuration if specified
    project_cfg = None
    if project_config:
        project_cfg = config_manager.load_project_config(project_config)
        if not project_cfg:
            logger.error("Project configuration not found", project=project_config)
            raise click.Abort()
        
        logger.info("Using project configuration", 
                   project=project_config, title=project_cfg.title)

    # Check for standards-based config files in source directory if auto-detect is enabled
    if auto_detect_config:
        detected_config = config_manager.detect_and_sync_standards_config(src_path, project_config or "detected")
        if detected_config:
            # Use detected config if no explicit project config was provided
            if not project_cfg:
                project_cfg = detected_config
                logger.info("Using auto-detected standards-based configuration", 
                           title=project_cfg.title, repo=project_cfg.repo_url)

    # Override parameters with project config if available
    if project_cfg:
        # Use project config repo if not provided via CLI
        if not repo:
            repo_url = project_cfg.repo_url
            if repo_url.startswith("https://github.com/"):
                repo = repo_url.replace("https://github.com/", "")
            else:
                repo = project_cfg.project_path.lstrip("/")
        
        # Use project config branch if not provided
        if not ref:
            ref = project_cfg.branch
            
        # Use project config profile if not overridden
        if profile == "balanced":
            profile = project_cfg.profile
    
    # Validate required parameters after project config override
    if not repo:
        logger.error("Repository identifier is required (use --repo or --project-config)")
        raise click.Abort()
    
    if not ref:
        logger.error("Git reference is required (use --ref or --project-config)")
        raise click.Abort()

    logger.info(
        "Starting contextor optimize",
        src=src,
        out=out,
        repo=repo,
        ref=ref,
        topics=topics,
        profile=profile,
        project_config=project_config,
    )

    # Parse topics
    topic_list = []
    if topics:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    elif project_cfg:
        # Use project config topics if none provided
        topic_list = project_cfg.topics

    # Initialize components
    loader = DocumentLoader(src_path, repo=repo, ref=ref, project_config=project_cfg)
    emitter = MDCEmitter(out_path)

    # Process files
    processed = 0
    written = 0
    skipped = 0
    errors = 0

    try:
        for doc_info in loader.discover_files():
            try:
                # Apply transforms
                transformed_content = apply_transforms(
                    doc_info.content,
                    profile=profile,
                    source_path=doc_info.path,
                )

                # Emit .mdc file
                was_written = emitter.emit_mdc(
                    content=transformed_content,
                    metadata={
                        "repo": repo,
                        "ref": ref,
                        "path": doc_info.path,
                        "url": doc_info.canonical_url,
                        "title": doc_info.title,
                        "topics": topic_list,
                    },
                )

                processed += 1
                if was_written:
                    written += 1
                else:
                    skipped += 1

            except Exception as e:
                logger.error("Failed to process file", path=doc_info.path, error=str(e))
                errors += 1

    except Exception as e:
        logger.error("Failed to process directory", error=str(e))
        raise click.Abort() from e

    # Prepare metrics
    metrics = {
        "processed": processed,
        "written": written,
        "skipped": skipped,
        "errors": errors,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": {
            "repo": repo,
            "ref": ref,
            "src_path": str(src_path),
            "out_path": str(out_path),
        },
        "profile": profile,
        "topics": topic_list,
    }

    logger.info(
        "Optimization complete",
        processed=processed,
        written=written,
        skipped=skipped,
        errors=errors,
    )

    # Write metrics if requested
    if metrics_output:
        metrics_path = Path(metrics_output)
        try:
            # Ensure parent directory exists
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)
            logger.info("Metrics written", path=metrics_output)
        except Exception as e:
            logger.error("Failed to write metrics", path=metrics_output, error=str(e))

    if errors > 0:
        raise click.Abort()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

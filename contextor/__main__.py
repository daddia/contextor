"""CLI entry point for Contextor."""

from pathlib import Path

import click
import structlog

from .emit import MDCEmitter
from .loader import DocumentLoader
from .transforms import apply_transforms

logger = structlog.get_logger()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Convert documentation trees to Model Context Protocol files."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--src", required=True, help="Source directory containing Markdown/MDX files"
)
@click.option("--out", required=True, help="Output directory for .mdc files")
@click.option(
    "--repo", required=True, help="Repository identifier (e.g., 'vercel/next.js')"
)
@click.option("--ref", required=True, help="Git reference (branch or commit SHA)")
@click.option("--topics", default="", help="Comma-separated list of topics")
@click.option(
    "--profile",
    default="balanced",
    help="Optimization profile: lossless, balanced, or compact",
)
@click.option("--config", default="", help="Configuration file path (YAML)")
def optimize(src, out, repo, ref, topics, profile, config):
    """Convert a documentation directory to .mdc files.

    This command processes Markdown/MDX files from a source directory,
    applies content transforms, and outputs .mdc files with rich metadata.
    """
    # Convert string paths to Path objects
    src_path = Path(src)
    out_path = Path(out)
    config_path = Path(config) if config else None

    # Validate source directory exists
    if not src_path.exists() or not src_path.is_dir():
        logger.error("Source directory does not exist or is not a directory", src=src)
        raise click.Abort()

    logger.info(
        "Starting contextor optimize",
        src=src,
        out=out,
        repo=repo,
        ref=ref,
        topics=topics,
        profile=profile,
    )

    # Parse topics
    topic_list = []
    if topics:
        topic_list = [t.strip() for t in topics.split(",") if t.strip()]

    # Initialize components
    loader = DocumentLoader(src_path, repo=repo, ref=ref, config_path=config_path)
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

    logger.info(
        "Optimization complete",
        processed=processed,
        written=written,
        skipped=skipped,
        errors=errors,
    )

    if errors > 0:
        raise click.Abort()


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

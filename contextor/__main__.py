"""CLI entry point for Contextor."""

import json
from datetime import datetime
from pathlib import Path

import click

from .benchmark import PerformanceBenchmark
from .emit import MDCEmitter
from .loader import DocumentLoader
from .logging_config import (
    configure_logging,
    get_logger,
    log_operation,
    log_operation_complete,
)
from .project_config import ProjectConfigManager
from .transforms import apply_transforms

logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Set logging level",
)
@click.option(
    "--json-logs/--human-logs",
    default=None,
    help="Output logs in JSON format (auto-detected by default)",
)
@click.pass_context
def cli(ctx, log_level, json_logs):
    """Convert documentation trees to Model Context Protocol files."""
    # Configure logging early
    configure_logging(level=log_level, json_output=json_logs)

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
    "--repo",
    default="",
    help="Repository identifier (e.g., 'vercel/next.js') - optional if using project config",
)
@click.option(
    "--ref",
    default="",
    help="Git reference (branch or commit SHA) - optional if using project config",
)
@click.option("--topics", default="", help="Comma-separated list of topics")
@click.option(
    "--profile",
    default="balanced",
    help="Optimization profile: lossless, balanced, or compact",
)
@click.option(
    "--project-config",
    default="",
    help="Project configuration name (e.g., 'nextjs', 'react')",
)
@click.option(
    "--auto-detect-config",
    is_flag=True,
    default=True,
    help="Automatically detect and use standards-based config files from target repo",
)
@click.option("--metrics-output", default="", help="Output path for run metrics JSON")
def optimize(
    src,
    out,
    repo,
    ref,
    topics,
    profile,
    project_config,
    auto_detect_config,
    metrics_output,
):
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

        logger.info(
            "Using project configuration",
            project=project_config,
            title=project_cfg.title,
        )

    # Check for standards-based config files in source directory if auto-detect is enabled
    if auto_detect_config:
        detected_config = config_manager.detect_and_sync_standards_config(
            src_path, project_config or "detected"
        )
        if detected_config:
            # Use detected config if no explicit project config was provided
            if not project_cfg:
                project_cfg = detected_config
                logger.info(
                    "Using auto-detected standards-based configuration",
                    title=project_cfg.title,
                    repo=project_cfg.repo_url,
                )

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
        logger.error(
            "Repository identifier is required (use --repo or --project-config)"
        )
        raise click.Abort()

    if not ref:
        logger.error("Git reference is required (use --ref or --project-config)")
        raise click.Abort()

    # Start main operation with structured logging
    main_context = log_operation(
        logger,
        "contextor_optimize",
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
            # Start file processing with structured logging
            from .logging_config import log_file_operation, log_operation_complete

            file_context = log_file_operation(
                logger,
                "process_file",
                doc_info.path,
                title=doc_info.title,
                url=doc_info.canonical_url,
            )

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
                outcome = "written" if was_written else "skipped"
                if was_written:
                    written += 1
                else:
                    skipped += 1

                log_operation_complete(
                    logger,
                    file_context,
                    success=True,
                    outcome=outcome,
                    content_length=len(transformed_content),
                )

            except Exception as e:
                log_operation_complete(
                    logger,
                    file_context,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                errors += 1

    except Exception as e:
        log_operation_complete(
            logger,
            main_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
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

    # Complete main operation
    log_operation_complete(
        logger,
        main_context,
        success=errors == 0,
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
            logger.info("Metrics written", path=metrics_output, metrics=metrics)
        except Exception as e:
            logger.error("Failed to write metrics", path=metrics_output, error=str(e))

    if errors > 0:
        raise click.Abort()


@cli.command()
@click.option(
    "--source-dir", required=True, help="Directory containing .mdc files to analyze"
)
@click.option(
    "--features",
    default="topic-extraction,cross-linking,quality-scoring,duplicate-detection",
    help="Comma-separated list of features to enable",
)
@click.option(
    "--config", default="", help="Path to intelligence configuration YAML file"
)
@click.option(
    "--incremental/--full",
    default=True,
    help="Run incremental analysis (skip unchanged files)",
)
@click.option(
    "--metrics-output", default="", help="Output path for analysis metrics JSON"
)
def intelligence(source_dir, features, config, incremental, metrics_output):
    """Run Advanced Content Intelligence analysis on .mdc files.

    This command analyzes existing .mdc files to extract topics, identify
    relationships, detect duplicates, and assess content quality.
    """
    try:
        # Import intelligence module (optional dependency)
        from .intelligence import IntelligenceAnalyzer
    except ImportError as e:
        logger.error(
            "Intelligence analysis requires optional dependencies. "
            "Install with: pip install contextor[intelligence]",
            error=str(e),
        )
        raise click.Abort() from e

    source_path = Path(source_dir)

    # Validate source directory exists
    if not source_path.exists() or not source_path.is_dir():
        logger.error(
            "Source directory does not exist or is not a directory",
            source_dir=source_dir,
        )
        raise click.Abort()

    # Check for .mdc files
    mdc_files = list(source_path.rglob("*.mdc"))
    if not mdc_files:
        logger.error("No .mdc files found in source directory", source_dir=source_dir)
        raise click.Abort()

    # Parse features
    feature_set = set()
    if features:
        feature_set = {f.strip() for f in features.split(",") if f.strip()}

    # Load configuration if provided
    analysis_config = {}
    if config:
        config_path = Path(config)
        if config_path.exists():
            try:
                import yaml

                with open(config_path, encoding="utf-8") as f:
                    analysis_config = yaml.safe_load(f) or {}
                logger.info("Loaded intelligence configuration", config_path=config)
            except Exception as e:
                logger.error(
                    "Failed to load configuration", config_path=config, error=str(e)
                )
                raise click.Abort() from e
        else:
            logger.warning("Configuration file not found", config_path=config)

    # Start intelligence analysis with structured logging
    analysis_context = log_operation(
        logger,
        "intelligence_analysis",
        source_dir=source_dir,
        features=list(feature_set),
        incremental=incremental,
        mdc_files_count=len(mdc_files),
    )

    # Initialize and run analyzer
    try:
        analyzer = IntelligenceAnalyzer(source_path, analysis_config)
        results = analyzer.analyze(features=feature_set, incremental=incremental)

        log_operation_complete(
            logger,
            analysis_context,
            success=results.get("errors", 0) == 0,
            processed=results.get("processed", 0),
            updated=results.get("updated", 0),
            skipped=results.get("skipped", 0),
            errors=results.get("errors", 0),
        )

        # Write metrics if requested
        if metrics_output:
            metrics_path = Path(metrics_output)
            try:
                metrics_path.parent.mkdir(parents=True, exist_ok=True)
                with open(metrics_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                logger.info("Analysis metrics written", path=metrics_output)
            except Exception as e:
                logger.error(
                    "Failed to write metrics", path=metrics_output, error=str(e)
                )

        if results.get("errors", 0) > 0:
            raise click.Abort()

    except Exception as e:
        log_operation_complete(
            logger,
            analysis_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise click.Abort() from e


@cli.command()
@click.option(
    "--budget",
    default=900,
    type=int,
    help="Performance budget in seconds (default: 900 = 15 minutes)",
)
@click.option("--output", default="", help="Output path for benchmark results JSON")
@click.option(
    "--test-data-path",
    default="",
    help="Path for test data (uses temp directory if not specified)",
)
@click.option(
    "--keep-test-data",
    is_flag=True,
    default=False,
    help="Keep test data after benchmarking",
)
def benchmark(budget, output, test_data_path, keep_test_data):
    """Run performance benchmarks to validate performance budget.

    This command creates test datasets of varying sizes and measures
    how long the optimize operation takes to process them.
    """
    benchmark_context = log_operation(
        logger,
        "performance_benchmark",
        budget_seconds=budget,
        output=output,
        test_data_path=test_data_path,
        keep_test_data=keep_test_data,
    )

    try:
        benchmark_runner = PerformanceBenchmark(budget_seconds=budget)

        base_path = Path(test_data_path) if test_data_path else None
        cleanup = not keep_test_data

        logger.info(
            "Starting performance benchmark",
            budget_seconds=budget,
            base_path=str(base_path) if base_path else "temp",
            cleanup=cleanup,
        )

        results = benchmark_runner.run_full_benchmark(
            base_path=base_path,
            cleanup=cleanup,
        )

        # Save results if output path specified
        if output:
            benchmark_runner.save_results(Path(output))

        # Print summary
        budget_failures = [r for r in results if not r["within_budget"]]
        total_duration = sum(r["duration_seconds"] for r in results)

        click.echo("\n" + "=" * 60)
        click.echo("PERFORMANCE BENCHMARK SUMMARY")
        click.echo("=" * 60)

        for result in results:
            status = "✅ PASS" if result["within_budget"] else "❌ FAIL"
            click.echo(
                f"{result['dataset'].upper():>6}: "
                f"{result['duration_seconds']:>6.1f}s "
                f"({result['processed']:>3} files, "
                f"{result['input_size_mb']:>5.1f}MB) "
                f"{status}"
            )

        click.echo("-" * 60)
        click.echo(f"TOTAL: {total_duration:>6.1f}s (Budget: {budget}s)")

        if budget_failures:
            click.echo(
                f"\n❌ {len(budget_failures)} dataset(s) exceeded performance budget!"
            )
            log_operation_complete(
                logger,
                benchmark_context,
                success=False,
                total_duration=round(total_duration, 3),
                budget_failures=len(budget_failures),
                results=results,
            )
            raise click.Abort()
        else:
            click.echo("\n✅ All datasets within performance budget!")
            log_operation_complete(
                logger,
                benchmark_context,
                success=True,
                total_duration=round(total_duration, 3),
                budget_failures=0,
                results=results,
            )

    except Exception as e:
        log_operation_complete(
            logger,
            benchmark_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise click.Abort() from e


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

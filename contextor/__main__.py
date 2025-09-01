"""CLI entry point for Contextor."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

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
from .utils import format_number, format_size, get_content_stats

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
def cli(ctx: Any, log_level: str, json_logs: bool) -> None:
    """Convert documentation trees to Model Context Protocol files."""
    # Configure logging early
    configure_logging(level=log_level, json_output=json_logs)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "--project-config",
    required=True,
    help="Project configuration name (e.g., 'nextjs', 'tailwindcss')",
)
@click.option(
    "--out",
    required=True,
    help="Output directory for .mdc files (will create project subdirectory)",
)
@click.option(
    "--workspace",
    default="/tmp/contextor-workspace",
    help="Workspace directory for cloning repositories",
)
@click.option(
    "--keep-workspace/--clean-workspace",
    default=False,
    help="Keep workspace after processing",
)
@click.option("--metrics-output", default="", help="Output path for run metrics JSON")
def fetch(
    project_config: str,
    out: str,
    workspace: str,
    keep_workspace: bool,
    metrics_output: str,
) -> None:
    """Fetch and process documentation from a configured project.

    This command automatically clones the repository, processes documentation,
    and outputs .mdc files with integrated token analysis.
    """
    import subprocess
    from pathlib import Path

    # Initialize config manager
    config_manager = ProjectConfigManager()

    # Load project configuration
    project_cfg = config_manager.load_project_config(project_config)
    if not project_cfg:
        logger.error("Project configuration not found", project=project_config)
        raise click.Abort()

    logger.info(
        "Starting fetch workflow",
        project=project_config,
        title=project_cfg.title,
        repo=project_cfg.repo_url,
    )

    # Setup workspace
    workspace_path = Path(workspace)
    repo_path = workspace_path / project_config
    out_path = Path(out) / project_config

    # Start fetch operation with structured logging
    fetch_context = log_operation(
        logger,
        "contextor_fetch",
        project=project_config,
        repo=project_cfg.repo_url,
        branch=project_cfg.branch,
        workspace=str(workspace_path),
        out=str(out_path),
    )

    try:
        # Ensure workspace exists
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Clone or update repository
        if repo_path.exists():
            logger.info("Updating existing repository", path=repo_path)
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.warning("Git pull failed, will re-clone", error=e.stderr)
                import shutil

                shutil.rmtree(repo_path)

        if not repo_path.exists():
            logger.info(
                "Cloning repository",
                repo=project_cfg.repo_url,
                branch=project_cfg.branch,
            )
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    project_cfg.branch,
                    project_cfg.repo_url,
                    str(repo_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        # Determine source paths from configuration
        source_paths = []
        for folder in project_cfg.folders:
            src_path = repo_path / folder
            if src_path.exists():
                source_paths.append(src_path)
                logger.info("Found source directory", path=src_path)
            else:
                logger.warning("Source directory not found", path=src_path)

        if not source_paths:
            logger.error("No valid source directories found")
            raise click.Abort()

        # Process each source path
        total_processed = 0
        total_written = 0
        total_errors = 0

        for src_path in source_paths:
            logger.info("Processing source directory", src=src_path, out=out_path)

            # Initialize components for this source
            loader = DocumentLoader(
                src_path,
                repo=project_cfg.project_path.lstrip("/"),
                ref=project_cfg.branch,
                project_config=project_cfg,
            )
            emitter = MDCEmitter(out_path)

            # Process files
            for doc_info in loader.discover_files():
                try:
                    # Apply transforms
                    transformed_content = apply_transforms(
                        doc_info.content,
                        profile=project_cfg.profile,
                        source_path=doc_info.path,
                    )

                    # Emit .mdc file
                    was_written = emitter.emit_mdc(
                        content=transformed_content,
                        metadata={
                            "repo": project_cfg.project_path.lstrip("/"),
                            "ref": project_cfg.branch,
                            "path": doc_info.path,
                            "url": doc_info.canonical_url,
                            "title": doc_info.title,
                            "topics": project_cfg.topics,
                        },
                    )

                    total_processed += 1
                    if was_written:
                        total_written += 1

                except Exception as e:
                    logger.error(
                        "Failed to process file", file=doc_info.path, error=str(e)
                    )
                    total_errors += 1

            # Finalize statistics
            final_stats = emitter.finalize_stats()

        # Clean up workspace if requested
        if not keep_workspace:
            logger.info("Cleaning up workspace", path=workspace_path)
            import shutil

            shutil.rmtree(workspace_path, ignore_errors=True)

        # Prepare metrics
        metrics = {
            "processed": total_processed,
            "written": total_written,
            "skipped": total_processed - total_written,
            "errors": total_errors,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_seconds": round(time.time() - fetch_context["start_time"], 3),
            "branch": project_cfg.branch,
            "total_tokens": final_stats["summary"]["tokens"],
            "project": {
                "name": project_config,
                "title": project_cfg.title,
                "repo": project_cfg.repo_url,
                "branch": project_cfg.branch,
                "folders": project_cfg.folders,
            },
            "workspace": str(workspace_path),
            "output": str(out_path),
            "token_analysis": final_stats,
        }

        # Update project configuration with scan metadata
        project_cfg.update_scan_metadata(metrics)
        config_manager.save_project_config(project_config, project_cfg)

        # Write metrics if requested
        if metrics_output:
            metrics_path = Path(metrics_output)
            try:
                metrics_path.parent.mkdir(parents=True, exist_ok=True)
                with open(metrics_path, "w", encoding="utf-8") as f:
                    json.dump(metrics, f, indent=2)
                logger.info("Metrics written", path=metrics_output)
            except Exception as e:
                logger.error(
                    "Failed to write metrics", path=metrics_output, error=str(e)
                )

        log_operation_complete(
            logger,
            fetch_context,
            success=total_errors == 0,
            processed=total_processed,
            written=total_written,
            errors=total_errors,
            total_tokens=final_stats["summary"]["tokens"],
        )

        if total_errors > 0:
            raise click.Abort()

    except Exception as e:
        log_operation_complete(
            logger,
            fetch_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise click.Abort() from e


@cli.command()
@click.option(
    "--projects",
    required=True,
    help="Comma-separated list of project configurations (e.g., 'nextjs,tailwindcss')",
)
@click.option(
    "--out",
    required=True,
    help="Output directory for .mdc files (will create project subdirectories)",
)
@click.option(
    "--workspace",
    default="/tmp/contextor-workspace",
    help="Workspace directory for cloning repositories",
)
@click.option(
    "--keep-workspace/--clean-workspace",
    default=False,
    help="Keep workspace after processing",
)
@click.option("--metrics-output", default="", help="Output path for batch metrics JSON")
def batch_fetch(
    projects: str,
    out: str,
    workspace: str,
    keep_workspace: bool,
    metrics_output: str,
) -> None:
    """Fetch and process documentation from multiple configured projects.

    This command processes multiple projects in sequence, providing
    comprehensive metrics for the entire batch operation.
    """
    from pathlib import Path

    # Parse project list
    project_list = [p.strip() for p in projects.split(",") if p.strip()]
    if not project_list:
        logger.error("No valid projects specified")
        raise click.Abort()

    logger.info(
        f"Starting batch fetch for {len(project_list)} projects", projects=project_list
    )

    # Start batch operation
    batch_context = log_operation(
        logger,
        "contextor_batch_fetch",
        projects=project_list,
        workspace=workspace,
        out=out,
    )

    batch_results = []
    total_processed = 0
    total_written = 0
    total_errors = 0

    try:
        for project_name in project_list:
            logger.info(f"Processing project: {project_name}")

            try:
                # Use subprocess to call the fetch command for each project
                import subprocess

                subprocess.run(
                    [
                        "poetry",
                        "run",
                        "contextor",
                        "fetch",
                        "--project-config",
                        project_name,
                        "--out",
                        out,
                        "--workspace",
                        workspace,
                        "--keep-workspace" if keep_workspace else "--clean-workspace",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Try to read the generated stats
                project_stats_path = (
                    Path(out) / project_name / ".metadata" / "stats.json"
                )
                if project_stats_path.exists():
                    with open(project_stats_path, encoding="utf-8") as f:
                        project_stats = json.load(f)

                    batch_results.append(
                        {
                            "project": project_name,
                            "success": True,
                            "stats": project_stats["summary"],
                            "averages": project_stats["averages"],
                        }
                    )

                    total_processed += project_stats["summary"]["files"]
                    total_written += project_stats["summary"][
                        "files"
                    ]  # Assuming all written for successful projects

                else:
                    batch_results.append(
                        {
                            "project": project_name,
                            "success": True,
                            "stats": None,
                            "error": "Stats file not found",
                        }
                    )

            except subprocess.CalledProcessError as e:
                logger.error(
                    f"Failed to process project {project_name}", error=e.stderr
                )
                batch_results.append(
                    {
                        "project": project_name,
                        "success": False,
                        "error": e.stderr,
                    }
                )
                total_errors += 1

        # Prepare batch metrics
        batch_metrics = {
            "total_projects": len(project_list),
            "successful_projects": len([r for r in batch_results if r["success"]]),
            "failed_projects": len([r for r in batch_results if not r["success"]]),
            "total_processed": total_processed,
            "total_written": total_written,
            "total_errors": total_errors,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "projects": batch_results,
            "workspace": workspace,
            "output": out,
        }

        # Display summary
        click.echo("\n" + "=" * 60)
        click.echo("BATCH PROCESSING SUMMARY")
        click.echo("=" * 60)

        total_tokens = sum(
            r["stats"]["tokens"] for r in batch_results if r["success"] and r["stats"]
        )

        click.echo(f"Projects processed: {len(project_list)}")
        click.echo(f"Successful: {batch_metrics['successful_projects']}")
        click.echo(f"Failed: {batch_metrics['failed_projects']}")
        click.echo(f"Total files: {total_processed}")
        click.echo(f"Total tokens: {total_tokens:,}")

        for result in batch_results:
            status = "✅" if result["success"] else "❌"
            if result["success"] and result["stats"]:
                click.echo(
                    f"{status} {result['project']}: {result['stats']['files']} files, {result['stats']['tokens']:,} tokens"
                )
            else:
                click.echo(
                    f"{status} {result['project']}: {result.get('error', 'Unknown error')}"
                )

        # Write batch metrics if requested
        if metrics_output:
            metrics_path = Path(metrics_output)
            try:
                metrics_path.parent.mkdir(parents=True, exist_ok=True)
                with open(metrics_path, "w", encoding="utf-8") as f:
                    json.dump(batch_metrics, f, indent=2)
                logger.info("Batch metrics written", path=metrics_output)
            except Exception as e:
                logger.error(
                    "Failed to write batch metrics", path=metrics_output, error=str(e)
                )

        log_operation_complete(
            logger,
            batch_context,
            success=total_errors == 0,
            total_projects=len(project_list),
            successful_projects=batch_metrics["successful_projects"],
            total_tokens=total_tokens,
        )

        if total_errors > 0:
            raise click.Abort()

    except Exception as e:
        log_operation_complete(
            logger,
            batch_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise click.Abort() from e


@cli.command()
@click.option(
    "--project",
    default="",
    help="Show history for specific project (or all if not specified)",
)
@click.option(
    "--detailed/--summary", default=False, help="Show detailed scan information"
)
def scan_history(project: str, detailed: bool) -> None:
    """Show scan history and metadata for projects."""
    config_manager = ProjectConfigManager()

    if project:
        # Show specific project
        projects_to_show = [project]
        project_cfg = config_manager.load_project_config(project)
        if not project_cfg:
            logger.error("Project configuration not found", project=project)
            raise click.Abort()
    else:
        # Show all projects
        projects_to_show = config_manager.list_available_projects()

    click.echo("\n" + "=" * 60)
    click.echo("PROJECT SCAN HISTORY")
    click.echo("=" * 60)

    for project_name in projects_to_show:
        project_cfg = config_manager.load_project_config(project_name)
        if not project_cfg:
            continue

        metadata = project_cfg.metadata

        click.echo(f"\n📂 **{project_cfg.title}** ({project_name})")
        click.echo(f"   Repository: {project_cfg.repo_url}")

        if metadata.get("last_scanned_at"):
            last_scan = metadata["last_scan_stats"]
            click.echo(f"   Last scanned: {metadata['last_scanned_at']}")
            click.echo(f"   Duration: {metadata.get('last_scan_duration', 0):.1f}s")
            click.echo(
                f"   Files: {last_scan.get('files', 0):,} | Tokens: {last_scan.get('tokens', 0):,}"
            )
            click.echo(
                f"   Branch: {metadata.get('last_scan_source', {}).get('branch', 'unknown')}"
            )

            if detailed and metadata.get("scan_history"):
                click.echo(
                    f"\n   📊 Scan History ({len(metadata['scan_history'])} entries):"
                )
                for i, scan in enumerate(
                    metadata["scan_history"][-5:], 1
                ):  # Show last 5
                    status = "✅" if scan.get("success", False) else "❌"
                    click.echo(
                        f"      {i}. {scan.get('timestamp', 'Unknown')} - "
                        f"{scan.get('files', 0)} files, {scan.get('tokens', 0):,} tokens "
                        f"({scan.get('duration', 0):.1f}s) {status}"
                    )
        else:
            click.echo("   ⚠️  Never scanned")

    click.echo()


@cli.command()
def list_projects() -> None:
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
    src: str,
    out: str,
    repo: str,
    ref: str,
    topics: str,
    profile: str,
    project_config: str,
    auto_detect_config: bool,
    metrics_output: str,
) -> None:
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
        if profile == "balanced" and project_cfg.profile:
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

    # Import logging functions at the top level to avoid UnboundLocalError
    from .logging_config import log_file_operation

    try:
        for doc_info in loader.discover_files():
            # Start file processing with structured logging

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

    # Finalize statistics from emitter
    final_stats = emitter.finalize_stats()

    # Prepare enhanced metrics with token analysis
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
        "token_analysis": final_stats,
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

    # Clean up old metadata directories and files if they exist
    old_metadata_dir = out_path / ".metadata"
    if old_metadata_dir.exists():
        try:
            import shutil

            shutil.rmtree(old_metadata_dir)
            logger.info("Cleaned up old .metadata directory", path=old_metadata_dir)
        except Exception as e:
            logger.warning(
                "Failed to clean up old .metadata directory",
                path=old_metadata_dir,
                error=str(e),
            )

    old_metrics_path = out_path.parent / f"{out_path.name}-metrics.json"
    if old_metrics_path.exists():
        try:
            old_metrics_path.unlink()
            logger.info("Cleaned up old metrics file", path=old_metrics_path)
        except Exception as e:
            logger.warning(
                "Failed to clean up old metrics file",
                path=old_metrics_path,
                error=str(e),
            )

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
def intelligence(
    source_dir: str, features: str, config: str, incremental: bool, metrics_output: str
) -> None:
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
    analysis_config: dict[str, Any] = {}
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
def benchmark(
    budget: int, output: str, test_data_path: str, keep_test_data: bool
) -> None:
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


@cli.command()
@click.option(
    "--source-dir", required=True, help="Directory containing .mdc files to analyze"
)
@click.option(
    "--detailed/--summary",
    default=False,
    help="Show detailed per-file statistics",
)
@click.option("--output", default="", help="Output path for token analysis JSON")
def tokens(source_dir: str, detailed: bool, output: str) -> None:
    """Analyze token counts for .mdc files.

    This command analyzes token counts for all .mdc files in a directory,
    providing statistics useful for LLM context management.
    """
    from pathlib import Path

    source_path = Path(source_dir)

    # Validate source directory exists
    if not source_path.exists() or not source_path.is_dir():
        logger.error(
            "Source directory does not exist or is not a directory",
            source_dir=source_dir,
        )
        raise click.Abort()

    # Find all .mdc files
    mdc_files = list(source_path.rglob("*.mdc"))
    if not mdc_files:
        logger.error("No .mdc files found in source directory", source_dir=source_dir)
        raise click.Abort()

    logger.info(f"Analyzing {len(mdc_files)} .mdc files...")

    # Start token analysis with structured logging
    analysis_context = log_operation(
        logger,
        "token_analysis",
        source_dir=source_dir,
        detailed=detailed,
        mdc_files_count=len(mdc_files),
    )

    total_stats = {
        "files": 0,
        "lines": 0,
        "words": 0,
        "characters": 0,
        "tokens": 0,
        "tokens_estimated_words": 0,
        "tokens_estimated_chars": 0,
        "code_blocks": 0,
        "inline_code": 0,
        "links": 0,
        "headings": 0,
        "size_bytes": 0,
    }

    file_stats = []

    try:
        for file_path in mdc_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                stats = get_content_stats(content)

                # Add file info
                stats["file"] = str(file_path.relative_to(source_path))
                stats["size_bytes"] = file_path.stat().st_size

                # Accumulate totals
                total_stats["files"] += 1
                for key in [
                    "lines",
                    "words",
                    "characters",
                    "tokens",
                    "tokens_estimated_words",
                    "tokens_estimated_chars",
                    "code_blocks",
                    "inline_code",
                    "links",
                    "headings",
                    "size_bytes",
                ]:
                    total_stats[key] += stats.get(key, 0)

                if detailed:
                    file_stats.append(stats)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        # Calculate averages
        if total_stats["files"] > 0:
            avg_stats = {
                "tokens_per_file": total_stats["tokens"] / total_stats["files"],
                "words_per_file": total_stats["words"] / total_stats["files"],
                "lines_per_file": total_stats["lines"] / total_stats["files"],
                "chars_per_file": total_stats["characters"] / total_stats["files"],
                "size_per_file": total_stats["size_bytes"] / total_stats["files"],
            }
        else:
            avg_stats = {}

        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("TOKEN ANALYSIS SUMMARY")
        click.echo("=" * 60)

        click.echo(f"Files analyzed: {format_number(total_stats['files'])}")
        click.echo(f"Total size: {format_size(total_stats['size_bytes'])}")
        click.echo(f"Total lines: {format_number(total_stats['lines'])}")
        click.echo(f"Total words: {format_number(total_stats['words'])}")
        click.echo(f"Total characters: {format_number(total_stats['characters'])}")
        click.echo()
        click.echo(f"🎯 TOTAL TOKENS: {format_number(total_stats['tokens'])}")
        click.echo(
            f"   Est. from words: {format_number(total_stats['tokens_estimated_words'])}"
        )
        click.echo(
            f"   Est. from chars: {format_number(total_stats['tokens_estimated_chars'])}"
        )
        click.echo()
        click.echo("Content breakdown:")
        click.echo(f"  Code blocks: {format_number(total_stats['code_blocks'])}")
        click.echo(f"  Inline code: {format_number(total_stats['inline_code'])}")
        click.echo(f"  Links: {format_number(total_stats['links'])}")
        click.echo(f"  Headings: {format_number(total_stats['headings'])}")

        if avg_stats:
            click.echo()
            click.echo("Averages per file:")
            click.echo(f"  Tokens: {avg_stats['tokens_per_file']:.1f}")
            click.echo(f"  Words: {avg_stats['words_per_file']:.1f}")
            click.echo(f"  Lines: {avg_stats['lines_per_file']:.1f}")
            click.echo(f"  Size: {format_size(int(avg_stats['size_per_file']))}")

        if detailed:
            click.echo("\n" + "-" * 60)
            click.echo("DETAILED FILE STATISTICS")
            click.echo("-" * 60)

            # Sort by token count descending
            file_stats.sort(key=lambda x: x["tokens"], reverse=True)

            for stats in file_stats[:10]:  # Show top 10
                click.echo(f"\n📄 {stats['file']}")
                click.echo(
                    f"   Tokens: {format_number(stats['tokens'])} | "
                    f"Words: {format_number(stats['words'])} | "
                    f"Lines: {format_number(stats['lines'])} | "
                    f"Size: {format_size(stats['size_bytes'])}"
                )

            if len(file_stats) > 10:
                click.echo(f"\n... and {len(file_stats) - 10} more files")

        # Prepare results for JSON output
        results = {
            "summary": total_stats,
            "averages": avg_stats,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if detailed:
            results["files"] = file_stats

        # Save results if requested
        if output:
            output_path = Path(output)
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                logger.info("Token analysis results written", path=output)
            except Exception as e:
                logger.error("Failed to write results", path=output, error=str(e))

        log_operation_complete(
            logger,
            analysis_context,
            success=True,
            files_analyzed=total_stats["files"],
            total_tokens=total_stats["tokens"],
            avg_tokens_per_file=avg_stats.get("tokens_per_file", 0),
        )

    except Exception as e:
        log_operation_complete(
            logger,
            analysis_context,
            success=False,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise click.Abort() from e


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()

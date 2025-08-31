"""Performance benchmarking utilities for Contextor."""

import json
import tempfile
import time
from pathlib import Path
from typing import Any

from .logging_config import get_logger, log_operation, log_operation_complete

logger = get_logger(__name__)


class PerformanceBenchmark:
    """Performance benchmarking for Contextor operations."""

    def __init__(self, budget_seconds: int = 900):
        """Initialize benchmark with performance budget.

        Args:
            budget_seconds: Maximum allowed time in seconds (default: 15 minutes)
        """
        self.budget_seconds = budget_seconds
        self.results: list[dict[str, Any]] = []

    def create_test_dataset(
        self, size: str, base_path: Path, file_count: int, lines_per_file: int
    ) -> Path:
        """Create a test dataset of specified size.

        Args:
            size: Dataset size name (small, medium, large)
            base_path: Base directory for test data
            file_count: Number of files to create
            lines_per_file: Number of content lines per file

        Returns:
            Path to created dataset directory
        """
        dataset_path = base_path / size
        dataset_path.mkdir(parents=True, exist_ok=True)

        context = log_operation(
            logger,
            "create_test_dataset",
            size=size,
            file_count=file_count,
            lines_per_file=lines_per_file,
            dataset_path=str(dataset_path),
        )

        try:
            for i in range(1, file_count + 1):
                file_path = dataset_path / f"doc-{i:03d}.md"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# Test Document {i}\n\n")
                    f.write(f"This is test content for document {i}.\n\n")
                    f.write("## Overview\n\n")
                    f.write(
                        "This document contains sample content for performance testing.\n\n"
                    )

                    # Add variable content to make files realistic
                    sections = [
                        "Getting Started",
                        "Configuration",
                        "API Reference",
                        "Examples",
                    ]
                    for _, section in enumerate(sections):
                        f.write(f"## {section}\n\n")
                        for line_num in range(lines_per_file // len(sections)):
                            f.write(
                                f"Line {line_num + 1} in {section} section with content to make the file larger. "
                            )
                            f.write(
                                "This simulates real documentation with varying content lengths.\n"
                            )
                        f.write("\n")

                    # Add some code blocks for realism
                    f.write("## Code Examples\n\n")
                    f.write("```python\n")
                    f.write("def example_function():\n")
                    f.write('    """Example function for testing."""\n')
                    f.write("    return 'Hello, World!'\n")
                    f.write("```\n\n")

                    f.write("```javascript\n")
                    f.write("function exampleFunction() {\n")
                    f.write("  // Example function for testing\n")
                    f.write("  return 'Hello, World!';\n")
                    f.write("}\n")
                    f.write("```\n")

            # Calculate total size
            total_size = sum(f.stat().st_size for f in dataset_path.rglob("*.md"))

            log_operation_complete(
                logger,
                context,
                success=True,
                total_files=file_count,
                total_size_bytes=total_size,
                total_size_mb=round(total_size / 1024 / 1024, 2),
            )

            return dataset_path

        except Exception as e:
            log_operation_complete(
                logger,
                context,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def benchmark_optimize(
        self,
        src_path: Path,
        dataset_name: str,
        repo: str = "test/repo",
        ref: str = "main",
    ) -> dict[str, Any]:
        """Benchmark the optimize operation.

        Args:
            src_path: Source directory to optimize
            dataset_name: Name of the dataset being benchmarked
            repo: Repository identifier
            ref: Git reference

        Returns:
            Benchmark results dictionary
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "output"
            # metrics_path = Path(temp_dir) / "metrics.json"  # unused for now

            context = log_operation(
                logger,
                "benchmark_optimize",
                dataset=dataset_name,
                src_path=str(src_path),
                out_path=str(out_path),
            )

            try:
                # Import here to avoid circular imports
                from .emit import MDCEmitter
                from .loader import DocumentLoader
                from .transforms import apply_transforms

                start_time = time.time()

                # Initialize components
                loader = DocumentLoader(src_path, repo=repo, ref=ref)
                emitter = MDCEmitter(out_path)

                # Process files
                processed = 0
                written = 0
                skipped = 0
                errors = 0

                for doc_info in loader.discover_files():
                    try:
                        # Apply transforms
                        transformed_content = apply_transforms(
                            doc_info.content,
                            profile="balanced",
                            source_path=doc_info.path,
                        )

                        # Emit .mdc file
                        was_written = emitter.emit_mdc(
                            content=transformed_content,
                            metadata={
                                "repo": repo,
                                "ref": ref,
                                "path": doc_info.path,
                                "url": doc_info.canonical_url or "",
                                "title": doc_info.title,
                                "topics": [],
                            },
                        )

                        processed += 1
                        if was_written:
                            written += 1
                        else:
                            skipped += 1

                    except Exception as e:
                        logger.warning(
                            "Failed to process file during benchmark",
                            path=doc_info.path,
                            error=str(e),
                        )
                        errors += 1

                end_time = time.time()
                duration = end_time - start_time

                # Calculate file statistics
                input_files = list(src_path.rglob("*.md")) + list(
                    src_path.rglob("*.mdx")
                )
                total_input_size = sum(f.stat().st_size for f in input_files)

                output_files = (
                    list(out_path.rglob("*.mdc")) if out_path.exists() else []
                )
                total_output_size = sum(f.stat().st_size for f in output_files)

                result = {
                    "dataset": dataset_name,
                    "duration_seconds": round(duration, 3),
                    "processed": processed,
                    "written": written,
                    "skipped": skipped,
                    "errors": errors,
                    "input_files": len(input_files),
                    "output_files": len(output_files),
                    "input_size_bytes": total_input_size,
                    "output_size_bytes": total_output_size,
                    "input_size_mb": round(total_input_size / 1024 / 1024, 2),
                    "output_size_mb": round(total_output_size / 1024 / 1024, 2),
                    "compression_ratio": round(total_output_size / total_input_size, 3)
                    if total_input_size > 0
                    else 0,
                    "files_per_second": round(processed / duration, 2)
                    if duration > 0
                    else 0,
                    "mb_per_second": round(
                        (total_input_size / 1024 / 1024) / duration, 2
                    )
                    if duration > 0
                    else 0,
                    "budget_seconds": self.budget_seconds,
                    "within_budget": duration <= self.budget_seconds,
                }

                log_operation_complete(
                    logger,
                    context,
                    success=errors == 0,
                    **result,
                )

                self.results.append(result)
                return result

            except Exception as e:
                log_operation_complete(
                    logger,
                    context,
                    success=False,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

    def run_full_benchmark(
        self, base_path: Path | None = None, cleanup: bool = True
    ) -> list[dict[str, Any]]:
        """Run a full performance benchmark with multiple dataset sizes.

        Args:
            base_path: Base directory for test data (uses temp dir if None)
            cleanup: Whether to clean up test data after benchmarking

        Returns:
            List of benchmark results
        """
        if base_path is None:
            temp_dir = tempfile.mkdtemp(prefix="contextor-benchmark-")
            base_path = Path(temp_dir)
            cleanup = True
        else:
            base_path = Path(base_path)
            base_path.mkdir(parents=True, exist_ok=True)

        context = log_operation(
            logger,
            "full_benchmark",
            base_path=str(base_path),
            budget_seconds=self.budget_seconds,
        )

        try:
            datasets = [
                ("small", 50, 20),  # 50 files, ~1MB total
                ("medium", 200, 50),  # 200 files, ~5MB total
                ("large", 500, 75),  # 500 files, ~15MB total
            ]

            results = []

            for dataset_name, file_count, lines_per_file in datasets:
                logger.info(
                    "Creating test dataset",
                    dataset=dataset_name,
                    files=file_count,
                    lines_per_file=lines_per_file,
                )

                dataset_path = self.create_test_dataset(
                    dataset_name,
                    base_path,
                    file_count,
                    lines_per_file,
                )

                logger.info(
                    "Running benchmark",
                    dataset=dataset_name,
                    path=str(dataset_path),
                )

                result = self.benchmark_optimize(dataset_path, dataset_name)
                results.append(result)

                # Log result summary
                status = "✅ PASS" if result["within_budget"] else "❌ FAIL"
                logger.info(
                    "Benchmark completed",
                    dataset=dataset_name,
                    duration=f"{result['duration_seconds']}s",
                    budget=f"{self.budget_seconds}s",
                    status=status,
                    files_per_second=result["files_per_second"],
                    mb_per_second=result["mb_per_second"],
                )

            # Overall summary
            total_duration = sum(r["duration_seconds"] for r in results)
            budget_failures = [r for r in results if not r["within_budget"]]

            log_operation_complete(
                logger,
                context,
                success=len(budget_failures) == 0,
                total_duration=round(total_duration, 3),
                datasets=len(results),
                budget_failures=len(budget_failures),
                results=results,
            )

            return results

        except Exception as e:
            log_operation_complete(
                logger,
                context,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        finally:
            if cleanup and base_path.exists():
                import shutil

                shutil.rmtree(base_path, ignore_errors=True)

    def save_results(self, output_path: Path) -> None:
        """Save benchmark results to JSON file.

        Args:
            output_path: Path to save results
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "benchmark_results": self.results,
                    "budget_seconds": self.budget_seconds,
                    "summary": self._generate_summary(),
                },
                f,
                indent=2,
            )

        logger.info("Benchmark results saved", path=str(output_path))

    def _generate_summary(self) -> dict[str, Any]:
        """Generate a summary of benchmark results."""
        if not self.results:
            return {}

        total_duration = sum(r["duration_seconds"] for r in self.results)
        budget_failures = [r for r in self.results if not r["within_budget"]]

        return {
            "total_datasets": len(self.results),
            "total_duration_seconds": round(total_duration, 3),
            "budget_failures": len(budget_failures),
            "within_budget": len(budget_failures) == 0,
            "average_files_per_second": round(
                sum(r["files_per_second"] for r in self.results) / len(self.results), 2
            ),
            "average_mb_per_second": round(
                sum(r["mb_per_second"] for r in self.results) / len(self.results), 2
            ),
        }

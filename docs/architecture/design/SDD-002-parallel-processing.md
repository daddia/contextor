# Parallel Processing - Solution Design Document & Implementation Plan

## 1. Architecture Changes Required

#### A. Async/Await Pipeline (Quick Win - 1-2 weeks)

**Files to Modify:**
- `contextor/__main__.py` - Main processing loop
- `contextor/loader.py` - Async file discovery
- `contextor/transforms/__init__.py` - Async transform pipeline
- `contextor/emit.py` - Async file emission

**Implementation:**

```python
# contextor/transforms/__init__.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

async def apply_transforms_async(
    content: str,
    profile: str = "balanced",
    source_path: str = "",
    executor: ThreadPoolExecutor = None,
) -> str:
    """Apply transformation pipeline with parallel processing."""

    # Phase 1: Clean MDX (CPU intensive)
    content = await asyncio.get_event_loop().run_in_executor(
        executor, clean_mdx, content
    )

    # Phase 2: Normalize Markdown (CPU intensive)
    content = await asyncio.get_event_loop().run_in_executor(
        executor, normalize_markdown, content
    )

    # Phase 3: Fix links (I/O light)
    content = fix_links(content, source_path)

    # Phase 4: Size optimization (CPU intensive)
    if profile in ["balanced", "compact"]:
        content = await asyncio.get_event_loop().run_in_executor(
            executor, compress_content, content, profile == "compact"
        )

    return content

async def process_documents_parallel(
    documents: List[DocumentInfo],
    profile: str,
    emitter: MDCEmitter,
    max_workers: int = None,
) -> Tuple[int, int, int, int]:
    """Process multiple documents in parallel."""

    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) + 4)

    semaphore = asyncio.Semaphore(max_workers)

    async def process_single_document(doc_info: DocumentInfo) -> dict:
        async with semaphore:
            try:
                # Transform content
                transformed_content = await apply_transforms_async(
                    doc_info.content,
                    profile=profile,
                    source_path=doc_info.path,
                )

                # Emit file (I/O operation)
                was_written = await emitter.emit_mdc_async(
                    content=transformed_content,
                    metadata={...}
                )

                return {
                    "status": "success",
                    "written": was_written,
                    "path": doc_info.path,
                    "content_length": len(transformed_content)
                }

            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "path": doc_info.path
                }

    # Process all documents concurrently
    tasks = [process_single_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate results
    processed = len(results)
    written = sum(1 for r in results if r.get("written"))
    skipped = sum(1 for r in results if r.get("status") == "success" and not r.get("written"))
    errors = sum(1 for r in results if r.get("status") == "error")

    return processed, written, skipped, errors
```

#### B. Batch Processing with Memory Management (2-3 weeks)

**New Files to Create:**
- `contextor/parallel.py` - Parallel processing coordinator
- `contextor/batch.py` - Batch processing utilities

```python
# contextor/parallel.py
import asyncio
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

@dataclass
class ProcessingConfig:
    max_workers: Optional[int] = None
    batch_size: int = 50
    memory_limit_mb: int = 512
    use_process_pool: bool = False

class ParallelProcessor:
    """Manages parallel document processing with memory constraints."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.max_workers = config.max_workers or min(32, (os.cpu_count() or 1) + 4)

    async def process_documents_in_batches(
        self,
        document_iterator: Iterator[DocumentInfo],
        profile: str,
        emitter: MDCEmitter,
    ) -> dict:
        """Process documents in memory-efficient batches."""

        total_processed = 0
        total_written = 0
        total_skipped = 0
        total_errors = 0

        if self.config.use_process_pool:
            executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            executor = ThreadPoolExecutor(max_workers=self.max_workers)

        try:
            async for batch in self._create_batches(document_iterator):
                batch_results = await self._process_batch(
                    batch, profile, emitter, executor
                )

                total_processed += batch_results["processed"]
                total_written += batch_results["written"]
                total_skipped += batch_results["skipped"]
                total_errors += batch_results["errors"]

                # Memory cleanup between batches
                await asyncio.sleep(0.1)

        finally:
            executor.shutdown(wait=True)

        return {
            "processed": total_processed,
            "written": total_written,
            "skipped": total_skipped,
            "errors": total_errors
        }

    async def _create_batches(
        self,
        document_iterator: Iterator[DocumentInfo]
    ) -> Iterator[List[DocumentInfo]]:
        """Create memory-efficient batches of documents."""
        batch = []
        current_memory_mb = 0

        for doc_info in document_iterator:
            doc_size_mb = len(doc_info.content) / (1024 * 1024)

            if (len(batch) >= self.config.batch_size or
                current_memory_mb + doc_size_mb > self.config.memory_limit_mb):

                if batch:  # Yield current batch
                    yield batch
                    batch = []
                    current_memory_mb = 0

            batch.append(doc_info)
            current_memory_mb += doc_size_mb

        if batch:  # Yield final batch
            yield batch
```

#### C. Process Pool for CPU-Intensive Operations (3-4 weeks)

**Enhanced Transform Pipeline:**

```python
# contextor/transforms/parallel.py
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from typing import List, Tuple

def transform_document_worker(
    doc_data: Tuple[str, str, str]  # content, profile, source_path
) -> Tuple[str, bool, Optional[str]]:  # transformed_content, success, error
    """Worker function for process pool transformation."""
    try:
        content, profile, source_path = doc_data

        # Import here to avoid pickle issues
        from . import apply_transforms

        transformed = apply_transforms(content, profile, source_path)
        return transformed, True, None

    except Exception as e:
        return "", False, str(e)

class ParallelTransformPipeline:
    """CPU-intensive transform operations using process pools."""

    def __init__(self, max_processes: Optional[int] = None):
        self.max_processes = max_processes or max(1, mp.cpu_count() - 1)

    def transform_batch(
        self,
        documents: List[DocumentInfo],
        profile: str
    ) -> List[Tuple[str, bool, Optional[str]]]:
        """Transform a batch of documents using process pool."""

        # Prepare data for worker processes
        doc_data = [
            (doc.content, profile, doc.path)
            for doc in documents
        ]

        with ProcessPoolExecutor(max_workers=self.max_processes) as executor:
            results = list(executor.map(transform_document_worker, doc_data))

        return results
```

### 2. Configuration Changes

#### A. Performance Configuration (pyproject.toml)

```toml
[tool.contextor.performance]
# Parallel processing settings
max_workers = "auto"  # auto, or specific number
batch_size = 50
memory_limit_mb = 512
use_process_pool = false  # true for CPU-intensive workloads

# Transform-specific settings
[tool.contextor.transforms]
parallel_transforms = true
cpu_intensive_threshold = 1048576  # 1MB - use process pool above this size
```

#### B. CLI Options Enhancement

```python
# contextor/__main__.py additions
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Enable parallel processing (default: enabled)"
)
@click.option(
    "--max-workers",
    type=int,
    default=None,
    help="Maximum number of worker threads/processes"
)
@click.option(
    "--batch-size",
    type=int,
    default=50,
    help="Number of documents to process in each batch"
)
@click.option(
    "--memory-limit",
    type=int,
    default=512,
    help="Memory limit per batch in MB"
)
```

### 3. Expected Performance Improvements

#### Current Performance (Sequential):
- **Small dataset (50 files)**: ~10-15 seconds
- **Medium dataset (200 files)**: ~45-60 seconds
- **Large dataset (500 files)**: ~120-180 seconds

#### Expected Performance (Parallel):
- **Small dataset**: ~3-5 seconds (**70% improvement**)
- **Medium dataset**: ~12-18 seconds (**75% improvement**)
- **Large dataset**: ~30-50 seconds (**75% improvement**)

### 4. Implementation Timeline

#### Phase 1: Async Pipeline (Week 1-2)
- [ ] Convert `apply_transforms` to async
- [ ] Implement `process_documents_parallel`
- [ ] Add async file I/O operations
- [ ] Update CLI to use async processing

#### Phase 2: Batch Processing (Week 3-4)
- [ ] Implement `ParallelProcessor` class
- [ ] Add memory management and batching
- [ ] Create configuration system
- [ ] Add performance monitoring

#### Phase 3: Process Pool Optimization (Week 5-6)
- [ ] Implement `ParallelTransformPipeline`
- [ ] Add CPU-intensive operation detection
- [ ] Optimize for large file processing
- [ ] Add fallback mechanisms

#### Phase 4: Testing & Optimization (Week 7-8)
- [ ] Performance benchmarking and tuning
- [ ] Memory usage optimization
- [ ] Error handling and recovery
- [ ] Documentation and examples

### 5. Testing Strategy

#### A. Performance Tests
```python
# tests/test_parallel_performance.py
import pytest
from contextor.parallel import ParallelProcessor, ProcessingConfig

@pytest.mark.performance
def test_parallel_vs_sequential_performance():
    """Compare parallel vs sequential processing performance."""
    # Test with different dataset sizes
    # Measure processing time and memory usage
    # Assert minimum performance improvement thresholds

@pytest.mark.memory
def test_memory_usage_batching():
    """Ensure memory usage stays within limits."""
    # Process large datasets with memory constraints
    # Monitor memory usage throughout processing
    # Assert memory limits are respected
```

#### B. Integration Tests
```python
# tests/test_parallel_integration.py
def test_parallel_output_consistency():
    """Ensure parallel processing produces identical results."""
    # Process same dataset sequentially and in parallel
    # Compare output files and content hashes
    # Assert identical results
```

### 6. Monitoring and Observability

#### A. Performance Metrics
```python
# Add to existing logging
logger.info(
    "Parallel processing complete",
    parallel_enabled=True,
    max_workers=max_workers,
    batch_size=batch_size,
    total_batches=batch_count,
    avg_batch_time=avg_batch_time,
    cpu_utilization=cpu_percent,
    memory_peak_mb=memory_peak,
    speedup_factor=sequential_time / parallel_time
)
```

### 7. Backward Compatibility

- **Default behavior**: Parallel processing enabled by default
- **Fallback mode**: Automatic fallback to sequential processing on errors
- **CLI compatibility**: All existing CLI options continue to work
- **Configuration**: Optional performance configuration, sensible defaults

This implementation provides **significant performance improvements** (70-75% faster processing) while maintaining code quality, error handling, and backward compatibility. The phased approach allows for incremental deployment and testing.

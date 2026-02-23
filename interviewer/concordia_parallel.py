from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Sequence, TypeVar, cast

T = TypeVar("T")
R = TypeVar("R")


def resolve_worker_count(
    num_jobs: int,
    requested_workers: int | None,
    *,
    default_workers: int = 4,
) -> int:
    """Resolve an effective worker count for simulation batches."""
    if num_jobs <= 1:
        return 1

    if requested_workers is None:
        candidate = default_workers
    else:
        candidate = requested_workers

    if candidate <= 0:
        candidate = default_workers

    return max(1, min(num_jobs, candidate))


def parallel_map_ordered(
    items: Sequence[T],
    worker: Callable[[T], R],
    *,
    max_workers: int,
    label: str = "parallel jobs",
) -> list[R]:
    """Run jobs in a thread pool and return results in input order."""
    if not items:
        return []

    if max_workers <= 1 or len(items) == 1:
        return [worker(item) for item in items]

    results: list[R | None] = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(worker, item): idx for idx, item in enumerate(items)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as exc:  # pragma: no cover - depends on worker failures
                raise RuntimeError(
                    f"{label}: job {idx + 1}/{len(items)} failed"
                ) from exc

    return cast(list[R], results)

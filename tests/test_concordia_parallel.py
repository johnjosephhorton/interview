from __future__ import annotations

import pytest

from interviewer.concordia_parallel import parallel_map_ordered, resolve_worker_count


def test_resolve_worker_count_bounds():
    assert resolve_worker_count(1, 8) == 1
    assert resolve_worker_count(10, None, default_workers=4) == 4
    assert resolve_worker_count(3, 10) == 3
    assert resolve_worker_count(5, 0, default_workers=2) == 2


def test_parallel_map_keeps_input_order():
    items = [5, 4, 3, 2, 1]
    out = parallel_map_ordered(items, lambda x: x * x, max_workers=3, label="test")
    assert out == [25, 16, 9, 4, 1]


def test_parallel_map_wraps_worker_failure():
    items = [0, 1, 2]

    def _worker(x: int) -> int:
        if x == 1:
            raise ValueError("boom")
        return x

    with pytest.raises(RuntimeError):
        parallel_map_ordered(items, _worker, max_workers=2, label="failing test")

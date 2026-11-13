from __future__ import annotations

from suppression.queue import QueueRequest, QueueServer, simulate_queue


def test_two_servers_parallelize_arrivals() -> None:
    result = simulate_queue(
        [QueueRequest("a", 0, 10), QueueRequest("b", 0, 10), QueueRequest("c", 0, 10)],
        [QueueServer("one", 0, 100), QueueServer("two", 0, 100)],
    )
    assert len(result.assignments) == 3
    assert result.assignments[2].wait_min == 10
    assert result.assignments[2].start_min == 10


def test_priority_preempts_fifo_order() -> None:
    result = simulate_queue(
        [
            QueueRequest("low", 0, 10, priority=0),
            QueueRequest("high", 1, 5, priority=10),
        ],
        [QueueServer("one", 0, 100)],
    )
    assert result.assignments[0].request_id == "high"
    assert result.assignments[0].wait_min == 0
    assert result.assignments[1].request_id == "low"


def test_unserved_when_window_too_short() -> None:
    result = simulate_queue(
        [QueueRequest("late", 10, 10)],
        [QueueServer("one", 0, 15)],
    )
    assert result.unserved == ("late",)
    assert result.assignments == ()


def test_utilization_is_busy_over_available() -> None:
    result = simulate_queue(
        [QueueRequest("a", 0, 10)],
        [QueueServer("one", 0, 20)],
    )
    assert result.utilization["one"] == 0.5


def test_invalid_inputs() -> None:
    import pytest

    with pytest.raises(ValueError):
        QueueServer("bad", 10, 0)
    with pytest.raises(ValueError):
        QueueRequest("bad", -1, 5)
    with pytest.raises(ValueError):
        simulate_queue([], [])

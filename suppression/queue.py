"""Deterministic non-preemptive queue for suppression resources.

This is a small discrete-event feasibility model inspired by Bookbinder and
Martell's time-dependent helitack queue. It does not model random arrivals or
service distributions; it schedules the requests it is given.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QueueServer:
    """One resource available over a time window."""

    id: str
    available_start_min: float
    available_end_min: float

    def __post_init__(self) -> None:
        if self.available_end_min < self.available_start_min:
            raise ValueError("server availability end must be >= start")


@dataclass(frozen=True)
class QueueRequest:
    """One request waiting for a server."""

    id: str
    arrival_min: float
    service_min: float
    priority: int = 0

    def __post_init__(self) -> None:
        if self.arrival_min < 0.0:
            raise ValueError("arrival_min must be non-negative")
        if self.service_min <= 0.0:
            raise ValueError("service_min must be positive")


@dataclass(frozen=True)
class QueueAssignment:
    request_id: str
    server_id: str
    wait_min: float
    start_min: float
    end_min: float

    def to_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "server_id": self.server_id,
            "wait_min": self.wait_min,
            "start_min": self.start_min,
            "end_min": self.end_min,
        }


@dataclass(frozen=True)
class QueueResult:
    assignments: tuple[QueueAssignment, ...]
    unserved: tuple[str, ...]
    utilization: dict[str, float]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "assignments": [assignment.to_dict() for assignment in self.assignments],
            "unserved": list(self.unserved),
            "utilization": dict(self.utilization),
            "warnings": list(self.warnings),
        }


def simulate_queue(
    requests: tuple[QueueRequest, ...] | list[QueueRequest],
    servers: tuple[QueueServer, ...] | list[QueueServer],
) -> QueueResult:
    """Assign requests to the earliest available eligible server.

    Requests are ordered by descending priority and then arrival time. Ties are
    broken by request id. A request is unserved when no server can finish it
    within its availability window.
    """
    if not servers:
        raise ValueError("at least one server is required")
    server_ready = {server.id: server.available_start_min for server in servers}
    busy: dict[str, float] = {server.id: 0.0 for server in servers}
    assignments: list[QueueAssignment] = []
    unserved: list[str] = []
    warnings: list[str] = []
    ordered = sorted(requests, key=lambda item: (-item.priority, item.arrival_min, item.id))
    for request in ordered:
        candidates = []
        for server in servers:
            start = max(request.arrival_min, server_ready[server.id])
            end = start + request.service_min
            if end <= server.available_end_min + 1e-9:
                candidates.append((start, server.id, end))
        if not candidates:
            unserved.append(request.id)
            warnings.append(f"request {request.id} could not be served within availability")
            continue
        start, server_id, end = min(candidates, key=lambda item: (item[0], item[1]))
        assignments.append(
            QueueAssignment(
                request_id=request.id,
                server_id=server_id,
                wait_min=max(0.0, start - request.arrival_min),
                start_min=start,
                end_min=end,
            )
        )
        server_ready[server_id] = end
        busy[server_id] += request.service_min
    utilization = {
        server.id: (
            busy[server.id] / (server.available_end_min - server.available_start_min)
            if server.available_end_min > server.available_start_min
            else 0.0
        )
        for server in servers
    }
    return QueueResult(
        assignments=tuple(assignments),
        unserved=tuple(unserved),
        utilization=utilization,
        warnings=tuple(warnings),
    )


__all__ = [
    "QueueAssignment",
    "QueueRequest",
    "QueueResult",
    "QueueServer",
    "simulate_queue",
]

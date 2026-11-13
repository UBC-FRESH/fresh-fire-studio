"""Deterministic suppression dispatch and task-timing prototype.

This is a feasibility calculator, not an optimizer. It follows the resource and
task order in a P179 scenario, applies Euclidean travel, and derives line
construction service time from the resource's line-production rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

from .models import Base, Line, Resource, Scenario, Task


class DispatchError(RuntimeError):
    """Raised when a scenario cannot be scheduled."""


def _distance_m(first: tuple[float, float], second: tuple[float, float]) -> float:
    return hypot(second[0] - first[0], second[1] - first[1])


def _line_length_m(points: list[tuple[float, float]]) -> float:
    return sum(
        _distance_m(first, second)
        for first, second in zip(points, points[1:])
    )


@dataclass(frozen=True)
class Assignment:
    """One derived task timing for one resource."""

    task_id: str
    resource_id: str
    requested_start_min: float
    actual_start_min: float
    actual_end_min: float
    travel_min: float
    service_min: float
    delay_min: float
    late: bool
    line_id: str | None = None
    drop_id: str | None = None
    line_length_m: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "resource_id": self.resource_id,
            "requested_start_min": self.requested_start_min,
            "actual_start_min": self.actual_start_min,
            "actual_end_min": self.actual_end_min,
            "travel_min": self.travel_min,
            "service_min": self.service_min,
            "delay_min": self.delay_min,
            "late": self.late,
            "line_id": self.line_id,
            "drop_id": self.drop_id,
            "line_length_m": self.line_length_m,
        }


@dataclass(frozen=True)
class DispatchResult:
    """Derived assignments and resource-level diagnostics."""

    assignments: tuple[Assignment, ...]
    utilization: dict[str, float] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "assignments": [assignment.to_dict() for assignment in self.assignments],
            "utilization": dict(self.utilization),
            "warnings": list(self.warnings),
        }


def _service_minutes(task: Task, resource: Resource, line_length_m: float) -> float:
    requested = task.end_min - task.start_min
    if task.kind.value == "construct_line" and line_length_m > 0.0 and resource.line_rate_m_h > 0.0:
        return line_length_m / resource.line_rate_m_h * 60.0
    return requested


def _task_target(task: Task, line_points: list[tuple[float, float]] | None) -> tuple[float, float] | None:
    if line_points:
        return line_points[0]
    if task.target:
        return task.target[0]
    return None


def apply_line_timings(scenario: Scenario, result: DispatchResult) -> Scenario:
    """Return a scenario whose line windows use derived dispatch timings.

    Task windows are left as requested. This is deliberate: a dispatch-derived
    line can finish after the requested task window, and that lateness is part
    of the diagnostic.
    """
    by_line = {assignment.line_id: assignment for assignment in result.assignments if assignment.line_id}
    lines: list[Line] = []
    for line in scenario.lines:
        assignment = by_line.get(line.id)
        if assignment is None:
            lines.append(line)
            continue
        if (
            line.breached_at_min is not None
            and line.breached_at_min < assignment.actual_end_min - 1e-6
        ):
            raise DispatchError(
                f"line {line.id} would breach before dispatch-derived construction ends"
            )
        lines.append(
            line.model_copy(
                update={
                    "constructed_start_min": assignment.actual_start_min,
                    "constructed_end_min": assignment.actual_end_min,
                }
            )
        )
    return scenario.model_copy(update={"lines": lines})


def dispatch_scenario(scenario: Scenario) -> DispatchResult:
    """Schedule the scenario's existing task/resource pairings."""
    bases: dict[str, Base] = {base.id: base for base in scenario.bases}
    resources: dict[str, Resource] = {resource.id: resource for resource in scenario.resources}
    lines = {line.id: line for line in scenario.lines}
    assignments: list[Assignment] = []
    warnings: list[str] = []
    service_by_resource: dict[str, float] = {resource.id: 0.0 for resource in scenario.resources}
    ready_at: dict[str, float] = {
        resource.id: resource.available_start_min for resource in scenario.resources
    }
    location: dict[str, tuple[float, float]] = {
        resource.id: (
            bases[resource.home_base_id].x,
            bases[resource.home_base_id].y,
        )
        for resource in scenario.resources
    }
    by_resource: dict[str, list[Task]] = {resource.id: [] for resource in scenario.resources}
    for task in scenario.tasks:
        by_resource[task.resource_id].append(task)

    for resource_id, tasks in by_resource.items():
        resource = resources[resource_id]
        for task in sorted(tasks, key=lambda item: (item.start_min, item.id)):
            line = lines.get(task.line_id) if task.line_id else None
            line_length = _line_length_m(line.points) if line is not None else 0.0
            target = _task_target(task, line.points if line is not None else None)
            if target is None:
                target = location[resource_id]
                if line_length <= 0.0:
                    warnings.append(f"task {task.id} has no target; travel set to zero")
            distance = _distance_m(location[resource_id], target)
            if resource.speed_kmh > 0.0:
                travel = distance / (resource.speed_kmh * 1000.0 / 60.0)
            else:
                travel = 0.0
                if distance > 0.0:
                    warnings.append(f"resource {resource_id} has no speed; travel set to zero")
            service = _service_minutes(task, resource, line_length)
            actual_start = max(task.start_min, ready_at[resource_id] + travel)
            actual_end = actual_start + service
            delay = max(0.0, actual_start - task.start_min)
            late = actual_end > task.end_min + 1e-6
            if late:
                warnings.append(
                    f"task {task.id} ends at {actual_end:.1f} min, after requested {task.end_min:.1f}"
                )
            if actual_end > resource.available_end_min + 1e-6:
                warnings.append(
                    f"task {task.id} exceeds resource {resource_id} availability"
                )
            assignment = Assignment(
                task_id=task.id,
                resource_id=resource_id,
                requested_start_min=task.start_min,
                actual_start_min=actual_start,
                actual_end_min=actual_end,
                travel_min=travel,
                service_min=service,
                delay_min=delay,
                late=late,
                line_id=task.line_id,
                drop_id=task.drop_id,
                line_length_m=line_length,
            )
            assignments.append(assignment)
            service_by_resource[resource_id] += service
            ready_at[resource_id] = actual_end
            location[resource_id] = target

    utilization = {
        resource_id: (
            service_by_resource[resource_id]
            / (resource.available_end_min - resource.available_start_min)
            if resource.available_end_min > resource.available_start_min
            else 0.0
        )
        for resource_id, resource in resources.items()
    }
    return DispatchResult(
        assignments=tuple(sorted(assignments, key=lambda item: (item.actual_start_min, item.task_id))),
        utilization=utilization,
        warnings=tuple(warnings),
    )


__all__ = [
    "Assignment",
    "DispatchError",
    "DispatchResult",
    "apply_line_timings",
    "dispatch_scenario",
]

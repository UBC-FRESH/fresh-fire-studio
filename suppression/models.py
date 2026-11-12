"""P179.0 suppression/response contract.

This module deliberately contains no 3D or fire-growth code. It defines the
resources, tasks, line/drop effects and validation rules that a later fire
simulation and renderer must share.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ResourceKind(StrEnum):
    IA_CREW = "ia_crew"
    GROUND_CREW = "ground_crew"
    ENGINE = "engine"
    DOZER = "dozer"
    HELICOPTER = "helicopter"
    AIRTANKER = "airtanker"
    WATER_TENDER = "water_tender"
    PUMP = "pump"
    COMMAND = "command"


class TaskKind(StrEnum):
    MOBILIZE = "mobilize"
    TRAVEL = "travel"
    ASSESS = "assess"
    ANCHOR = "anchor"
    CONSTRUCT_LINE = "construct_line"
    LAY_HOSE = "lay_hose"
    SET_PUMP = "set_pump"
    DROP = "drop"
    PATROL = "patrol"
    MOP_UP = "mop_up"
    DEMOBILIZE = "demobilize"


class Suppressant(StrEnum):
    WATER = "water"
    FOAM = "foam"
    RETARDANT = "retardant"


class LineState(StrEnum):
    PLANNED = "planned"
    BUILDING = "building"
    HELD = "held"
    BREACHED = "breached"
    ABANDONED = "abandoned"


Point = tuple[float, float]


class Base(BaseModel):
    id: str = Field(min_length=1)
    label: str = ""
    x: float
    y: float
    kind: Literal["airtanker", "helicopter", "ground", "command"] = "ground"


class WaterSource(BaseModel):
    id: str = Field(min_length=1)
    label: str = ""
    x: float
    y: float
    capacity_l: float | None = Field(default=None, ge=0)
    refill_rate_l_min: float | None = Field(default=None, ge=0)


class Resource(BaseModel):
    id: str = Field(min_length=1)
    label: str = ""
    kind: ResourceKind
    home_base_id: str
    crew_size: int = Field(default=0, ge=0)
    speed_kmh: float = Field(default=0, ge=0)
    line_rate_m_h: float = Field(default=0, ge=0)
    flow_l_min: float = Field(default=0, ge=0)
    capacity_l: float = Field(default=0, ge=0)
    available_start_min: float = Field(default=0, ge=0)
    available_end_min: float = Field(default=1440, ge=0)


class Task(BaseModel):
    id: str = Field(min_length=1)
    resource_id: str
    kind: TaskKind
    start_min: float = Field(ge=0)
    end_min: float = Field(ge=0)
    target: list[Point] = Field(default_factory=list)
    line_id: str | None = None
    drop_id: str | None = None
    note: str = ""

    @model_validator(mode="after")
    def _time_order(self) -> Task:
        if self.end_min < self.start_min:
            raise ValueError("task end_min must be >= start_min")
        return self


class Line(BaseModel):
    id: str = Field(min_length=1)
    task_id: str
    points: list[Point] = Field(min_length=2)
    width_m: float = Field(default=2.0, gt=0)
    constructed_start_min: float = Field(ge=0)
    constructed_end_min: float = Field(ge=0)
    state: LineState = LineState.PLANNED
    breached_at_min: float | None = Field(default=None, ge=0)
    fuel_removed: float = Field(default=0.0, ge=0, le=1)
    moisture: float = Field(default=0.0, ge=0, le=1)

    @model_validator(mode="after")
    def _line_order(self) -> Line:
        if self.constructed_end_min < self.constructed_start_min:
            raise ValueError("line construction end must be >= start")
        if self.breached_at_min is not None:
            if self.state != LineState.BREACHED:
                raise ValueError("breached_at_min requires line state breached")
            if self.breached_at_min < self.constructed_end_min:
                raise ValueError("breached_at_min must be after construction end")
        return self


class Drop(BaseModel):
    id: str = Field(min_length=1)
    task_id: str
    resource_id: str
    suppressant: Suppressant = Suppressant.WATER
    start_min: float = Field(ge=0)
    end_min: float = Field(ge=0)
    center: Point
    length_m: float = Field(gt=0)
    width_m: float = Field(gt=0)
    coverage_l_m2: float = Field(gt=0)
    effect_duration_min: float = Field(default=15.0, gt=0)
    canopy_penetration: float = Field(default=1.0, ge=0, le=1)

    @model_validator(mode="after")
    def _drop_order(self) -> Drop:
        if self.end_min < self.start_min:
            raise ValueError("drop end_min must be >= start_min")
        return self


class Objective(BaseModel):
    containment_area_ha: float | None = Field(default=None, ge=0)
    max_area_ha: float | None = Field(default=None, ge=0)
    deadline_min: float | None = Field(default=None, ge=0)
    priority: Literal["life", "community", "resource", "ecological"] = "community"


class EffectEvent(BaseModel):
    """A time-bounded spatial effect consumed by the fire model."""

    effect_id: str
    source_id: str
    kind: Literal["line", "water", "foam", "retardant", "mop_up"]
    start_min: float = Field(ge=0)
    end_min: float = Field(ge=0)
    geometry: list[Point] = Field(min_length=2)
    width_m: float = Field(default=0, ge=0)
    fuel_removed: float | None = Field(default=None, ge=0, le=1)
    moisture: float | None = Field(default=None, ge=0, le=1)
    coverage_l_m2: float | None = Field(default=None, ge=0)
    strength: float = Field(default=1.0, ge=0, le=1)
    decay_min: float = Field(default=0, ge=0)


class Scenario(BaseModel):
    scenario_id: str = Field(min_length=1)
    fire_slug: str
    label: str = ""
    timeline_start_min: float = Field(default=0, ge=0)
    timeline_end_min: float = Field(default=1440, ge=0)
    bases: list[Base] = Field(default_factory=list)
    water_sources: list[WaterSource] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    lines: list[Line] = Field(default_factory=list)
    drops: list[Drop] = Field(default_factory=list)
    objective: Objective = Field(default_factory=Objective)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_contract(self) -> Scenario:
        if self.timeline_end_min < self.timeline_start_min:
            raise ValueError("timeline end must be >= start")
        base_ids = {base.id for base in self.bases}
        if len(base_ids) != len(self.bases):
            raise ValueError("base ids must be unique")
        resource_ids = {resource.id for resource in self.resources}
        if len(resource_ids) != len(self.resources):
            raise ValueError("resource ids must be unique")
        task_ids = {task.id for task in self.tasks}
        if len(task_ids) != len(self.tasks):
            raise ValueError("task ids must be unique")
        if len({line.id for line in self.lines}) != len(self.lines):
            raise ValueError("line ids must be unique")
        if len({drop.id for drop in self.drops}) != len(self.drops):
            raise ValueError("drop ids must be unique")
        for resource in self.resources:
            if resource.home_base_id not in base_ids:
                raise ValueError(f"resource {resource.id} references unknown base {resource.home_base_id}")
        for task in self.tasks:
            if task.resource_id not in resource_ids:
                raise ValueError(f"task {task.id} references unknown resource {task.resource_id}")
            if task.end_min > self.timeline_end_min + 1e-6:
                raise ValueError(f"task {task.id} ends after the scenario timeline")
            resource = next(item for item in self.resources if item.id == task.resource_id)
            if task.start_min < resource.available_start_min - 1e-6:
                raise ValueError(f"task {task.id} starts before resource availability")
            if task.end_min > resource.available_end_min + 1e-6:
                raise ValueError(f"task {task.id} ends after resource availability")
        task_by_id = {task.id: task for task in self.tasks}
        for line in self.lines:
            if line.task_id not in task_ids:
                raise ValueError(f"line {line.id} references unknown task {line.task_id}")
            task = task_by_id[line.task_id]
            if line.constructed_start_min < task.start_min - 1e-6 or line.constructed_end_min > task.end_min + 1e-6:
                raise ValueError(f"line {line.id} construction must fall within task {task.id}")
            if line.breached_at_min is not None and line.breached_at_min > self.timeline_end_min + 1e-6:
                raise ValueError(f"line {line.id} breach is after the scenario timeline")
        for drop in self.drops:
            if drop.task_id not in task_ids:
                raise ValueError(f"drop {drop.id} references unknown task {drop.task_id}")
            if drop.resource_id not in resource_ids:
                raise ValueError(f"drop {drop.id} references unknown resource {drop.resource_id}")
            task = task_by_id[drop.task_id]
            if drop.start_min < task.start_min - 1e-6 or drop.end_min > task.end_min + 1e-6:
                raise ValueError(f"drop {drop.id} must fall within task {task.id}")
            resource = next(item for item in self.resources if item.id == drop.resource_id)
            required = drop.length_m * drop.width_m * drop.coverage_l_m2
            if resource.capacity_l and required > resource.capacity_l * 1.001:
                raise ValueError(
                    f"drop {drop.id} needs {required:.0f} L but resource {resource.id} carries {resource.capacity_l:.0f} L"
                )
        by_resource: dict[str, list[Task]] = {}
        for task in self.tasks:
            by_resource.setdefault(task.resource_id, []).append(task)
        for resource_id, tasks in by_resource.items():
            ordered = sorted(tasks, key=lambda item: item.start_min)
            for previous, current in zip(ordered, ordered[1:]):
                if current.start_min < previous.end_min - 1e-6:
                    raise ValueError(
                        f"resource {resource_id} is double-booked: {previous.id} overlaps {current.id}"
                    )
        return self

    def effect_events(self) -> list[EffectEvent]:
        """Return the time-bounded line/drop effects for a fire model.

        This is the P179.0 hand-off. A later fire kernel can rasterize these
        polygons and apply fuel removal, moisture, coverage and decay.
        """
        events: list[EffectEvent] = []
        for line in self.lines:
            events.append(
                EffectEvent(
                    effect_id=f"line-{line.id}",
                    source_id=line.id,
                    kind="line",
                    start_min=line.constructed_start_min,
                    end_min=line.constructed_end_min,
                    geometry=line.points,
                    width_m=line.width_m,
                    fuel_removed=line.fuel_removed,
                    moisture=line.moisture,
                    strength=1.0,
                )
            )
        for drop in self.drops:
            x, y = drop.center
            half_l, half_w = drop.length_m / 2, drop.width_m / 2
            events.append(
                EffectEvent(
                    effect_id=f"drop-{drop.id}",
                    source_id=drop.id,
                    kind=drop.suppressant.value,
                    start_min=drop.start_min,
                    end_min=drop.end_min,
                    geometry=[
                        (x - half_l, y - half_w),
                        (x + half_l, y - half_w),
                        (x + half_l, y + half_w),
                        (x - half_l, y + half_w),
                    ],
                    coverage_l_m2=drop.coverage_l_m2,
                    strength=drop.canopy_penetration,
                    decay_min=drop.effect_duration_min,
                )
            )
        return events

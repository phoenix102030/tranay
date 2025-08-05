from typing import Optional

import attrs


@attrs.define(frozen=True)
class TrafficData:
    id: str
    sampled_seconds: float
    travel_time: float
    density: float
    occupancy: float
    waiting_time: float
    speed: float
    departed: int
    arrived: int
    entered: int
    left: int
    lane_changed_from: int
    lane_changed_to: int
    speed_relative: Optional[float] = None


@attrs.define(frozen=True)
class Interval:
    begin: float
    end: float
    id: str
    data: dict[str, list[TrafficData]]

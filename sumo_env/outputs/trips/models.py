from typing import Optional

import attrs


@attrs.define(frozen=True)
class TripInfo:
    id: str
    depart: float
    depart_lane: str
    depart_pos: float
    depart_speed: float
    depart_delay: float
    arrival: float
    arrival_lane: str
    arrival_pos: float
    arrival_speed: float
    duration: float
    route_length: float
    waiting_time: float
    waiting_count: int
    stop_time: float
    time_loss: float
    reroute_no: int
    devices: str
    v_type: str
    speed_factor: float
    vaporized: Optional[str] = None

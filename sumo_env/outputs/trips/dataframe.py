from collections.abc import Iterable
from typing import Any

import polars as pl

from sumo_env.outputs.common.dataframe import to_polars
from sumo_env.outputs.trips.models import TripInfo

SCHEMA = {
    "id": pl.Utf8,
    "depart": pl.Float64,
    "depart_lane": pl.Utf8,
    "depart_pos": pl.Float64,
    "depart_speed": pl.Float64,
    "depart_delay": pl.Float64,
    "arrival": pl.Float64,
    "arrival_lane": pl.Utf8,
    "arrival_pos": pl.Float64,
    "arrival_speed": pl.Float64,
    "duration": pl.Float64,
    "route_length": pl.Float64,
    "waiting_time": pl.Float64,
    "waiting_count": pl.Int32,
    "stop_time": pl.Float64,
    "time_loss": pl.Float64,
    "reroute_no": pl.Int32,
    "devices": pl.Utf8,
    "v_type": pl.Utf8,
    "speed_factor": pl.Float64,
    "vaporized": pl.Utf8,
}


def tripinfo_to_dict(tripinfo: TripInfo) -> dict[str, Any]:
    """Convert TripInfo to a dictionary."""
    return {
        "id": tripinfo.id,
        "depart": tripinfo.depart,
        "depart_lane": tripinfo.depart_lane,
        "depart_pos": tripinfo.depart_pos,
        "depart_speed": tripinfo.depart_speed,
        "depart_delay": tripinfo.depart_delay,
        "arrival": tripinfo.arrival,
        "arrival_lane": tripinfo.arrival_lane,
        "arrival_pos": tripinfo.arrival_pos,
        "arrival_speed": tripinfo.arrival_speed,
        "duration": tripinfo.duration,
        "route_length": tripinfo.route_length,
        "waiting_time": tripinfo.waiting_time,
        "waiting_count": tripinfo.waiting_count,
        "stop_time": tripinfo.stop_time,
        "time_loss": tripinfo.time_loss,
        "reroute_no": tripinfo.reroute_no,
        "devices": tripinfo.devices,
        "v_type": tripinfo.v_type,
        "speed_factor": tripinfo.speed_factor,
        "vaporized": tripinfo.vaporized,
    }


def map_tripinfo_data(tripinfos: TripInfo | Iterable[TripInfo]) -> list[dict[str, Any]]:
    """Map TripInfo objects to records."""
    if isinstance(tripinfos, TripInfo):
        tripinfos = [tripinfos]
    return [tripinfo_to_dict(tripinfo) for tripinfo in tripinfos]


def tripinfos_to_polars(tripinfos: TripInfo | Iterable[TripInfo]) -> pl.DataFrame:
    """Convert tripinfo objects to a Polars DataFrame."""
    return to_polars([tripinfos], map_tripinfo_data, SCHEMA)

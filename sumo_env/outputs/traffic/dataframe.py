from typing import Any, Iterator, Optional

import polars as pl

from sumo_env.outputs.common.dataframe import stream_to_polars, to_polars
from sumo_env.outputs.traffic.models import Interval, TrafficData

SCHEMA = {
    "begin": pl.Float64,
    "end": pl.Float64,
    "id": pl.Utf8,
    "edge_id": pl.Utf8,
    "lane_id": pl.Utf8,
    "sampled_seconds": pl.Float64,
    "travel_time": pl.Float64,
    "density": pl.Float64,
    "occupancy": pl.Float64,
    "waiting_time": pl.Float64,
    "speed": pl.Float64,
    "departed": pl.Int32,
    "arrived": pl.Int32,
    "entered": pl.Int32,
    "left": pl.Int32,
    "lane_changed_from": pl.Int32,
    "lane_changed_to": pl.Int32,
    "speed_relative": pl.Float64,
}


def get_interval_metadata(interval: Interval) -> dict[str, Any]:
    """Extract interval metadata."""
    return {
        "begin": interval.begin,
        "end": interval.end,
        "id": interval.id,
    }


def traffic_data_to_dict(
    traffic: TrafficData, edge_id: Optional[str] = None
) -> dict[str, Any]:
    """Convert TrafficData to dict."""
    return {
        "edge_id": edge_id,
        "lane_id": traffic.id,
        "sampled_seconds": traffic.sampled_seconds,
        "travel_time": traffic.travel_time,
        "density": traffic.density,
        "occupancy": traffic.occupancy,
        "waiting_time": traffic.waiting_time,
        "speed": traffic.speed,
        "departed": traffic.departed,
        "arrived": traffic.arrived,
        "entered": traffic.entered,
        "left": traffic.left,
        "lane_changed_from": traffic.lane_changed_from,
        "lane_changed_to": traffic.lane_changed_to,
        "speed_relative": traffic.speed_relative,
    }


def map_interval_data(
    interval: Interval,
) -> list[dict[str, Any]]:
    """Map interval data to records."""
    return [
        {**get_interval_metadata(interval), **traffic_data_to_dict(lane, edge_id)}
        for edge_id, lanes in interval.data.items()
        for lane in lanes
    ]


def intervals_to_polars(intervals: list[Interval]) -> pl.DataFrame:
    """Convert traffic intervals to Polars DataFrame."""
    return to_polars(intervals, map_interval_data, SCHEMA)


def intervals_to_polars_lazy(
    intervals: Iterator[Interval], chunk_size: int = 10000
) -> pl.LazyFrame:
    """
    Transform a stream of traffic intervals to a Polars LazyFrame.

    Args:
        intervals: Iterator yielding Interval objects
        chunk_size: Number of intervals to process per chunk

    Returns:
        Polars LazyFrame with traffic data
    """
    return stream_to_polars(intervals, map_interval_data, SCHEMA, chunk_size)

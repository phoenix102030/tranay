from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Any

import polars as pl
from attrs import asdict, define


@define(frozen=True)
class Measurement:
    timestamp: datetime.datetime
    sensor_id: str

    def __attrs_post_init__(self):
        if not self.sensor_id.strip():
            raise ValueError("Sensor ID cannot be empty")
        if self.timestamp.tzinfo is not None:
            raise ValueError("Timestamp must be timezone-naive")

    def time_diff(self, other: Measurement) -> datetime.timedelta:
        return abs(self.timestamp - other.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def measurements_to_dataframe(measurements: list[Measurement]) -> pl.DataFrame:
    """Convert a list of Measurement objects to a Polars DataFrame."""
    df = pl.DataFrame([m.to_dict() for m in measurements])
    measurement_types = [m.__class__.__name__ for m in measurements]
    return df.with_columns(pl.Series("measurement_type", measurement_types))


def aggregate_by_sensor(
    df: pl.DataFrame, aggregator: Callable[[pl.Expr], pl.Expr]
) -> pl.DataFrame:
    numeric_cols = [
        col
        for col in df.columns
        if col not in ["timestamp", "sensor_id", "measurement_type"]
        and df[col].dtype in [pl.Int64, pl.Float64]
    ]
    return df.group_by("sensor_id").agg(
        **{col: aggregator(pl.col(col)) for col in numeric_cols}
    )


def filter_by_time(
    df: pl.DataFrame, start_time: datetime.datetime, end_time: datetime.datetime
) -> pl.DataFrame:
    """Filter measurements within the given time window."""
    return df.filter(
        (pl.col("timestamp") >= start_time) & (pl.col("timestamp") <= end_time)
    )


def align_measurements(
    df1: pl.DataFrame,
    df2: pl.DataFrame,
    time_tolerance: datetime.timedelta = datetime.timedelta(minutes=5),
) -> pl.DataFrame:
    """Align measurements from two DataFrames by sensor_id and timestamp."""
    required_cols = ["timestamp", "sensor_id"]
    if not all(col in df1.columns for col in required_cols) or not all(
        col in df2.columns for col in required_cols
    ):
        raise ValueError(
            "Both DataFrames must contain 'timestamp' and 'sensor_id' columns"
        )

    df1_sorted = df1.sort(["sensor_id", "timestamp"])
    df2_sorted = df2.sort(["sensor_id", "timestamp"])

    # Merge 2 dataframes with a time tolerance
    result = df1_sorted.join_asof(
        df2_sorted,
        by="sensor_id",
        on="timestamp",
        tolerance=f"{time_tolerance.total_seconds()}s",
        strategy="nearest",
    )

    common_cols = [
        col
        for col in df1.columns
        if col in df2.columns and col not in ["timestamp", "sensor_id"]
    ]
    other_df1_cols = [
        col
        for col in df1.columns
        if col not in df2.columns and col not in ["timestamp", "sensor_id"]
    ]
    other_df2_cols = [
        col
        for col in df2.columns
        if col not in df1.columns and col not in ["timestamp", "sensor_id"]
    ]

    return result.select(
        pl.col("timestamp"),
        pl.col("sensor_id"),
        *[pl.col(col).alias(f"{col}_left") for col in common_cols + other_df1_cols],
        *[
            pl.col(f"{col}_right").alias(f"{col}_right")
            for col in common_cols + other_df2_cols
        ],
    )

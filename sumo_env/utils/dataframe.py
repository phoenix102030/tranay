from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import polars as pl

from sumo_env.utils.constants import NS_TO_S


def transform_columns(
    columns: list[str], transform: Callable[[pl.Expr], pl.Expr], suffix: str = ""
) -> list[pl.Expr]:
    return [transform(pl.col(col)).alias(f"{col}{suffix}") for col in columns]


def format_duration(duration: pl.Expr) -> pl.Expr:
    """Create an expression to format a Duration into a human-readable string (e.g., '1d 2h 12m')."""
    components = [
        (duration.dt.total_days(), "d"),  # Days
        (duration.dt.total_hours() % 24, "h"),  # Hours
        (duration.dt.total_minutes() % 60, "m"),  # Minutes
        (duration.dt.total_seconds() % 60, "s"),  # Seconds
    ]

    return (
        pl.concat_str(
            [
                pl.when(value > 0)
                .then(pl.concat_str([value.cast(pl.String), pl.lit(unit)]))
                .otherwise(pl.lit(""))
                for value, unit in components
            ]
        )
        .str.strip_chars()
        .str.replace(r"^\s*$", "0s")
    )


def seconds_to_datetime(
    columns: list[str], ref_date: datetime, suffix: str = ""
) -> list[pl.Expr]:
    """
    Generate expressions to convert seconds in specified columns to datetime, using a reference date.
    """
    transform = lambda expr: pl.lit(ref_date).cast(pl.Datetime) + expr.cast(
        pl.Float64
    ).mul(NS_TO_S).cast(pl.Duration("ns"))
    return transform_columns(columns, transform, suffix)


def seconds_to_duration(columns: list[str], suffix: str = "") -> list[pl.Expr]:
    """
    Generate expressions to convert seconds in specified columns to Polars Duration.
    """
    transform = lambda expr: expr.cast(pl.Float64).mul(NS_TO_S).cast(pl.Duration("ns"))
    return transform_columns(columns, transform, suffix)


def seconds_to_formated_duration(columns: list[str], suffix: str = "") -> list[pl.Expr]:
    """
    Convert seconds in specified columns to human-readable duration strings (e.g., '1d 2h 12m')
    """
    transform = lambda expr: format_duration(
        expr.cast(pl.Float64).mul(NS_TO_S).cast(pl.Duration("ns"))
    )
    return transform_columns(columns, transform, suffix)


def export_csv(df: pl.DataFrame, file_path: Path) -> None:
    """Export DataFrame to CSV."""
    df.write_csv(str(file_path))

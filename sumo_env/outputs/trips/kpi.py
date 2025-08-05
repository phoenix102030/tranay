from pathlib import Path
from typing import List, Tuple

import polars as pl

from sumo_env.outputs.trips.dataframe import tripinfos_to_polars
from sumo_env.outputs.trips.parser import parse_tripinfos
from sumo_env.utils.dataframe import seconds_to_formated_duration
from sumo_env.utils.xml import root


def create_category(categories: List[Tuple[List[str], str]]) -> pl.DataFrame:
    """Create a Polars DataFrame mapping vehicle types to categories."""
    return pl.DataFrame(
        {
            "v_type": [vtype for vtypes, _ in categories for vtype in vtypes],
            "category": [category for vtypes, category in categories for _ in vtypes],
        },
        schema={"v_type": pl.Utf8, "category": pl.Utf8},
    )


def transform_tripinfo_df(df: pl.DataFrame, category: pl.DataFrame) -> pl.DataFrame:
    """Transform DataFrame by adding category and time_loss_depart_delay columns."""
    return df.join(category, on="v_type", how="left").with_columns(
        category=pl.col("category").fill_null("Other"),
        time_loss=pl.col("time_loss").cast(pl.Float64),
        depart_delay=pl.col("depart_delay").cast(pl.Float64),
        duration=pl.col("duration").cast(pl.Float64),
        time_loss_depart_delay=pl.col("time_loss").cast(pl.Float64)
        + pl.col("depart_delay").cast(pl.Float64),
        waiting_time=pl.col("waiting_time").cast(pl.Float64),
    )


def aggregate_metrics(df: pl.DataFrame) -> pl.DataFrame:
    """Aggregate metrics by category, computing sums, means, and totals."""
    metrics = [
        "time_loss",
        "depart_delay",
        "duration",
        "time_loss_depart_delay",
        "waiting_time",
    ]
    grouped = df.group_by("category").agg(
        **{f"{metric}_sum": pl.col(metric).sum() for metric in metrics},
        **{f"{metric}_mean": pl.col(metric).mean() for metric in metrics},
    )

    totals = df.select(
        **{f"{metric}_sum": pl.col(metric).sum() for metric in metrics},
        **{f"{metric}_mean": pl.col(metric).mean() for metric in metrics},
        category=pl.lit("Total"),
    ).select(grouped.columns)

    return pl.concat([grouped, totals])


def process_tripinfo_file(
    file_path: Path, categories: List[Tuple[List[str], str]]
) -> pl.DataFrame:
    """Generate KPI DataFrame from tripinfo XML."""
    category = create_category(categories)
    df = tripinfos_to_polars(parse_tripinfos(root(file_path)))
    transformed_df = transform_tripinfo_df(df, category)
    aggregated_df = aggregate_metrics(transformed_df)
    duration_df = aggregated_df.with_columns(
        seconds_to_formated_duration(
            [col for col in aggregated_df.columns if col != "category"]
        )
    )
    return duration_df.melt(
        id_vars="category", variable_name="metrics", value_name="value"
    ).pivot(on="category", index="metrics", values="value")

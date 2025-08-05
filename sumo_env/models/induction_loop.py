from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import polars as pl
from attrs import define, field

from sumo_env.models.constants import Tags
from sumo_env.models.measurement import Measurement
from sumo_env.utils.constants import MPS_TO_KPH
from sumo_env.utils.dataframe import transform_columns
from sumo_env.utils.datetime import to_naive_tz
from sumo_env.utils.xml import create_elem, to_attrs

# TODO: move the output par into outputs/induction_loop

DEFAULT_DETECTION_LENGTH = 0.0
DEFAULT_V_TYPES = ["passenger"]

# May use the schema with polars
SCHEMA = {
    "timestamp": pl.Datetime,
    "sensor_id": pl.Utf8,
    "flow": pl.Int32,
    "speed": pl.Float32,
    "occupancy": pl.Float32,
    "harmonic_speed": pl.Float32,
}


@define(frozen=True)
class InductionLoopMeasurement(Measurement):
    flow: float
    speed: float
    occupancy: float
    harmonic_speed: float

    @classmethod
    def from_xml(
        cls, elem: ET.Element, ref_datetime: datetime
    ) -> InductionLoopMeasurement:
        return InductionLoopMeasurement(
            timestamp=to_naive_tz(
                ref_datetime + timedelta(seconds=float(elem.get("end", "")))
            ),  # Remove the timezone for comparison
            sensor_id=elem.get("id", ""),
            flow=float(elem.get("flow", 0)),
            speed=float(elem.get("speed", 0)),
            occupancy=float(elem.get("occupancy", 0)),
            harmonic_speed=float(elem.get("harmonicMeanSpeed", 0)),
        )


def parse_sumo_measurements(
    xml_file: Path, ref_datetime: datetime
) -> list[InductionLoopMeasurement]:
    return [
        InductionLoopMeasurement.from_xml(interval, ref_datetime)
        for interval in ET.parse(str(xml_file)).findall("interval")
    ]


def aggregate_by_edge(measurements_df: pl.DataFrame) -> pl.DataFrame:
    return (
        measurements_df.with_columns(
            sensor_id=pl.col("sensor_id").str.extract(
                r"^(.*)_\d+$", 1
            )  # Remove the lane id suffix
        )
        .group_by(["sensor_id", "timestamp"])
        .agg(flow=pl.col("flow").sum(), speed=pl.col("speed").mean())
        .sort("timestamp")
    )


def convert_speed_to_kph(df: pl.DataFrame) -> pl.DataFrame:
    """Convert specified speed columns from m/s to km/h."""
    columns_to_convert = ["speed", "harmonic_speed"]
    return df.with_columns(
        transform_columns(columns_to_convert, lambda c: c * MPS_TO_KPH)
    )


@define(frozen=True)
class InductionLoop:
    """Represents an induction loop detector in SUMO for simulation configuration."""

    id: str
    lane_id: str
    pos: float
    file: Path
    length: Optional[int] = None
    period: Optional[int] = None
    friendly_pos: bool = False
    v_types: List[str] = field(factory=list)
    next_edges: List[str] = field(factory=list)
    detect_persons: Optional[str] = None

    def to_xml(self) -> ET.Element:
        mandatory_attrs = {
            "id": self.id,
            "lane": self.lane_id,
            "pos": str(self.pos),
            "file": str(self.file),
        }
        optional_attrs = {
            "length": str(self.length) if self.length is not None else None,
            "period": str(self.period) if self.period is not None else None,
            "friendlyPos": "true" if self.friendly_pos else None,
            "vTypes": ",".join(self.v_types) if self.v_types else None,
            "nextEdges": ",".join(self.next_edges) if self.next_edges else None,
            "detectPersons": (
                self.detect_persons if self.detect_persons is not None else None
            ),
        }

        return create_elem(
            Tags.INDUCTION_LOOP, to_attrs(mandatory_attrs, optional_attrs)  # type: ignore[arg-type]
        )

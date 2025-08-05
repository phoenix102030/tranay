from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Optional

from attr import define

from sumo_env.models.calibrator import Flow
from sumo_env.utils.converter import kph_to_mps

DELIMITER = ";"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@define(frozen=True)
class Measure:
    count_point_id: int
    count_point_name: str
    measure_datetime: datetime.datetime
    flow: Optional[float]
    occupancy: Optional[float]
    speed: Optional[float]
    flow_confidence: Optional[str]
    occupancy_confidence: Optional[str]
    speed_confidence: Optional[str]

    # TODO: remove the date
    def to_calibrator_flow(self, period: float, **kwargs) -> Flow:
        return Flow(
            begin=self.measure_datetime.hour * 3600
            + self.measure_datetime.minute * 60
            + self.measure_datetime.second
            - period,  # datetime.datetime.timestamp(self.measure_datetime),
            end=self.measure_datetime.hour * 3600
            + self.measure_datetime.minute * 60
            + self.measure_datetime.second
            - 1,
            speed=kph_to_mps(self.speed) if self.speed is not None else None,
            vehsPerHour=self.flow,
            **kwargs,
        )


def aggregate_by_site(measures: list[Measure]) -> dict[str, list[Measure]]:
    grouped = defaultdict(list)
    for measure in measures:
        grouped[str(measure.count_point_name)].append(measure)
    return dict(grouped)


def measures_to_flows(measures: list[Measure], period: float, **kwargs) -> list[Flow]:
    return [measure.to_calibrator_flow(period, **kwargs) for measure in measures]


def parse_measure_row(row: str) -> Measure:
    values = row.split(DELIMITER)
    # TODO: May check if the values are not None
    return Measure(
        count_point_id=int(values[0]),  # if values[0].strip() else None,
        count_point_name=values[1],
        measure_datetime=datetime.datetime.strptime(
            values[2], DATETIME_FORMAT
        ),  # if values[2].strip() else None,
        flow=float(values[3]) if values[3].strip() else None,
        occupancy=float(values[4]) if values[4].strip() else None,
        speed=float(values[5]) if values[5].strip() else None,
        flow_confidence=values[6],
        occupancy_confidence=values[7],
        speed_confidence=values[8],
    )


# TODO: this function can be moved to a more general module
def parse_measures(file_content: str) -> list[Measure]:
    lines = file_content.strip().split("\n")
    return list(map(parse_measure_row, lines[1:]))

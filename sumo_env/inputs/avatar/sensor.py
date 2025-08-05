from pathlib import Path
from typing import Optional

import sumolib
from attr import define

from sumo_env.models.calibrator import Calibrator
from sumo_env.models.induction_loop import InductionLoop
from sumo_env.sumo.edge.access import closest_edge_from_lon_lat
from sumo_env.sumo.lane.access import lane_ids_from_edge_id
from sumo_env.utils.file import split_lines

DELIMITER = ";"
QUOTE_CHAR = '"'
POINT_PREFIX = "POINT ("
POINT_SUFFIX = ")"


@define(frozen=True)
class Sensor:
    count_point_id: int
    count_point_name: str
    op_road_name: str
    longitude: float
    latitude: float

    # TODO: construct outside (remove net)
    def to_induction_loops(
        self, net: sumolib.net.Net, file: Path, **kwargs
    ) -> list[InductionLoop]:
        edge_id, pos = closest_edge_from_lon_lat(
            self.longitude, self.latitude, net, radius=5.0
        ) or (None, 0.0)
        return (
            [
                InductionLoop(
                    id=self.count_point_name + "_" + lane_id,
                    lane_id=lane_id,
                    pos=pos,
                    file=file,
                    friendly_pos=True,
                    **kwargs,
                )
                for lane_id in lane_ids_from_edge_id(net, edge_id)
            ]
            if edge_id is not None
            else []
        )

    # TODO: construct outside (remove net)
    def to_calibrator(self, net: sumolib.net.Net, **kwargs) -> Optional[Calibrator]:
        edge_id, pos = closest_edge_from_lon_lat(
            self.longitude, self.latitude, net, radius=5.0
        ) or (None, 0.0)
        return (
            Calibrator(id=self.count_point_name, edge=edge_id, pos=pos, **kwargs)
            if edge_id is not None
            else None
        )


def parse_coordinates(point_str: str) -> tuple[float, float]:
    coords = point_str.replace(POINT_PREFIX, "").replace(POINT_SUFFIX, "").split()
    return float(coords[0]), float(coords[1])


def parse_sensor_row(row: str) -> Sensor:
    values = row.split(DELIMITER)
    lon, lat = parse_coordinates(values[3])
    return Sensor(
        count_point_id=int(values[0]),
        count_point_name=values[1].strip(QUOTE_CHAR),
        op_road_name=values[2].strip(QUOTE_CHAR),
        longitude=lon,
        latitude=lat,
    )


def parse_sensors(file_content: str) -> list[Sensor]:
    lines = split_lines(file_content)
    return list(map(parse_sensor_row, lines[1:]))


def induction_loops_from_sensor(
    sensor_name: str, lane_ids: list[str], pos: float, file: Path, **kwargs
) -> list[InductionLoop]:
    return (
        [
            InductionLoop(
                id=f"{sensor_name}_{lane_id}",
                lane_id=lane_id,
                pos=pos,
                file=file,
                friendly_pos=True,
                **kwargs,
            )
            for lane_id in lane_ids
        ]
        if lane_ids
        else []
    )

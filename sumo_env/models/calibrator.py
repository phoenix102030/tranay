from __future__ import annotations

from collections.abc import Callable
from itertools import repeat
from operator import add, mul, sub, truediv
from pathlib import Path
from typing import Any, List, Optional, cast
from xml.etree import ElementTree as ET

from attrs import define, evolve, field

from sumo_env.models.constants import (
    SUMOCalibrator,
    SUMOFlow,
    Tags,
)
from sumo_env.utils.xml import create_elem, to_attrs


@define(frozen=True)
class Flow:
    """Represents a flow definition within a calibrator in SUMO."""

    begin: float
    end: float
    route: Optional[str] = None
    vehsPerHour: Optional[float] = None
    speed: Optional[float] = None
    type: Optional[str] = None
    depart_pos: Optional[str] = None
    depart_speed: Optional[str] = None
    arrival_pos: Optional[str] = None
    arrival_speed: Optional[str] = None

    def update_param(self, param_name: str, value: Any) -> Flow:
        valid_params = {
            "begin": self.begin,
            "end": self.end,
            "route": self.route,
            "vehsPerHour": self.vehsPerHour,
            "speed": self.speed,
            "type": self.type,
            "depart_pos": self.depart_pos,
            "depart_speed": self.depart_speed,
            "arrival_pos": self.arrival_pos,
            "arrival_speed": self.arrival_speed,
        }

        valid_params[param_name] = value
        return evolve(self, **{param_name: value})

    def same_struct_as(self, other: Flow) -> bool:
        return self.begin == other.begin and self.end == other.end

    def apply_binary_op(
        self, other: Flow | float, op: Callable[[float, float], float]
    ) -> Flow:
        if isinstance(other, Flow) and not self.same_struct_as(other):
            raise ValueError("The flows must have the same structure")

        other_value = other.vehsPerHour if isinstance(other, Flow) else other
        other_value = 0 if other_value is None else other_value
        return evolve(
            self,
            vehsPerHour=op(
                self.vehsPerHour if self.vehsPerHour is not None else 0,
                other_value,
            ),
        )

    def __add__(self, other: Flow | float) -> Flow:
        return self.apply_binary_op(other, add)

    def __sub__(self, other: Flow | float) -> Flow:
        return self.apply_binary_op(other, sub)

    def __mul__(self, other: Flow | float) -> Flow:
        return self.apply_binary_op(other, mul)

    def __truediv__(self, other: Flow | float) -> Flow:
        return self.apply_binary_op(other, truediv)

    def __pow__(self, other: Flow | float) -> Flow:
        return self.apply_binary_op(other, pow)

    def to_xml(self) -> ET.Element:
        mandatory_attrs = {
            SUMOFlow.BEGIN: str(self.begin),
            SUMOFlow.END: str(self.end),
        }
        optional_attrs = {
            SUMOFlow.ROUTE: self.route,
            SUMOFlow.VEHS_PER_HOUR: (
                str(self.vehsPerHour) if self.vehsPerHour is not None else None
            ),
            SUMOFlow.SPEED: str(self.speed) if self.speed is not None else None,
            SUMOFlow.TYPE: self.type,
            SUMOFlow.DEPART_POS: self.depart_pos,
            SUMOFlow.DEPART_SPEED: self.depart_speed,
            SUMOFlow.ARRIVAL_POS: self.arrival_pos,
            SUMOFlow.ARRIVAL_SPEED: self.arrival_speed,
        }
        return create_elem(
            Tags.FLOW,
            to_attrs(mandatory_attrs, optional_attrs),  # type: ignore[arg-type]
        )


def apply_to_flows(
    flow_list1: List[Flow],
    operand: List[Flow] | float,
    op: Callable[[float, float], float],
) -> List[Flow]:
    return [
        f1.apply_binary_op(cast(Flow | float, f2), op)
        for f1, f2 in zip(
            flow_list1, operand if isinstance(operand, list) else repeat(operand)
        )
    ]


@define(frozen=True)
class Calibrator:
    """Represents a calibrator in SUMO for simulation configuration."""

    id: str
    edge: Optional[str] = None  # Either edge or lane must be specified
    lane: Optional[str] = None  # Either edge or lane must be specified
    pos: float = 0.0  # Position on edge/lane (ignored in SUMO currently)
    flows: List[Flow] = field(factory=list)
    period: Optional[float] = None  # Default is step-length in SUMO (1s)
    route_probe: Optional[str] = None
    jam_threshold: Optional[float] = None  # Default is 0.5 in SUMO
    file: Optional[Path] = None
    v_types: List[str] = field(
        factory=list
    )  # Vehicle types to consider for calibration (empty means all)

    def to_xml(self) -> ET.Element:
        mandatory_attrs = {
            SUMOCalibrator.ID: self.id,
            SUMOCalibrator.POS: str(self.pos),
        }
        optional_attrs = {
            SUMOCalibrator.EDGE: self.edge,
            SUMOCalibrator.LANE: self.lane,
            SUMOCalibrator.JAM_THRESHOLD: (
                str(self.jam_threshold) if self.period is not None else None
            ),
            SUMOCalibrator.PERIOD: (
                str(self.period) if self.period is not None else None
            ),
            SUMOCalibrator.ROUTE_PROBE: self.route_probe,
            SUMOCalibrator.OUTPUT: str(self.file) if self.file is not None else None,
            SUMOCalibrator.V_TYPES: " ".join(self.v_types) if self.v_types else None,
        }
        calibrator_elem = create_elem(
            Tags.CALIBRATOR,
            to_attrs(mandatory_attrs, optional_attrs),  # type: ignore[arg-type]
        )
        for flow in self.flows:
            calibrator_elem.append(flow.to_xml())
        return calibrator_elem

    def add_flows(self, flows: List[Flow]) -> Calibrator:
        return evolve(self, flows=self.flows + flows)

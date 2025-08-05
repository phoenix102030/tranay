from __future__ import annotations

import sumolib
from attrs import define, field

from sumo_env.models.constants import VehClass


@define(frozen=True)
class Lane:
    id: str
    edge_id: str
    index: int
    length: float
    max_speed: float
    allowed_types: list[str] = field(factory=list)
    disallowed_types: list[str] = field(factory=list)

    def get_lanes(self) -> list[Lane]:
        return [self]

    @classmethod
    def from_sumolib(cls, sumo_lane: sumolib.net.lane.Lane) -> Lane:
        """
        Create a Lane instance from a sumolib lane object.

        Args:
            sumo_lane: A sumolib.net.lane.Lane object

        Returns:
            Lane: A new Lane instance
        """
        return cls(
            id=sumo_lane.getID(),
            edge_id=sumo_lane.getEdge().getID(),
            index=sumo_lane.getIndex(),
            length=sumo_lane.getLength(),
            max_speed=sumo_lane.getSpeed(),
            allowed_types=sumo_lane.getPermissions(),
            disallowed_types=list(
                set(VehClass) - set(sumo_lane.getPermissions())
            ),  # There is no method in sumolib to get disallowed types
        )

from __future__ import annotations

import sumolib
from attrs import define

from sumo_env.models.lane import Lane


# TODO add more attributes
@define(frozen=True)
class Edge:
    id: str
    from_node: str
    to_node: str
    length: float
    lanes: list[Lane]

    def get_lanes(self) -> list[Lane]:
        return self.lanes

    @classmethod
    def from_sumolib(cls, sumo_edge: sumolib.net.edge.Edge) -> Edge:
        """
        Create an Edge instance from a sumolib edge object.

        Args:
            sumo_edge: A sumolib.net.edge.Edge object

        Returns:
            Edge: A new Edge instance
        """
        lanes = [Lane.from_sumolib(lane) for lane in sumo_edge.getLanes()]

        return cls(
            id=sumo_edge.getID(),
            from_node=sumo_edge.getFromNode().getID(),
            to_node=sumo_edge.getToNode().getID(),
            length=sumo_edge.getLength(),
            lanes=lanes,
        )

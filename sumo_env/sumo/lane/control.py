from sumo_env.models.lane import Lane
from sumo_env.models.vehicle_type import VehicleType
from sumo_env.sim.sumo import SumoConnection


def set_allowed_types(
    api: SumoConnection, lane: Lane, allowed_types: list[VehicleType]
) -> None:
    api.lane.setAllowed(lane.id, [vtype.id for vtype in allowed_types])  # type: ignore[attr-defined]


def set_disallowed_types(
    api: SumoConnection, lane: Lane, disallowed_types: list[VehicleType]
) -> None:
    api.lane.setDisallowed(lane.id, [vtype.id for vtype in disallowed_types])  # type: ignore[attr-defined]

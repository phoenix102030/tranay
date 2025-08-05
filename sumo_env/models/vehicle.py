from attrs import define

from sumo_env.models.vehicle_type import VehicleType


@define(frozen=True)
class Vehicle:
    id: str
    type: VehicleType

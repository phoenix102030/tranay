from __future__ import annotations

from enum import StrEnum


class Tags(StrEnum):
    CALIBRATOR = "calibrator"
    FLOW = "flow"
    ADITIONAL = "additional"
    INDUCTION_LOOP = "inductionLoop"


class VehClass(StrEnum):
    """Valid vehicle class values for SUMO elements."""

    PASSENGER = "passenger"
    TRUCK = "truck"
    BUS = "bus"
    TAXI = "taxi"
    DELIVERY = "delivery"
    TRAILER = "trailer"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    PEDESTRIAN = "pedestrian"
    TRAM = "tram"
    RAIL = "rail"
    RAIL_URBAN = "rail_urban"
    RAIL_ELECTRIC = "rail_electric"
    CUSTOM1 = "custom1"
    CUSTOM2 = "custom2"


class DepartPos(StrEnum):
    """Valid departPos values for SUMO elements (e.g., flows, vehicles)."""

    FREE = "free"
    RANDOM = "random"
    BASE = "base"
    LAST = "last"


class DepartSpeed(StrEnum):
    """Valid departSpeed values for SUMO elements (e.g., flows, vehicles)."""

    MAX = "max"
    DESIRED = "desired"
    SPEED_LIMIT = "speedLimit"
    RANDOM = "random"


class SUMOCalibrator(StrEnum):
    ID = "id"
    EDGE = "edge"
    LANE = "lane"
    POS = "pos"
    OUTPUT = "output"
    PERIOD = "period"
    ROUTE_PROBE = "routeProbe"
    JAM_THRESHOLD = "jamThreshold"
    V_TYPES = "vTypes"


class SUMOFlow(StrEnum):
    BEGIN = "begin"
    END = "end"
    ROUTE = "route"
    VEHS_PER_HOUR = "vehsPerHour"
    SPEED = "speed"
    TYPE = "type"
    DEPART_POS = "departPos"
    DEPART_SPEED = "departSpeed"
    ARRIVAL_POS = "arrivalPos"
    ARRIVAL_SPEED = "arrivalSpeed"


DEFAULT_JAM_THRESHOLD = 0.5
DEFAULT_V_CLASS = VehClass.PASSENGER
DEFAULT_DEPART_POS = DepartPos.FREE
DEFAULT_DEPART_SPEED = DepartSpeed.MAX
DEFAULT_GAP = 2.5

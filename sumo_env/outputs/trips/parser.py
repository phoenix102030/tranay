import xml.etree.ElementTree as ET
from collections.abc import Iterator as _IterParseIterator
from typing import Iterator

from sumo_env.outputs.common.parser import parse_attributes
from sumo_env.outputs.trips.constants import (
    TRIPINFO_ATTRIBUTES,
    TRIPINFO_TAG,
)
from sumo_env.outputs.trips.models import TripInfo


def parse_tripinfo(element: ET.Element) -> TripInfo:
    """Parse a tripinfo element into a TripInfo object."""
    attrs = parse_attributes(element, TRIPINFO_ATTRIBUTES)
    return TripInfo(
        id=attrs.get("id", ""),
        depart=float(attrs.get("depart", 0)),
        depart_lane=attrs.get("departLane", ""),
        depart_pos=float(attrs.get("departPos", 0)),
        depart_speed=float(attrs.get("departSpeed", 0)),
        depart_delay=float(attrs.get("departDelay", 0)),
        arrival=float(attrs.get("arrival", 0)),
        arrival_lane=attrs.get("arrivalLane", ""),
        arrival_pos=float(attrs.get("arrivalPos", 0)),
        arrival_speed=float(attrs.get("arrivalSpeed", 0)),
        duration=float(attrs.get("duration", 0)),
        route_length=float(attrs.get("routeLength", 0)),
        waiting_time=float(attrs.get("waitingTime", 0)),
        waiting_count=int(attrs.get("waitingCount", 0)),
        stop_time=float(attrs.get("stopTime", 0)),
        time_loss=float(attrs.get("timeLoss", 0)),
        reroute_no=int(attrs.get("rerouteNo", 0)),
        devices=attrs.get("devices", ""),
        v_type=attrs.get("vType", ""),
        speed_factor=float(attrs.get("speedFactor", 0)),
        vaporized=attrs.get("vaporized", ""),
    )


def parse_tripinfos(root: ET.Element) -> list[TripInfo]:
    """Parse the entire tripinfos XML into a list of TripInfo objects."""
    return [parse_tripinfo(elem) for elem in root if elem.tag == TRIPINFO_TAG]


def parse_tripinfos_stream(iterator: _IterParseIterator) -> Iterator[TripInfo]:
    """
    Stream TripInfo objects from a tripinfos XML iterator.
    """
    for event, elem in iterator:
        if event == "end" and elem.tag == TRIPINFO_TAG:
            yield parse_tripinfo(elem)
            elem.clear()

import xml.etree.ElementTree as ET
from collections.abc import Iterator

from sumo_env.outputs.common.parser import (
    parse_attributes,
    parse_elements,
)
from sumo_env.outputs.traffic.constants import (
    BEGIN_ATTR,
    COMMON_ATTRIBUTES,
    END_ATTR,
    ID_ATTR,
    INTERVAL_TAG,
    LANE_SPECIFIC_ATTRIBUTES,
    LANE_TAG,
)
from sumo_env.outputs.traffic.models import Interval, TrafficData
from sumo_env.utils.xml import extract_attribute

ATTR_TO_FIELD = {
    "sampledSeconds": "sampled_seconds",
    "traveltime": "travel_time",
    "density": "density",
    "occupancy": "occupancy",
    "waitingTime": "waiting_time",
    "speed": "speed",
    "departed": "departed",
    "arrived": "arrived",
    "entered": "entered",
    "left": "left",
    "laneChangedFrom": "lane_changed_from",
    "laneChangedTo": "lane_changed_to",
    "speedRelative": "speed_relative",
}


def parse_traffic_data(element: ET.Element, attr_map: dict) -> TrafficData:
    """Parse traffic data from an edge or lane element."""
    attrs = {
        **parse_attributes(element, attr_map),
    }
    remapped_attrs = {ATTR_TO_FIELD.get(k, k): v for k, v in attrs.items()}
    return TrafficData(id=element.get(ID_ATTR, ""), **remapped_attrs)


def parse_edge_data(edge: ET.Element) -> list[TrafficData]:
    lanes = parse_elements(
        edge,
        LANE_TAG,
        lambda lane: parse_traffic_data(
            lane, {**COMMON_ATTRIBUTES, **LANE_SPECIFIC_ATTRIBUTES}
        ),
    ) or [parse_traffic_data(edge, COMMON_ATTRIBUTES)]

    return lanes


def parse_interval(
    interval: ET.Element,
) -> Interval:
    """Parse an interval into an Interval object."""
    return Interval(
        begin=float(extract_attribute(interval, BEGIN_ATTR)),
        end=float(extract_attribute(interval, END_ATTR)),
        id=extract_attribute(interval, ID_ATTR),
        data={edge.get(ID_ATTR, ""): parse_edge_data(edge) for edge in list(interval)},
    )


def parse_meandata(root: ET.Element) -> list[Interval]:
    """Parse the entire meandata XML into a list of Interval objects."""
    return parse_elements(root, INTERVAL_TAG, parse_interval)


def parse_meandata_stream(iterator: Iterator) -> Iterator[Interval]:
    """
    Stream intervals from a meandata XML iterator.
    """
    for event, elem in iterator:
        if event == "end" and elem.tag == INTERVAL_TAG:
            yield parse_interval(elem)
            elem.clear()

from typing import Optional, Tuple

import numpy as np
import sumolib

from sumo_env.models.constants import DEFAULT_GAP
from sumo_env.models.edge import Edge
from sumo_env.sim.sumo import SumoConnection
from sumo_env.sumo.network.access import lon_lat_to_x_y


def edge_from_net(net: sumolib.net.Net, edge_id: str) -> Edge:
    return net.getEdge(edge_id)


def total_lane_length(api: SumoConnection, edge: Edge, nb_lanes: int) -> float:
    lane_ids = [f"{edge.id}_{lane}" for lane in range(nb_lanes)]
    return sum(api.lane.getLength(lane_id) for lane_id in lane_ids)


def average_lane_length(total_length: float, nb_lanes: int) -> float:
    return total_length / nb_lanes if nb_lanes > 0 else 0.0


def get_edge_length(api: SumoConnection, edge: Edge) -> float:
    return api.lane.getLength(edge.id + "_0")


def speed_limit(api: SumoConnection, edge: Edge) -> float:
    return api.lane.getMaxSpeed(
        edge.id + "_0"
    )  # Note: Need to get the speed from the lane


def speed(api: SumoConnection, edge: Edge) -> float:
    return api.edge.getLastStepMeanSpeed(edge.id)


def mean_vehicle_gap(api: SumoConnection, vehicle_ids: list[str]) -> float:
    gaps = [api.vehicle.getMinGap(veh) for veh in vehicle_ids]
    mean_gap = np.mean(gaps) if gaps else DEFAULT_GAP
    return mean_gap if not np.isnan(mean_gap) else DEFAULT_GAP


def net_occupancy(api: SumoConnection, edge: Edge) -> float:
    return api.edge.getLastStepOccupancy(edge.id)


def concentration(
    nb_vehicles: int,
    mean_vehicle_length: float,
    mean_gap: float,
    avg_lane_length: float,
    nb_lanes: int,
) -> float:
    total_vehicle_space = nb_vehicles * (mean_vehicle_length + mean_gap)
    total_road_space = avg_lane_length * nb_lanes
    return min(
        total_vehicle_space / total_road_space if total_road_space > 0 else 0.0, 1.0
    )


def brut_occupancy(api: SumoConnection, edge: Edge) -> float:
    nb_vehicles = api.edge.getLastStepVehicleNumber(edge.id)
    mean_vehicle_length = api.edge.getLastStepLength(edge.id)
    nb_lanes = api.edge.getLaneNumber(edge.id)
    vehicle_ids = api.edge.getLastStepVehicleIDs(edge.id)

    total_length = total_lane_length(api, edge, nb_lanes)
    avg_lane_length = average_lane_length(total_length, nb_lanes)
    mean_gap = mean_vehicle_gap(api, vehicle_ids)

    return concentration(
        nb_vehicles, mean_vehicle_length, mean_gap, avg_lane_length, nb_lanes
    )


def neighboring_edges(
    net: sumolib.net.Net, x: float, y: float, radius: float
) -> list[tuple[sumolib.net.edge.Edge, float]]:
    """
    Retrieves edges near a given (x, y) point within a radius.
    """
    return net.getNeighboringEdges(x, y, radius)


def find_closest_edge(
    edges_with_distances: list[tuple[sumolib.net.edge.Edge, float]],
) -> sumolib.net.edge.Edge:
    """
    Finds the edge with the smallest distance from a list of edge-distance pairs.
    """
    sorted_edges = sorted(edges_with_distances, key=lambda pair: pair[1])
    return sorted_edges[0][0]


def edge_offset_distance(
    edge: sumolib.net.edge.Edge, point: Tuple[float, float]
) -> tuple[float, float]:
    """
    Computes the offset and distance of a point relative to an edge's shape.
    """
    return sumolib.geomhelper.polygonOffsetAndDistanceToPoint(
        point, edge.getShape(), False
    )


def closest_edge_from_x_y(
    net: sumolib.net.Net,
    x: float,
    y: float,
    radius: float = 3.0,  # TODO: maybe add a constant for the default radius (no magic value)
) -> Optional[Tuple[str, float]]:
    """
    Returns the ID and offset of the closest edge to a given (x, y) point, or None if no edge is found.
    """
    point = (x, y)
    edges_with_distances = neighboring_edges(net, x, y, radius)
    closest_edge = (
        find_closest_edge(edges_with_distances) if edges_with_distances else None
    )

    return (
        (str(closest_edge.getID()), edge_offset_distance(closest_edge, point)[0])
        if closest_edge is not None
        else None
    )


def closest_edge_from_lon_lat(
    lon: float, lat: float, net: sumolib.net.Net, radius: float = 5.0
) -> Optional[tuple[str, float]]:
    x, y = lon_lat_to_x_y(net, lon, lat)
    return closest_edge_from_x_y(net, x, y, radius)

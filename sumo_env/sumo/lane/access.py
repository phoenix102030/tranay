import sumolib

from sumo_env.sumo.edge.access import edge_from_net


def lanes_from_sumo_edge(edge: sumolib.net.edge.Edge) -> list[sumolib.net.lane.Lane]:
    return edge.getLanes()


def lane_ids_from_sumo_lane(lanes: list[sumolib.net.lane.Lane]) -> list[str]:
    return list(map(lambda lane: lane.getID(), lanes))


def lane_ids_from_edge_id(net: sumolib.net.Net, edge_id: str) -> list[str]:
    return lane_ids_from_sumo_lane(lanes_from_sumo_edge(edge_from_net(net, edge_id)))

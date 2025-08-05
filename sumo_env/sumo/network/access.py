from pathlib import Path

import sumolib


def load(file: Path, **kwargs) -> sumolib.net.Net:
    return sumolib.net.readNet(str(file), **kwargs)


def lon_lat_to_x_y(net: sumolib.net.Net, lon: float, lat: float) -> tuple[float, float]:
    return net.convertLonLat2XY(lon, lat)


def get_entry_edges(net: sumolib.net.Net) -> list[sumolib.net.edge.Edge]:
    return [e for e in net.getEdges() if not e.getIncoming()]


def get_exit_edges(net: sumolib.net.Net) -> list[sumolib.net.edge.Edge]:
    return [e for e in net.getEdges() if not e.getOutgoing()]


def is_reachable(
    net: sumolib.net.Net,
    origin: list[sumolib.net.edge.Edge],
    destination: list[sumolib.net.edge.Edge],
) -> bool:
    try:
        path, _ = net.getShortestPath(origin, destination)
        return path is not None
    except Exception:
        return False


def valid_od_pairs(net: sumolib.net.Net) -> list[tuple[str, str]]:
    entries = get_entry_edges(net)
    exits = get_exit_edges(net)

    return [
        (o.getID(), d.getID())
        for o in entries
        for d in exits
        if is_reachable(net, o, d)
    ]

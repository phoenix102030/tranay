MEANDATA_TAG = "meandata"
INTERVAL_TAG = "interval"
EDGE_TAG = "edge"
LANE_TAG = "lane"

BEGIN_ATTR = "begin"
END_ATTR = "end"
ID_ATTR = "id"

COMMON_ATTRIBUTES = {
    "sampledSeconds": float,
    "traveltime": float,
    "density": float,
    "occupancy": float,
    "waitingTime": float,
    "speed": float,
    "departed": int,
    "arrived": int,
    "entered": int,
    "left": int,
    "laneChangedFrom": int,
    "laneChangedTo": int,
}

LANE_SPECIFIC_ATTRIBUTES = {"speedRelative": float}

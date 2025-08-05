import datetime

KPH_TO_MPS = 1000 / 3600


def datetime_to_seconds(dt: datetime.datetime) -> float:
    return dt.timestamp()


def kph_to_mps(speed: float) -> float:
    return speed * KPH_TO_MPS

from pathlib import Path

from attrs import define


@define(frozen=True)
class Network:
    file: Path

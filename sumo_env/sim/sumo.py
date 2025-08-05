import concurrent.futures
from collections.abc import Iterator
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any

import libsumo
import sumolib
import traci

from sumo_env.sim.simu import (
    Connection,
    EmptyCallback,
    SimulationStep,
    SimuLauncher,
    SumoOption,
    Time,
)


def arguments(
    sumocfg: Path,
    params: list[SumoOption] = ["--start", "--no-warnings", "true", "--quit-on-end"],
) -> list[SumoOption]:
    return [
        "-c",
        str(sumocfg),
    ] + params


class SumoConnection:
    def __init__(self, conn: ModuleType, binary_name: str):
        self.conn = conn
        self.binary_name = binary_name

    def start(self, cmd: list[SumoOption]):
        self.conn.start(cmd)

    def step(self, step: Time):
        step_time = self.time() + step
        self.conn.simulationStep(step_time)
        return step_time

    def close(self):
        self.conn.close()

    def time(self) -> Time:
        return self.conn.simulation.getTime()

    def __getattr__(self, name) -> object:
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self.conn, name)

    def binary(self):
        return str(sumolib.checkBinary(self.binary_name))

    # SUMO Properties
    @property
    def lane(self) -> Any:
        return self.conn.lane

    @property
    def edge(self) -> Any:
        return self.conn.edge

    @property
    def vehicle(self) -> Any:
        return self.conn.vehicle


class ConnectionType(Enum):
    traci = 0
    traci_with_gui = 1
    libsumo = 2

    def make(self) -> SumoConnection:
        match self:
            case ConnectionType.libsumo:
                return SumoConnection(libsumo, "sumo")
            case ConnectionType.traci:
                return SumoConnection(traci, "sumo")
            case ConnectionType.traci_with_gui:
                return SumoConnection(traci, "sumo-gui")
            case e:
                raise ValueError(f"Unexpected connextion type: {e}")


def run_sumo(
    conn: Connection,
    options: list[SumoOption],
    step_increment: Time,
    end: Time,
) -> Iterator[SimulationStep]:
    with SimuLauncher(conn, EmptyCallback(), step_increment, end, options) as simu:
        for step in simu:
            yield step


def run_standalone(
    conn: Connection, options: list[SumoOption], step_increment: Time, end: Time
) -> None:
    for _ in run_sumo(conn, options, step_increment, end):
        pass


def run_multi_sumo(
    conn: Connection,
    options_list: list[list[SumoOption]],
    step_increment: Time,
    end: Time,
) -> None:
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                run_standalone,
                conn,
                options,
                step_increment,
                end,
            )
            for options in options_list
        ]
        [future.result() for future in concurrent.futures.as_completed(futures)]

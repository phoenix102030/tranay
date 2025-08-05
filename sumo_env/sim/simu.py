from collections.abc import Iterator
from types import ModuleType
from typing import Protocol

Step = int
Time = float
SimulationStep = tuple[Step, Time]
SumoOption = str


class ConnectionCallback(Protocol):
    def on_start(self) -> None: ...

    def on_close(self) -> None: ...


class EmptyCallback:
    def on_start(self) -> None:
        pass

    def on_close(self) -> None:
        pass


class Connection(Protocol):
    def start(self): ...

    def step(self, time: Time) -> Time: ...

    def close(self): ...

    def time(self) -> Time: ...

    def binary(self) -> str: ...

    def module(self) -> ModuleType: ...


class SimuLauncher:
    def __init__(
        self,
        conn: Connection,
        callback: ConnectionCallback,
        step_increment: Time,
        end: Time,
        options: list[SumoOption],
    ):
        self.conn = conn
        self.callback = callback
        self.step_increment = step_increment
        self.end = end
        self.options = [self.conn.binary(), *options]
        self.count = 0

    def __enter__(self):
        self.conn.start(self.options)
        self.callback.on_start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.callback.on_close()
        self.conn.close()

    def __iter__(self) -> Iterator[SimulationStep]:
        while self.conn.time() < self.end:
            self.count += 1
            yield (self.count, self.conn.step(self.step_increment))

    def api(self) -> Connection:
        return self.conn

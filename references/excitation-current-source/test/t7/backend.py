"""Abstract T7 backend + factory.

Stage scripts talk only to this interface, never to ``labjack.ljm`` directly.
That keeps every procedure runnable with no hardware (``--mock``) and makes the
real LJM path a drop-in swap on the bench.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Sequence


class T7Backend(ABC):
    """Minimal register-level interface mirroring the LJM eRead/eWrite calls."""

    @abstractmethod
    def write_name(self, name: str, value: float) -> None: ...

    @abstractmethod
    def write_names(self, names: Sequence[str], values: Sequence[float]) -> None: ...

    @abstractmethod
    def read_name(self, name: str) -> float: ...

    @abstractmethod
    def read_names(self, names: Sequence[str]) -> List[float]: ...

    @abstractmethod
    def info(self) -> Dict[str, object]: ...

    @abstractmethod
    def close(self) -> None: ...

    # Context-manager sugar so stages can `with get_backend(...) as t7:`
    def __enter__(self) -> "T7Backend":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def get_backend(mock: bool = True, identifier: str = "ANY", **mock_kwargs) -> T7Backend:
    """Return a real or mock backend.

    mock=True (default for hardware-free dry runs) builds a MockT7Backend;
    extra kwargs (config, scenario, seed, ...) pass through to it. mock=False
    opens a real T7 over LJM by ``identifier`` (serial / IP / "ANY").
    """
    if mock:
        from t7.mock_backend import MockT7Backend

        return MockT7Backend(**mock_kwargs)
    from t7.ljm_backend import LJMBackend

    return LJMBackend(identifier=identifier)
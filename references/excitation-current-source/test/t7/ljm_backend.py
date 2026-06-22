"""Real LabJack T7 Pro backend via the LJM library.

Requires the LJM runtime + ``labjack-ljm`` python package (see
``test/requirements.txt``); imported lazily so the mock path needs neither.
Untested against silicon in this repo -- the bench operator validates it in
Stage 1. The mock backend mirrors the same call surface for dry runs.
"""

from __future__ import annotations

from typing import Dict, List, Sequence


class LJMBackend:
    """Thin wrapper over ljm.eReadName / eReadNames / eWriteName(s)."""

    def __init__(self, identifier: str = "ANY", device: str = "T7", connection: str = "ANY"):
        try:
            from labjack import ljm  # noqa: WPS433 (lazy, optional dependency)
        except ImportError as exc:  # pragma: no cover - depends on host install
            raise RuntimeError(
                "labjack-ljm is not installed. Install the LJM runtime and "
                "`pip install labjack-ljm`, or run the stage with --mock."
            ) from exc
        self._ljm = ljm
        self._handle = ljm.openS(device, connection, identifier)

    def write_name(self, name: str, value: float) -> None:
        self._ljm.eWriteName(self._handle, name, value)

    def write_names(self, names: Sequence[str], values: Sequence[float]) -> None:
        self._ljm.eWriteNames(self._handle, len(names), list(names), list(values))

    def read_name(self, name: str) -> float:
        return float(self._ljm.eReadName(self._handle, name))

    def read_names(self, names: Sequence[str]) -> List[float]:
        vals = self._ljm.eReadNames(self._handle, len(names), list(names))
        return [float(v) for v in vals]

    def info(self) -> Dict[str, object]:
        name = self._ljm.eReadNameString(self._handle, "DEVICE_NAME_DEFAULT")
        serial = int(self._ljm.eReadName(self._handle, "SERIAL_NUMBER"))
        fw = self._ljm.eReadName(self._handle, "FIRMWARE_VERSION")
        return {"backend": "ljm", "device_name": name, "serial": serial, "firmware": fw}

    def close(self) -> None:
        try:
            self._ljm.close(self._handle)
        except Exception:  # pragma: no cover - best-effort close
            pass

    def __enter__(self) -> "LJMBackend":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
"""Read PipeWire state without importing a PipeWire Python binding."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any

from .profiles import quantum_ms

_METADATA_RE = re.compile(r"key:'([^']+)'\s+value:'([^']*)'")


@dataclass(frozen=True)
class PipeWireState:
    quantum: int | None = None
    rate: int | None = None
    source: str = "unknown"
    driver: str | None = None
    nodes: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def buffer_ms(self) -> float | None:
        if self.quantum is None or self.rate is None:
            return None
        return quantum_ms(self.quantum, self.rate)

    @property
    def is_complete(self) -> bool:
        return self.quantum is not None and self.rate is not None


def parse_pw_metadata(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, value in _METADATA_RE.findall(text):
        if value:
            values[key] = value
    return values


def _as_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def parse_pw_dump(text: str) -> tuple[int | None, int | None, str | None, tuple[str, ...]]:
    """Return quantum, rate, driver name, and node names from pw-dump JSON."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None, None, None, ()

    if not isinstance(payload, list):
        return None, None, None, ()

    quantum = None
    rate = None
    driver = None
    nodes: list[str] = []

    for item in payload:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "PipeWire:Interface:Node":
            continue
        info = item.get("info")
        props = info.get("props") if isinstance(info, dict) else None
        if not isinstance(props, dict):
            continue

        name = props.get("node.name")
        if isinstance(name, str) and name:
            nodes.append(name)

        node_quantum = _as_int(props.get("clock.quantum"))
        node_rate = _as_int(props.get("clock.rate")) or _as_int(props.get("audio.rate"))
        if quantum is None and node_quantum is not None:
            quantum = node_quantum
        if rate is None and node_rate is not None:
            rate = node_rate

        media_class = props.get("media.class")
        is_driver = props.get("node.driver") is True
        if driver is None and isinstance(name, str) and (
            is_driver or media_class in {"Audio/Sink", "Audio/Source"}
        ):
            driver = name

    return quantum, rate, driver, tuple(nodes)


def _run(args: list[str], timeout: float = 5.0) -> tuple[str | None, str | None]:
    if shutil.which(args[0]) is None:
        return None, f"{args[0]} not found in PATH"
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"{args[0]} failed: {exc}"
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        return None, f"{args[0]} failed: {message}"
    return proc.stdout, None


def collect_state() -> PipeWireState:
    warnings: list[str] = []
    metadata_text, metadata_error = _run(["pw-metadata", "-n", "settings"])
    dump_text, dump_error = _run(["pw-dump"])

    if metadata_error:
        warnings.append(metadata_error)
    if dump_error:
        warnings.append(dump_error)

    metadata = parse_pw_metadata(metadata_text or "")
    dump_quantum, dump_rate, driver, nodes = parse_pw_dump(dump_text or "")

    meta_quantum = _as_int(metadata.get("clock.force-quantum"))
    meta_rate = _as_int(metadata.get("clock.force-rate"))

    quantum = meta_quantum or dump_quantum
    rate = meta_rate or dump_rate
    source = "pw-metadata" if meta_quantum or meta_rate else "pw-dump"

    return PipeWireState(
        quantum=quantum,
        rate=rate,
        source=source,
        driver=driver,
        nodes=nodes,
        warnings=tuple(warnings),
    )

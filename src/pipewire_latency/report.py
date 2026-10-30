"""Human and machine readable output."""

from __future__ import annotations

import json
from pathlib import Path

from .profiles import Profile
from .state import PipeWireState


def state_payload(state: PipeWireState, profile: Profile | None = None, config_path: Path | None = None) -> dict:
    payload: dict = {
        "quantum": state.quantum,
        "rate": state.rate,
        "buffer_ms": round(state.buffer_ms, 3) if state.buffer_ms is not None else None,
        "source": state.source,
        "driver": state.driver,
        "nodes": list(state.nodes),
        "warnings": list(state.warnings),
    }
    if profile is not None:
        payload["profile"] = {
            "name": profile.name,
            "quantum": profile.quantum,
            "rate": profile.rate,
            "buffer_ms": round(profile.buffer_ms, 3),
        }
    if config_path is not None:
        payload["config_path"] = str(config_path)
        payload["config_exists"] = config_path.exists()
    return payload


def render_json(state: PipeWireState, profile: Profile | None = None, config_path: Path | None = None) -> str:
    return json.dumps(state_payload(state, profile, config_path), indent=2)


def render_info(state: PipeWireState) -> str:
    lines = [
        "PipeWire state",
        f"  quantum : {state.quantum if state.quantum is not None else 'unknown'}",
        f"  rate    : {state.rate if state.rate is not None else 'unknown'} Hz",
        f"  buffer  : {state.buffer_ms:.3f} ms" if state.buffer_ms is not None else "  buffer  : unknown",
        f"  source  : {state.source}",
        f"  driver  : {state.driver or 'unknown'}",
        f"  nodes   : {len(state.nodes)}",
    ]
    if state.warnings:
        lines.append("  warnings:")
        lines.extend(f"    - {warning}" for warning in state.warnings)
    return "\n".join(lines)


def render_report(
    state: PipeWireState,
    profile: Profile | None,
    config_path: Path,
) -> str:
    lines = [
        "# PipeWire latency report",
        "",
        "## Active graph",
        "",
        f"- Quantum: `{state.quantum if state.quantum is not None else 'unknown'}`",
        f"- Sample rate: `{state.rate if state.rate is not None else 'unknown'}` Hz",
    ]
    if state.buffer_ms is not None:
        lines.append(f"- Buffer latency: `{state.buffer_ms:.3f}` ms")
    lines.extend(
        [
            f"- Source: `{state.source}`",
            f"- Driver: `{state.driver or 'unknown'}`",
            f"- Nodes: `{len(state.nodes)}`",
            "",
            "## Config",
            "",
            f"- Path: `{config_path}`",
            f"- Present: `{'yes' if config_path.exists() else 'no'}`",
        ]
    )
    if profile is not None:
        lines.extend(
            [
                "",
                "## Suggested profile",
                "",
                f"- Name: `{profile.name}`",
                f"- Quantum: `{profile.quantum}`",
                f"- Rate: `{profile.rate}` Hz",
                f"- Buffer latency: `{profile.buffer_ms:.3f}` ms",
                f"- {profile.description}",
            ]
        )
    if state.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in state.warnings)
    lines.extend(
        [
            "",
            "## Note",
            "",
            "Buffer latency is quantum divided by sample rate. Round-trip latency",
            "also includes the interface, kernel, and application buffers.",
            "",
        ]
    )
    return "\n".join(lines)

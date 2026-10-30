"""Latency profiles and the small amount of math behind them."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    name: str
    quantum: int
    rate: int
    min_quantum: int
    max_quantum: int
    description: str

    @property
    def buffer_ms(self) -> float:
        return quantum_ms(self.quantum, self.rate)


PROFILES: dict[str, Profile] = {
    "safe": Profile(
        name="safe",
        quantum=1024,
        rate=48000,
        min_quantum=256,
        max_quantum=8192,
        description="High stability, higher latency. Good for weak systems and Bluetooth.",
    ),
    "balanced": Profile(
        name="balanced",
        quantum=256,
        rate=48000,
        min_quantum=64,
        max_quantum=2048,
        description="Default desktop profile. Small latency without chasing xruns.",
    ),
    "gaming": Profile(
        name="gaming",
        quantum=64,
        rate=48000,
        min_quantum=16,
        max_quantum=1024,
        description="Low latency for competitive games. Needs a stable audio interface.",
    ),
    "music": Profile(
        name="music",
        quantum=128,
        rate=48000,
        min_quantum=32,
        max_quantum=1024,
        description="Low latency for live monitoring and soft synths.",
    ),
    "pro-audio": Profile(
        name="pro-audio",
        quantum=32,
        rate=48000,
        min_quantum=16,
        max_quantum=512,
        description="Aggressive low latency. Expect xruns on USB and onboard audio.",
    ),
}


def get_profile(name: str) -> Profile:
    try:
        return PROFILES[name]
    except KeyError as exc:
        names = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile '{name}'. Expected one of: {names}") from exc


def quantum_ms(quantum: int, rate: int) -> float:
    if quantum <= 0:
        raise ValueError("quantum must be positive")
    if rate <= 0:
        raise ValueError("rate must be positive")
    return (quantum / rate) * 1000.0

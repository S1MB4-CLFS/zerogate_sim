from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a ZeroGateSim demo run."""

    seed: int = 42
    n_steps: int = 600
    dt: float = 0.05
    noise_floor: float = 0.12
    near_zero_ratio: float = 0.12
    gate_threshold: float = 0.55
    strength_threshold: float = 0.40
    output_dir: Path = Path("runs/demo_seed_42")

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["output_dir"] = str(self.output_dir)
        return data

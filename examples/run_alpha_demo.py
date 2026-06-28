from pathlib import Path

from zerogate_sim.config import SimulationConfig
from zerogate_sim.demo import run_demo


if __name__ == "__main__":
    config = SimulationConfig(seed=42, output_dir=Path("runs/example_seed_42"))
    paths = run_demo(config)
    print("Generated:")
    for key, value in paths.items():
        print(f"{key}: {value}")

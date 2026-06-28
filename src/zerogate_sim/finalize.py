from __future__ import annotations

import argparse
import csv
from pathlib import Path

from zerogate_sim.final_output import build_final_output_rows_from_earned_rows, write_final_output_rows
from zerogate_sim.reporting import write_evidence_bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create final trinary output from an existing ZeroGateSim matrix directory without rerunning the simulation."
    )
    parser.add_argument("--matrix-dir", type=Path, required=True, help="Existing matrix output directory containing matrix_earned_one_summary.csv.")
    parser.add_argument("--no-bundle", action="store_true", help="Do not rebuild matrix_bundle.zip after writing final output files.")
    return parser


def read_earned_rows(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def finalize_matrix_dir(matrix_dir: Path, *, make_bundle: bool = True) -> dict[str, Path]:
    matrix_dir = Path(matrix_dir)
    earned_csv = matrix_dir / "matrix_earned_one_summary.csv"
    if not earned_csv.exists():
        raise FileNotFoundError(f"Required file not found: {earned_csv}")
    rows = build_final_output_rows_from_earned_rows(read_earned_rows(earned_csv))
    paths = write_final_output_rows(matrix_dir, rows)
    if make_bundle:
        paths["matrix_bundle"] = write_evidence_bundle(
            matrix_dir,
            bundle_name="matrix_bundle.zip",
            bundle_kind="zerogate_trinary_matrix_evidence_bundle",
        )
    return paths


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = finalize_matrix_dir(args.matrix_dir, make_bundle=not args.no_bundle)
    print("ZeroGateSim final trinary output complete.")
    for name, path in paths.items():
        print(f"- {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
from pathlib import Path

from zerogate_sim.v1_8_2_numeric_contract import (
    BACKEND_CODES,
    BACKEND_LINEAGES,
    CASES_PER_BACKEND,
    GENERATOR_CONTRACT_ID,
    REPLICATES_PER_REGIME,
    ROOT_SEED,
    TOTAL_CASES,
    VERSION,
    DevelopmentDataError,
    canonical_json,
    generator_contract_sha256,
    sha256_bytes,
    validate_recipe,
    write_canonical_json_exclusive,
    write_exclusive,
)

ROLES = ("expresser", "latent", "trap")
ENVELOPES = (
    ((0.82, 0.78, 0.84), (0.28, 0.74, 0.86), (0.84, 0.15, 0.84), (0.72, 0.48, 0.80)),
    ((0.56, 0.53, 0.57), (0.74, 0.62, 0.48), (0.30, 0.52, 0.60), (0.60, 0.28, 0.56)),
    ((0.14, 0.18, 0.86), (0.20, 0.22, 0.84), (0.18, 0.28, 0.82), (0.72, 0.22, 0.15)),
)
AMPLITUDE_MULTIPLIERS = (0.94, 1.0, 1.06)
FREQUENCIES = (12.0, 13.0, 14.0)
NOISE_SCALES = (0.018, 0.028, 0.038)
RELATION_MIXES = (0.28, 0.34, 0.40)

SPLIT_FILES = {
    "recipes": Path("public") / "development_numeric_recipes.jsonl",
    "join_keys": Path("sealed") / "development_join_keys.csv",
    "label_vault": Path("sealed") / "development_label_vault.csv",
    "group_vault": Path("sealed") / "development_group_vault.csv",
    "manifest": Path("development_split_manifest.json"),
    "receipt": Path("development_split_receipt.json"),
}


def _u64(*parts: object) -> int:
    data = ":".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big")


def _u01(*parts: object) -> float:
    return _u64(*parts) / float(2**64)


def _blind_id(root_seed: int, row_index: int) -> str:
    digest = hashlib.sha256(f"zg82:{root_seed}:{row_index}".encode("ascii")).hexdigest()
    return f"zg82_{digest[:24]}"


def _atomic_case_id(root_seed: int, row_index: int) -> str:
    digest = hashlib.sha256(f"zg82-atomic:{root_seed}:{row_index}".encode("ascii")).hexdigest()
    return f"za82_{digest[:24]}"


def _backend_parameters(backend_code: int, replicate: int) -> list[float]:
    if backend_code == 0:
        return [(0.72, 0.82, 0.90)[replicate]]
    if backend_code == 1:
        return [(0.93, 0.95, 0.97)[replicate]]
    if backend_code == 2:
        return [(1.2, 1.6, 2.0)[replicate]]
    return [(0.42, 0.48, 0.54)[replicate], (0.020, 0.030, 0.040)[replicate]]


def build_recipe_rows(
    *, root_seed: int = ROOT_SEED
) -> tuple[list[dict[str, object]], list[tuple[str, str, str, str]]]:
    if type(root_seed) is not int or root_seed != ROOT_SEED:
        raise DevelopmentDataError(f"root_seed is locked to {ROOT_SEED}")
    recipes: list[dict[str, object]] = []
    sealed: list[tuple[str, str, str, str]] = []
    row_index = 0
    for backend_code in BACKEND_CODES:
        for role_index, role in enumerate(ROLES):
            for archetype_index in range(4):
                regime_code = role_index * 4 + archetype_index
                for replicate in range(REPLICATES_PER_REGIME):
                    multiplier = AMPLITUDE_MULTIPLIERS[replicate]
                    envelope = [
                        min(0.96, round(value * multiplier, 12))
                        for value in ENVELOPES[role_index][archetype_index]
                    ]
                    late_echo = role_index == 2 and archetype_index == 1
                    echo_mix = (0.62, 0.68, 0.74)[replicate] if late_echo else (0.08, 0.12, 0.16)[replicate]
                    peer_coherence = (0.86, 0.90, 0.94)[replicate] if late_echo else (0.14, 0.20, 0.26)[replicate]
                    # Keep the convex mixture valid for echo-heavy cases without
                    # changing the nuisance relation values elsewhere.
                    relation_mix = 0.10 if late_echo else RELATION_MIXES[replicate]
                    seed = _u64(root_seed, backend_code, regime_code, replicate)
                    recipe = {
                        "backend_code": backend_code,
                        "backend_parameters": _backend_parameters(backend_code, replicate),
                        "echo_mix": echo_mix,
                        "envelope": envelope,
                        "frequency": FREQUENCIES[replicate],
                        "noise_scale": NOISE_SCALES[replicate],
                        "peer_coherence": peer_coherence,
                        "phase": round(2.0 * math.pi * _u01(seed, "phase"), 15),
                        "regime_code": regime_code,
                        "relation_mix": relation_mix,
                        "replicate_code": replicate,
                        "row_index": row_index,
                        "seed_u64": seed,
                    }
                    recipes.append(validate_recipe(recipe, source=f"recipe {row_index}"))
                    sealed.append(
                        (
                            _blind_id(root_seed, row_index),
                            role,
                            BACKEND_LINEAGES[backend_code],
                            _atomic_case_id(root_seed, row_index),
                        )
                    )
                    row_index += 1
    if len(recipes) != TOTAL_CASES or row_index != TOTAL_CASES:
        raise DevelopmentDataError("development recipe construction did not produce 144 rows")
    return recipes, sealed


def _csv_bytes(header: tuple[str, ...], rows: list[tuple[object, ...]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def build_development_split(out: str | Path, *, root_seed: int = ROOT_SEED) -> dict[str, Path]:
    output_dir = Path(out)
    if output_dir.exists() and (not output_dir.is_dir() or output_dir.is_symlink() or any(output_dir.iterdir())):
        raise DevelopmentDataError(f"development split output must be an empty safe directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: output_dir / relative for name, relative in SPLIT_FILES.items()}
    recipes, sealed = build_recipe_rows(root_seed=root_seed)
    recipe_bytes = "".join(canonical_json(row) + "\n" for row in recipes).encode("utf-8")
    join_rows = [(index, blind_id) for index, (blind_id, _, _, _) in enumerate(sealed)]
    label_rows = [(blind_id, role) for blind_id, role, _, _ in sealed]
    group_rows = [(blind_id, lineage, atomic_id) for blind_id, _, lineage, atomic_id in sealed]
    write_exclusive(paths["recipes"], recipe_bytes)
    write_exclusive(paths["join_keys"], _csv_bytes(("row_index", "blind_case_id"), join_rows))
    write_exclusive(paths["label_vault"], _csv_bytes(("blind_case_id", "evaluation_role"), label_rows))
    write_exclusive(
        paths["group_vault"],
        _csv_bytes(
            ("blind_case_id", "generator_lineage_id", "atomic_case_id"),
            group_rows,
        ),
    )
    manifest = {
        "version": VERSION,
        "manifest_state": "SEALED_CLASS_CONDITIONED_DEVELOPMENT_SPLIT",
        "generator_contract_id": GENERATOR_CONTRACT_ID,
        "generator_contract_sha256": generator_contract_sha256(),
        "row_count": TOTAL_CASES,
        "cases_per_backend": CASES_PER_BACKEND,
        "recipe_sha256": sha256_bytes(recipe_bytes),
        "join_key_sha256": sha256_bytes(paths["join_keys"].read_bytes()),
        "label_vault_sha256": sha256_bytes(paths["label_vault"].read_bytes()),
        "group_vault_sha256": sha256_bytes(paths["group_vault"].read_bytes()),
        "generator_construction": "class_conditioned_controlled_synthetic_recipes",
        "public_recipes_contain_roles_ids_or_semantic_archetype_names": False,
        "raw_generator_reads_sealed_vaults": False,
        "observable_extractor_is_label_free": True,
        "sealed_vaults_must_not_be_opened_before_score_freeze": True,
    }
    write_canonical_json_exclusive(paths["manifest"], manifest)
    receipt = {
        "version": VERSION,
        "receipt_state": "CALLER_RETAINED_DEVELOPMENT_SPLIT_ROOT",
        "split_manifest_sha256": sha256_bytes(paths["manifest"].read_bytes()),
        "recipe_sha256": manifest["recipe_sha256"],
        "join_key_sha256": manifest["join_key_sha256"],
        "label_vault_sha256": manifest["label_vault_sha256"],
        "group_vault_sha256": manifest["group_vault_sha256"],
        "generator_contract_sha256": manifest["generator_contract_sha256"],
        "row_count": TOTAL_CASES,
        "external_timestamp_proof": False,
    }
    write_canonical_json_exclusive(paths["receipt"], receipt)
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the one-pass v1.8.2 development data chain without opening labels."
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.out
    if root.exists():
        raise DevelopmentDataError(f"CLI output must not already exist: {root}")
    root.mkdir(parents=True, exist_ok=False)

    # Imports stay inside the orchestration entry point. The raw generator and
    # extractor modules themselves never import this sealed split authority.
    from zerogate_sim.v1_8_2_development_fingerprint import build_development_fingerprint
    from zerogate_sim.v1_8_2_observable_extractor import extract_development_observables
    from zerogate_sim.v1_8_2_raw_generators import generate_raw_development_corpus
    from zerogate_sim.v1_8_predictor_package import verify_predictor_package

    split = build_development_split(root / "split")
    recipe_sha = sha256_bytes(split["recipes"].read_bytes())
    raw = generate_raw_development_corpus(
        split["recipes"],
        root / "raw_generation",
        expected_recipe_sha256=recipe_sha,
    )
    raw_sha = sha256_bytes(raw["manifest"].read_bytes())
    extracted = extract_development_observables(
        raw["manifest"],
        root / "extraction",
        expected_raw_manifest_sha256=raw_sha,
    )
    extraction_sha = sha256_bytes(extracted["extraction_manifest"].read_bytes())
    observable_sha = sha256_bytes(extracted["observable_inputs"].read_bytes())
    source_sha = sha256_bytes(extracted["source_manifest"].read_bytes())
    fingerprint = build_development_fingerprint(
        extraction_manifest_path=extracted["extraction_manifest"],
        observable_input_path=extracted["observable_inputs"],
        recipe_path=split["recipes"],
        raw_manifest_path=raw["manifest"],
        source_manifest_path=extracted["source_manifest"],
        out=root / "development_fingerprint.json",
        expected_extraction_manifest_sha256=extraction_sha,
        expected_observable_input_sha256=observable_sha,
        expected_recipe_sha256=recipe_sha,
        expected_raw_manifest_sha256=raw_sha,
        expected_source_manifest_sha256=source_sha,
    )
    package = verify_predictor_package()
    retained = (
        ("split_receipt", split["receipt"]),
        ("observable_inputs", extracted["observable_inputs"]),
        ("source_manifest", extracted["source_manifest"]),
        ("development_fingerprint", fingerprint),
    )
    for name, path in retained:
        print(f"{name}={path} sha256={sha256_bytes(path.read_bytes())}")
    print(f"v1_8_1_package_contract_sha256={package.contract_sha256}")
    print(f"v1_8_1_schema_sha256={package.schema_sha256}")
    print(f"v1_8_1_predictor_config_sha256={package.predictor_config_sha256}")
    print(f"v1_8_1_development_plan_sha256={package.development_plan_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

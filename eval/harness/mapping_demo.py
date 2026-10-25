"""Print CAWASMA CVSS v3.1 environmental-score examples.

The five examples are real checks: their base vectors are read from
config/checks.yaml, so the numbers in docs/cvss-mapping.md match what the
scanner will score. Requires the ``cvss`` package (in the ml extra). Run from
the repository root:

    python eval/harness/mapping_demo.py
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "config" / "cvss_mapping.yaml"
CHECKS_PATH = ROOT / "config" / "checks.yaml"

# Same finding on a public page vs an admin endpoint, for five checks.
EXAMPLE_IDS = ["HDR-001", "HDR-002", "HDR-007", "CKI-001", "API-003"]


def examples() -> list[tuple[str, str, str]]:
    """(check_id, title, base vector) for each example, from checks.yaml."""
    checks = {c["check_id"]: c for c in yaml.safe_load(CHECKS_PATH.read_text())["checks"]}
    return [(cid, checks[cid]["title"], checks[cid]["base_cvss_vector"]) for cid in EXAMPLE_IDS]


def environmental_score(vector: str, requirements: dict[str, str]) -> float:
    from cvss import CVSS3

    suffix = "/".join(f"{name}:{requirements[name]}" for name in ("CR", "IR", "AR"))
    return CVSS3(f"{vector}/{suffix}").environmental_score


def main() -> None:
    from cvss import CVSS3

    mapping = yaml.safe_load(MAPPING_PATH.read_text())
    public = mapping["sensitivity_classes"]["LOW"]
    admin = mapping["sensitivity_classes"]["CRITICAL"]

    print("CAWASMA CVSS v3.1 environmental mapping examples")
    print("public=LOW, admin=CRITICAL; modified base metrics remain undefined")
    print()
    for check_id, title, vector in examples():
        base = CVSS3(vector).base_score
        public_score = environmental_score(vector, public)
        admin_score = environmental_score(vector, admin)
        print(
            f"{check_id} {title}: base={base:.1f} public={public_score:.1f} "
            f"admin={admin_score:.1f}"
        )


if __name__ == "__main__":
    main()

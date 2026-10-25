"""Print CAWASMA CVSS v3.1 environmental-score examples.

Requires the ``cvss`` package. Run from the repository root:

    python eval/harness/mapping_demo.py
"""
from __future__ import annotations

from pathlib import Path

import yaml
from cvss import CVSS3

ROOT = Path(__file__).resolve().parents[2]
MAPPING_PATH = ROOT / "config" / "cvss_mapping.yaml"

EXAMPLES = [
    (
        "Missing HSTS",
        "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:N/A:N",
    ),
    (
        "Missing CSP",
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N",
    ),
    (
        "Version disclosure",
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N",
    ),
    (
        "Missing session cookie HttpOnly",
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N",
    ),
    (
        "Unauthenticated sensitive endpoint",
        "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
    ),
]


def environmental_score(vector: str, requirements: dict[str, str]) -> float:
    suffix = "/".join(f"{name}:{requirements[name]}" for name in ("CR", "IR", "AR"))
    return CVSS3(f"{vector}/{suffix}").environmental_score


def main() -> None:
    mapping = yaml.safe_load(MAPPING_PATH.read_text())
    public = mapping["sensitivity_classes"]["LOW"]
    admin = mapping["sensitivity_classes"]["CRITICAL"]

    print("CAWASMA CVSS v3.1 environmental mapping examples")
    print("public=LOW, admin=CRITICAL; modified base metrics remain undefined")
    print()
    for name, vector in EXAMPLES:
        base = CVSS3(vector).base_score
        public_score = environmental_score(vector, public)
        admin_score = environmental_score(vector, admin)
        print(
            f"{name}: base={base:.1f} public={public_score:.1f} "
            f"admin={admin_score:.1f}"
        )


if __name__ == "__main__":
    main()

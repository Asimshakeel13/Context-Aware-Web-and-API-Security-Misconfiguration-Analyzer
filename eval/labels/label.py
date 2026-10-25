"""Interactive sensitivity labeller for endpoints_raw.csv."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "eval" / "labels" / "endpoints_raw.csv"
OUTPUT = ROOT / "eval" / "labels" / "endpoints_labelled.csv"
CLASSES = {
    "1": "LOW",
    "2": "MEDIUM",
    "3": "HIGH",
    "4": "CRITICAL",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"missing {path}; run collect_endpoints.py first")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_labels(path: Path) -> dict[tuple[str, str, str], dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {
            (row["target"], row["method"], row["path"]): row
            for row in csv.DictReader(handle)
        }


def write_labels(path: Path, labels: dict[tuple[str, str, str], dict[str, str]]) -> None:
    fields = ["target", "method", "path", "sensitivity_class", "labeler", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(labels[key] for key in sorted(labels))


def main() -> int:
    rows = read_rows(INPUT)
    labels = read_labels(OUTPUT)
    pending = [
        row for row in rows
        if (row["target"], row["method"], row["path"]) not in labels
    ]
    print(f"{len(labels)} labelled, {len(pending)} remaining")
    for row in pending:
        key = (row["target"], row["method"], row["path"])
        print(f"\n{len(labels) + 1}: [{row['target']}] {row['method']} {row['path']}")
        print("1 LOW  2 MEDIUM  3 HIGH  4 CRITICAL  s skip  q save and quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            break
        if choice == "s":
            continue
        if choice not in CLASSES:
            print("Invalid choice; this endpoint remains pending.")
            continue
        labels[key] = {
            **row,
            "sensitivity_class": CLASSES[choice],
            "labeler": input("labeler (optional): ").strip(),
            "notes": input("notes (optional): ").strip(),
        }
        write_labels(OUTPUT, labels)
    write_labels(OUTPUT, labels)
    print(f"saved {len(labels)} labels to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

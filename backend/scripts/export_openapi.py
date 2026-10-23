"""Write the OpenAPI document to docs/openapi.json (make openapi).

    python scripts/export_openapi.py           # write the file
    python scripts/export_openapi.py --check   # exit 1 if the file is out of date

The committed file is what the frontend generates its client from; CI and the
test suite fail when it no longer matches the code.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.main import create_app

OUTPUT = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def render() -> str:
    return json.dumps(create_app().openapi(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only verify the file is current")
    args = parser.parse_args(argv)
    current = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != current:
            print(f"{OUTPUT} is out of date: run `make openapi` and commit it.")
            return 1
        print(f"{OUTPUT} is up to date.")
        return 0
    OUTPUT.write_text(current, encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

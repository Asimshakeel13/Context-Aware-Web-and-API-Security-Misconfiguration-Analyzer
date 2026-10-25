"""Collect bounded, same-origin endpoint paths from CAWASMA evaluation targets."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "eval" / "labels" / "endpoints_raw.csv"
TARGETS = {
    "juice-shop": "http://127.0.0.1:3001",
    "dvwa": "http://127.0.0.1:3002",
    "vampi": "http://127.0.0.1:3003",
    "crapi": "http://127.0.0.1:3004",
}
OPENAPI_PATHS = ("/openapi.json", "/swagger.json", "/api-docs", "/openapi.yaml")
MAX_PAGES = 80
MAX_BODY = 1_000_000
ID_SEGMENT = re.compile(r"^(?:\d+|[0-9a-f]{8}-[0-9a-f-]{4,}|[0-9a-f]{24})$", re.I)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src", "action"} and value:
                self.links.add(value)


def fetch(url: str) -> tuple[str, str] | None:
    try:
        request = Request(url, headers={"User-Agent": "CAWASMA-eval-endpoint-collector"})
        with urlopen(request, timeout=8) as response:
            body = response.read(MAX_BODY)
            content_type = response.headers.get("Content-Type", "")
            return body.decode("utf-8", errors="replace"), content_type
    except (OSError, URLError):
        return None


def normalize_path(path: str) -> str:
    parsed = urlparse(path)
    clean = parsed.path or "/"
    parts = [segment for segment in clean.split("/") if segment]
    normalized = [":id" if ID_SEGMENT.fullmatch(segment) else segment for segment in parts]
    result = "/" + "/".join(normalized)
    return result if result != "/" else result


def add_openapi_paths(base: str, rows: set[tuple[str, str]]) -> None:
    for candidate in OPENAPI_PATHS:
        result = fetch(urljoin(base, candidate))
        if not result:
            continue
        body, content_type = result
        try:
            if candidate.endswith(".yaml") or "yaml" in content_type:
                import yaml
                document = yaml.safe_load(body)
            else:
                document = json.loads(body)
        except (ValueError, TypeError):
            continue
        if isinstance(document, dict) and isinstance(document.get("paths"), dict):
            for path, operation_map in document["paths"].items():
                if isinstance(path, str) and isinstance(operation_map, dict):
                    for method in operation_map:
                        if method.lower() in {"get", "head", "options", "post", "put", "patch", "delete"}:
                            rows.add((method.upper(), normalize_path(path)))
            return


def crawl(base: str, rows: set[tuple[str, str]]) -> None:
    origin = urlparse(base).netloc
    queue: deque[str] = deque([base])
    seen: set[str] = set()
    while queue and len(seen) < MAX_PAGES:
        url = queue.popleft()
        parsed = urlparse(url)
        if parsed.netloc != origin or url in seen:
            continue
        seen.add(url)
        result = fetch(url)
        if not result:
            continue
        body, content_type = result
        rows.add(("GET", normalize_path(url)))
        if "html" not in content_type.lower():
            continue
        parser = LinkParser()
        parser.feed(body)
        for link in parser.links:
            child = urljoin(url, link)
            child_parsed = urlparse(child)
            if child_parsed.netloc == origin and child_parsed.scheme in {"http", "https"}:
                rows.add(("GET", normalize_path(child)))
                if child not in seen:
                    queue.append(child)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help=f"subset of: {', '.join(TARGETS)}")
    parser.add_argument("--base-url", action="append", default=[], metavar="NAME=URL",
                        help="scan NAME at URL instead of the defaults (repeatable)")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)

    if args.base_url:
        targets = dict(item.split("=", 1) for item in args.base_url if "=" in item)
        bad = [url for url in targets.values() if urlparse(url).scheme not in {"http", "https"}]
        if len(targets) != len(args.base_url) or bad:
            print("--base-url must be NAME=http(s)://host[:port]", file=sys.stderr)
            return 2
    else:
        unknown = sorted(set(args.targets) - set(TARGETS))
        if unknown:
            print(f"unknown target(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        targets = {name: TARGETS[name] for name in args.targets} if args.targets else TARGETS

    output_rows: set[tuple[str, str, str]] = set()
    empty: list[str] = []
    for target, base in targets.items():
        rows: set[tuple[str, str]] = set()
        add_openapi_paths(base, rows)
        crawl(base, rows)
        print(f"{target}: {len(rows)} endpoints from {base}", file=sys.stderr)
        if not rows:
            empty.append(target)
        output_rows.update((target, method, path) for method, path in rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["target", "method", "path"])
        writer.writerows(sorted(output_rows))
    print(f"wrote {len(output_rows)} endpoint rows to {args.output}")
    if empty:
        # An unreachable target must not look like a target with no endpoints.
        print(f"FAILED: no endpoints from {', '.join(empty)} (is it running and reachable?)",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

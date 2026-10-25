"""Convert the CAWASMA planning PDFs to Markdown (one-off import tool).

Heading levels, bold, inline code, code blocks and bullets are inferred from
the documents' consistent fonts; tables come from PyMuPDF's table finder.

    python pdf2md.py input.pdf output.md "Source note"
"""
from __future__ import annotations

import collections
import re
import sys

import pymupdf

CODE_BLOCK_SIZE = 10.5          # prompts are set as mono 10.5 blocks
FOOTER = re.compile(r"^Page \d+ of \d+$")
ITEM_START = re.compile(r"^(\d+\.|[a-z]\)|[-·•])\s")
ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\ufeff]")


def is_mono(span: dict) -> bool:
    return "Mono" in span["font"]


def is_bold(span: dict) -> bool:
    return "Semib" in span["font"] or "Bold" in span["font"]


def inline(spans: list[dict]) -> str:
    """Join spans of one line, wrapping bold and inline code."""
    out, prev_style = [], None
    for s in spans:
        text = s["text"]
        if not text:
            continue
        style = "code" if is_mono(s) else "bold" if is_bold(s) else None
        if style == prev_style and out:
            out[-1] = (out[-1][0] + text, style)
        else:
            out.append((text, style))
        prev_style = style
    parts = []
    for text, style in out:
        core, lead, trail = text.strip(), text[: len(text) - len(text.lstrip())], text[len(text.rstrip()):]
        if not core:
            parts.append(text)
        elif style == "code":
            parts.append(f"{lead}`{core}`{trail}")
        elif style == "bold":
            parts.append(f"{lead}**{core}**{trail}")
        else:
            parts.append(text)
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def table_rows(extracted: list[list[str | None]]) -> tuple[list[list[str]], list[int]]:
    """Cell text cleaned, empty rows/columns dropped, and 'echo' columns removed:
    a column whose cells only repeat the text of the other columns (a misread frame)."""
    def cell(c: str | None) -> str:
        c = re.sub(r"(\w)-\n(\w)", r"\1-\2", c or "")   # "FR-\n01" -> "FR-01"
        return c.replace("\n", " ").replace("|", "\\|").strip()

    rows = [[cell(c) for c in row] for row in extracted]
    rows = [r for r in rows if any(r)]
    width = max((len(r) for r in rows), default=0)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = []
    for col in range(width):
        values = [r[col] for r in rows]
        if not any(values):
            continue
        rest = [_squash("".join(r[c] for c in range(width) if c != col)) for r in rows]
        tested = [(v, other) for v, other in zip(values, rest) if v and other]
        if tested and all(other in _squash(v) for v, other in tested):
            continue   # this column only repeats text that is in the other columns
        keep.append(col)
    return [[r[c] for c in keep] for r in rows if any(r[c] for c in keep)], keep


def table_md(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return lines


def analyse(doc) -> tuple[dict[float, str], set[str], float]:
    """Heading sizes (largest first -> #, ##, ###), repeated small lines, body size."""
    chars: collections.Counter = collections.Counter()
    heading_like: collections.Counter = collections.Counter()
    small_lines: collections.Counter = collections.Counter()
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for sp in l["spans"]:
                    n = len(sp["text"].strip())
                    size = round(sp["size"], 1)
                    chars[size] += n
                    if ("Serif" in sp["font"] or is_bold(sp)) and not is_mono(sp):
                        heading_like[size] += n
    body = chars.most_common(1)[0][0]
    for page in doc:
        seen = set()
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                spans = [sp for sp in l["spans"] if sp["text"].strip()]
                if spans and max(sp["size"] for sp in spans) < body * 0.7:
                    seen.add("".join(sp["text"] for sp in spans).strip())
        small_lines.update(seen)
    sizes = sorted((sz for sz, n in heading_like.items()
                    if sz > body + 0.3 and n == chars[sz]), reverse=True)[:3]
    headings = dict(zip(sizes, ["#", "##", "###"]))
    running = {t for t, pages in small_lines.items() if pages >= 2}
    return headings, running, body


def convert(path: str) -> list[tuple[str, object]]:
    """Return a flat list of (kind, payload) elements in reading order."""
    elements: list[tuple[str, object]] = []
    doc = pymupdf.open(path)
    headings, running, body = analyse(doc)
    for page in doc:
        # Reject false tables: one-row ones are shaded code spans; a page frame
        # shows up as a "table" that contains real tables or whole paragraphs.
        found = [t for t in page.find_tables(strategy="lines").tables
                 if t.row_count >= 2 and t.col_count >= 2]
        tables, cleaned, boxes = [], {}, []
        for t in found:
            outer = pymupdf.Rect(t.bbox)
            contains_other = any(o is not t and outer.contains(pymupdf.Rect(o.bbox)) for o in found)
            rows, keep = table_rows(t.extract())   # extract now: it reads the page lazily
            longest = max((len(c) for row in rows for c in row), default=0)
            if rows and not contains_other and longest <= 600:
                tables.append(t)
                cleaned[id(t)] = rows
                # Skip text only inside the kept cells, not under a dropped frame column.
                box = pymupdf.Rect()
                for row in t.rows:
                    for c in keep:
                        if c < len(row.cells) and row.cells[c] is not None:
                            box |= pymupdf.Rect(row.cells[c])
                boxes.append(box if not box.is_empty else outer)
        # List bullets are drawn as small shapes, not text: remember where they are.
        markers = [(d["rect"].x1, (d["rect"].y0 + d["rect"].y1) / 2)
                   for d in page.get_drawings()
                   if d["rect"].width < 8 and d["rect"].height < 8 and d.get("fill")]
        items: list[tuple[float, str, object]] = [(t.bbox[1], "table", cleaned[id(t)])
                                                  for t in tables]
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                rect = pymupdf.Rect(line["bbox"])
                if any(b.intersects(rect) for b in boxes):
                    continue
                size = round(max(s["size"] for s in spans), 1)
                text = "".join(s["text"] for s in spans).strip()
                # Only small text is a running header: the title can repeat its words.
                if (size < body * 0.7 and text in running) or FOOTER.match(text):
                    continue
                if all(is_mono(s) for s in spans) and round(spans[0]["size"], 1) == CODE_BLOCK_SIZE:
                    raw = "".join(s["text"] for s in line["spans"])
                    items.append((rect.y0, "code", (rect.x0, raw.rstrip())))
                elif size in headings and not any(is_mono(s) for s in spans):
                    items.append((rect.y0, "heading", (headings[size], text)))
                else:
                    text_md = inline(line["spans"])
                    mid = (rect.y0 + rect.y1) / 2
                    if any(abs(my - mid) <= rect.height / 2 + 1 and 0 < rect.x0 - mx < 25
                           for mx, my in markers):
                        text_md = "· " + text_md
                    items.append((rect.y0, "text", (rect.x0, rect.y0, rect.y1, size, text_md)))
        # A bullet glyph is its own line; attach it to the text line at the same height.
        glyphs = [i for i in items if i[1] == "text" and i[2][4] in {"·", "•"}]
        for glyph in glyphs:
            g_top, g_bottom = glyph[2][1], glyph[2][2]
            mid = (g_top + g_bottom) / 2
            nearest = min((i for i in items if i[1] == "text" and i is not glyph
                           and i[2][4] not in {"·", "•"} and i[2][1] - 2 <= mid <= i[2][2] + 2),
                          key=lambda i: abs(i[2][1] - g_top), default=None)
            items.remove(glyph)
            if nearest is not None:
                x, top, bottom, size, text = nearest[2]
                items[items.index(nearest)] = (nearest[0], "text", (x, top, bottom, size, "· " + text))
        items.sort(key=lambda i: i[0])
        elements += [(kind, payload) for _, kind, payload in items]
    return elements


def render(elements: list[tuple[str, object]], note: str) -> str:
    out: list[str] = []
    para: list[str] = []
    code: list[tuple[float, str]] = []
    prev_bottom: float | None = None
    bullet_next = False
    title: list[str] = []
    pending_table: list[list[str]] = []

    def flush_table() -> None:
        if pending_table:
            out.extend(table_md(pending_table) + [""])
            pending_table.clear()

    def flush_para() -> None:
        if para:
            out.extend([" ".join(para), ""])
            para.clear()

    def flush_code() -> None:
        if code:
            left = min(x for x, _ in code)
            out.append("```text")
            out.extend(("  " * round((x - left) / 10)) + t.strip() for x, t in code)
            out.extend(["```", ""])
            code.clear()

    title_done = False
    for kind, payload in elements:
        if kind != "code":
            flush_code()
        if kind != "table":
            flush_table()
        if kind == "heading":
            flush_para()
            level, text = payload  # type: ignore[misc]
            if level == "#":
                if not title_done:  # a title may wrap over several lines
                    title.append(text)
                continue
            if title and not title_done:
                out.extend([f"# {' '.join(title)}", "", f"> {note}", ""])
                title_done = True
            out.extend([f"{level} {text}", ""])
            prev_bottom = None
        elif kind == "code":
            flush_para()
            prev_bottom = None
            code.append(payload)  # type: ignore[arg-type]
        elif kind == "table":
            rows = payload  # type: ignore[assignment]
            if not para and pending_table and rows and len(rows[0]) == len(pending_table[0]):
                # Continuation after a page break; the PDF may repeat the header row.
                pending_table.extend(rows[1:] if rows[0] == pending_table[0] else rows)
                continue
            flush_para()
            flush_table()
            prev_bottom = None
            pending_table.extend(rows)
        else:
            x, top, bottom, size, text = payload  # type: ignore[misc]
            if title and not title_done:
                out.extend([f"# {' '.join(title)}", "", f"> {note}", ""])
                title_done = True
            text = ZERO_WIDTH.sub("", text).strip()
            if text in {"·", "•"}:          # bullet glyph on its own line
                flush_para()
                bullet_next = True
                prev_bottom = bottom
                continue
            close = prev_bottom is not None and 0 <= top - prev_bottom < size * 0.8
            if bullet_next:
                flush_para()
                para.append("- " + text)
                bullet_next = False
            elif para and close and not ITEM_START.match(text):
                if para[-1].endswith("-") and not para[-1].endswith(" -"):
                    para[-1] = para[-1] + text      # re-join a hyphenated word
                else:
                    para.append(text)
            else:
                flush_para()
                para.append(("- " + text.lstrip("·• ").strip()) if text[:1] in "·•" else text)
            prev_bottom = bottom
    flush_para()
    flush_code()
    flush_table()
    md = "\n".join(out)
    # Inline code broken by a line wrap: `docker-` `compose.yml`, `GET` `/api/x`.
    md = re.sub(r"`([^`\n]*-)` `([^`\n]+)`", r"`\1\2`", md)
    md = re.sub(r"`([^`\n]+)` `(/[^`\n]*)`", r"`\1 \2`", md)
    md = re.sub(r"` ([,.;:)])", r"`\1", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Tight lists: no blank line between consecutive items.
    item = r"(?:- |\d+\. )"
    md = re.sub(rf"(^{item}[^\n]*)\n\n(?={item})", r"\1\n", md, flags=re.M)
    md = re.sub(rf"(^{item}[^\n]*)\n\n(?={item})", r"\1\n", md, flags=re.M)
    # A title split over two lines arrives as "# A" + paragraph "B": rejoin.
    return md.strip() + "\n"


if __name__ == "__main__":
    src, dst, note = sys.argv[1:4]
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(render(convert(src), note))

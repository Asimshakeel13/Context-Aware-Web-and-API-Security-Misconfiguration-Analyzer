"""Check that every text chunk of each PDF appears in its Markdown (needs pdftotext).

    python docs/project/tools/verify.py      # from the repo root
"""
import pathlib
import re
import subprocess
pairs = {"CAWASMA — Complete Project Summary (current)":"project-summary.md","CAWASMA — Revised Project Summary (old vs new)":"revised-summary-old-vs-new.md","CAWASMA — Software Requirements Specification":"srs.md","CAWASMA — Requirements Specification & Development Plan":"requirements-and-development-plan.md","CAWASMA — Per-Person Development Plan (3 partners)":"per-person-development-plan.md","CAWASMA_plan_atta":"plan-atta.md","CAWASMA_plan_asim":"plan-asim.md","CAWASMA_plan_neelam":"plan-neelam.md","CAWASMA — Asim's Claude Code Prompts":"prompts-asim.md","CAWASMA — Neelam's Claude Code Prompts":"prompts-neelam.md"}
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
problems = 0
for raw, md in pairs.items():
    text = pathlib.Path("docs/project", md).read_text()
    flat = norm(text)
    lost = [c.strip() for line in subprocess.run(["pdftotext", "-layout", f"pdf/{raw}.pdf", "-"], capture_output=True, text=True, check=True).stdout.splitlines()
            for c in re.split(r"\s{3,}", line.strip())
            if len(norm(c)) >= 12 and norm(c) not in flat and not re.match(r"^page\d+of\d+$", norm(c))]
    long_cells = [l for l in text.splitlines() if l.startswith("|") and len(l) > 1500]
    ok = text.startswith("# ") and not lost and not long_cells
    problems += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {md:40} lost={len(lost)} title={text.startswith('# ')} giant-rows={len(long_cells)}")
print("problems:", problems)

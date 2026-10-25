# Project plan and requirements

The team's planning documents, imported from the PDFs we were given (kept
locally in `pdf/`, which is git-ignored). These describe **what we are
building and who does what**; the rest of `docs/` describes the system as it is
implemented so far.

| Document | What it is | Mainly for |
|----------|------------|------------|
| [Software Requirements Specification](srs.md) | The agreed requirements: functional (FR-01…), non-functional (NFR-01…), use cases, traceability matrix. **The reference when anything disagrees.** | everyone |
| [Requirements Specification & Development Plan](requirements-and-development-plan.md) | Gap analysis of the original idea, existing tools, requirements, sprint plan, evaluation targets, risks | everyone |
| [Complete Project Summary (current)](project-summary.md) | One-document overview: scope, contributions, data model, comparison with ZAP/Nikto, team and sprints | everyone, the jury |
| [Revised Project Summary (old vs new)](revised-summary-old-vs-new.md) | What changed from the original proposal, and why | everyone |
| [Per-Person Development Plan](per-person-development-plan.md) | The three roles, shared contracts, the FINDING shape, sprint-by-sprint tasks for each partner | everyone |
| [Plan: Atta](plan-atta.md) · [Plan: Asim](plan-asim.md) · [Plan: Neelam](plan-neelam.md) | One page per partner: what you own, tasks, dependencies, definition of done | each partner |
| [Asim's prompts](prompts-asim.md) · [Neelam's prompts](prompts-neelam.md) | The step-by-step Claude Code prompts for each partner's work, with run order | Asim, Neelam |

## Which document wins

1. **SRS**: it states that it supersedes the original project summary.
2. The **shared contracts** in `docs/` (`api-contract.md`, `check-spec-format.md`,
   `cvss-mapping-contract.md`, `schema.md`): these turn the SRS into exact formats.
   They change only when all three partners agree.
3. The summaries and plans: context and schedule.

Where the implementation docs (`01`–`11`) disagree with the SRS, they describe
the current code, not the target. The main known difference: scoring still
uses the interim multiplier formula, while the SRS requires CVSS v3.1
environmental scoring (see CLAUDE.md, "Current state vs goal").

## Updating

The PDFs stay the originals. When one changes, put the new PDF in `pdf/` and
re-run the import, which also checks that no text was lost:

```bash
pip install pymupdf==1.25.1          # once; pdftotext (poppler-utils) is also needed
bash docs/project/tools/import.sh    # from the repo root
```

Don't hand-edit the imported files; changes would be overwritten. Put
decisions and corrections in the documents they belong to (the SRS PDF, or the
contracts above).

# eval/

Evaluation of detection and scoring accuracy (owner: Asim). Placeholder; don't
edit without asking Asim.

Suggested layout:

- `targets/`: Dockerfiles/config for deliberately misconfigured apps, run via
  `docker compose -f docker-compose.eval.yml up -d` on the isolated
  `cawasma-eval` network
- `datasets/`: labelled endpoints and expected findings / severities
- `scripts/`: runners that scan the targets and compute metrics

The scanner is HTTPS-only and blocks private IPs (SSRF guard); see the notes in
`docker-compose.eval.yml` for how eval scans reach the targets.

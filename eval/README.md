# eval/

Evaluation of detection and scoring accuracy (owner: Asim).

Suggested layout:

- `targets/`: Dockerfiles/config for deliberately misconfigured apps
- `ground_truth/`: expected findings, classes, and scores for each target
- `labels/`: labelled endpoint and response examples for ML evaluation
- `harness/`: runners and metric computation code
- `results/`: generated evaluation outputs and reports
- `notebooks/`: exploratory analysis notebooks and figures

The scanner is HTTPS-only and blocks private IPs (SSRF guard); see the notes in
`docker-compose.eval.yml` for how eval scans reach the targets.

## Running the target lab

```bash
make eval-up
python eval/labels/collect_endpoints.py
python eval/labels/label.py
make eval-down
make eval-reset
```

The four target services are published on loopback ports 3001–3004 and use
digest-pinned amd64 images. The Compose network is marked `internal: true`, so
the targets have no outbound internet route. The current backend does not yet
consume `ALLOWED_INTERNAL_HOSTS`; the eval-only anchor in
`docker-compose.eval.yml` records the allow-list Atta must wire into the SSRF
guard before scans are run.

The endpoint collector is a bounded, same-origin HTTP discovery tool for lab
data collection. It reads OpenAPI paths when available and then follows HTML
links up to a fixed page limit. It is not a replacement for CAWASMA's
HTTPS-only scanner.

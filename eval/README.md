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

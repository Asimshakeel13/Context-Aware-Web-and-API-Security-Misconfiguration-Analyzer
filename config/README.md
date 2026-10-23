# config/

Shared, non-code configuration for the services in `docker-compose.yml`
(owner: Atta). Application settings live in `.env` / `backend/app/config.py`,
not here.

- `checks.yaml`, `cvss_mapping.yaml`, `chains.yaml`: spec files **owned by
  Asim** (docs/check-spec-format.md, docs/cvss-mapping-contract.md). Validate
  with `make validate-config`; mounted read-only at `/config` in the containers.
- `postgres/init/`: SQL run by the postgres container on first start of a fresh
  volume (`/docker-entrypoint-initdb.d`). Creates the `cawasma_test` database
  used by `TEST_DATABASE_URL`. Changes only apply after `make reset`.

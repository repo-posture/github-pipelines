# SSCA GitHub Actions — V2

V2 composite actions live under **`v2/<action>/`** (no `-v2` suffix — the folder is already V2).  
V1 actions remain at the repository root (`sbom-generation/`, `slsa-generation/`, …).

Workflows reference local actions as `uses: ./v2/<action>`.

## E2E workflows (8 total)

| Workflow | Signing | Step order |
|----------|---------|------------|
| [`container-kms.yml`](../.github/workflows/container-kms.yml) | Vault KMS | sbom-generation → sbom-ingestion → sbom-policy-enforcement → slsa-attest → slsa-verify → artifact-sign → artifact-verify |
| [`container-keypair.yml`](../.github/workflows/container-keypair.yml) | Cosign keypair | Full container sequence |
| [`non-container-kms.yml`](../.github/workflows/non-container-kms.yml) | Vault KMS | Same (local artifact) |
| [`non-container-keypair.yml`](../.github/workflows/non-container-keypair.yml) | Cosign keypair | Full non-container sequence |
| [`repo-kms.yml`](../.github/workflows/repo-kms.yml) | Vault KMS | sbom-generation (`repo-sbom-generation`) → sbom-ingestion → sbom-policy-enforcement |
| [`container-keyless.yml`](../.github/workflows/container-keyless.yml) | Keyless OIDC | Full container sequence |
| [`non-container-keyless.yml`](../.github/workflows/non-container-keyless.yml) | Keyless OIDC | Full non-container sequence |
| [`repo-keyless.yml`](../.github/workflows/repo-keyless.yml) | Keyless OIDC | Repo SBOM sequence only |

Generation writes to `SBOM_LOCAL_PATH` (default `/tmp/sbom`) with `attest_sbom: false`; ingestion attests/uploads.

Repository mode has no SLSA or artifact-signing flows (plugin support is SBOM-only).

## Composite actions in `v2/`

| Directory | Purpose |
|-----------|---------|
| `sbom-generation` | Container / local SBOM orchestrate |
| `repo-sbom-generation` | Repository SBOM orchestrate |
| `sbom-policy-enforcement` | SBOM verify + OPA enforce |
| `slsa-generation` / `slsa-verification` | SLSA attest / verify |
| `artifact-signing` / `artifact-verification` | Cosign sign / verify |
| `sbom-ingestion` | Optional ingestion path |

## Configuration

**Plugin env (UPPERCASE, Jenkins-aligned)** — set on the workflow job `env:` block; composites map them into the plugin container:

| Variable | Container | Non-container | Repository |
|----------|-----------|---------------|------------|
| `SOURCE_TYPE` | `docker` | `local` | `repository` |
| `SBOM_SOURCE` | image ref | file path | (repo action uses `REPO_*`) |
| `SLSA_SOURCE` | image ref | file path | — |

Do **not** set legacy `PLUGIN_REGISTRY`; registry host/type is inferred from `SBOM_SOURCE` / `SLSA_SOURCE`.

Composite **inputs** stay lowercase (`sbom_source`, `source_type`) per GitHub Actions; each action exports **UPPERCASE** env vars to the Docker plugin (`SBOM_SOURCE`, `SOURCE_TYPE`, …).

**Secrets:** `HARNESS_API_KEY`, `VAULT_ADDR`, `VAULT_TOKEN`, optional `DOCKER_USERNAME` / `DOCKER_PASSWORD`

**Variables:** `HARNESS_*`, `HARNESS_PROJECT_ID=Github`, `KMS_KEY`, `DEVSECOPS_TARGET_IMAGE`, `FULCIO_URL`, `OPA_POLICY_SET_REF`, `GIT_REPO_URL`, `GIT_BRANCH`

See [`scripts/configure-e2e-secrets-and-run.sh`](../scripts/configure-e2e-secrets-and-run.sh) to configure the repo and dispatch a workflow.

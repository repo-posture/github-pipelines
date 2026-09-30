# github-pipelines — SCS GitHub Actions E2E

GitHub Actions V2 pipelines for Harness SCS, mirroring the scenario matrix used in:

- GitLab: `scs-templates-test/scs-gitlab-automation/`
- Jenkins: `jenkins-scs-local/jenkinsfiles/`

Plugin images default to the `test-githubV2` tags (`harness/ssca-plugin:test-githubV2`, etc.).

Remote repo: https://github.com/repo-posture/github-pipelines  
(Companion to [repo-posture/jenkins-pipelines](https://github.com/repo-posture/jenkins-pipelines).)

## V2 E2E workflows

| Workflow | Artifact | Signing | Maps to |
|----------|----------|---------|---------|
| `container-kms.yml` | Docker image | Vault KMS | GitLab `container-docker-kms` / Jenkins `container-kms-docker` |
| `container-keyless.yml` | Docker image | GitHub OIDC keyless | GitLab `container-docker-kl` / Jenkins `container-keyless-docker` |
| `container-keypair.yml` | Docker image | Cosign keypair | GitLab `container-docker-kp` / Jenkins `container-keypair-docker` |
| `non-container-kms.yml` | Local zip | Vault KMS | GitLab `local-orch-kms` / Jenkins `non-container-kms-orch` |
| `non-container-keyless.yml` | Local zip | GitHub OIDC keyless | GitLab `local-orch-kl` / Jenkins `non-container-keyless` |
| `non-container-keypair.yml` | Local zip | Cosign keypair | GitLab `local-orch-kp` / Jenkins `non-container-keypair-orch` |
| `repo-kms.yml` | Git repo SBOM | Vault KMS (SBOM only) | Jenkins `repo-*` |
| `repo-keyless.yml` | Git repo SBOM | Keyless (SBOM only) | Jenkins `repo-*` |

Dispatch any workflow from the Actions tab (`workflow_dispatch`). Container/KMS/keypair flows accept an `attest` boolean input.

## Layout

| Path | Purpose |
|------|---------|
| `v2/<action>/` | V2 composite actions (`sbom-generation`, `sbom-ingestion`, `artifact-signing`, …) |
| `.github/workflows/` | E2E scenario workflows |
| `.github/actions/prepare-non-container-artifact/` | Builds sample zip for local-artifact flows |
| Root `sbom-generation/`, … | Legacy V1 actions (kept for compatibility) |

## One-time setup

```bash
export VAULT_TOKEN=...
export HARNESS_QA_API_KEY=...          # QA0 / target cluster API key
export DOCKER_USERNAME=...
export DOCKER_PASSWORD=...
# keypair scenarios only:
export COSIGN_PRIVATE_KEY="$(cat cosign.key)"
export COSIGN_PASSWORD=...
export COSIGN_PUBLIC_KEY="$(cat cosign.pub)"

./scripts/configure-e2e-secrets-and-run.sh
# optional: WORKFLOW=container-keyless.yml ./scripts/configure-e2e-secrets-and-run.sh
```

Defaults in the configure script target **QA0** (same coords as `jenkins-scs-local`). Override via env before running if you need another cluster.

## Required repo secrets / variables

**Secrets:** `HARNESS_QA_API_KEY`, `VAULT_ADDR`, `VAULT_TOKEN`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`  
**Keypair only:** `COSIGN_PRIVATE_KEY`, `COSIGN_PASSWORD`, `COSIGN_PUBLIC_KEY`

**Variables:** `HARNESS_QA_ACCOUNT_URL`, `HARNESS_QA_ACCOUNT_ID`, `HARNESS_QA_ORG_ID`, `HARNESS_QA_PROJECT_ID`, `KMS_KEY`, `DEVSECOPS_TARGET_IMAGE`, `OPA_QA_POLICY_SET_REF`, `FULCIO_QA_URL`, `SBOM_TOOL`, `SBOM_FORMAT`, `SBOM_LOCAL_PATH`, `GIT_REPO_URL`, `GIT_BRANCH`

## Manual dispatch

```bash
gh workflow run container-kms.yml -R repo-posture/github-pipelines --ref main
gh workflow run container-keyless.yml -R repo-posture/github-pipelines --ref main -f attest=true
gh workflow run container-keypair.yml -R repo-posture/github-pipelines --ref main -f attest=true
gh workflow run non-container-kms.yml -R repo-posture/github-pipelines --ref main
```

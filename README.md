# github-pipelines — SCS GitHub Actions E2E

Companion to [repo-posture/jenkins-pipelines](https://github.com/repo-posture/jenkins-pipelines).

Each file under `.github/workflows/` is the GitHub Actions equivalent of one Jenkinsfile in [`pipelines/`](https://github.com/repo-posture/jenkins-pipelines/tree/main/pipelines). Workflows **build/push (or prepare a local artifact)**, then run the same SCS chain: SBOM orchestrate, artifact sign/verify, SLSA attest/verify, policy enforce.

Plugin image tags default to `test-githubV2` via the local `v2/` composite actions.

Remote repo: https://github.com/repo-posture/github-pipelines

## Workflow ↔ Jenkinsfile

| GitHub workflow | Jenkinsfile |
|-----------------|-------------|
| `container-keyless-docker.yml` | `Jenkinsfile.container-keyless-docker` |
| `container-keyless-ecr.yml` | `Jenkinsfile.container-keyless-ecr` |
| `container-keyless-acr.yml` | `Jenkinsfile.container-keyless-acr` |
| `container-keyless-har.yml` | `Jenkinsfile.container-keyless-har` |
| `container-keypair-docker.yml` | `Jenkinsfile.container-keypair-docker` |
| `container-keypair-ecr.yml` | `Jenkinsfile.container-keypair-ecr` |
| `container-keypair-acr.yml` | `Jenkinsfile.container-keypair-acr` |
| `container-keypair-har.yml` | `Jenkinsfile.container-keypair-har` |
| `container-kms-docker.yml` | `Jenkinsfile.container-kms-docker` |
| `container-kms-ecr.yml` | `Jenkinsfile.container-kms-ecr` |
| `container-kms-acr.yml` | `Jenkinsfile.container-kms-acr` |
| `container-kms-har.yml` | `Jenkinsfile.container-kms-har` |
| `non-container-keyless.yml` | `Jenkinsfile.non-container-keyless` |
| `non-container-keyless-ing.yml` | `Jenkinsfile.non-container-keyless-ing` |
| `non-container-keypair-orch.yml` | `Jenkinsfile.non-container-keypair-orch` |
| `non-container-keypair-ing.yml` | `Jenkinsfile.non-container-keypair-ing` |
| `non-container-kms-orch.yml` | `Jenkinsfile.non-container-kms-orch` |
| `non-container-kms-ing.yml` | `Jenkinsfile.non-container-kms-ing` |
| `repo-gen-syft-spdx.yml` | `Jenkinsfile.repo-gen-syft-spdx` |
| `repo-gen-syft-cdx.yml` | `Jenkinsfile.repo-gen-syft-cdx` |
| `repo-gen-cdxgen.yml` | `Jenkinsfile.repo-gen-cdxgen` |
| `repo-ingest.yml` | `Jenkinsfile.repo-ingest` |
| `repo-drift.yml` | `Jenkinsfile.repo-drift` |
| `section-d-container-ingest.yml` | `Jenkinsfile.section-d-container-ingest` |
| `section-d-keypair-attest.yml` | `Jenkinsfile.section-d-keypair-attest` |
| `section-d-kms-attest.yml` | `Jenkinsfile.section-d-kms-attest` |

Keyless container workflows also run **cdxgen** orchestrate + enforce, matching the Jenkins keyless `SSCA/cdxgen` stages.

Dispatch from the Actions tab (`workflow_dispatch`) or:

```bash
gh workflow run container-kms-docker.yml -R repo-posture/github-pipelines --ref main
gh workflow run container-keyless-ecr.yml -R repo-posture/github-pipelines --ref main
gh workflow run non-container-kms-orch.yml -R repo-posture/github-pipelines --ref main
```

## Layout

| Path | Purpose |
|------|---------|
| `.github/workflows/` | One workflow per Jenkins pipeline |
| `v2/<action>/` | V2 composite actions |
| `.github/actions/prepare-non-container-artifact/` | Sample zip for local-artifact orch flows |
| `scripts/generate-jenkins-parity-workflows.py` | Regenerates the workflow matrix |
| `scripts/configure-e2e-secrets-and-run.sh` | Sets repo secrets/vars and dispatches a workflow |

## Secrets / variables

**Secrets:** `HARNESS_QA_API_KEY`, `VAULT_ADDR`, `VAULT_TOKEN`, `DOCKER_USERNAME`, `DOCKER_PASSWORD`  
**Keypair:** `COSIGN_PRIVATE_KEY`, `COSIGN_PASSWORD`, `COSIGN_PUBLIC_KEY`  
**ECR:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`  
**ACR:** `ACR_CLIENT_ID`, `ACR_CLIENT_SECRET`  
**HAR:** `HAR_USERNAME`, `HAR_PASSWORD`

**Variables:** `HARNESS_QA_ACCOUNT_URL`, `HARNESS_QA_ACCOUNT_ID`, `HARNESS_QA_ORG_ID`, `HARNESS_QA_PROJECT_ID`, `KMS_KEY`, `OPA_QA_POLICY_SET_REF`, `FULCIO_QA_URL`, `ECR_REGISTRY`, `AWS_REGION`, `ACR_LOGIN_SERVER`, `HAR_REPO_PATH`, `GIT_REPO_URL`

```bash
export VAULT_TOKEN=... HARNESS_QA_API_KEY=... DOCKER_USERNAME=... DOCKER_PASSWORD=...
./scripts/configure-e2e-secrets-and-run.sh
# WORKFLOW=container-keyless-docker.yml ./scripts/configure-e2e-secrets-and-run.sh
```

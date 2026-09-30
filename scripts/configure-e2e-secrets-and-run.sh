#!/usr/bin/env bash
# Configure jatin471/test-githubV2 secrets/vars and dispatch a V2 E2E workflow.
# Usage:
#   export VAULT_TOKEN HARNESS_QA_API_KEY [DOCKER_USERNAME DOCKER_PASSWORD]
#   export COSIGN_PRIVATE_KEY COSIGN_PASSWORD COSIGN_PUBLIC_KEY   # keypair flows
#   ./scripts/configure-e2e-secrets-and-run.sh
#   WORKFLOW=container-keyless.yml ./scripts/configure-e2e-secrets-and-run.sh

set -euo pipefail

REPO="${REPO:-jatin471/test-githubV2}"
LOGIN="$(gh api user --jq .login)"
echo "Configuring $REPO as gh user '$LOGIN'"

: "${VAULT_TOKEN:?Set VAULT_TOKEN}"
: "${HARNESS_QA_API_KEY:?Set HARNESS_QA_API_KEY}"

gh secret set VAULT_ADDR -R "$REPO" -b "${VAULT_ADDR:-https://vaultqa.harness.io}"
gh secret set VAULT_TOKEN -R "$REPO" -b "$VAULT_TOKEN"
gh secret set HARNESS_QA_API_KEY -R "$REPO" -b "$HARNESS_QA_API_KEY"

if [[ -n "${DOCKER_USERNAME:-}" && -n "${DOCKER_PASSWORD:-}" ]]; then
  gh secret set DOCKER_USERNAME -R "$REPO" -b "$DOCKER_USERNAME"
  gh secret set DOCKER_PASSWORD -R "$REPO" -b "$DOCKER_PASSWORD"
fi

if [[ -n "${COSIGN_PRIVATE_KEY:-}" ]]; then
  gh secret set COSIGN_PRIVATE_KEY -R "$REPO" -b "$COSIGN_PRIVATE_KEY"
  gh secret set COSIGN_PASSWORD -R "$REPO" -b "${COSIGN_PASSWORD:-}"
  gh secret set COSIGN_PUBLIC_KEY -R "$REPO" -b "${COSIGN_PUBLIC_KEY:?Set COSIGN_PUBLIC_KEY with COSIGN_PRIVATE_KEY}"
fi

# QA0 defaults — same cluster as jenkins-scs-local
gh variable set HARNESS_QA_ACCOUNT_URL -R "$REPO" -b "${HARNESS_QA_ACCOUNT_URL:-https://qa0.harness.io}"
gh variable set HARNESS_QA_ACCOUNT_ID -R "$REPO" -b "${HARNESS_QA_ACCOUNT_ID:-ppbLW9YpRharzPs_JtWT7g}"
gh variable set HARNESS_QA_ORG_ID -R "$REPO" -b "${HARNESS_QA_ORG_ID:-SSCA}"
gh variable set HARNESS_QA_PROJECT_ID -R "$REPO" -b "${HARNESS_QA_PROJECT_ID:-SSCA_Sanity_Automation}"
gh variable set FULCIO_QA_URL -R "$REPO" -b "${FULCIO_QA_URL:-https://qa0.harness.io/gateway/harness-fulcio/}"
gh variable set KMS_KEY -R "$REPO" -b "${KMS_KEY:-SSCA_AUTOMATION_COSIGN_KEY}"
gh variable set DEVSECOPS_TARGET_IMAGE -R "$REPO" -b "${DEVSECOPS_TARGET_IMAGE:-docker.io/autosscauser/scs-automation-test:github-v2}"
gh variable set OPA_QA_POLICY_SET_REF -R "$REPO" -b "${OPA_QA_POLICY_SET_REF:-opa_policy_set_for_at}"
gh variable set SBOM_TOOL -R "$REPO" -b "${SBOM_TOOL:-Syft}"
gh variable set SBOM_FORMAT -R "$REPO" -b "${SBOM_FORMAT:-cyclonedx-json}"
gh variable set SBOM_LOCAL_PATH -R "$REPO" -b "${SBOM_LOCAL_PATH:-/tmp/sbom}"
gh variable set GIT_REPO_URL -R "$REPO" -b "${GIT_REPO_URL:-https://github.com/KartikSaurya/Buggy-App.git}"
gh variable set GIT_BRANCH -R "$REPO" -b "${GIT_BRANCH:-main}"

WORKFLOW="${WORKFLOW:-container-kms.yml}"
gh workflow run "$WORKFLOW" -R "$REPO" --ref main
echo "Dispatched $WORKFLOW on $REPO — see https://github.com/$REPO/actions"

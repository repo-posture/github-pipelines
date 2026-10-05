#!/usr/bin/env bash
# Sourced by v2 composite actions before `docker run`.
# Docker --env-file cannot carry multiline PEMs or values containing '#'.
#
# Defines:
#   build_plugin_docker_env  → sets PLUGIN_ENV_FILE and PLUGIN_DOCKER_E_ARGS=()
#   cleanup_plugin_docker_env

build_plugin_docker_env() {
  PLUGIN_ENV_FILE="$(mktemp)"
  PLUGIN_DOCKER_E_ARGS=()

  env | grep -E '^(HARNESS_|GITHUB_|SBOM_|SOURCE_|SIGNING_|PLUGIN_|SSCA_|VAULT_|DOCKER_|ATTEST_|POLICY_|VERIFY_|REPO_|SLSA_|REGISTRY_|KMS_|GCP_|AWS_|CLIENT_|TENANT_|AZURE_|RUNNER_|ACTIONS_ID_TOKEN|OIDC_|FULCIO_)' \
    | grep -vE 'COSIGN_(PRIVATE|PUBLIC)_KEY=' \
    | grep -vE '^PLUGIN_NON_HARNESS_OIDC_TOKEN=' \
    | grep -vE '^HARNESS_API_KEY=' \
    | grep -vE '^HARNESS_SSCA_SERVICE_TOKEN=' \
    > "$PLUGIN_ENV_FILE" || true

  local var
  for var in \
    HARNESS_API_KEY \
    HARNESS_SSCA_SERVICE_TOKEN \
    SSCA_ARTIFACT_SIGNING_COSIGN_PRIVATE_KEY \
    SSCA_ARTIFACT_VERIFICATION_COSIGN_PUBLIC_KEY \
    SSCA_SLSA_GENERATION_COSIGN_PRIVATE_KEY \
    SSCA_SLSA_VERIFICATION_COSIGN_PUBLIC_KEY \
    SSCA_ORCHESTRATION_COSIGN_PRIVATE_KEY \
    SSCA_ENFORCEMENT_COSIGN_PUBLIC_KEY \
    PLUGIN_NON_HARNESS_OIDC_TOKEN
  do
    if [ -n "${!var:-}" ]; then
      PLUGIN_DOCKER_E_ARGS+=(-e "${var}=${!var}")
    fi
  done
}

cleanup_plugin_docker_env() {
  rm -f "${PLUGIN_ENV_FILE:-}"
}

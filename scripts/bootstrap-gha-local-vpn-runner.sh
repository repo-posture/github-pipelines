#!/usr/bin/env bash
# Register a GitHub Actions runner with the same role as GitLab `tags: [local-vpn]`.
# Must run on Linux with Docker, on a network that can reach https://vaultqa.harness.io
# (GKE sscs-play, or any internal/VPN host — NOT a GitHub-hosted VM).
set -euo pipefail

REPO="${REPO:-repo-posture/github-pipelines}"
RUNNER_NAME="${RUNNER_NAME:-scs-gke-gha-local-vpn}"
LABELS="${LABELS:-linux,local-vpn}"
MODE="${MODE:-docker}"  # docker | print-k8s

need() { command -v "$1" >/dev/null || { echo "need $1" >&2; exit 1; }; }
need gh
need python3

echo "Probe Vault (must succeed from THIS machine)..."
if ! curl -fsS -m 10 -o /dev/null "https://vaultqa.harness.io/v1/sys/health?standbyok=true"; then
  echo "Cannot reach vaultqa.harness.io from here — same failure as GHA ubuntu-latest." >&2
  echo "Use the sscs-play GKE cluster (GitLab scs-gke-runner) or a VPN/internal host." >&2
  exit 1
fi
echo "Vault reachable."

TOKEN=$(gh api -X POST "repos/${REPO}/actions/runners/registration-token" --jq .token)
if [[ -z "$TOKEN" ]]; then
  echo "Failed to mint registration token (need repo admin)." >&2
  exit 1
fi

if [[ "$MODE" == "print-k8s" ]]; then
  echo
  echo "kubectl -n github-scs-runner create secret generic gha-runner --from-literal=token='$TOKEN' --dry-run=client -o yaml | kubectl apply -f -"
  echo "kubectl apply -f scripts/gke-gha-local-vpn-runner.yaml"
  echo
  echo "Token expires in ~1 hour. Apply immediately, then:"
  echo "  kubectl -n github-scs-runner logs -l app=gha-local-vpn -f"
  exit 0
fi

need docker
echo "Starting runner container ${RUNNER_NAME} ..."
docker rm -f "$RUNNER_NAME" 2>/dev/null || true
docker run -d --name "$RUNNER_NAME" --restart unless-stopped --privileged \
  -e REPO_URL="https://github.com/${REPO}" \
  -e RUNNER_NAME="$RUNNER_NAME" \
  -e RUNNER_TOKEN="$TOKEN" \
  -e RUNNER_LABELS="$LABELS" \
  -e RUNNER_WORKDIR=/tmp/runner \
  -e DISABLE_AUTO_UPDATE=1 \
  myoung34/github-runner:latest

echo "Waiting for GitHub to list the runner..."
for i in $(seq 1 20); do
  if gh api "repos/${REPO}/actions/runners" --jq '.runners[] | select(.name=="'"$RUNNER_NAME"'") | "\(.status) labels=\([.labels[].name]|join(","))"' 2>/dev/null | grep -q .; then
    gh api "repos/${REPO}/actions/runners" --jq '.runners[] | select(.name=="'"$RUNNER_NAME"'") | {name,status,labels:[.labels[].name]}'
    echo "Ready. Dispatch a KMS workflow:"
    echo "  gh workflow run container-kms-docker -R ${REPO}"
    exit 0
  fi
  sleep 3
done
echo "Container started but GitHub has not listed it yet. Check: docker logs ${RUNNER_NAME}"
exit 1

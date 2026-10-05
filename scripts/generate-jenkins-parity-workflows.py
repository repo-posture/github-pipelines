#!/usr/bin/env python3
"""Generate GitHub Actions workflows that mirror repo-posture/jenkins-pipelines."""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / ".github" / "workflows"
OUT.mkdir(parents=True, exist_ok=True)

HARNESS_QA = {
    "url": "${{ vars.HARNESS_QA_ACCOUNT_URL }}",
    "key": "${{ secrets.HARNESS_QA_API_KEY }}",
    "aid": "${{ vars.HARNESS_QA_ACCOUNT_ID }}",
    "org": "${{ vars.HARNESS_QA_ORG_ID }}",
    "proj": "${{ vars.HARNESS_QA_PROJECT_ID }}",
}

HARNESS_COMMON = f"""\
          HARNESS_ACCOUNT_URL: {HARNESS_QA['url']}
          HARNESS_API_KEY: {HARNESS_QA['key']}
          HARNESS_ACCOUNT_ID: {HARNESS_QA['aid']}
          HARNESS_ORG_ID: {HARNESS_QA['org']}
          HARNESS_PROJECT_ID: {HARNESS_QA['proj']}"""

KMS_INPUTS = f"""\
          VAULT_ADDR: ${{{{ vars.VAULT_ADDR || 'https://vaultqa.harness.io' }}}}
          VAULT_TOKEN: ${{{{ secrets.VAULT_TOKEN }}}}
          KMS_KEY: ${{{{ vars.KMS_KEY }}}}"""

KEYPAIR_SIGN = f"""\
          COSIGN_PRIVATE_KEY: ${{{{ secrets.COSIGN_PRIVATE_KEY }}}}
          COSIGN_PASSWORD: ${{{{ secrets.COSIGN_PASSWORD }}}}"""

KEYPAIR_VERIFY = f"""\
          COSIGN_PUBLIC_KEY: ${{{{ secrets.COSIGN_PUBLIC_KEY }}}}"""

KEYLESS = "          PLUGIN_KEYLESS_TYPE: non-harness"


def header(name: str, desc: str, keyless: bool = False) -> str:
    perms = "  contents: read\n"
    if keyless:
        perms += "  id-token: write\n"
    return f"""# Mirrors jenkins-pipelines/pipelines/Jenkinsfile.{name}
# {desc}
name: "{name}"

on:
  workflow_dispatch:

permissions:
{perms}
jobs:
"""


def docker_login(registry: str) -> str:
    if registry == "docker":
        return """\
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
"""
    if registry == "ecr":
        return """\
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ vars.AWS_REGION || 'us-east-1' }}
      - name: Login to Amazon ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2
"""
    if registry == "acr":
        return """\
      - uses: azure/docker-login@v2
        with:
          login-server: ${{ vars.ACR_LOGIN_SERVER || 'sscatest.azurecr.io' }}
          username: ${{ secrets.ACR_CLIENT_ID }}
          password: ${{ secrets.ACR_CLIENT_SECRET }}
"""
    if registry == "har":
        return """\
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      - uses: docker/login-action@v3
        with:
          registry: pkg.qa0.harness.io
          username: ${{ secrets.HAR_USERNAME }}
          password: ${{ secrets.HAR_PASSWORD }}
"""
    return ""


def build_push(registry: str, tag_suffix: str) -> str:
    login = docker_login(registry)
    if registry == "docker":
        return f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    outputs:
      image: ${{{{ steps.meta.outputs.image }}}}
    steps:
      - uses: actions/checkout@v4
{login}      - name: Build and push
        id: meta
        run: |
          set -eux
          IMAGE="docker.io/autosscauser/scs-github-automation-test:${{{{ github.run_number }}}}-{tag_suffix}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          docker build -t "$IMAGE" .
          docker push "$IMAGE"
          echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
"""
    if registry == "ecr":
        return f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    outputs:
      image: ${{{{ steps.meta.outputs.image }}}}
      registry: ${{{{ steps.ecr.outputs.registry }}}}
    steps:
      - uses: actions/checkout@v4
{login}      - name: Build and push
        id: meta
        env:
          ECR_REGISTRY: ${{{{ vars.ECR_REGISTRY || '211125722538.dkr.ecr.us-east-1.amazonaws.com/scs-automation-test' }}}}
        run: |
          set -eux
          IMAGE="${{ECR_REGISTRY}}:${{{{ github.run_number }}}}-{tag_suffix}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          aws ecr create-repository --repository-name scs-automation-test --region "${{{{ vars.AWS_REGION || 'us-east-1' }}}}" 2>/dev/null || true
          docker build -t "$IMAGE" .
          docker push "$IMAGE"
          echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
"""
    if registry == "acr":
        return f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    outputs:
      image: ${{{{ steps.meta.outputs.image }}}}
    steps:
      - uses: actions/checkout@v4
{login}      - name: Build and push
        id: meta
        env:
          ACR: ${{{{ vars.ACR_LOGIN_SERVER || 'sscatest.azurecr.io' }}}}
        run: |
          set -eux
          IMAGE="${{ACR}}/scs-automation-test:${{{{ github.run_number }}}}-{tag_suffix}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          docker build -t "$IMAGE" .
          docker push "$IMAGE"
          echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
"""
    if registry == "har":
        return f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    outputs:
      image: ${{{{ steps.meta.outputs.image }}}}
    steps:
      - uses: actions/checkout@v4
{login}      - name: Build and push
        id: meta
        env:
          HAR_PATH: ${{{{ vars.HAR_REPO_PATH || 'ppblw9yprharzps_jtwt7g/ssca_har_automation_registry/scs-automation-test' }}}}
        run: |
          set -eux
          TMP="autosscauser/scs-github-automation-test:${{{{ github.run_number }}}}-{tag_suffix}"
          IMAGE="pkg.qa0.harness.io/${{HAR_PATH}}:${{{{ github.run_number }}}}-{tag_suffix}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          docker build -t "$TMP" .
          docker push "$TMP"
          docker tag "$TMP" "$IMAGE"
          docker push "$IMAGE"
          echo "image=$IMAGE" >> "$GITHUB_OUTPUT"
"""
    raise ValueError(registry)


def docker_creds(registry: str) -> str:
    if registry == "docker":
        return """\
          DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
          DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}"""
    if registry == "ecr":
        return """\
          DOCKER_USERNAME: AWS
          DOCKER_PASSWORD: ${{ needs.build.outputs.registry && secrets.AWS_SECRET_ACCESS_KEY || secrets.AWS_SECRET_ACCESS_KEY }}"""
    if registry == "acr":
        return """\
          DOCKER_USERNAME: ${{ secrets.ACR_CLIENT_ID }}
          DOCKER_PASSWORD: ${{ secrets.ACR_CLIENT_SECRET }}"""
    if registry == "har":
        return """\
          DOCKER_USERNAME: ${{ secrets.HAR_USERNAME }}
          DOCKER_PASSWORD: ${{ secrets.HAR_PASSWORD }}"""
    return ""


def source_type(registry: str) -> str:
    return {"docker": "docker", "ecr": "ecr", "acr": "acr", "har": "har"}[registry]


def image_ref(registry: str, tag_suffix: str) -> str:
    """Deterministic image ref for SCS steps.

    Do not pass needs.build.outputs.image across jobs: if the ref embeds a
    secret (e.g. DOCKER_USERNAME), GitHub blanks the dependent-job value.
    """
    if registry == "docker":
        return (
            "docker.io/autosscauser/scs-github-automation-test:"
            f"${{{{ github.run_number }}}}-{tag_suffix}"
        )
    if registry == "ecr":
        return (
            "${{ vars.ECR_REGISTRY || '211125722538.dkr.ecr.us-east-1.amazonaws.com/scs-automation-test' }}"
            f":${{{{ github.run_number }}}}-{tag_suffix}"
        )
    if registry == "acr":
        return (
            "${{ vars.ACR_LOGIN_SERVER || 'sscatest.azurecr.io' }}/scs-automation-test"
            f":${{{{ github.run_number }}}}-{tag_suffix}"
        )
    if registry == "har":
        return (
            "pkg.qa0.harness.io/${{ vars.HAR_REPO_PATH || 'ppblw9yprharzps_jtwt7g/ssca_har_automation_registry/scs-automation-test' }}"
            f":${{{{ github.run_number }}}}-{tag_suffix}"
        )
    raise ValueError(registry)


# Local filesystem path for SBOM output. Jenkins uses PLUGIN_SBOMDESTINATION=harness
# (platform semantic); GHA v2 actions treat it as a host path for docker -v.
SBOM_DEST = "/tmp/sbom"


def signing_block(mode: str) -> str:
    if mode == "kms":
        return KMS_INPUTS
    if mode == "keypair":
        return KEYPAIR_SIGN
    if mode == "keyless":
        return KEYLESS
    return ""


def verify_block(mode: str) -> str:
    if mode == "kms":
        return KMS_INPUTS
    if mode == "keypair":
        return KEYPAIR_VERIFY
    if mode == "keyless":
        return KEYLESS
    return ""


def container_pipeline(name: str, registry: str, mode: str, tag_suffix: str, with_cdxgen: bool = False) -> str:
    """Full container chain matching Jenkins: build → sbom → sign → verify → slsa → enforce."""
    keyless = mode == "keyless"
    st = source_type(registry)
    img = image_ref(registry, tag_suffix)
    desc = f"Container · {registry.upper()} · {mode}"
    h = header(name, desc, keyless=keyless)
    build = build_push(registry, tag_suffix)
    login = docker_login(registry)
    creds = docker_creds(registry)
    sign = signing_block(mode)
    ver = verify_block(mode)
    env_lines = []
    if keyless:
        env_lines.append("      FULCIO_URL: ${{ vars.FULCIO_QA_URL }}")
    if registry == "ecr":
        env_lines += [
            "      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}",
            "      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}",
            "      AWS_REGION: ${{ vars.AWS_REGION || 'us-east-1' }}",
        ]
    if registry == "acr":
        env_lines += [
            "      CLIENT_ID: ${{ secrets.ACR_CLIENT_ID }}",
            "      CLIENT_SECRET: ${{ secrets.ACR_CLIENT_SECRET }}",
            "      TENANT_ID: ${{ vars.AZURE_TENANT_ID || 'b229b2bb-5f33-4d22-bce0-730f6474e906' }}",
        ]
    env_fulcio = ("    env:\n" + "\n".join(env_lines) + "\n") if env_lines else ""

    # For ECR, refresh login password each job
    ecr_login_fix = ""
    if registry == "ecr":
        ecr_login_fix = """\
      - name: ECR password for plugins
        id: ecrpw
        run: |
          TOKEN=$(aws ecr get-login-password --region "${{ vars.AWS_REGION || 'us-east-1' }}")
          echo "::add-mask::$TOKEN"
          echo "token=$TOKEN" >> "$GITHUB_OUTPUT"
"""
        creds = """\
          DOCKER_USERNAME: AWS
          DOCKER_PASSWORD: ${{ steps.ecrpw.outputs.token }}"""

    cdxgen_steps = ""
    if with_cdxgen and mode == "keyless":
        cdxgen_steps = f"""\
      - name: SBOM generation (cdxgen)
        uses: ./v2/sbom-generation
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: {st}
          SBOM_TOOL: cdxgen
          SBOM_FORMAT: cyclonedx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "true"
{sign}
{creds}
      - name: SBOM enforce (cdxgen)
        continue-on-error: true
        uses: ./v2/sbom-policy-enforcement
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: {st}
          VERIFY_SBOM: "true"
          POLICY_SET_REF: ${{{{ vars.OPA_QA_POLICY_SET_REF }}}}
{ver}
{creds}
"""

    attest_sbom = "true" if mode == "keyless" else "false"
    jobs = f"""\
{build}
  scs:
    name: SCS pipeline
    needs: [build]
    runs-on: ubuntu-latest
{env_fulcio}    steps:
      - uses: actions/checkout@v4
{login}{ecr_login_fix}      - name: SBOM orchestrate (Syft)
        uses: ./v2/sbom-generation
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: {st}
          SBOM_TOOL: Syft
          SBOM_FORMAT: cyclonedx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "{attest_sbom}"
{sign}
{creds}
{cdxgen_steps}      - name: Artifact sign
        uses: ./v2/artifact-signing
        with:
{HARNESS_COMMON}
          SIGNING_SOURCE: {img}
          SOURCE_TYPE: {st}
{sign}
{creds}
      - name: Artifact verify
        uses: ./v2/artifact-verification
        with:
{HARNESS_COMMON}
          SIGNING_SOURCE: {img}
          SOURCE_TYPE: {st}
{ver}
{creds}
      - name: SLSA attest
        uses: ./v2/slsa-generation
        with:
{HARNESS_COMMON}
          SLSA_SOURCE: {img}
          SOURCE_TYPE: {st}
          ATTEST_SLSA: "true"
{sign}
{creds}
      - name: SLSA verify
        uses: ./v2/slsa-verification
        with:
{HARNESS_COMMON}
          SLSA_SOURCE: {img}
          SOURCE_TYPE: {st}
          VERIFY_SLSA: "true"
{ver}
{creds}
      - name: SBOM enforce
        continue-on-error: true
        uses: ./v2/sbom-policy-enforcement
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: {st}
          VERIFY_SBOM: "true"
          POLICY_SET_REF: ${{{{ vars.OPA_QA_POLICY_SET_REF }}}}
{ver}
{creds}
"""
    return h + jobs


def prepare_artifact_step() -> str:
    return """\
      - uses: ./.github/actions/prepare-non-container-artifact
"""


def non_container_orch(name: str, mode: str) -> str:
    keyless = mode == "keyless"
    h = header(name, f"Non-container orchestrate · {mode}", keyless=keyless)
    sign = signing_block(mode)
    ver = verify_block(mode)
    env_fulcio = (
        "    env:\n      FULCIO_URL: ${{ vars.FULCIO_QA_URL }}\n"
        if keyless
        else ""
    )
    attest = "true" if mode == "keyless" else "false"
    return h + f"""\
  scs:
    name: Non-container orch
    runs-on: ubuntu-latest
{env_fulcio}    steps:
      - uses: actions/checkout@v4
{prepare_artifact_step()}      - name: SBOM orchestrate
        uses: ./v2/sbom-generation
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SBOM_SOURCE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_NAME: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_VERSION: local-orch-{mode}-${{{{ github.run_number }}}}
          SBOM_TOOL: Syft
          SBOM_FORMAT: cyclonedx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "{attest}"
{sign}
      - name: Artifact sign
        uses: ./v2/artifact-signing
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SIGNING_SOURCE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_NAME: scs-sample-app.zip
          ARTIFACT_VERSION: local-orch-{mode}-${{{{ github.run_number }}}}
{sign}
      - name: Artifact verify
        uses: ./v2/artifact-verification
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SIGNING_SOURCE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_NAME: scs-sample-app.zip
          ARTIFACT_VERSION: local-orch-{mode}-${{{{ github.run_number }}}}
{ver}
      - name: SLSA attest
        uses: ./v2/slsa-generation
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SLSA_SOURCE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_NAME: scs-sample-app.zip
          ARTIFACT_VERSION: local-orch-{mode}-${{{{ github.run_number }}}}
          ATTEST_SLSA: "true"
{sign}
      - name: SLSA verify
        uses: ./v2/slsa-verification
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SLSA_SOURCE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/artifacts/scs-sample-app.zip
          ARTIFACT_NAME: scs-sample-app.zip
          ARTIFACT_VERSION: local-orch-{mode}-${{{{ github.run_number }}}}
          VERIFY_SLSA: "true"
{ver}
"""


def non_container_ing(name: str, mode: str) -> str:
    keyless = mode == "keyless"
    h = header(name, f"Non-container ingestion · {mode}", keyless=keyless)
    sign = signing_block(mode)
    ver = verify_block(mode)
    env_fulcio = (
        "    env:\n      FULCIO_URL: ${{ vars.FULCIO_QA_URL }}\n"
        if keyless
        else ""
    )
    return h + f"""\
  scs:
    name: Non-container ingest
    runs-on: ubuntu-latest
{env_fulcio}    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: |
          set -eux
          mkdir -p target
          echo "scenario=local-ing-{mode} build=${{{{ github.run_number }}}}" > target/scs-github-automation-test.jar
      - name: Generate SBOM (Syft)
        run: |
          set -eux
          docker run --rm -v "$PWD:/work" -w /work anchore/syft:latest \\
            "file:/work/target/scs-github-automation-test.jar" -o spdx-json=/work/sbom.json
      - name: SBOM ingest
        uses: ./v2/sbom-ingestion
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SBOM_SOURCE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_NAME: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_VERSION: local-ing-{mode}-${{{{ github.run_number }}}}
          PLUGIN_SBOMDESTINATION: ${{{{ github.workspace }}}}/sbom.json
          ATTEST_SBOM: "false"
{sign}
      - name: Artifact sign
        uses: ./v2/artifact-signing
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SIGNING_SOURCE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_NAME: scs-github-automation-test.jar
          ARTIFACT_VERSION: local-ing-{mode}-${{{{ github.run_number }}}}
{sign}
      - name: Artifact verify
        uses: ./v2/artifact-verification
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SIGNING_SOURCE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_NAME: scs-github-automation-test.jar
          ARTIFACT_VERSION: local-ing-{mode}-${{{{ github.run_number }}}}
{ver}
      - name: SLSA attest
        uses: ./v2/slsa-generation
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SLSA_SOURCE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_NAME: scs-github-automation-test.jar
          ARTIFACT_VERSION: local-ing-{mode}-${{{{ github.run_number }}}}
          ATTEST_SLSA: "true"
{sign}
      - name: SLSA verify
        uses: ./v2/slsa-verification
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: local
          SLSA_SOURCE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          PLUGIN_WORKSPACE: ${{{{ github.workspace }}}}/target/scs-github-automation-test.jar
          ARTIFACT_NAME: scs-github-automation-test.jar
          ARTIFACT_VERSION: local-ing-{mode}-${{{{ github.run_number }}}}
          VERIFY_SLSA: "true"
{ver}
"""


def repo_clone_step(branch: str = "main") -> str:
    return f"""\
      - name: Clone sample repository
        env:
          HARNESS_API_KEY: ${{{{ secrets.HARNESS_QA_API_KEY }}}}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
        run: |
          set -eux
          rm -rf repo
          ENC=$(python3 -c "import urllib.parse,os; print(urllib.parse.quote(os.environ['HARNESS_API_KEY'], safe=''))")
          git -c http.extraHeader="x-api-key: ${{HARNESS_API_KEY}}" \\
            clone --depth 1 -b {branch} \\
            "https://x-api-key:${{ENC}}@${{REPO_URL#https://}}" repo
          git -C repo remote set-url origin "$REPO_URL"
          ls -la repo
"""


def repo_gen(name: str, tool: str, fmt: str, repo_path: str = "/", plugin_image: str = "") -> str:
    h = header(name, f"Repo SBOM generation · {tool} · {fmt}")
    plugin = ""
    if plugin_image:
        plugin = f"\n          PLUGIN_IMAGE: {plugin_image}"
    return h + f"""\
  scs:
    name: Repo generation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{repo_clone_step()}      - name: Repository SBOM generation
        uses: ./v2/repo-sbom-generation
        with:
{HARNESS_COMMON}{plugin}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_PATH: {repo_path}
          REPO_VARIANT: main
          REPO_VARIANT_TYPE: branch
          REPO_CLONED_CODEBASE: ${{{{ github.workspace }}}}/repo
          SBOM_TOOL: {tool}
          SBOM_FORMAT: {fmt}
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "false"
      - name: SBOM policy enforce
        continue-on-error: true
        uses: ./v2/sbom-policy-enforcement
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: repository
          SBOM_SOURCE: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_PATH: {repo_path}
          REPO_VARIANT: main
          REPO_VARIANT_TYPE: branch
          REPO_CLONED_CODEBASE: ${{{{ github.workspace }}}}/repo
          VERIFY_SBOM: "false"
          POLICY_SET_REF: ${{{{ vars.OPA_REPO_POLICY_SET_REF || 'sbom_package_age_policy_set_for_at' }}}}
"""


def repo_ingest() -> str:
    h = header("repo-ingest", "Repo SBOM ingestion (pre-generated SPDX)")
    return h + f"""\
  scs:
    name: Repo ingest
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{repo_clone_step()}      - name: Generate SBOM file (Syft SPDX)
        run: |
          set -eux
          docker run --rm -v "$PWD:/work" -w /work anchore/syft:latest \\
            "dir:/work/repo" -o "spdx-json=/work/sbom.spdx.json"
      - name: SBOM ingest
        uses: ./v2/sbom-ingestion
        with:
{HARNESS_COMMON}
          SOURCE_TYPE: repository
          SBOM_SOURCE: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_PATH: /
          REPO_VARIANT: main
          REPO_VARIANT_TYPE: branch
          REPO_CLONED_CODEBASE: ${{{{ github.workspace }}}}/repo
          PLUGIN_SBOMDESTINATION: ${{{{ github.workspace }}}}/sbom.spdx.json
          ATTEST_SBOM: "false"
"""


def repo_drift() -> str:
    h = header("repo-drift", "Repo SBOM drift detection (main vs go)")
    return h + f"""\
  baseline:
    name: Baseline SBOM (branch go)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{repo_clone_step('go')}      - name: Orchestrate go (baseline)
        uses: ./v2/repo-sbom-generation
        with:
{HARNESS_COMMON}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_PATH: /
          REPO_VARIANT: go
          REPO_VARIANT_TYPE: branch
          REPO_CLONED_CODEBASE: ${{{{ github.workspace }}}}/repo
          SBOM_TOOL: Syft
          SBOM_FORMAT: spdx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "false"

  drift:
    name: Drift SBOM (main vs go)
    needs: [baseline]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
{repo_clone_step('main')}      - name: Orchestrate main + drift
        uses: ./v2/repo-sbom-generation
        env:
          PLUGIN_SBOM_DRIFT: repository
          PLUGIN_SBOM_DRIFT_VARIANT: go
          PLUGIN_SBOM_DRIFT_VARIANT_TYPE: branch
        with:
{HARNESS_COMMON}
          REPO_URL: ${{{{ vars.GIT_REPO_URL || 'https://git.qa0.harness.io/ppbLW9YpRharzPs_JtWT7g/SSCA/SSCA_Sanity_Automation/sbom-direct-indirect-dependencies.git' }}}}
          REPO_PATH: /
          REPO_VARIANT: main
          REPO_VARIANT_TYPE: branch
          REPO_CLONED_CODEBASE: ${{{{ github.workspace }}}}/repo
          SBOM_TOOL: Syft
          SBOM_FORMAT: spdx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "false"
"""


def section_d_container_ingest() -> str:
    h = header("section-d-container-ingest", "JK-047 container SBOM file ingest")
    img = image_ref("docker", "d-ing")
    return h + f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{{{ secrets.DOCKER_USERNAME }}}}
          password: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: Build and push
        id: meta
        run: |
          set -eux
          IMAGE="{img}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          docker build -t "$IMAGE" .
          docker push "$IMAGE"

  scs:
    name: Container ingest
    needs: [build]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{{{ secrets.DOCKER_USERNAME }}}}
          password: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: Generate SBOM file (syft)
        run: |
          set -eux
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$PWD:/work" -w /work \\
            anchore/syft:latest "{img}" -o "cyclonedx-json=/work/container-ingest.cdx.json"
      - name: Container SBOM ingest
        uses: ./v2/sbom-ingestion
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: docker
          PLUGIN_SBOMDESTINATION: ${{{{ github.workspace }}}}/container-ingest.cdx.json
          ATTEST_SBOM: "false"
          DOCKER_USERNAME: ${{{{ secrets.DOCKER_USERNAME }}}}
          DOCKER_PASSWORD: ${{{{ secrets.DOCKER_PASSWORD }}}}
"""


def section_d_attest(name: str, mode: str) -> str:
    h = header(name, f"Section D attest-only · {mode}")
    sign = signing_block(mode)
    ver = verify_block(mode)
    img = image_ref("docker", f"d-{mode}")
    return h + f"""\
  build:
    name: Build & push image
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{{{ secrets.DOCKER_USERNAME }}}}
          password: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: Build and push
        id: meta
        run: |
          set -eux
          IMAGE="{img}"
          printf 'FROM alpine:3.19\\nLABEL build="%s"\\n' "${{{{ github.run_number }}}}" > Dockerfile
          docker build -t "$IMAGE" .
          docker push "$IMAGE"

  scs:
    name: Attest
    needs: [build]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{{{ secrets.DOCKER_USERNAME }}}}
          password: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: SBOM orchestrate + attest
        uses: ./v2/sbom-generation
        with:
{HARNESS_COMMON}
          SBOM_SOURCE: {img}
          SOURCE_TYPE: docker
          SBOM_TOOL: Syft
          SBOM_FORMAT: cyclonedx-json
          PLUGIN_SBOMDESTINATION: {SBOM_DEST}
          ATTEST_SBOM: "true"
{sign}
          DOCKER_USERNAME: ${{{{ secrets.DOCKER_USERNAME }}}}
          DOCKER_PASSWORD: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: SLSA attest
        uses: ./v2/slsa-generation
        with:
{HARNESS_COMMON}
          SLSA_SOURCE: {img}
          SOURCE_TYPE: docker
          ATTEST_SLSA: "true"
{sign}
          DOCKER_USERNAME: ${{{{ secrets.DOCKER_USERNAME }}}}
          DOCKER_PASSWORD: ${{{{ secrets.DOCKER_PASSWORD }}}}
      - name: SLSA verify
        uses: ./v2/slsa-verification
        with:
{HARNESS_COMMON}
          SLSA_SOURCE: {img}
          SOURCE_TYPE: docker
          VERIFY_SLSA: "true"
{ver}
          DOCKER_USERNAME: ${{{{ secrets.DOCKER_USERNAME }}}}
          DOCKER_PASSWORD: ${{{{ secrets.DOCKER_PASSWORD }}}}
"""


def write(name: str, body: str) -> None:
    path = OUT / f"{name}.yml"
    # Collapse blank lines that are only whitespace-heavy
    lines = body.splitlines()
    cleaned = []
    for line in lines:
        cleaned.append(line.rstrip())
    text = "\n".join(cleaned).rstrip() + "\n"
    path.write_text(text)
    print(f"wrote {path.name}")


def main() -> None:
    # Container · keyless × registries (with cdxgen like Jenkins keyless)
    for reg, suffix in [("docker", "kl"), ("ecr", "ecr-kl"), ("acr", "acr-kl"), ("har", "har-kl")]:
        write(f"container-keyless-{reg}", container_pipeline(f"container-keyless-{reg}", reg, "keyless", suffix, with_cdxgen=True))

    # Container · keypair × registries
    for reg, suffix in [("docker", "kp"), ("ecr", "ecr-kp"), ("acr", "acr-kp"), ("har", "har-kp")]:
        write(f"container-keypair-{reg}", container_pipeline(f"container-keypair-{reg}", reg, "keypair", suffix))

    # Container · kms × registries
    for reg, suffix in [("docker", "kms"), ("ecr", "ecr-kms"), ("acr", "acr-kms"), ("har", "har-kms")]:
        write(f"container-kms-{reg}", container_pipeline(f"container-kms-{reg}", reg, "kms", suffix))

    # Non-container
    write("non-container-keyless", non_container_orch("non-container-keyless", "keyless"))
    write("non-container-keypair-orch", non_container_orch("non-container-keypair-orch", "keypair"))
    write("non-container-kms-orch", non_container_orch("non-container-kms-orch", "kms"))
    write("non-container-keyless-ing", non_container_ing("non-container-keyless-ing", "keyless"))
    write("non-container-keypair-ing", non_container_ing("non-container-keypair-ing", "keypair"))
    write("non-container-kms-ing", non_container_ing("non-container-kms-ing", "kms"))

    # Repo
    write("repo-gen-syft-spdx", repo_gen("repo-gen-syft-spdx", "Syft", "spdx-json"))
    write("repo-gen-syft-cdx", repo_gen("repo-gen-syft-cdx", "Syft", "cyclonedx-json"))
    # Jenkins uses harness/ssca-cdxgen-plugin + REPO_PATH=npm
    write(
        "repo-gen-cdxgen",
        repo_gen(
            "repo-gen-cdxgen",
            "cdxgen",
            "cyclonedx-json",
            repo_path="npm",
            plugin_image="harness/ssca-cdxgen-plugin:test-githubV2",
        ),
    )
    write("repo-ingest", repo_ingest())
    write("repo-drift", repo_drift())

    # Section D
    write("section-d-container-ingest", section_d_container_ingest())
    write("section-d-keypair-attest", section_d_attest("section-d-keypair-attest", "keypair"))
    write("section-d-kms-attest", section_d_attest("section-d-kms-attest", "kms"))

    print(f"\nTotal workflows: {len(list(OUT.glob('*.yml')))}")


if __name__ == "__main__":
    main()

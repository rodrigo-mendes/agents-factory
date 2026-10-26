#!/usr/bin/env bash
# ==============================================================================
# build-push.sh — Generic OCI Function build-and-push template
#
# Copy this file to services/<function-name>/build-push.sh and chmod +x it.
# All values are sourced from services/.env (relative to this script) and
# from func.yaml in the same directory — NO hardcoded values.
#
# Usage:
#   ./build-push.sh [TAG]
#
# Resolution order for the image tag:
#   1. First positional argument ($1)
#   2. version: field in ./func.yaml
#
# Required in services/.env (one directory up from this script):
#   OCIR_REGION     OCI region code prefix, e.g. "gru" (sa-saopaulo-1)
#   OCIR_NAMESPACE  Object Storage namespace of the tenancy
#   OCIR_REPO       Repository path under the namespace, e.g. "serverless-app"
#   OCIR_USERNAME   "<namespace>/<iam-user>" or federated IDCS email
#   OCIR_PASSWORD   OCIR auth token (NOT the OCI account password)
#
# Optional env var override (not in .env):
#   PLATFORM        Docker --platform value; defaults to "linux/amd64"
#                   Override to "linux/arm64" for local Apple Silicon builds —
#                   always push linux/amd64 to OCI Functions.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

# ── Pre-flight (optional, runs if the centralized script is present) ──────────
PREFLIGHT="${SCRIPT_DIR}/../../scripts/preflight.sh"
if [[ -x "${PREFLIGHT}" ]]; then
  echo "==> Running pre-flight checks..."
  "${PREFLIGHT}" "${SCRIPT_DIR}"
  echo ""
fi

# ── Load environment ──────────────────────────────────────────────────────────
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found."
  echo "       Copy services/.env.example to services/.env and fill in values."
  exit 1
fi
# shellcheck source=/dev/null
source "${ENV_FILE}"

# ── Validate required variables ───────────────────────────────────────────────
for var in OCIR_REGION OCIR_NAMESPACE OCIR_REPO OCIR_USERNAME OCIR_PASSWORD; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: ${var} is not set in ${ENV_FILE}"
    exit 1
  fi
done

# ── Docker login ──────────────────────────────────────────────────────────────
echo "==> Logging in to ${OCIR_REGION}.ocir.io"
echo "${OCIR_PASSWORD}" | docker login "${OCIR_REGION}.ocir.io" \
    -u "${OCIR_USERNAME}" --password-stdin

# ── Resolve function name and tag ─────────────────────────────────────────────
FUNC_NAME=$(grep '^name:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')
TAG="${1:-$(grep '^version:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')}"

PLATFORM="${PLATFORM:-linux/amd64}"
IMAGE="${OCIR_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}/${FUNC_NAME}:${TAG}"

# ── Build ─────────────────────────────────────────────────────────────────────
echo "==> Building ${IMAGE} (platform: ${PLATFORM})"
# Unset proxy vars — prevents corporate proxy interference with layer pulls
# inside the Docker build context.
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  docker build --platform "${PLATFORM}" -t "${IMAGE}" "${SCRIPT_DIR}"

# ── Push ──────────────────────────────────────────────────────────────────────
echo "==> Pushing ${IMAGE}"
docker push "${IMAGE}"

echo ""
echo "Done! Image URI:"
echo "  ${IMAGE}"

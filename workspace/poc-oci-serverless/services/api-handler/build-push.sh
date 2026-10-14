#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Build and push OCI Function image to OCIR
# Usage: ./build-push.sh [tag]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

# Run pre-flight checks if script is available
PREFLIGHT="${SCRIPT_DIR}/../../scripts/preflight.sh"
if [[ -x "${PREFLIGHT}" ]]; then
  echo "==> Running pre-flight checks..."
  "${PREFLIGHT}" "${SCRIPT_DIR}"
  echo ""
fi

# Load environment variables
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found. Copy ../.env.example to ../.env and fill in values."
  exit 1
fi
source "${ENV_FILE}"

# Validate required variables
for var in OCIR_REGION OCIR_NAMESPACE OCIR_REPO OCIR_USERNAME OCIR_PASSWORD; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: ${var} is not set in ${ENV_FILE}"
    exit 1
  fi
done

# Docker login to OCIR
echo "==> Logging in to ${OCIR_REGION}.ocir.io"
echo "${OCIR_PASSWORD}" | docker login "${OCIR_REGION}.ocir.io" -u "${OCIR_USERNAME}" --password-stdin

# Function name from func.yaml
FUNC_NAME=$(grep '^name:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')

# Tag: argument > func.yaml version
if [[ -n "${1:-}" ]]; then
  TAG="$1"
else
  TAG=$(grep '^version:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')
fi

PLATFORM="${PLATFORM:-linux/amd64}"
IMAGE="${OCIR_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}/${FUNC_NAME}:${TAG}"

echo "==> Building ${IMAGE} (platform: ${PLATFORM})"
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  docker build --platform "${PLATFORM}" -t "${IMAGE}" "${SCRIPT_DIR}"

echo "==> Pushing ${IMAGE}"
docker push "${IMAGE}"

echo ""
echo "Done! Image URI:"
echo "  ${IMAGE}"

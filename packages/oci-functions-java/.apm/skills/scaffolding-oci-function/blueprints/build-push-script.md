# Blueprint: build-push.sh Script

> **Runnable template**: [`assets/build-push.sh`](../assets/build-push.sh) — copy that file to
> `services/<function-name>/build-push.sh` and `chmod +x` it. It contains the identical script
> below, kept in a single place to avoid the 6-copy duplication seen in the PoC services.

Reference listing (for documentation purposes — the authoritative copy is `assets/build-push.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"

if [[ -f "${SCRIPT_DIR}/../../scripts/preflight.sh" ]]; then
  echo "==> Running pre-flight checks..."
  "${SCRIPT_DIR}/../../scripts/preflight.sh" "${SCRIPT_DIR}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} not found."
  exit 1
fi
source "${ENV_FILE}"

for var in OCIR_REGION OCIR_NAMESPACE OCIR_REPO OCIR_USERNAME OCIR_PASSWORD; do
  if [[ -z "${!var:-}" ]]; then
    echo "ERROR: ${var} not set in ${ENV_FILE}"
    exit 1
  fi
done

echo "==> Logging in to ${OCIR_REGION}.ocir.io"
echo "${OCIR_PASSWORD}" | docker login "${OCIR_REGION}.ocir.io" -u "${OCIR_USERNAME}" --password-stdin

FUNC_NAME=$(grep '^name:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')
TAG="${1:-$(grep '^version:' "${SCRIPT_DIR}/func.yaml" | awk '{print $2}')}"
PLATFORM="${PLATFORM:-linux/amd64}"
IMAGE="${OCIR_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}/${FUNC_NAME}:${TAG}"

echo "==> Building ${IMAGE} (platform: ${PLATFORM})"
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy \
  docker build --platform "${PLATFORM}" -t "${IMAGE}" "${SCRIPT_DIR}"

echo "==> Pushing ${IMAGE}"
docker push "${IMAGE}"

echo ""
echo "Done! Image URI: ${IMAGE}"
```

## Required `.env` variables

| Variable | Description |
|---|---|
| `OCIR_REGION` | OCI region identifier (e.g. `sa-saopaulo-1`) |
| `OCIR_NAMESPACE` | OCIR namespace (tenancy object storage namespace) |
| `OCIR_REPO` | Repository path inside OCIR |
| `OCIR_USERNAME` | `<tenancy>/<username>` or IDCS user |
| `OCIR_PASSWORD` | Auth token (not account password) |

## Notes

- `set -euo pipefail` ensures the script fails fast on any error or unset variable.
- Proxy variables are explicitly unset for the `docker build` call to avoid proxy interference with layer pulls inside the build.
- The `PLATFORM` variable defaults to `linux/amd64`; override it for Apple Silicon (`linux/arm64`) local builds if needed, but always push `linux/amd64` for OCI.
- The script reads `name:` and `version:` from `func.yaml`; keep those fields accurate.

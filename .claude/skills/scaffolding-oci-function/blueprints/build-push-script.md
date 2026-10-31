# Blueprint: build-push.py Script

> **Runnable template**: [`assets/build-push.py`](../assets/build-push.py) — copy that file to
> `services/<function-name>/build-push.py` and run it with `python3 build-push.py [TAG]`
> (Python 3.8+, standard library only; Linux, macOS and Windows). It is kept in a single place to
> avoid the 6-copy duplication seen in the PoC services. Offline tests with a fake `docker`:
> `python3 tests/run_tests.py` (from the skill folder).

## What it does (in order)

1. **Pre-flight** — if `services/../scripts/preflight.sh` (i.e. `<repo>/scripts/preflight.sh`) exists
   and is executable, prints `==> Running pre-flight checks...` and runs it with the function directory
   as argument (through `bash` on Windows). A non-zero exit stops the script with that exit code.
2. **Load `services/.env`** — missing file → `ERROR: <path> not found.` and exit 1. The file is read as
   `KEY=VALUE` lines (`export`, quotes, `$VAR`/`${VAR}` expansion and `#` comments supported); it is
   not executed as shell code. Values already in the environment count too.
3. **Validate** `OCIR_REGION`, `OCIR_NAMESPACE`, `OCIR_REPO`, `OCIR_USERNAME`, `OCIR_PASSWORD` →
   `ERROR: <VAR> is not set in <path>` and exit 1.
4. **Login** — `docker login <OCIR_REGION>.ocir.io -u <OCIR_USERNAME> --password-stdin`; the password
   goes on stdin only (never on the command line, never printed).
5. **Resolve** the function name (`name:` in `func.yaml`) and the tag (first argument, else `version:`
   in `func.yaml`). A missing `func.yaml` exits 2, a missing field exits 1.
6. **Build** — `docker build --platform <PLATFORM> -t <image> <function dir>` with `HTTP_PROXY`,
   `HTTPS_PROXY`, `http_proxy`, `https_proxy` removed from that call's environment only.
7. **Push** — `docker push <image>`, then prints `Done! Image URI:` and the image.

Image: `<OCIR_REGION>.ocir.io/<OCIR_NAMESPACE>/<OCIR_REPO>/<name>:<tag>`. Any docker failure stops
the script with docker's exit code.

## Required `.env` variables

| Variable | Description |
|---|---|
| `OCIR_REGION` | OCI region key used in the registry host (e.g. `gru` for `sa-saopaulo-1`) |
| `OCIR_NAMESPACE` | OCIR namespace (tenancy object storage namespace) |
| `OCIR_REPO` | Repository path inside OCIR |
| `OCIR_USERNAME` | `<tenancy>/<username>` or IDCS user |
| `OCIR_PASSWORD` | Auth token (not account password) |

## Optional environment variables

| Variable | Default | Use |
|---|---|---|
| `PLATFORM` | `linux/amd64` | `linux/arm64` for local Apple Silicon builds; always push `linux/amd64` to OCI |
| `DOCKER_CMD` | `docker` | Alternative docker CLI (the tests point it at a fake) |

## Notes

- Same contract as the former `build-push.sh` (inputs, steps, output lines, exit codes); the one
  difference is that `services/.env` is parsed, not `source`d — keep it to plain `KEY=VALUE` lines.
- The script reads `name:` and `version:` from `func.yaml`; keep those fields accurate.

#!/usr/bin/env python3
# ==============================================================================
# generate-dashboard-traffic.py — generates load to populate the 3 dashboards
# of func-rr-rest-proxy (Operations Overview, Upstream Dependencies, Route Analytics).
#
# Fires real traffic on the ANONYMOUS routes of the API Gateway, spread over time
# so time-series widgets have multiple data points:
#   - GET  /proxy/health          -> volume, /health GET (D1, D3)
#   - POST /proxy/item/webhook    -> spans RMS/TargetServices, custom metrics (D1, D2, D3)
#       * PAYLOAD valid items      -> 200
#       * PAYLOAD empty item id    -> 207 (RestProxyError{207})
#       * Invalid JSON             -> 400 (RestProxyError{400})
#       * EVENT mode               -> span RMS.ItemsDelta
#
# Store routes (/proxy/store/*) are AUTHENTICATION_ONLY (JWT disabled) -> not
# callable; store widgets remain empty (expected). Throttle likewise.
#
# All configurable values are exposed as environment variables or CLI flags.
# No OCIDs, tenancy IDs, profile names, or namespaces are hardcoded.
#
# Usage (all parameters are optional — env vars or flags):
#   ./generate-dashboard-traffic.py [--rounds N] [--sleep SEC] [--url API_BASE_URL]
#
# Environment variables (can replace any flag):
#   ROUNDS          Number of traffic rounds          (default: 4)
#   SLEEP           Seconds to sleep between waves    (default: 40)
#   API_BASE_URL    API Gateway base URL              (resolved via terraform output if not set)
#   TF_DIR          Terraform environment directory   (default: <repo-root>/infra/environments/dev)
#   SIM             Optional webhook simulator script (default: <repo-root>/services/func-rr-rest-proxy/scripts/simulate-webhook.py, else .sh)
#
# Examples:
#   ./generate-dashboard-traffic.py
#   ./generate-dashboard-traffic.py --rounds 2 --sleep 20
#   ./generate-dashboard-traffic.py --url https://abc123.apigateway.sa-saopaulo-1.oci.customer-oci.com
#   ROUNDS=6 SLEEP=30 ./generate-dashboard-traffic.py
#   API_BASE_URL=https://abc123... ./generate-dashboard-traffic.py --rounds 2
#
# Source: workspace/poc-oci-serverless/scripts/generate-dashboard-traffic.sh (ported to Python)
# ==============================================================================
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402  (só helpers; NÃO chama L.init())


def _seq_count(s):
    try:
        n = float(s)
    except ValueError:
        L.err_raw(f"seq: invalid floating point argument: '{s}'")
        return 0
    return max(0, int(n // 1))


def main(argv):
    rounds = os.environ.get("ROUNDS") or "4"
    sleep_s = os.environ.get("SLEEP") or "40"
    api_base_url = os.environ.get("API_BASE_URL", "")
    prog = os.path.basename(__file__)

    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--rounds", "--sleep", "--url"):
            if i + 1 >= len(argv):
                L.unbound(prog)
            val = argv[i + 1]
            if a == "--rounds":
                rounds = val
            elif a == "--sleep":
                sleep_s = val
            else:
                api_base_url = val
            i += 2
        elif a in ("-h", "--help"):
            L.print_help(os.path.abspath(__file__))
            return 0
        else:
            L.err_raw(f"Unknown argument: {a}")
            return 2

    script_dir = L.SCRIPT_DIR
    rc, top = L.run(L.GIT_CMD + ["-C", script_dir, "rev-parse", "--show-toplevel"])
    top = top.rstrip("\r\n") if rc == 0 else ""
    repo_root = top or os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", "..", ".."))
    tf_dir = os.environ.get("TF_DIR") or os.path.join(repo_root, "infra", "environments", "dev")
    sim = os.environ.get("SIM") or (L.find_project_script(
        os.path.join(repo_root, "services", "func-rr-rest-proxy", "scripts"), "simulate-webhook") or "")

# --- resolve base URL ---------------------------------------------------------
    if not api_base_url:
        if L.have(L.TERRAFORM_CMD) and os.path.isdir(tf_dir):
            # `$(terraform ... 2>/dev/null || true)`: stdout é usado qualquer que seja o rc
            _rc, out = L.run(L.TERRAFORM_CMD + [f"-chdir={tf_dir}", "output", "-raw", "api_base_url"])
            api_base_url = out.rstrip("\r\n")
    if not api_base_url:
        L.err_raw("ERROR: API_BASE_URL not resolved.")
        L.err_raw("  Options:")
        L.err_raw("    --url <url>                       pass via flag")
        L.err_raw("    API_BASE_URL=<url> ./script.py    pass via env var")
        L.err_raw(f"    terraform output api_base_url     from {tf_dir} (requires active Terraform state)")
        return 1
    os.environ["API_BASE_URL"] = api_base_url

# item ids per round (arbitrary test identifiers — not infrastructure OCIDs)
    itemsets = [
        os.environ.get("ITEM_SET_1") or "100010000",
        os.environ.get("ITEM_SET_2") or "100010000,100010049",
        os.environ.get("ITEM_SET_3") or "100010000,100010049,100010050",
        os.environ.get("ITEM_SET_4") or "100010000,100010049,100010050,100010051",
    ]

    def hdr(msg):
        print(f"\n=== {msg} ===")

    def hit(method, path, data=""):
        """method path [data] -> log status code"""
        if method == "GET":
            code = L.http_code(api_base_url + path)
        else:
            code = L.http_code(api_base_url + path, method=method, data=data)
        print(f"  {method:<4} {path:<24} -> {code}")

    sim_ok = bool(sim) and (os.path.isfile(sim) if sim.endswith(".py") else L.is_executable(sim))

    def run_sim(*args):
        """"$SIM" ... 2>&1 | grep -iE 'HTTP|status|PASS|FAIL' | head -3 || true"""
        sys.stdout.flush()
        try:
            p = subprocess.run(L.project_script_cmd(sim) + list(args), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
            text = p.stdout.decode("utf-8", "replace")
        except OSError:
            text = ""
        shown = [ln for ln in text.splitlines() if re.search(r"HTTP|status|PASS|FAIL", ln, re.IGNORECASE)][:3]
        for ln in shown:
            print(ln)

    print(f"Target: {api_base_url} | rounds={rounds} sleep={sleep_s}s | "
          f"simulate-webhook: {'ok' if sim_ok else 'absent'}")

    n_rounds = _seq_count(rounds)
    for r in range(1, n_rounds + 1):
        hdr(f"Round {r}/{rounds}")

        # Wave 1: health (volume, /health GET)
        for _ in range(3):
            hit("GET", "/proxy/health")

        # Wave 2: webhook OK (valid PAYLOAD) — uses simulate-webhook if present
        if sim_ok:
            idx = (r - 1) % len(itemsets)
            run_sim("--mode", "PAYLOAD", "--items", itemsets[idx], "--uuid", f"mass-r{r}-ok")
        else:
            hit("POST", "/proxy/item/webhook",
                '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r' + str(r)
                + '-ok","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A",'
                  '"itemDescription":"sim"}],"count":1}}')

        L.sleep(sleep_s)

        # Wave 3: webhook 207 (one empty item id -> partial failure)
        hit("POST", "/proxy/item/webhook",
            '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r' + str(r)
            + '-207","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A",'
              '"itemDescription":"ok"},{"action":"UPDATE","item":"","status":"A",'
              '"itemDescription":"invalid"}],"count":2}}')

        # Wave 4: webhook 400 (malformed JSON -> parse error)
        hit("POST", "/proxy/item/webhook", '{"type":"PAYLOAD","payload":{"items":[ BROKEN JSON')

        L.sleep(sleep_s)

        # Wave 5: webhook EVENT (triggers span RMS.ItemsDelta in APM)
        if sim_ok:
            run_sim("--mode", "EVENT", "--uuid", f"mass-r{r}-event")
        else:
            hit("POST", "/proxy/item/webhook",
                '{"type":"EVENT","service":"foundation/item","uuid":"mass-r' + str(r)
                + '-event","since":"2026-05-29T02:27:59.838Z"}')

        try:
            more = r < int(rounds)
        except ValueError:
            more = False
        if more:
            L.sleep(sleep_s)

    hdr("Traffic generation complete")
    print("Wait ~3 min (metric ingestion latency) / a few min (APM trace ingestion), then validate dashboards.")
    print("  check-dashboards.py                        # render-readiness (5th pillar)")
    print("  check-dashboards.py --name-filter '<name>' # single dashboard")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

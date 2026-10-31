#!/usr/bin/env python3
# ==============================================================================
# register-webhook.py — registra/gerencia um webhook no RMS/MFCS apontando para
# uma listenerUrl (nossa function). Chama:
#   {RMS_MERCH_BASE}/services/administration/operations/webhooks/manage
# com OAuth2 Bearer (client-credentials; creds via env ou Vault).
#
# Uso:
#   python3 register-webhook.py --service foundation/item --listener https://gw/v1/proxy/item/webhook
#   python3 register-webhook.py --action list
#   python3 register-webhook.py --action disable --service foundation/item --listener <url>
#
# Opções:
#   --action register|list|disable   (default register)
#   --service <s>                     (default foundation/item)
#   --listener <url>                  (obrigatório p/ register/disable)
# Env overrides: CREDENTIAL_NAME(APP_TESTE_BLUM) INCLUDE_PAYLOAD(Y) INTERVAL_SECONDS(10)
#   PAGE_LIMIT(1000) INCLUDE(include=items.action,items.item,items.status,items.itemDescription)
#   HEARTBEAT_HOURS(1) WEBHOOK_HTTP_METHOD(POST) MANAGE_URL
#
# ATENÇÃO: register/disable MUDAM estado no RMS (ele passa a chamar a listenerUrl).
# ==============================================================================
"""Port of register-webhook.sh (standard library only)."""

import json
import os
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_rms as L  # noqa: E402


def env(name, default):
    return os.environ.get(name) or default


def build_body(cfg, enabled):
    """jq -n ... (pretty, 2-space indent). Returns "" when an --argjson value is not JSON."""
    numbers = {}
    for key in ("INTERVAL_SECONDS", "PAGE_LIMIT", "HEARTBEAT_HOURS"):
        try:
            numbers[key] = json.loads(cfg[key])
        except ValueError:
            sys.stderr.write("jq: Invalid JSON text passed to --argjson\n")
            return ""
    body = {"collectionSize": 1, "items": [{
        "service": cfg["SERVICE"], "credentialName": cfg["CREDENTIAL_NAME"], "listenerUrl": cfg["LISTENER"],
        "includePayload": cfg["INCLUDE_PAYLOAD"], "enabled": enabled,
        "intervalSeconds": numbers["INTERVAL_SECONDS"], "pageLimit": numbers["PAGE_LIMIT"],
        "queryParameter": cfg["INCLUDE"], "heartbeatIntervalHours": numbers["HEARTBEAT_HOURS"]}]}
    return json.dumps(body, indent=2, ensure_ascii=False)


def send(url, token, method, body):
    headers = {"Authorization": "Bearer %s" % token, "Accept": "application/json"}
    if body:
        headers["Content-Type"] = "application/json"
    return L.http_request(method, url, headers=headers, data=body or None, timeout=60)


def main(argv):
    opts = L.parse_args(argv, {"--action": "action", "--service": "service", "--listener": "listener"},
                        script_path=os.path.abspath(__file__))
    action = opts.get("action", "register")
    cfg = {
        "SERVICE": opts.get("service", env("SERVICE", "foundation/item")),
        "LISTENER": opts.get("listener", os.environ.get("LISTENER", "")),
        "CREDENTIAL_NAME": env("CREDENTIAL_NAME", "APP_TESTE_BLUM"),
        "INCLUDE_PAYLOAD": env("INCLUDE_PAYLOAD", "Y"),
        "INTERVAL_SECONDS": env("INTERVAL_SECONDS", "10"),
        "PAGE_LIMIT": env("PAGE_LIMIT", "1000"),
        "INCLUDE": env("INCLUDE", "include=items.action,items.item,items.status,items.itemDescription"),
        "HEARTBEAT_HOURS": env("HEARTBEAT_HOURS", "1"),
    }
    method = env("WEBHOOK_HTTP_METHOD", "POST")
    manage_url = env("MANAGE_URL", L.RMS_MERCH_BASE + "/services/administration/operations/webhooks/manage")

    token = L.rms_token(log=lambda _msg: None)
    if token is None:
        return 1

    if action in ("register", "disable"):
        if not cfg["LISTENER"]:
            L.err("--listener é obrigatório p/ %s" % action)
            return 2
        enabled = "N" if action == "disable" else "Y"
        L.hdr("WEBHOOK %s -> %s" % (action, manage_url))
        L.info("service=%s credentialName=%s enabled=%s" % (cfg["SERVICE"], cfg["CREDENTIAL_NAME"], enabled))
        L.info("listenerUrl=%s" % cfg["LISTENER"])
        body = build_body(cfg, enabled)
        L.info("body: %s" % body)
        code, resp_body = send(manage_url, token, method, body)
    elif action == "list":
        L.hdr("WEBHOOK list -> %s" % manage_url)
        code, resp_body = send(manage_url, token, "GET", "")
    else:
        L.err("ação inválida: %s" % action)
        return 2

    L.out("%s-- HTTP %s --%s\n" % (L.C_BLD, code, L.C_RST))
    L.print_json_or_raw(resp_body)
    if code.startswith("2"):
        L.pass_("%s -> HTTP %s" % (action, code))
    elif code.startswith("30"):
        L.fail("%s -> HTTP %s (redirect IDCS Cloud Gate: RMS só aceita de rede allowlistada — "
               "rode de dentro da OCI/VPN)" % (action, code))
    elif code in ("401", "403"):
        L.fail("%s -> HTTP %s (auth: credentialName/scope/token)" % (action, code))
    else:
        L.fail("%s -> HTTP %s (405/404? ajuste WEBHOOK_HTTP_METHOD/MANAGE_URL)" % (action, code))
    return L.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

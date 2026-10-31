#!/usr/bin/env python3
# ==============================================================================
# simulate-webhook.py — simula a engine de webhook do RMS fazendo POST de um
# envelope EVENT/PAYLOAD numa listenerUrl (a function consumidora). Testa o
# fluxo sem depender do RMS disparar.
#
# Uso:
#   python3 simulate-webhook.py --listener https://gw/v1/proxy/item/webhook
#   python3 simulate-webhook.py --listener <url> --mode EVENT
#   python3 simulate-webhook.py --listener <url> --service foundation/item --items 100010000,100010049
#
# Opções: --listener <url> (obrigatório) | --mode EVENT|PAYLOAD (default PAYLOAD)
#         --service <s> (default foundation/item) | --items csv | --uuid <id>
#         --expect <regex> (default ^(200|207)$)
# ==============================================================================
"""Port of simulate-webhook.sh (standard library only)."""

import os
import re
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_rms as L  # noqa: E402

ENVIRONMENT = "rgbu-rex-brxs-par1-mfcs"


def build_items(items):
    """Same string as the bash build_items (first line only, whitespace removed, empties skipped)."""
    fields = items.split("\n", 1)[0].split(",")
    while fields and fields[-1] == "":  # read -ra drops trailing empty fields
        fields.pop()
    parts = []
    for raw in fields:
        ident = re.sub(r"\s", "", raw)
        if not ident:
            continue
        parts.append('{"action":"UPDATE","item":"%s","status":"A","itemDescription":"sim %s"}' % (ident, ident))
    return ",".join(parts)


def count_fields(items):
    """awk -F',' '{print NF}' <<< "$ITEMS" (one NF per line)."""
    return "\n".join(str(0 if line == "" else line.count(",") + 1) for line in items.split("\n"))


def main(argv):
    opts = L.parse_args(argv, {"--listener": "listener", "--mode": "mode", "--service": "service",
                               "--items": "items", "--uuid": "uuid", "--expect": "expect"},
                        script_path=os.path.abspath(__file__))
    listener = opts.get("listener", "")
    mode = opts.get("mode", "PAYLOAD").upper()
    service = opts.get("service", "foundation/item")
    items = opts.get("items", os.environ.get("ITEMS") or "100010000,100010049,100010050")
    uuid = opts.get("uuid", os.environ.get("UUID") or "sim-webhook-0001")
    expect = opts.get("expect", r"^(200|207)$")
    timestamp = os.environ.get("TIMESTAMP") or "2026-05-29T13:35:59.223Z"
    since = os.environ.get("SINCE") or "2026-05-29T02:27:59.838Z"

    if not listener:
        L.err("--listener é obrigatório")
        return 2

    head = '{"type":"%s","timestamp":"%s","service":"%s","uuid":"%s","environment":"%s","since":"%s"' % (
        mode, timestamp, service, uuid, ENVIRONMENT, since)
    if mode == "EVENT":
        body = head + "}"
    elif mode == "PAYLOAD":
        body = head + ',"payload":{"items":[%s],"hasMore":false,"limit":1000,"count":%s}}' % (
            build_items(items), count_fields(items))
    else:
        L.err("MODE inválido: %s (EVENT|PAYLOAD)" % mode)
        return 2

    L.hdr("SIMULATE WEBHOOK (%s, %s) -> %s" % (mode, service, listener))
    L.info("uuid=%s items=%s" % (uuid, items))
    L.info("body: %s" % body)
    code, resp_body = L.http_request("POST", listener, headers={"Content-Type": "application/json"},
                                     data=body, timeout=65)
    L.out("%s-- resposta (HTTP %s) --%s\n%s\n" % (L.C_BLD, code, L.C_RST, resp_body))
    try:
        matched = re.search(expect, code) is not None
    except re.error:  # bash [[ =~ ]] with an invalid regex is simply false
        matched = False
    if matched:
        L.pass_("POST (%s) -> HTTP %s" % (mode, code))
    elif code == "000":
        L.skip("HTTP 000 (cold start) — repita p/ aquecer")
    else:
        L.fail("POST (%s) -> HTTP %s (esperado %s)" % (mode, code, expect))
    return L.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

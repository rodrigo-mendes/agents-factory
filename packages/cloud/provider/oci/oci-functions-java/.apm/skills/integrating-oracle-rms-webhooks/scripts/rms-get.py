#!/usr/bin/env python3
# ==============================================================================
# rms-get.py — GET em endpoints foundation do RMS/MFCS (by-id ou delta).
#
#   by-id : GET {base}/services/foundation/<ent>/<id>        (path-param)
#   delta : GET {base}/services/foundation/<ent>?since=&before=&limit=&include=
#
# Uso:
#   python3 rms-get.py --entity item --id 100010000
#   python3 rms-get.py --entity item --since 2026-05-29T02:01:56Z --before 2026-05-29T02:06:57Z
#   python3 rms-get.py --entity item --since ... --include "items.item,items.itemDescription"
#   python3 rms-get.py --entity diffid --id G_COLOR
#
# Opções: --entity <e> (default item) | --id <id> | --since <ts> | --before <ts>
#         --limit <n> (default 1000) | --include <csv> | --raw (só body)
# ==============================================================================
"""Port of rms-get.sh (standard library only)."""

import os
import sys
import urllib.parse

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_rms as L  # noqa: E402


def enc(value):
    """jq @uri: keep only unreserved chars (A-Za-z0-9-_.~)."""
    return urllib.parse.quote(value, safe="-_.~")


def main(argv):
    opts = L.parse_args(
        argv,
        {"--entity": "entity", "--id": "id", "--since": "since", "--before": "before",
         "--limit": "limit", "--include": "include"},
        flags={"--raw": "raw"}, script_path=os.path.abspath(__file__))
    entity = opts.get("entity", "item")
    ident = opts.get("id", "")
    since = opts.get("since", "")
    before = opts.get("before", "")
    limit = opts.get("limit", "1000")
    include = opts.get("include", "")
    raw = opts.get("raw", False)

    url = L.rms_url(entity, ident)
    if not ident:
        sep = "?"
        for key, value, encode in (("limit", limit, False), ("since", since, True),
                                   ("before", before, True), ("include", include, True)):
            if value:
                url += "%s%s=%s" % (sep, key, enc(value) if encode else value)
                sep = "&"

    token = L.rms_token(log=lambda _msg: None)
    if token is None:
        return 1

    if not raw:
        L.hdr("RMS GET %s%s" % (entity, "/" + ident if ident else ""))
        L.info(url)

    code, body = L.http_request("GET", url, headers={
        "Authorization": "Bearer %s" % token, "Accept": "application/json"}, timeout=60)

    if raw:
        L.out(body + "\n")
    else:
        L.out("%s-- HTTP %s --%s\n" % (L.C_BLD, code, L.C_RST))
        L.print_json_or_raw(body)

    if code.startswith("2"):
        return 0
    if code.startswith("30"):
        L.err("HTTP %s → redirect IDCS Cloud Gate. RMS só aceita de rede allowlistada (egress OCI/VPN); "
              "local recebe 302. Rode de dentro da OCI ou via VPN." % code)
    elif code == "404":
        L.err("HTTP 404 — id inexistente OU path errado (base MerchIntegrations? /foundation/<ent>/{id}?)")
    elif code in ("401", "403"):
        L.err("HTTP %s — token/scope não aceitos" % code)
    else:
        L.err("HTTP %s" % code)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

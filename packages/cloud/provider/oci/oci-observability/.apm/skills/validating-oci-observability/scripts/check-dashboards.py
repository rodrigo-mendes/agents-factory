#!/usr/bin/env python3
# ==============================================================================
# check-dashboards.py — 5º pilar: valida que os Management Dashboards RENDERIZAM.
#
# Import válido ≠ render válido: o `oci_management_dashboard_management_dashboards_import`
# aceita JSON estruturalmente correto que o Console não consegue desenhar. Este check
# valida os campos de render-readiness que faltavam nos pos-mortems P7/P8/P10:
#   - dashboard em estado ACTIVE
#   - cada saved-search tem widget-template + widget-vm (não vazios)
#   - data-config[].type ∈ {monitoringDataSource, tracesDataSource}
#   - metric widgets (monitoringDataSource) declaram o param `regionName`
#     (senão importa mas fica em branco — P10)
#   - cross-check: há datapoints por trás (custom namespace + oci_faas) => ingestão
#
# Uso: ./check-dashboards.py [--name-filter "REST Proxy"]
# Env: OCI_PROFILE, OCI_AUTH, OCI_REGION, COMPARTMENT_OCID, LOOKBACK_MIN
# ==============================================================================
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402

VALID_TYPES = "monitoringDataSource tracesDataSource"


def _items(text):
    v = L.jload(text)
    return [] if v is L.NOINPUT else L.jiter(L.jget(L.jget(v, "data"), "items"))


def _dash_rows(text, name_filter):
    rows = []
    try:
        for d in _items(text):
            if not isinstance(d, dict):
                break
            if d.get("is-oob-dashboard") is True:
                continue
            name = d.get("display-name")
            if name_filter != "":
                if not isinstance(name, str):
                    break  # jq `test` em não-string -> erro -> para
                if not re.search(name_filter, name):
                    continue
            state = d.get("lifecycle-state")
            rows.append(L.tsv([name, state if L.jtruthy(state) else "UNKNOWN"]))
    except (ValueError, L.JqError, re.error):
        pass
    return [r for r in rows if r]


def _ss_rows(text):
    rows = []
    try:
        for s in _items(text):
            if not isinstance(s, dict):
                break
            if s.get("is-oob-saved-search") is True:
                continue
            wt = s.get("widget-template")
            dc = s.get("data-config")
            dc0 = dc[0] if isinstance(dc, list) and dc else None
            dctype = L.jget(dc0, "type") if dc0 is None or isinstance(dc0, dict) else None
            pc = s.get("parameters-config")
            pc = pc if L.jtruthy(pc) else []
            names = [L.jget(p, "name") for p in pc] if isinstance(pc, list) else []
            rows.append(L.tsv([s.get("display-name"),
                               wt if L.jtruthy(wt) else "",
                               dctype if L.jtruthy(dctype) else "",
                               "yes" if "regionName" in names else "no"]))
    except (ValueError, L.JqError):
        pass
    return [r for r in rows if r]


def _read_tab_fields(row):
    """`IFS=$'\\t' read -r a b c d` — tab é IFS-whitespace: tabs seguidos colapsam."""
    parts = re.split(r"\t+", row.strip("\t"), maxsplit=3)
    parts += [""] * (4 - len(parts))
    return parts


def main(argv):
    L.init()

    name_filter = ""
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--name-filter":
            if i + 1 >= len(argv):
                L.unbound(os.path.basename(__file__))
            name_filter = argv[i + 1]
            i += 2
        elif a in ("-h", "--help"):
            L.print_help(os.path.abspath(__file__))
            return 0
        else:
            L.err(f"Argumento desconhecido: {a}")
            return 2

    L.require_tools()
    L.require_session()

    L.hdr("Pilar 5 — Dashboards (render-readiness)")
    L.info(f"Compartment: {L.COMPARTMENT_OCID}")
    if name_filter:
        L.info(f"Filtro de nome: '{name_filter}'")

# --- 1. Dashboards ACTIVE ------------------------------------------------------
    rc, dash_json = L.oci_cli("management-dashboard", "dashboard", "list",
                              "--compartment-id", L.COMPARTMENT_OCID, "--all")
    if rc != 0:
        dash_json = "{}"

    dash_rows = _dash_rows(dash_json, name_filter)
    if not dash_rows:
        L.fail("Nenhum dashboard custom encontrado no compartment (esperado >=1).")
    else:
        for row in dash_rows:
            name = row.split("\t", 1)[0]
            state = row.rsplit("\t", 1)[-1]
            if state == "ACTIVE":
                L.pass_(f"Dashboard ACTIVE: {name}")
            else:
                L.fail(f"Dashboard não-ACTIVE ({state}): {name}")

# --- 2. Saved-searches: render fields -----------------------------------------
    rc, ss_json = L.oci_cli("management-dashboard", "saved-search", "list",
                            "--compartment-id", L.COMPARTMENT_OCID, "--all")
    if rc != 0:
        ss_json = "{}"

    ss_rows = _ss_rows(ss_json)
    if not ss_rows:
        L.skip("Nenhuma saved-search custom (dashboards sem widgets?).")
    else:
        for row in ss_rows:
            ss_name, wt, dctype, has_region = _read_tab_fields(row)
            # widget-template presente
            if wt and wt not in ("None", "null"):
                L.pass_(f"widget-template OK: {ss_name}")
            else:
                L.fail(f"widget-template AUSENTE (não renderiza): {ss_name}")
            # data-config type válido
            if f" {dctype} " in f" {VALID_TYPES} ":
                L.pass_(f"dataSource '{dctype}' OK: {ss_name}")
            else:
                L.fail(f"dataSource inválido/ausente ('{dctype}'): {ss_name}")
            # metric widget precisa de regionName param
            if dctype == "monitoringDataSource":
                if has_region == "yes":
                    L.pass_(f"regionName param OK (metric): {ss_name}")
                else:
                    L.fail(f"regionName param AUSENTE (metric fica em branco — P10): {ss_name}")

# --- 3. Cross-check ingestão (há dado por trás?) ------------------------------
    st = L.iso_minus_min(L.LOOKBACK_MIN or "60")
    et = L.iso_now()

    def metric_has_data(ns, mql):
        _rc, out = L.oci_cli("monitoring", "metric-data", "summarize-metrics-data",
                             "--compartment-id", L.COMPARTMENT_OCID, "--namespace", ns, "--query-text", mql,
                             "--start-time", st, "--end-time", et)
        try:
            n = L.count_datapoints(out)
        except (ValueError, L.JqError):
            return False
        return n != "" and n > 0

    for label, app_ocid, ns, prefix, _fn in L.FUNCTIONS_META:
        if metric_has_data("oci_faas", f'FunctionInvocationCount[1m]{{applicationId="{app_ocid}"}}.sum()'):
            L.pass_(f"ingestão oci_faas OK: {label}")
        else:
            L.skip(f"sem datapoints oci_faas p/ {label} (gere tráfego: scripts/generate-dashboard-traffic.py)")
        if metric_has_data(ns, f"{prefix}Invocation[1m].sum()"):
            L.pass_(f"ingestão custom ({ns}) OK: {label}")
        else:
            L.skip(f"sem datapoints custom ({ns}) p/ {label}")

    return L.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

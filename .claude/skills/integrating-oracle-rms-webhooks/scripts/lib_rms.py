#!/usr/bin/env python3
# ==============================================================================
# lib_rms.py — config + helpers compartilhados pelos scripts de integração RMS/MFCS.
# Uso: os demais scripts fazem `import lib_rms` (mesmo diretório). Não executar.
# Todas as variáveis podem ser sobrescritas por env antes de chamar.
# Overrides p/ testes: OCI_CMD (default oci), TERRAFORM_CMD (default terraform).
# ==============================================================================
"""Shared config/helpers for the RMS/MFCS scripts (port of lib-rms.sh). Standard library only."""

import base64
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

# ------------------------------------------------------------------------------
# Config base (sobrescrevível por env var)
# ------------------------------------------------------------------------------
OCI_PROFILE = os.environ.get("OCI_PROFILE") or "poc"
OCI_AUTH = os.environ.get("OCI_AUTH") or "security_token"
OCI_REGION = os.environ.get("OCI_REGION") or "sa-saopaulo-1"

# Base MerchIntegrations (IRMÃ de RmsReSTServices — NÃO filha).
RMS_MERCH_BASE = os.environ.get("RMS_MERCH_BASE") or (
    "https://<mfcs-host>/<mfcs-tenant>/MerchIntegrations")  # placeholder: set RMS_MERCH_BASE
# OAuth2 IDCS.
RMS_TOKEN_URL = os.environ.get("RMS_TOKEN_URL") or (
    "https://idcs-<id>.identity.oraclecloud.com/oauth2/v1/token")  # placeholder: set RMS_TOKEN_URL
RMS_SCOPE = os.environ.get("RMS_SCOPE") or "rgbu:merch:<APP-ENV>"  # placeholder: set RMS_SCOPE

# Nomes dos recursos Vault no terraform state (creds OAuth). Sobrescrevível.
RMS_TF_SECRET_ID_RESOURCE = os.environ.get("RMS_TF_SECRET_ID_RESOURCE") or "oci_vault_secret.rest_proxy_oauth_client_id[0]"
RMS_TF_SECRET_SECRET_RESOURCE = (os.environ.get("RMS_TF_SECRET_SECRET_RESOURCE")
                                 or "oci_vault_secret.rest_proxy_oauth_client_secret[0]")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------------------
# Cores / logging
# ------------------------------------------------------------------------------
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", newline="\n")  # LF + UTF-8 like the bash original
    except (AttributeError, ValueError):
        pass

if sys.stdout.isatty():
    C_RED, C_GRN, C_YLW = "\033[0;31m", "\033[0;32m", "\033[0;33m"
    C_BLU, C_BLD, C_RST = "\033[0;34m", "\033[1m", "\033[0m"
else:
    C_RED = C_GRN = C_YLW = C_BLU = C_BLD = C_RST = ""


def out(text=""):
    sys.stdout.write(text)
    sys.stdout.flush()


def info(msg):
    out("%s[i]%s %s\n" % (C_BLU, C_RST, msg))


def warn(msg):
    sys.stdout.flush()
    sys.stderr.write("%s[!]%s %s\n" % (C_YLW, C_RST, msg))
    sys.stderr.flush()


def err(msg):
    sys.stdout.flush()
    sys.stderr.write("%s[x]%s %s\n" % (C_RED, C_RST, msg))
    sys.stderr.flush()


def hdr(msg):
    out("\n%s== %s ==%s\n" % (C_BLD, msg, C_RST))


COUNTS = {"pass": 0, "fail": 0, "warn": 0}


def pass_(msg):
    COUNTS["pass"] += 1
    out("%s  PASS%s %s\n" % (C_GRN, C_RST, msg))


def fail(msg):
    COUNTS["fail"] += 1
    out("%s  FAIL%s %s\n" % (C_RED, C_RST, msg))


def skip(msg):
    COUNTS["warn"] += 1
    out("%s  WARN%s %s\n" % (C_YLW, C_RST, msg))


def summary():
    """Prints the result line; returns the exit code (0 when FAIL=0)."""
    out("\n%s---------------------------------------------%s\n" % (C_BLD, C_RST))
    out("RESULTADO: %sPASS=%d%s %sFAIL=%d%s %sWARN=%d%s\n" % (
        C_GRN, COUNTS["pass"], C_RST, C_RED, COUNTS["fail"], C_RST, C_YLW, COUNTS["warn"], C_RST))
    return 0 if COUNTS["fail"] == 0 else 1


def print_help(script_path):
    """Same as `grep '^#' "$0" | sed 's/^# \\{0,1\\}//' | sed '/^!/d'`."""
    with open(script_path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                continue
            line = line.rstrip("\n")[1:]
            if line.startswith(" "):
                line = line[1:]
            if line.startswith("!"):
                continue
            out(line + "\n")


def parse_args(argv, spec, flags=(), script_path=None):
    """Sequential parser mirroring the bash `while/case` loops.

    spec: {"--opt": "key"} options that take a value; flags: {"--raw": "key"} boolean.
    Returns dict; exits 0 on -h/--help, 2 on unknown arg, 1 on missing value (bash `set -u`).
    """
    flags = dict(flags)
    values = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in spec:
            if i + 1 >= len(argv):
                sys.stderr.write("%s: $2: unbound variable\n" % os.path.basename(script_path or sys.argv[0]))
                sys.exit(1)
            values[spec[arg]] = argv[i + 1]
            i += 2
        elif arg in flags:
            values[flags[arg]] = True
            i += 1
        elif arg in ("-h", "--help"):
            print_help(script_path)
            sys.exit(0)
        else:
            err("arg desconhecido: %s" % arg)
            sys.exit(2)
    return values


# ------------------------------------------------------------------------------
# External commands (overridable for tests)
# ------------------------------------------------------------------------------
def split_cmd(value):
    """Splits a command override (e.g. OCI_CMD='"C:\\py\\python.exe" "fake_oci.py"')."""
    if os.name == "nt":
        parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in shlex.split(value, posix=False)]
    else:
        parts = shlex.split(value)
    if parts:
        resolved = shutil.which(parts[0])
        if resolved:
            parts[0] = resolved
    return parts


def run_cmd(argv):
    """Runs a command; returns (rc, stdout_bytes). stderr discarded (2>/dev/null)."""
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return 127, b""
    return proc.returncode, proc.stdout


def oci_cli(*args):
    cmd = split_cmd(os.environ.get("OCI_CMD") or "oci")
    return run_cmd(cmd + ["--profile", OCI_PROFILE, "--auth", OCI_AUTH, "--region", OCI_REGION] + list(args))


def tf_dir():
    """TF_DIR or <repo>/infra/environments/dev (repo root via git, lazily resolved)."""
    if os.environ.get("TF_DIR"):
        return os.environ["TF_DIR"]
    rc, stdout = run_cmd(["git", "-C", SCRIPT_DIR, "rev-parse", "--show-toplevel"])
    root = stdout.decode("utf-8", "replace").strip() if rc == 0 else ""
    if not root:
        root = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
    return os.path.join(root, "infra", "environments", "dev")


# ------------------------------------------------------------------------------
# Credenciais OAuth: env CLIENT_ID/CLIENT_SECRET, senão Vault (via terraform state).
# ------------------------------------------------------------------------------
def _tf_secret_ocid(resource):
    """terraform state show <resource> -> first `id = "..."` value."""
    cmd = split_cmd(os.environ.get("TERRAFORM_CMD") or "terraform")
    _rc, stdout = run_cmd(cmd + ["-chdir=%s" % tf_dir(), "state", "show", resource])
    for line in stdout.decode("utf-8", "replace").splitlines():
        stripped = line.lstrip(" \t")
        if stripped.startswith("id"):
            rest = stripped[2:].lstrip(" \t")
            if rest.startswith("="):
                fields = line.split('"')
                return fields[1] if len(fields) > 1 else ""
    return ""


def _vault_secret(secret_ocid):
    """Secret bundle content, base64-decoded (never printed)."""
    _rc, stdout = oci_cli("secrets", "secret-bundle", "get", "--secret-id", secret_ocid,
                          "--query", 'data."secret-bundle-content".content', "--raw-output")
    try:
        decoded = base64.b64decode(b"".join(stdout.split()), validate=False)
    except (ValueError, TypeError):
        return ""
    return decoded.decode("utf-8", "replace").rstrip("\n")


def rms_resolve_credentials(log=info):
    """Returns (client_id, client_secret); exits 1 when they cannot be resolved."""
    client_id = os.environ.get("CLIENT_ID", "")
    client_secret = os.environ.get("CLIENT_SECRET", "")
    if client_id and client_secret:
        log("Credenciais OAuth via env.")
        return client_id, client_secret
    log("Buscando credenciais OAuth no Vault (terraform state + oci CLI)...")
    id_ocid = _tf_secret_ocid(RMS_TF_SECRET_ID_RESOURCE)
    sec_ocid = _tf_secret_ocid(RMS_TF_SECRET_SECRET_RESOURCE)
    if not (id_ocid and sec_ocid):
        err("OCIDs dos secrets não achados no state. Defina CLIENT_ID/CLIENT_SECRET.")
        sys.exit(1)
    client_id = _vault_secret(id_ocid)
    client_secret = _vault_secret(sec_ocid)
    if not (client_id and client_secret):
        err("Falha ao ler Vault (sessão OCI válida? oci session authenticate --profile %s)." % OCI_PROFILE)
        sys.exit(1)
    log("Credenciais carregadas do Vault.")
    return client_id, client_secret


# ------------------------------------------------------------------------------
# HTTP (curl -s equivalent: no redirects followed, HTTP 000 on transport error)
# ------------------------------------------------------------------------------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_request(method, url, headers=None, data=None, timeout=60):
    """Returns (http_code_str, body_str). Body trailing newlines stripped like `$(...)`."""
    payload = data.encode("utf-8") if isinstance(data, str) else data
    req = urllib.request.Request(url, data=payload, method=method, headers=headers or {})
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            code, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        code = exc.code
        try:
            raw = exc.read()
        except Exception:  # noqa: BLE001 — body unreadable, keep code
            raw = b""
    except Exception:  # noqa: BLE001 — curl reports any transport failure as 000
        return "000", ""
    return "%03d" % code, raw.decode("utf-8", "replace").rstrip("\n")


def print_json_or_raw(body):
    """`printf '%s\\n' "$body" | (jq . 2>/dev/null || cat)` — pretty JSON, else raw body."""
    if body.strip() == "":
        return
    decoder = json.JSONDecoder()
    docs, idx, text = [], 0, body.strip()
    try:
        while idx < len(text):
            doc, end = decoder.raw_decode(text, idx)
            docs.append(doc)
            idx = end
            while idx < len(text) and text[idx].isspace():
                idx += 1
    except ValueError:
        out(body + "\n")
        return
    for doc in docs:
        out(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


# Obtém um access_token OAuth2 (nunca loga o token; o chamador decide se imprime).
def rms_token(log=info):
    """Returns the access_token, or None after printing the error (bash `return 1`)."""
    client_id, client_secret = rms_resolve_credentials(log)
    cred = base64.b64encode(("%s:%s" % (client_id, client_secret)).encode("utf-8")).decode("ascii")
    _code, resp = http_request(
        "POST", RMS_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Authorization": "Basic %s" % cred},
        data="grant_type=client_credentials&scope=%s" % RMS_SCOPE, timeout=30)
    tok = ""
    try:
        doc = json.loads(resp)
        value = doc.get("access_token") if isinstance(doc, dict) else None
        if value not in (None, False):
            tok = value if isinstance(value, str) else json.dumps(value)
    except ValueError:
        tok = ""
    if not tok:
        err("Falha ao obter token. Resposta: %s" % resp)
        return None
    return tok


# Monta URL foundation. rms_url(<entity>, [id])
#   com id  -> by-id path-param: {base}/services/foundation/<ent>/<id>
#   sem id  -> delta/publish:   {base}/services/foundation/<ent>
def rms_url(ent, ident=""):
    if ent.startswith("foundation/"):  # aceita "item" ou "foundation/item"
        ent = ent[len("foundation/"):]
    if ident:
        return "%s/services/foundation/%s/%s" % (RMS_MERCH_BASE, ent, ident)
    return "%s/services/foundation/%s" % (RMS_MERCH_BASE, ent)

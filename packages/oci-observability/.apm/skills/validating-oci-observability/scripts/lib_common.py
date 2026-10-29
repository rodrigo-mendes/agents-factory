#!/usr/bin/env python3
# ==============================================================================
# lib_common.py — configuração e helpers compartilhados pelos scripts de
# validação de observabilidade (port Python do antigo lib-common.sh).
#
# Uso: os demais scripts fazem `import lib_common as L` (a partir do próprio
# diretório) e chamam `L.init()` — equivalente ao antigo `source lib-common.sh`.
# Todas as variáveis podem ser sobrescritas por ambiente antes de chamar.
# NÃO executar direto (é um módulo).
#
# Comandos externos sobrescrevíveis por env var (string com argv, ou lista JSON):
#   VOO_OCI_CMD (oci) · VOO_TERRAFORM_CMD (terraform) · VOO_GIT_CMD (git)
#   VOO_BASH_CMD (bash — só p/ scripts .sh do projeto alvo: preflight, build-push,
#   simulate-webhook) · VOO_SLEEP_SCALE (1 — multiplica todos os sleeps; testes usam 0)
# ==============================================================================
"""Shared config and helpers for the validating-oci-observability scripts."""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------------------
# Saída UTF-8 (paridade com o bash, que emitia bytes UTF-8) + line buffering
# ------------------------------------------------------------------------------
def setup_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except (AttributeError, ValueError):
            pass


setup_stdio()


# ------------------------------------------------------------------------------
# Comandos externos (sobrescrevíveis por env var)
# ------------------------------------------------------------------------------
def cmd_from_env(var, default):
    """argv list from env var VAR: JSON list ('["python","fake.py"]') or a shell-like string."""
    raw = os.environ.get(var, "").strip()
    if not raw:
        return [default]
    if raw.startswith("["):
        return [str(x) for x in json.loads(raw)]
    if os.name == "nt":
        return [t[1:-1] if len(t) > 1 and t[0] == t[-1] and t[0] in "\"'" else t
                for t in shlex.split(raw, posix=False)]
    return shlex.split(raw)


def resolve(cmd):
    if os.sep in cmd[0] or "/" in cmd[0]:
        return list(cmd)  # caminho explícito: não procurar no PATH (nem relativo ao cwd atual)
    exe = shutil.which(cmd[0])
    return ([exe] + list(cmd[1:])) if exe else list(cmd)


def have(cmd):
    """`command -v` equivalent for the first argv element."""
    return shutil.which(cmd[0]) is not None


def run(cmd, timeout=None, cwd=None, capture=True, quiet=True):
    """Runs cmd. Returns (rc, stdout_text). rc 127 if not found, 124 on timeout."""
    try:
        p = subprocess.run(
            resolve(cmd), cwd=cwd, timeout=timeout,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.DEVNULL if quiet else None,
        )
    except subprocess.TimeoutExpired:
        return 124, ""
    except FileNotFoundError:
        return 127, ""
    except (NotADirectoryError, PermissionError, OSError):
        return 126, ""
    out = p.stdout.decode("utf-8", "replace") if capture and p.stdout is not None else ""
    return p.returncode, out


def sh_script_cmd(path):
    """argv to execute a project-local shell script (./x.sh). On Windows via VOO_BASH_CMD."""
    if os.name == "nt":
        return BASH_CMD + [path]
    return [path]


def find_project_script(directory, base):
    """Project script `base` in `directory`: prefer `base.py` (current scaffolding template), else an
    executable `base.sh` (projects scaffolded before the Python port). Returns the path or None."""
    py = os.path.join(directory, base + ".py")
    if os.path.isfile(py):
        return py
    sh = os.path.join(directory, base + ".sh")
    if is_executable(sh):
        return sh
    return None


def project_script_cmd(path):
    """argv for a project script found by find_project_script: .py runs with this Python, .sh as before."""
    if path.endswith(".py"):
        return [sys.executable, path]
    return sh_script_cmd(path)


def is_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)


def sleep(secs):
    """`sleep N` (N inválido -> erro no stderr e segue, como o coreutils)."""
    try:
        s = float(secs)
    except (TypeError, ValueError):
        err_raw(f"sleep: invalid time interval '{secs}'")
        return
    scale = float(os.environ.get("VOO_SLEEP_SCALE", "1") or "1")
    if s * scale > 0:
        time.sleep(s * scale)


def unbound(prog, name="$2"):
    """Mimics bash `set -u` on a missing option value: message + exit 127."""
    err_raw(f"{prog}: {name}: unbound variable")
    sys.exit(127)


def print_help(path):
    """`grep '^#' "$0" | sed 's/^# \\{0,1\\}//' | sed '/^!/d'`."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line.startswith("#"):
                continue
            line = re.sub(r"^# ?", "", line)
            if line.startswith("!"):
                continue
            print(line)


OCI_CMD = cmd_from_env("VOO_OCI_CMD", "oci")
TERRAFORM_CMD = cmd_from_env("VOO_TERRAFORM_CMD", "terraform")
GIT_CMD = cmd_from_env("VOO_GIT_CMD", "git")
BASH_CMD = cmd_from_env("VOO_BASH_CMD", "bash")


# ------------------------------------------------------------------------------
# HTTP (substitui `curl -s -o /dev/null -w '%{http_code}'`): sem seguir redirect,
# "000" em erro de conexão/timeout — mesma convenção do curl.
# ------------------------------------------------------------------------------
class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def http_code(url, method="GET", data=None, timeout=None):
    body = None
    headers = {}
    if data is not None:
        body = data.encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with _OPENER.open(req, timeout=timeout) as resp:
            resp.read()
            return f"{resp.status:03d}"
    except urllib.error.HTTPError as e:
        return f"{e.code:03d}"
    except Exception:  # noqa: BLE001 — curl reporta 000 p/ qualquer falha de transporte
        return "000"


# ------------------------------------------------------------------------------
# Cores / logging
# ------------------------------------------------------------------------------
if sys.stdout.isatty():
    C_RED, C_GRN, C_YLW = "\033[0;31m", "\033[0;32m", "\033[0;33m"
    C_BLU, C_BLD, C_RST = "\033[0;34m", "\033[1m", "\033[0m"
else:
    C_RED = C_GRN = C_YLW = C_BLU = C_BLD = C_RST = ""


def log(msg):
    print(msg)


def info(msg):
    print(f"{C_BLU}[i]{C_RST} {msg}")


def warn(msg):
    sys.stdout.flush()
    print(f"{C_YLW}[!]{C_RST} {msg}", file=sys.stderr)


def err(msg):
    sys.stdout.flush()
    print(f"{C_RED}[x]{C_RST} {msg}", file=sys.stderr)


def err_raw(msg):
    sys.stdout.flush()
    print(msg, file=sys.stderr)


def hdr(msg):
    print(f"\n{C_BLD}== {msg} =={C_RST}")


# Contadores globais de asserção (usados pelos scripts individuais).
PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0


def pass_(msg):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"{C_GRN}  PASS{C_RST} {msg}")


def fail(msg):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"{C_RED}  FAIL{C_RST} {msg}")


def skip(msg):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"{C_YLW}  WARN{C_RST} {msg}")


def summary():
    """Resumo final; retorna 1 se houve qualquer FAIL (0 caso contrário)."""
    print(f"\n{C_BLD}---------------------------------------------{C_RST}")
    print(f"{C_BLD}RESULTADO:{C_RST} {C_GRN}PASS={PASS_COUNT}{C_RST}  "
          f"{C_RED}FAIL={FAIL_COUNT}{C_RST}  {C_YLW}WARN={WARN_COUNT}{C_RST}")
    return 0 if FAIL_COUNT == 0 else 1


# ------------------------------------------------------------------------------
# Mini-jq: helpers que reproduzem a semântica dos filtros jq usados antes
# ------------------------------------------------------------------------------
class JqError(Exception):
    pass


NOINPUT = object()


def jload(text):
    """Parsed JSON; NOINPUT for empty input (jq prints nothing, exit 0); ValueError if invalid."""
    if not text.strip():
        return NOINPUT
    return json.loads(text)


def jget(v, key):
    """`.key` — null-safe; error on non-object."""
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get(key)
    raise JqError(key)


def jiter(v):
    """`.[]?` — arrays/objects iterate; anything else yields nothing."""
    if isinstance(v, list):
        return list(v)
    if isinstance(v, dict):
        return list(v.values())
    return []


def jtruthy(v):
    return not (v is None or v is False)


def jlen(v):
    if v is None:
        return 0
    if isinstance(v, bool):
        raise JqError("length")
    if isinstance(v, (int, float)):
        return abs(v)
    return len(v)


def jnum(x):
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e17:
        return str(int(x))
    return repr(x) if isinstance(x, float) else str(x)


def compact(v):
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


def jtext(v):
    """Raw output / string interpolation of a jq value."""
    if isinstance(v, str):
        return v
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return jnum(v)
    return compact(v)


def tsv(fields):
    """jq `@tsv`."""
    out = []
    for f in fields:
        if f is None:
            out.append("")
        elif isinstance(f, str):
            out.append(f.replace("\\", "\\\\").replace("\t", "\\t")
                       .replace("\n", "\\n").replace("\r", "\\r"))
        else:
            out.append(jtext(f))
    return "\t".join(out)


def count_datapoints(text):
    """`[.data[]?."aggregated-datapoints"[]?] | length` -> int, '' (no input) or raises."""
    v = jload(text)
    if v is NOINPUT:
        return ""
    return sum(len(jiter(jget(e, "aggregated-datapoints"))) for e in jiter(jget(v, "data")))


def to_int(s):
    """`${x:-0}` used in an arithmetic test."""
    try:
        return int(s) if s != "" else 0
    except (TypeError, ValueError):
        return 0


# ------------------------------------------------------------------------------
# Tempo (ISO-8601 UTC)
# ------------------------------------------------------------------------------
def iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_minus_min(m):
    try:
        mins = int(m)
    except (TypeError, ValueError):
        return ""
    return (datetime.now(timezone.utc) - timedelta(minutes=mins)).strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------------------
# Wrappers OCI CLI
# ------------------------------------------------------------------------------
OCI_PROFILE = os.environ.get("OCI_PROFILE") or "poc"
OCI_AUTH = os.environ.get("OCI_AUTH") or "security_token"
OCI_REGION = os.environ.get("OCI_REGION") or "sa-saopaulo-1"
LOOKBACK_MIN = os.environ.get("LOOKBACK_MIN") or "15"


def oci_cli(*args):
    """oci --profile --auth --region <args> 2>/dev/null -> (rc, stdout)."""
    return run(OCI_CMD + ["--profile", OCI_PROFILE, "--auth", OCI_AUTH,
                          "--region", OCI_REGION] + list(args))


def require_tools():
    """Verifica pré-requisito (oci CLI). Sai 1 se faltar. (jq não é mais necessário.)"""
    if not have(OCI_CMD):
        err("Ferramenta ausente: oci")
        sys.exit(1)


def _session_local_ok():
    rc, _ = run(OCI_CMD + ["session", "validate", "--profile", OCI_PROFILE,
                           "--auth", OCI_AUTH, "--local"])
    return rc == 0


def require_session():
    if not _session_local_ok():
        err(f"Sessão OCI '{OCI_PROFILE}' inválida/expirada.")
        err(f"Renove com: oci session authenticate --profile {OCI_PROFILE} --region {OCI_REGION}")
        sys.exit(2)


# ------------------------------------------------------------------------------
# require_fresh_session — gate ROBUSTO para varreduras longas.
#
# A sessão SecurityToken do perfil `poc` expira em ~1h (`--local` só checa o
# relógio). Este gate: 1) tenta `oci session refresh` (best-effort, teto 20s);
# 2) PROVA a sessão com uma chamada autenticada real (teto 20s; 124 = travou).
# Falha rápido com exit 2 ANTES de gastar minutos na varredura.
# ------------------------------------------------------------------------------
def require_fresh_session():
    if not _session_local_ok():
        err(f"Sessão OCI '{OCI_PROFILE}' expirada (validação local falhou).")
        err("Reautentique (login interativo no browser): oci session authenticate "
            f"--profile {OCI_PROFILE} --region {OCI_REGION}")
        sys.exit(2)

    # NB: `oci session refresh` sai 0 mesmo quando NÃO renova — só best-effort.
    rc, _ = run(OCI_CMD + ["session", "refresh", "--profile", OCI_PROFILE], timeout=20)
    if rc == 0:
        info(f"Sessão '{OCI_PROFILE}': tentativa de refresh concluída (validação real abaixo é quem decide).")

    probe_rc, _ = run(OCI_CMD + ["--profile", OCI_PROFILE, "--auth", OCI_AUTH, "--region", OCI_REGION,
                                 "--connection-timeout", "5", "--read-timeout", "10",
                                 "iam", "region", "list"], timeout=20)
    if probe_rc != 0:
        if probe_rc == 124:
            err(f"Sessão OCI '{OCI_PROFILE}': chamada autenticada TRAVOU (timeout) — token provavelmente "
                "expirado (o CLI fica em retry contra o endpoint de auth).")
        else:
            err(f"Sessão OCI '{OCI_PROFILE}' NÃO aceita pelo servidor (rc={probe_rc}) apesar do relógio local OK.")
        err("O token SecurityToken provavelmente expirou (TTL ~1h). Reautentique ANTES da varredura:")
        err(f"  oci session authenticate --profile {OCI_PROFILE} --region {OCI_REGION}")
        err("(login interativo no browser — não pode ser feito headless)")
        sys.exit(2)
    info(f"Sessão '{OCI_PROFILE}' validada ao vivo (chamada autenticada OK).")


# ------------------------------------------------------------------------------
# Terraform outputs (lidos UMA vez por processo — equivalente ao tf_prime)
# ------------------------------------------------------------------------------
_TF = None


def _tf_load():
    global _TF
    if _TF is None:
        rc, out = run(TERRAFORM_CMD + ["output", "-json"], cwd=TF_DIR) if os.path.isdir(TF_DIR) else (1, "")
        if rc != 0:
            out = "{}"
        try:
            _TF = jload(out)
        except ValueError:
            _TF = NOINPUT
    return _TF


def tf_out(name, fallback=""):
    """`.[$k].value // empty` (jq -r); vazio/"null" -> fallback."""
    data = _tf_load()
    try:
        v = jget(jget(data, name), "value") if isinstance(data, dict) else None
    except JqError:
        v = None
    if not jtruthy(v):
        return fallback
    if isinstance(v, (dict, list)):
        s = json.dumps(v, indent=2, ensure_ascii=False)
    else:
        s = jtext(v)
    return fallback if s in ("", "null") else s


# ------------------------------------------------------------------------------
# FUNCTIONS_META — "label|app_ocid|custom_namespace|prefixo_metrica|function_ocid"
#
# Spec: label | tf_output_base | custom_namespace | prefixo_metrica | fallback_app | fallback_fn
# tf_output_base resolve "<base>_application_id" e "<base>_function_id"; preferimos
# SEMPRE o valor vivo do `terraform output`; os OCIDs hardcoded são só fallback.
# Os 3 apps pub/sub (Pattern 02) compartilham o namespace `event_pubsub_analytics`.
# Fallbacks confirmados ao vivo (oci fn ... list, 2026-07-22, região sa-saopaulo-1).
# ------------------------------------------------------------------------------
_FUNCTIONS_META_SPEC = [
    "api-handler|api_handler|api_handler_analytics|ApiHandler|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyadf7booxbvvg6ernldcdbwrxahtw7w2jer3sfhp7ujjyq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyawaxod6lh5w37le6yfyinnsibpwpq6grvprgua2amij5q",
    "func-api-facade|api_facade|serverless_facade|ApiFacade|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyaetxnny6q7rr3trylculrbucuim3mti7tsa4i2zkzuoyq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaqlmzdfkvbe7rwtys7zsukahfmhu6t5ikqqm3mfkq6zdq",
    "func-rr-rest-proxy|rest_proxy|rest_proxy_analytics|RestProxy|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyased4pvcjmegljcx4uw47bypu53bbwkfsb2bajtoxv75a|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaizt447zllj2362ztaibza5dcsxw2cfcj3ocoeazuty4a",
    # --- Event-Driven Pub/Sub (Pattern 02) ---
    "func-event-producer|event_producer|event_pubsub_analytics|EventProduced|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyaocnsg26tu2cwf4mqdmhcn7guqtofqisgkyrpop2hxdkq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyasqb6jm3f5hadyrhlc6y4zqrldu3gm5restrrdip4u3va",
    "func-evt-consumer-notify|evt_consumer_notify|event_pubsub_analytics|NotifyEventProcessed|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyao6cktchg6zm4z3vtqytqkqvps2jlx7tqzfahc3jolmfq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaqxui43bkqdhs6gcctenbjs54ozsbnhy2oyal5dshw44a",
    "func-evt-consumer-audit|evt_consumer_audit|event_pubsub_analytics|AuditEventProcessed|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nya4afwc7uhswdby5cwm4zzv3xzot5nvoyomj4t4lcmieha|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nya4gsk4nyx7a23dqfeszxcljr7hgf2jyxlkgjx2r5vtnbq",
]

REPO_ROOT = ""
TF_DIR = ""
COMPARTMENT_OCID = ""
API_BASE_URL = ""
LOG_GROUP_ID = ""
APM_DOMAIN_ID = ""
NOTIFICATION_TOPIC_ID = ""
FUNCTIONS_META = []  # list of (label, app_ocid, namespace, prefix, function_ocid)


def init():
    """Equivalente ao `source lib-common.sh`: resolve repo/TF_DIR, lê outputs, monta FUNCTIONS_META."""
    global REPO_ROOT, TF_DIR, COMPARTMENT_OCID, API_BASE_URL, LOG_GROUP_ID
    global APM_DOMAIN_ID, NOTIFICATION_TOPIC_ID, FUNCTIONS_META
    # Repo root via git (qualquer localização); fallback: layout legado (2 níveis sob o root).
    rc, out = run(GIT_CMD + ["-C", SCRIPT_DIR, "rev-parse", "--show-toplevel"])
    top = out.rstrip("\r\n") if rc == 0 else ""
    REPO_ROOT = top or os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
    TF_DIR = os.environ.get("TF_DIR") or os.path.join(REPO_ROOT, "infra", "environments", "dev")

    COMPARTMENT_OCID = tf_out("compartment_ocid", "ocid1.compartment.oc1..aaaaaaaat3d6o3oron7jqrztl572jjrsdobf6bimutf57jirbzetc4magzja")
    API_BASE_URL = tf_out("api_base_url", "https://lopiafgboojvw37sqyoxptl7t4.apigateway.sa-saopaulo-1.oci.customer-oci.com/v1")
    LOG_GROUP_ID = tf_out("log_group_id", "")
    APM_DOMAIN_ID = tf_out("apm_domain_id", "")
    NOTIFICATION_TOPIC_ID = tf_out("notification_topic_id", "")

    FUNCTIONS_META = []
    for spec in _FUNCTIONS_META_SPEC:
        label, base, ns, pref, fb_app, fb_fn = spec.split("|")
        FUNCTIONS_META.append((label, tf_out(f"{base}_application_id", fb_app), ns, pref,
                               tf_out(f"{base}_function_id", fb_fn)))


if __name__ == "__main__":
    # Módulo compartilhado — executar direto não faz nada (como o antigo lib-common.sh).
    sys.exit(0)

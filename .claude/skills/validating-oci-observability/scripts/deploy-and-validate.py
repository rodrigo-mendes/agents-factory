#!/usr/bin/env python3
# ==============================================================================
# deploy-and-validate.py — RUNBOOK ponta-a-ponta para corrigir e validar a
# observabilidade em dev. Executa, em ordem:
#   1) pré-checagens (sessão OCI)
#   2) build + push das 3 imagens (tags do func.yaml) via scripts do projeto
#      (scripts/preflight.sh + services/<svc>/build-push.py, or build-push.sh in older projects)
#   3) terraform plan -out=tfplan e, SÓ com "yes" digitado no prompt,
#      terraform apply tfplan (popula config das functions, imagens, subscription)
#   4) validação dos pilares (validate-observability.py)
#
# Requisitos:
#   - Docker rodando (usado pelo build-push.sh do projeto)
#   - Sessão OCI ativa:  oci session authenticate --profile poc --region sa-saopaulo-1
#   - services/.env com credenciais OCIR
#
# Uso:
#   ./deploy-and-validate.py                # executa tudo (pede confirmação no apply)
#   ./deploy-and-validate.py --skip-build   # só plan + apply + validação
#   ./deploy-and-validate.py --plan-only    # para no terraform plan
# ==============================================================================
import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402

OCIR_HOST = "gru.ocir.io"
OCIR_NS = ""  # set in main() from $OCIR_NAMESPACE (`oci os ns get`); never hardcode a tenancy namespace
OCIR_REPO = "serverless-app"

# label|dir|tfvar_name
BUILDS = [
    "api-handler|api-handler|api_handler_image",
    "func-api-facade|func-api-facade|api_facade_image",
    "func-rr-rest-proxy|func-rr-rest-proxy|rest_proxy_image",
]


def _func_yaml_tag(svc):
    """grep '^version:' func.yaml | awk '{print $2}'"""
    path = os.path.join(svc, "func.yaml")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            tags = []
            for line in fh:
                if line.startswith("version:"):
                    f = line.split()
                    tags.append(f[1] if len(f) > 1 else "")
            return "\n".join(tags)
    except OSError:
        L.err_raw(f"grep: {path}: No such file or directory")
        return ""


def _call(cmd, cwd=None):
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        return subprocess.call(L.resolve(cmd), cwd=cwd)
    except FileNotFoundError:
        L.err_raw(f"{cmd[0]}: command not found")
        return 127
    except OSError as e:
        L.err_raw(f"{cmd[0]}: {e}")
        return 126


def main(argv):
    global OCIR_NS
    # required, no defaults: the alarm address and the tenancy namespace belong to whoever runs this
    alarm_email = os.environ.get("ALARM_EMAIL", "").strip()
    OCIR_NS = os.environ.get("OCIR_NAMESPACE", "").strip()
    missing = [n for n, v in (("ALARM_EMAIL", alarm_email), ("OCIR_NAMESPACE", OCIR_NS)) if not v]
    if missing:
        L.err_raw("Defina " + " e ".join(missing) + " antes de rodar (ALARM_EMAIL = endereço que recebe o "
                  "alarme de teste; OCIR_NAMESPACE = saída de `oci os ns get`).")
        return 2
    L.init()

    skip_build = "--skip-build" in argv
    plan_only = "--plan-only" in argv

    L.require_tools()
    L.require_session()

    services_dir = os.path.join(L.REPO_ROOT, "services")

    # --------------------------------------------------------------------------
    # 1) Build + push
    # --------------------------------------------------------------------------
    tf_image_vars = []
    for b in BUILDS:
        label, d, tfvar = b.split("|")
        svc = os.path.join(services_dir, d)
        tag = _func_yaml_tag(svc)
        image = f"{OCIR_HOST}/{OCIR_NS}/{OCIR_REPO}/{label}:{tag}"
        tf_image_vars += ["-var", f"{tfvar}={image}"]

        if not skip_build:
            L.hdr(f"BUILD+PUSH {label} -> {image}")
            preflight = os.path.join(L.REPO_ROOT, "scripts", "preflight.sh")
            if not os.path.isdir(svc) or _call(L.BASH_CMD + [preflight, svc], cwd=svc) != 0:
                L.err(f"preflight falhou em {label}")
                return 1
            build_push = L.find_project_script(svc, "build-push")
            if build_push:
                if _call(L.project_script_cmd(build_push) + [tag], cwd=svc) != 0:
                    L.err(f"build-push falhou em {label}")
                    return 1
                L.pass_(f"{label} publicado: {image}")
            else:
                L.err(f"{svc}/build-push.py (ou build-push.sh executável) não encontrado.")
                return 1
        else:
            L.info(f"SKIP build de {label}; usarei imagem {image}")

    # --------------------------------------------------------------------------
    # 2) terraform plan/apply
    # --------------------------------------------------------------------------
    L.hdr("TERRAFORM PLAN (dev)")
    tf_cwd = L.TF_DIR
    if not os.path.isdir(tf_cwd):
        # bash: `cd "$TF_DIR"` falhava sem abortar e seguia no diretório atual
        L.err_raw(f"cd: {tf_cwd}: No such file or directory")
        tf_cwd = None
    if _call(L.TERRAFORM_CMD + ["plan", "-out=tfplan"] + tf_image_vars
             + ["-var", f"alarm_notification_email={alarm_email}"], cwd=tf_cwd) != 0:
        L.err("terraform plan falhou")
        return 1

    if plan_only:
        L.info("--plan-only: parando após o plan. Revise 'tfplan' e rode 'terraform apply tfplan'.")
        return 0

    # Safety (2026-10-29): the apply "yes" must be typed by a person at a terminal; piped input
    # (e.g. `echo yes | ...` from an agent) cancels, unless the offline test harness opts in.
    if not (sys.stdin is not None and sys.stdin.isatty()) and os.environ.get("VOO_ALLOW_PIPE") != "1":
        L.warn("Apply cancelado: o 'yes' precisa ser digitado num terminal interativo (stdin não é TTY).")
        return 0
    sys.stdout.write(f"\n{L.C_BLD}Revise o plan acima. Aplicar? (yes/no): {L.C_RST}")
    sys.stdout.flush()
    answer = sys.stdin.readline()
    if answer.strip(" \t\n") != "yes":
        L.warn("Apply cancelado pelo usuário.")
        return 0

    L.hdr("TERRAFORM APPLY (dev)")
    if _call(L.TERRAFORM_CMD + ["apply", "tfplan"], cwd=tf_cwd) != 0:
        L.err("terraform apply falhou")
        return 1
    L.pass_("Infra aplicada: config das functions populado, imagens atualizadas, subscription criada.")
    L.warn(f"CONFIRME o email de subscription enviado pela OCI para {alarm_email} "
           "(senão os alarmes não notificam).")

    # --------------------------------------------------------------------------
    # 3) Validação
    # --------------------------------------------------------------------------
    L.hdr("VALIDAÇÃO DE OBSERVABILIDADE")
    L.info("Aguardando 60s para propagação das novas versões das functions...")
    L.sleep(60)
    return _call([sys.executable, os.path.join(L.SCRIPT_DIR, "validate-observability.py"), "--wait", "150"],
                 cwd=tf_cwd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# Onboarding — DevOps / Infra

Trilha para quem vai **provisionar a infraestrutura (Terraform), fazer deploy e operar** o ambiente.
Antes, faça a parte comum em **[README.md](README.md)** (pré-requisitos + autenticação OCI).

> Composição dos módulos: **[../../infra/README.md](../../infra/README.md)**.
> Setup detalhado: **[../../infra/SETUP.md](../../infra/SETUP.md)** e **[../../GETTING-STARTED.md](../../GETTING-STARTED.md)**.

---

## 1. Pré-requisitos específicos

- **Terraform 1.11+** — `brew install terraform`
- **OCI CLI** + sessão `poc` ativa (ver [README §4](README.md#4-autenticação-oci-compartilhada))
- **jq** — `brew install jq` (usado pelo script de cleanup)
- **Docker** 24+ (se você também for buildar/pushar imagens)

---

## 2. Autenticação e provider

O provider já está fixado em [`infra/environments/dev/versions.tf`](../../infra/environments/dev/versions.tf):

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    oci = {
      source  = "oracle/oci"      # NUNCA hashicorp/oci
      version = ">= 6.0, < 9.0"   # testado com 8.x
    }
  }
}

provider "oci" {
  auth                = "SecurityToken"   # usa ~/.oci/sessions/poc/
  config_file_profile = "poc"
  region              = var.region
}
```

Garanta a sessão antes de qualquer operação (renova em ~1h):

```bash
oci session authenticate --profile poc --region sa-saopaulo-1
oci session validate --profile poc --auth security_token
```

---

## 3. Variáveis do ambiente

As variáveis obrigatórias (compartment, região, imagens OCIR) ficam em
`infra/environments/dev/variables.tf`. O `terraform.tfvars` **não é versionado** (gitignored) e no ambiente
POC é **permission-blocked** — passe valores via `-var-file` (se tiver um tfvars local) ou `-var`:

```hcl
tenancy_ocid     = "ocid1.tenancy.oc1..aaa..."
compartment_ocid = "ocid1.compartment.oc1..aaa..."
compartment_name = "mom-fast-track-poc-oci-serverless"
region           = "sa-saopaulo-1"

# Imagens (uma por função) — repo real: mon-fast-track-oci-serverless
api_handler_image = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/api-handler:0.0.5"
api_facade_image  = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/func-api-facade:0.0.2"
rest_proxy_image  = "gru.ocir.io/<namespace>/mon-fast-track-oci-serverless/func-rr-rest-proxy:0.0.14"
```

Opcionais úteis (defaults): `enable_logging`, `enable_monitoring_alarms`, `alarm_duration_threshold_ms`,
`jwt_auth_enabled`, `use_nsg`, `function_shape`, `trace_enabled`. Detalhes:
[GETTING-STARTED §5.2](../../GETTING-STARTED.md#52-variáveis-opcionais).

---

## 4. Fluxo Terraform (dev)

```bash
cd infra/environments/dev

terraform init                                  # baixa provider + módulos
terraform validate                              # valida configuração
terraform plan  -var-file="terraform.tfvars"    # preview (não altera nada)
terraform apply -var-file="terraform.tfvars"    # cria/atualiza a infra
```

Os módulos são compostos em `main.tf` (plataforma) e `apps.tf` (3 function-apps + API Gateway):

| Módulo | Recursos |
|--------|----------|
| `network` | VCN, subnets pública/privada, IGW/NAT/Service GW, route tables, security lists, NSGs |
| `iam` | Dynamic Groups + Policies (Resource Principal) |
| `function-app` (×3) | 1 Application + 1 Function por instância |
| `api-gateway` | Gateway + Deployment (JWT, CORS, rate limit, rotas via `route_backends`) |
| `vault` | Vault KMS, Master Key, Object Storage bucket |
| `observability` | Log Group, Service Logs, Notification Topic, Alarms |
| `apm` | APM Domain (free tier), Data Keys |
| `dashboards` | Management Dashboards custom |

Mapa completo com inputs/outputs: **[../../infra/README.md](../../infra/README.md)**.

### 4.1 Passo manual pós-apply — ativar Application Logs

O provider OCI **não** configura o log de stdout das Applications via HCL. É um passo **único por
Application**, no Console. Procedimento completo (com Log Group, nomes e retenção):
**[GETTING-STARTED §6 → "Ativar Application Logs"](../../GETTING-STARTED.md#ativar-application-logs--passo-manual-obrigatório)**.

---

## 5. Verificar o deploy

```bash
cd infra/environments/dev
curl $(terraform output -raw health_check_url)          # {"status":"healthy",...}
curl $(terraform output -raw api_base_url)/hello
terraform output                                        # todos os endpoints/OCIDs
```

Outputs úteis: `api_base_url`, `health_check_url`, `api_handler_url_hello`, `api_facade_url_secret`,
`rest_proxy_url_store_create`, `log_group_id`, `notification_topic_id`.

---

## 6. Pipeline de deploy ponta-a-ponta

`preflight → build → push (OCIR) → atualizar *_image no tfvars → terraform apply → smoke test`.

**Recomendado (Claude Code):** `@oci-deployer /deploy-function` automatiza P0–P6 (build → push → deploy →
validação) — ver [`.claude/agents/oci-deployer.md`](../../.claude/agents/oci-deployer.md).

**Manual:**

```bash
# 1) build & push (dentro da service)
cd services/api-handler && ./build-push.sh 0.0.6

# 2) atualizar a tag da imagem em terraform.tfvars e aplicar
cd ../../infra/environments/dev
terraform apply -var-file="terraform.tfvars"

# 3) smoke test
curl $(terraform output -raw api_base_url)/hello
```

---

## 7. Observabilidade

- Validação ao vivo (5 pilares: logs, métricas, traces, alarmes, dashboards): skill
  `validating-oci-observability` — scripts em `.claude/skills/validating-oci-observability/scripts/`
  (entrada `validate-observability.sh`).
- Popular dashboards com tráfego real antes de validar:
  [`scripts/generate-dashboard-traffic.sh`](../../scripts/generate-dashboard-traffic.sh).
- Design/provisionamento de observabilidade: agent `@oci-observability`.

---

## 8. Testes de infraestrutura

```bash
cd infra
bash tests/run_structural_tests.sh
bash tests/run_tests.sh
```

Casos nativos Terraform (`.tftest.hcl`) em [`infra/tests/`](../../infra/tests/) — variáveis de
api-gateway, apm, functions, networking, etc.

---

## 9. Teardown

```bash
cd infra/environments/dev
terraform destroy -var-file="terraform.tfvars"
```

Se o `destroy` falhar parcialmente (state desatualizado, órfãos), use o fallback via OCI CLI
(requer `jq` e sessão `poc` válida):

```bash
./scripts/oci-cleanup.sh --dry-run     # lista o que existe, sem deletar
./scripts/oci-cleanup.sh               # remove respeitando dependências
```

> ⏱️ Se a sessão expirar no meio, re-autentique: `oci session authenticate --profile poc`.

---

## 10. Notas de estado (state)

- **Atual (dev):** state **local** por ambiente (`infra/environments/{dev,prod}/`). Não compartilhado —
  cuidado com edições concorrentes.
- **Produção/equipe:** migrar para backend remoto (OCI Object Storage, S3-compatível). O OCI Object
  Storage **não** oferece locking nativo — serialize o CI/CD (`max-parallel: 1`) ou use branch protection.
  Guia: skill `managing-terraform-state` e `.claude/rules/terraform-state-backend.md`.

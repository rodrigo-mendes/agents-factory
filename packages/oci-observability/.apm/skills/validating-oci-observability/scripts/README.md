# Scripts de Validação de Observabilidade (dev)

Valida os pilares de observabilidade dos serviços serverless OCI ao vivo:
**logs** (OCI Logging), **métricas** (OCI Monitoring — plataforma + custom),
**traces** (OCI APM), **alarmes/notificações** (Monitoring + ONS) e
**dashboards** (render-readiness).

Scripts em Python 3 (só biblioteca padrão; Windows e Linux). Chamam a OCI CLI
real via subprocess; o parsing JSON é feito em Python (não precisa de `jq`).

## Pré-requisitos

- Python 3.8+.
- OCI CLI autenticado no perfil `poc` (security token):
  ```bash
  oci session authenticate --profile poc --region sa-saopaulo-1
  ```
- `git` (localiza o repo) e `terraform` (lê `terraform output -json` em `infra/environments/dev`);
  se os outputs estiverem indisponíveis, caem em OCIDs de fallback do state atual.

## Variáveis de ambiente (opcionais)

| Var | Default | Descrição |
|-----|---------|-----------|
| `OCI_PROFILE` | `poc` | Perfil OCI CLI |
| `OCI_AUTH` | `security_token` | Método de auth |
| `OCI_REGION` | `sa-saopaulo-1` | Região |
| `TF_DIR` | `infra/environments/dev` | Diretório do ambiente Terraform |
| `LOOKBACK_MIN` | `15` | Janela (min) das queries |
| `VOO_OCI_CMD` | `oci` | Comando da OCI CLI (string ou lista JSON, ex. `["python","fake_oci.py"]`) |
| `VOO_TERRAFORM_CMD` / `VOO_GIT_CMD` | `terraform` / `git` | Idem para terraform / git |
| `VOO_BASH_CMD` | `bash` | Executa os `.sh` do projeto alvo (`scripts/preflight.sh`; `build-push`/`simulate-webhook` só quando o projeto ainda tem a versão `.sh` — a `.py` roda com o próprio Python; `simulate-webhook.sh`) no Windows |
| `VOO_SLEEP_SCALE` | `1` | Multiplica todos os sleeps (os testes usam `0`) |

## Scripts

| Script | Função |
|--------|--------|
| `lib_common.py` | Config + helpers compartilhados (módulo importado; não executar direto) |
| `smoke-invoke.py [N]` | Invoca rotas públicas p/ gerar tráfego (N repetições, default 3) |
| `check-logs.py` | Verifica entradas nos service logs + campos estruturados |
| `check-metrics.py` | Métricas `oci_faas` + custom; diagnostica dimensão (`applicationId` vs `resourceId`) dos alarmes |
| `check-traces.py` | Ingestão no APM (`IngestedBytes`/`PayloadRejections`) + pré-req APM_* no config |
| `check-alarms.py` | Alarmes habilitados + status + subscription ONS confirmada |
| `check-dashboards.py [--name-filter X]` | 5º pilar — dashboards ACTIVE + render-readiness (widget-template, dataSource-type, `regionName` nos metric) + ingestão |
| `trigger-alarm-test.py --i-have-user-approval [N] [MIN]` | Injeta erros e faz polling até alarme FIRING (sem a flag: exit 2, nada enviado) |
| `generate-dashboard-traffic.py [--rounds N] [--sleep S] [--url U]` | Gera carga para popular os dashboards |
| `deploy-and-validate.py [--skip-build] [--plan-only]` | Build + push + plan + apply (só após `yes` no prompt) + validação |
| `validate-observability.py [--no-smoke] [--wait S]` | Orquestra tudo e imprime tabela PASS/FAIL |

Exit codes: `0` OK · `1` algum FAIL (ou ferramenta ausente) · `2` sessão OCI inválida / argumento
desconhecido · `127` opção sem valor. `validate-observability.py` sai com o nº de pilares em FAIL.

## Uso típico

```bash
# validação completa (gera tráfego, espera ingestão, valida os pilares)
python validate-observability.py

# só validar (sem gerar tráfego novo)
python validate-observability.py --no-smoke

# testar caminho alarme -> notificação (injeta erros em dev)
python trigger-alarm-test.py --i-have-user-approval   # só com aprovação explícita do usuário
```

## Testes

`python tests/run_tests.py` — OCI CLI falsa (`tests/fakes/fake_oci.py` + `tests/fixtures/`),
git/terraform/bash falsos e um servidor HTTP em `127.0.0.1`. Não chama a OCI nem a rede.

## Interpretando falhas

- **metrics/traces FAIL com "config vazio"** → as Functions estão rodando com
  `config = {}` (sem `APM_*`/`COMPARTMENT_OCID`). Rode `terraform apply` em
  `infra/environments/dev` e reexecute. Ver Problema #1 do plano.
- **check-metrics: "resourceId=FUNCTION"** → os alarmes filtram por OCID de
  Application mas a métrica só casa por OCID de Function → alarmes não disparam.
  Corrigir a `query` dos alarmes no módulo `observability`.
- **alarms: sem subscription / PENDING** → aplicar a subscription (já no módulo)
  e confirmar o link enviado por email pela OCI.

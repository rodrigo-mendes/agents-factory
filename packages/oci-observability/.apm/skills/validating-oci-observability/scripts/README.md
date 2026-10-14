# Scripts de Validação de Observabilidade (dev)

Valida os 4 pilares de observabilidade dos serviços serverless OCI ao vivo:
**logs** (OCI Logging), **métricas** (OCI Monitoring — plataforma + custom),
**traces** (OCI APM) e **alarmes/notificações** (Monitoring + ONS).

## Pré-requisitos

- OCI CLI autenticado no perfil `poc` (security token):
  ```bash
  oci session authenticate --profile poc --region sa-saopaulo-1
  ```
- `jq` instalado.
- Rodar de um diretório com acesso aos outputs do Terraform (`infra/environments/dev`).
  Os scripts leem `terraform output -json`; se indisponível, caem em OCIDs de fallback do state atual.

## Variáveis de ambiente (opcionais)

| Var | Default | Descrição |
|-----|---------|-----------|
| `OCI_PROFILE` | `poc` | Perfil OCI CLI |
| `OCI_AUTH` | `security_token` | Método de auth |
| `OCI_REGION` | `sa-saopaulo-1` | Região |
| `TF_DIR` | `infra/environments/dev` | Diretório do ambiente Terraform |
| `LOOKBACK_MIN` | `15` | Janela (min) das queries |

## Scripts

| Script | Função |
|--------|--------|
| `lib-common.sh` | Config + helpers compartilhados (não executar direto) |
| `smoke-invoke.sh [N]` | Invoca rotas públicas p/ gerar tráfego (N repetições, default 3) |
| `check-logs.sh` | Verifica entradas nos service logs + campos estruturados |
| `check-metrics.sh` | Métricas `oci_faas` + custom; diagnostica filtro `resourceId` dos alarmes |
| `check-traces.sh` | Traces no APM (best-effort) + valida pré-req APM_* no config |
| `check-alarms.sh` | Alarmes habilitados + status + subscription ONS confirmada |
| `check-dashboards.sh [--name-filter X]` | 5º pilar — dashboards ACTIVE + render-readiness (widget-template, dataSource-type, `regionName` nos metric) + ingestão |
| `trigger-alarm-test.sh [N] [MIN]` | Injeta erros e faz polling até alarme FIRING |
| `validate-observability.sh` | Orquestra tudo e imprime tabela PASS/FAIL |

## Uso típico

```bash
# validação completa (gera tráfego, espera ingestão, valida 4 pilares)
./validate-observability.sh

# só validar (sem gerar tráfego novo)
./validate-observability.sh --no-smoke

# testar caminho alarme -> notificação (injeta erros em dev)
./trigger-alarm-test.sh
```

## Interpretando falhas

- **metrics/traces FAIL com "config vazio"** → as Functions estão rodando com
  `config = {}` (sem `APM_*`/`COMPARTMENT_OCID`). Rode `terraform apply` em
  `infra/environments/dev` e reexecute. Ver Problema #1 do plano.
- **check-metrics: "resourceId=FUNCTION"** → os alarmes filtram por OCID de
  Application mas a métrica só casa por OCID de Function → alarmes não disparam.
  Corrigir a `query` dos alarmes no módulo `observability`.
- **alarms: sem subscription / PENDING** → aplicar a subscription (já no módulo)
  e confirmar o link enviado por email pela OCI.

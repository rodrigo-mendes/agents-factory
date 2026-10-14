# Post-Mortem: Custom Dashboards — Live Test & Schema Discovery — func-rr-rest-proxy

**Data:** 2026-07-07
**Sessão:** Criação + apply ao vivo de 3 Management Dashboards (Operations Overview, Upstream Dependencies, Route Analytics)
**Status:** ✅ RESOLVED — 3 dashboards importados no OCI dev, métricas fluindo
**Tempo Total:** ~1 sessão (4 falhas de apply iterativas)
**Tempo Ideal (estimado):** ~15 minutos (1 apply)
**Fator de Ineficiência:** ~4x (todas as falhas eram conhecimento de schema ausente na skill)

---

## 1. Problemas Encontrados

Os problemas P1–P4 só apareceram no `terraform apply` — nenhum foi pego por `terraform plan`/`validate`, porque `oci_management_dashboard_management_dashboards_import` valida o JSON **apenas server-side no apply**.

### P1. Envelope de import sem `tiles`

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | `apply` HTTP 400: `can not omit nil fields for field: Dashboards, due to: ... field: Tiles ... data was expected to be a not-nil list` |
| **Root Cause** | JSON tinha `savedSearches` aninhado no dashboard, mas sem `tiles[]`. A API exige `tiles`. |
| **Impacto** | Nenhum dashboard criado (todos falharam) |
| **Solução** | Adicionar `tiles[]` por dashboard, um tile por widget referenciando `savedSearchId` |

### P2. Dashboard sem `savedSearches` aninhado

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | Após P1: HTTP 400 `... field: SavedSearches ... data was expected to be a not-nil list` |
| **Root Cause** | Tentativa de mover `savedSearches` para o topo (sibling de `dashboards`). A API exige `savedSearches` **dentro** de cada dashboard, junto com `tiles`. |
| **Impacto** | Import ainda falhando |
| **Solução** | Cada dashboard precisa de **AMBOS** `tiles[]` E `savedSearches[]` aninhados |

### P3. `featuresConfig` incompleto

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | HTTP 400: `featuresConfig must contain property crossService` → depois `featuresConfig.crossService must contain property shared` |
| **Root Cause** | `featuresConfig: {}` inválido. Estrutura exigida é aninhada. |
| **Impacto** | Import falhando (dashboard-level e savedSearch-level) |
| **Solução** | `featuresConfig = {"crossService":{"shared":false}}` em cada dashboard E cada savedSearch |

### P4. `providerId` inválido

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | HTTP 400: `Invalid providerId ... Valid providerIds are: opsi, APM, log-analytics, management-dashboard, management-agent, dbm and appmgmt` |
| **Root Cause** | JSON usava `providerId: oci-monitoring` — não é valor válido |
| **Impacto** | Import falhando |
| **Solução** | `providerId = management-dashboard` (para dashboards de MQL/métrica) |

### P5. Dimensão errada em queries oci_faas (widgets vazios)

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | Import OK, mas widgets D1 (oci_faas) sem dados. Métrica custom funcionava. |
| **Root Cause** | Query usava `resourceId="${application_id}"`. Em `oci_faas`, `resourceId` = OCID da **Function** (fnfunc); `applicationId` = OCID da **Application** (fnapp). O filtro por app OCID em `resourceId` não casa nada. |
| **Impacto** | Todos os 8 widgets oci_faas do D1 vazios |
| **Solução** | 14 queries `resourceId` → `applicationId`; re-import via `terraform apply -replace=` (recurso write-once) |

### P6. `compartment_name` errado quase quebrou IAM (evitado no plan review)

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | Plan mostrou `5 to change` em IAM: policy statements reescrevendo `mom-fast-track-poc-oci-serverless` → `serverless-dev` |
| **Root Cause** | `compartment_name` puxado do state = `serverless-dev` (display_name/tag), mas o **nome real** do compartment é `mom-fast-track-poc-oci-serverless`. IAM statements referenciam o compartment **por nome**. |
| **Impacto** | Se aplicado: todas as statements apontariam p/ compartment inexistente → funções perdem permissão (outage) |
| **Solução** | Detectado no plan review; `oci iam compartment get` confirmou nome real; passar `-var compartment_name=mom-fast-track-poc-oci-serverless` → plan limpo (0 change) |

---

## 2. Soluções Efetivas

- **Apply targeted** (`-target=module.dashboards`) — blast radius mínimo; plan esperado 3 add / 0 change / 0 destroy. Foi o que expôs o drift de IAM do P6 antes de causar dano.
- **Iterar pelo HTTP 400** — cada mensagem InvalidParameter nomeia o campo faltante. Correção campo-a-campo convergiu em 4 rounds.
- **Validar dado real via CLI** — `oci monitoring metric-data summarize-metrics-data` provou custom metric (2.0) e, sem filtro, revelou as dimensões reais do oci_faas (aplicationId vs resourceId), diagnosticando o P5.
- **`-replace`** para editar um recurso write-once sem destruir os outros.

## 3. Root Cause Analysis

Causa-raiz única: a skill `provisioning-custom-dashboard-oci-observability` **documentava o resource mas não o envelope JSON real** do import. Sem exemplo concreto, o JSON gerado errou schema em 4 campos independentes, cada um só detectável no apply. P5/P6 foram gaps de conhecimento env-específico (dimensão faas / nome do compartment) não propagados.

## 4. Análise de Capacidades

| Capacidade | Status antes | Gap |
|---|---|---|
| Skill dashboard tem envelope JSON | ❌ ausente | Causou P1–P4 |
| Skill lista providerId válidos | ❌ (`monitoring` errado) | Causou P4 |
| Faas dim (`applicationId`) documentada | ⚠️ parcial (em outras skills, não na de dashboard) | Causou P5 |
| Compartment-name-by-name caveat | ❌ ausente em agente | Quase P6 |
| Live-test discipline (validar só no apply) | ❌ ausente | Amplificou todos |

## 5. Propostas Implementadas

Aprendizados embutidos nas skills/agentes (esta sessão):
- `provisioning-custom-dashboard-oci-observability` — envelope confirmado (`tiles`+`savedSearches`+`featuresConfig`+`providerId`), correção `monitoring`→`management-dashboard`, anti-patterns (faas `resourceId`, IAM do deployer), disciplina de live-test.
- `oci-monitoring-alarms` + `monitoring-oci-apm-dashboards` — nota dimensão oci_faas `applicationId`.
- `oci-terraform` — caveat compartment_name por-nome; `oci-observability` — ponteiro schema import + live-test.
- Memórias: `dev-compartment-name-value`, `oci-observability-gotchas` (ponto 4 = schema import).
- Fonte-verdade: `infra/modules/dashboards/dashboards/*.json` (aplicados ao vivo).

## 6. Observações fora de escopo

- **Cold start ~68s** no 1º `/proxy/health` (warm depois ~3s). Investigar via `oci-debugger`.
- Webhook retornou **207** (partial success) — esperado; popula `RestProxyError{status_code=207}`.
- D2 (APM traces) — render dos spans não validado ao vivo (ingest de trace demora); confirmar no Trace Explorer.

---

# Fase 2 — Render & Populate

**Status:** ✅ RESOLVED — 3 dashboards renderizando + massa de dados gerada
**Contexto:** Após o import (Fase 1) os dashboards existiam mas o Console falhava ao desenhar os widgets, e depois D1/D3 ficavam em branco mesmo com métricas. Nova rodada de descoberta de schema — sempre só detectável **no Console/apply**, nunca no `plan`.

## 7. Problemas Encontrados (Fase 2)

### P7. Import-válido ≠ Render-válido

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | Import OK, mas Console: `Dashboard service had an internal error while adding widget` |
| **Root Cause** | JSON tinha `savedSearch` com `widgetTemplate`/`widgetVM` vazios e `uiConfig:{"vizType":"lineChart"}` + `dataConfig:[{type:"MQL",query}]`. A API **aceita** no import (validação estrutural), mas o Console não consegue instanciar o widget. |
| **Fix** | Cada savedSearch precisa `widgetTemplate:"visualizations/chartWidgetTemplate.html"` + `widgetVM:"visualizations/chartWidget"` + `uiConfig.chartInfo.jetConfig` + `dataConfig[].type:"monitoringDataSource"`. Shape-verdade = sample oficial `oracle-quickstart/oci-management-agent`. |

### P8. APM widget usa `tracesDataSource` (não APM_QL)

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | D2 (traces) não renderizava; nosso `dataConfig.type:"APM_QL"`+`apmDomainId` estava errado |
| **Root Cause** | Widget de trace real usa `type:"tracesDataSource"`, query em `parameters.apmQuery`, param `apmDomain` via filtro OOB (`OOBSS-APM-domain-filter`), `startTime`/`endTime` (não `time.start`), `maxDesiredDataPoints`, `dimensionFilters`, `simplifyDataSource`. Dashboard `featuresConfig:{crossService:{shared:true},serviceTypes:["APM"]}`. |
| **Como descobriu** | Editor **`{JSON}`** do Console (Dashboards → Create query-based widget → Data source=Traces) — copiou o shape real. |

### P9. Sintaxe TQL (APM Trace Query Language)

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | `PARSE_ERROR` / `ATTRIBUTE_ERROR` / `unknown_function` no Trace Explorer |
| **Root Cause** | Query usava camelCase + `by` + `percentage()`. Correto: atributos **PascalCase** (`ServiceName`, `OperationName`, `SpanDuration`, `SpanKind`, `TraceDuration`, `TraceStatus`); tags **bare sem aspas** (`peer.service`, `SpanErrorCount`); agregação com `as "alias"`; `group by` **depois** do `where`; **sem** `percentage()`. Erro = `SpanErrorCount>0` (span) ou `TraceStatus='ERROR'` (trace). |
| **Como descobriu** | Validação iterativa via `oci apm-traces query query-response run-query` + `trace trace get` (dump dos atributos reais do span). |

### P10. Metric widget importa mas fica EM BRANCO (faltava `regionName`)

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | D1/D3 renderizavam widget mas **sem dados** — métricas confirmadas ingeridas (14 invocations, RestProxyInvocation=14, RestProxyError=2) |
| **Root Cause** | `dataConfig.parameters` referencia `$(params.regionName)` e `$(params.time.start/end)`, mas a savedSearch **não declarava `parametersConfig`** com o param `regionName` (filtro OOB `OOBSS-management-dashboard-region-filter`) → resolvia vazio → query não executava. Faltava também `maxDataPoints:"useIntervalExact"` e o filtro regionName no dashboard. |
| **Fix** | savedSearch `parametersConfig:[time, compartmentId, regionName]` (capturado do `{JSON}` do Console, Data source=Monitoring) + `maxDataPoints` + regionName no dashboard `parametersConfig` + tile `parametersMap`. |

### P11. Cleanup — destroy do `_import` não apaga o dashboard

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | `-replace`/re-apply do D2 falhou: `401 NotAuthenticated ... RelatedResourceNotAuthorizedOrNotFound: Cannot find Resource <ocid>` |
| **Root Cause** | Destroy do recurso `oci_management_dashboard_management_dashboards_import` **não deleta** o dashboard/saved-searches (ficam ACTIVE, órfãos). Re-import com `override_same_name=true` tenta atualizar os órfãos de mesmo nome cujo estado ficou inconsistente. |
| **Fix** | Deletar órfãos por OCID antes (`oci management-dashboard dashboard delete` + `saved-search delete --force`), depois re-import limpo. |

### P12. Sessão OCI `security_token` expira ~1h

| Aspecto | Detalhe |
|---------|---------|
| **Sintoma** | Apply/validação falha no meio: `401 NotAuthenticated` no refresh de Vault/VCN; CLI aborta pedindo re-auth |
| **Root Cause** | Auth `SecurityToken` (profile `poc`) dura ~1h; sessão longa de trabalho estourou o token **3x**. Terraform não renova sozinho → apply pode escrever estado parcial. |
| **Fix** | Re-auth `oci session authenticate --profile poc --region sa-saopaulo-1` antes de applies longos; `oci session validate` p/ checar; InstancePrincipal em CI/CD. |

## 8. Meta-lição

**Não hand-authorar widgets de Management Dashboard OCI às cegas.** O shape render-válido (widgetTemplate/widgetVM/uiConfig/dataConfig por data source) só é confiável quando **capturado do editor `{JSON}` do Console** (Create query-based widget → escolhe Data source → `{JSON}`). Import valida estrutura; render exige o shape exato do provider. Traces = `tracesDataSource`; métrica = `monitoringDataSource` + `regionName`.

## 9. Massa de dados (populate)

Novo `scripts/generate-dashboard-traffic.sh` (reusa `simulate-webhook.sh`): 4 rodadas / waves (health, webhook OK, 207, 400, EVENT) espalhadas ~7 min. Gerou health×12, webhook OK×4, 207×4, 400×4, EVENT×4 (23 itens/rodada → RMS.ItemsDelta + 23 BrxServices.PostItem spans). **Esperado-vazio** (não bug): store create/update (JWT off), throttle (concorrência 0), "Errors by peer" (downstream respondeu sucesso → sem span error).

## 10. Capacidades / Propostas (Fase 2)

- `provisioning-custom-dashboard-oci-observability` blueprint: envelope **render-válido** (metric + traces + regionName + cleanup gotcha).
- Memória `oci-observability-gotchas`: import≠render, tracesDataSource, regionName, cleanup.
- **NOVO** 5º pilar `check-dashboards.sh` (valida render: widget-template/dataConfig.type/regionName/datapoints) — teria pego P7/P10 automaticamente.
- Memória `oci-session-expiry` (P12).
- Scripts registrados no CLAUDE.md.

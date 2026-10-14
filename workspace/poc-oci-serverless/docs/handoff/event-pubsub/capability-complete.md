---
kind: report
from: "@oci-observability"
to: user
capability: event-pubsub
refs: [deploy-report.md, observability-validation-report.md, diagnosis-report-sch-source.md]
outcome: success
createdAt: 2026-07-22T20:00:00Z
---

# Capability Complete — Event-Driven Pub/Sub (Pattern 02)

> **Source of truth for the current (green) state.** The `diagnosis-report*.md` files in this folder
> describe the PRE-FIX failing cycles (1–9) and are kept as historical evidence (the new pub/sub skills
> cite them). This record supersedes them for "what is live now".

## Arquitetura entregue (POC, dev)

```
Client ─POST /v1/events─▶ API Gateway ─▶ func-event-producer (APIGatewayFunction)
                                              │ PutMessages(key=event_type, value=DomainEvent+traceparent)
                                              ▼
                                   OCI Streaming: stream "event-stream" (pool PÚBLICO)
                                 ┌────────────┴────────────┐   (2 SCH = 2 cursores = fan-out real)
                          sch-event-notify           sch-event-audit
                                 ▼                          ▼
                     func-evt-consumer-notify     func-evt-consumer-audit
                     (forward REST httpbin)       (log + métrica AuditEventProcessed)
```

Pay-per-use: consumers `memory=1024 / timeout=300 / provisioned_concurrency=0` (escala a zero). Imagens `0.0.2`.

## Evidência (validado ao vivo 2026-07-22)

- **Fan-out real** — mesmo `event_id d48b2dae-127c-42f3-82d0-b2f22b629d27` processado por **ambos** os consumers (deploy-report cycle 10): producer `PUBLISHED` → notify `FORWARDED` + audit `AUDIT`, cada um com `records=1`.
- **Trace distribuído único** — TraceId **`f94cb37be4831757ca2f7edbb04c535f`** = `func-event-producer` (SERVER, `POST /events`) + `func-evt-consumer-audit` (CONSUMER) + `func-evt-consumer-notify` (CONSUMER) + notify CLIENT (`NotifyTarget.forward`). Os 2 CONSUMER re-parented via `traceparent` no **envelope da mensagem** (não HTTP). Reproduzido em 8 traces. Sem "Failed to export spans" (SimpleSpanProcessor).
- **4 métricas SCH** por connector: `ErrorsAtSource=0`, `ErrorsAtTarget=0`, `FunctionInvocationCount≥1` (notify+audit invocados).
- **Widget** `Events — Transaction Path` renderiza — 3 tiles de trace reescritas p/ tráfego pub/sub recente (fix: `TraceStatus` removido de `show spans`; filtro texto-livre `txnId` não é suportado no OCI Management Dashboard → drill por transação no APM Trace Explorer).

## Recursos / OCIDs

- Stream pool: PÚBLICO, endpoint `cell-1.streaming.sa-saopaulo-1.oci.oraclecloud.com`. Stream `event-stream` = `...xitxqll4lqot`.
- SCH: notify `...yfeocehevu`, audit `...lgornh5cz7` (ambos ACTIVE, source = stream público, private endpoint null).
- Producer app `...aocnsg26tu2cwf4mqdmhcn7guqtofqisgkyrpop2hxdkq` / fn `...asqb6jm3f5hadyrhlc6y4zqrldu3gm5restrrdip4u3va`.
- Consumer notify fn `...aqxui43bkqdhs6gcctenbjs54ozsbnhy2oyal5dshw44a`. Demais OCIDs: `terraform output` / `outputs.tf`.
- APM Domain + Management Dashboard `Events — Transaction Path (dev)`.

## Acceptance status (requisitos originais)

- [x] Infra streaming verificada/criada (módulos `streaming` + `service-connector`)
- [x] Arquitetura API Gateway → producer → 2 consumers
- [x] Observabilidade propagada **através do streaming** (trace distribuído único provado no APM)
- [x] Widget custom p/ caminho da transação (renderiza; drill por ID via Trace Explorer)
- [x] Deploy end-to-end no dev

## Backlog de hardening (não bloqueia; ver plano de evolução)

- **IAM least-privilege**: escopar os statements `serviceconnector` a `target.stream.id` / `target.function.id` (hoje compartment-wide).
- **Alarmes SCH**: `ErrorsAtSource/ErrorsAtTarget > 0` (CRITICAL) + no-throughput (WARNING) reusando o ONS topic — hoje ausentes (perda de dados silenciosa se o SCH falhar).
- **Streaming** `prevent_destroy` + docs de imutabilidade de `partitions`/`retention`.
- **obs-commons**: extrair as 3 cópias de `TracingSupport/MetricsPublisher/DomainEvent` p/ `libs/obs-commons` (risco de drift do contrato de trace).
- **StreamClient** `readTimeoutMillis=15000` (< timeout 60s) no producer; `/health` no producer; redeploy `0.0.3`.
  - ⚠️ **Blocker de build `0.0.3`**: após extrair `libs/obs-commons`, os Dockerfiles rodam `mvn package` dentro do container e precisam resolver `brx-fn-obs-commons:0.0.1` (hoje só no `~/.m2` local). Antes do build 0.0.3 o deployer tem que tornar a lib resolvível in-container (reactor raiz incluindo `libs/obs-commons`, `mvn install` no build-stage, ou publicar num registry). `mvn test` local está verde.
- **Tooling**: `FUNCTIONS_META` (validating-oci-observability) incluir os 3 apps pub/sub.

## Lições duras (encodadas nas skills `designing/provisioning-oci-event-driven-pubsub`)

1. **SCH não lê stream pool PRIVADO** — roda fora da VCN; pool tem que ser público (ou consumer in-VCN). *(Bloqueou ciclos 1–9.)*
2. Cold-start de imagem JVM pesada (~60s) vs deadline síncrono do SCH — memória/timeout não resolvem; escapes = PC (mín 10) / GraalVM native / decouple async.
3. **SimpleSpanProcessor** obrigatório em FaaS (Batch congela no freeze).
4. SCH Functions target exige `fn-function` **+** `fn-invocation`.
5. Atributos TF optional+computed exigem `-replace` (não remoção do HCL).
6. `TraceStatus` só em `show traces`; filtro texto-livre não vira tile no dashboard.

## Next action

Hardening opcional via o plano de evolução (WS4 infra security + WS3 Java + WS2 tooling). Nenhuma ação obrigatória — a capability está funcional e validada.

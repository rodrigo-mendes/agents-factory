# Package brief — oci (migrate authored package, by domain)

Frente 3: migrar o pacote OCI já autorado dentro de `workspace/poc-oci-serverless/.claude/`
(44 skills, 7 agentes, 26 rules) para 4 pacotes APM por domínio, usando o código do PoC como
exemplo embutido nos blueprints. Não há pesquisa `research_*` — conhecimento vive nas skills.

```yaml
slug: oci
language: en
frameworks:
  - OCI Functions (FDK Java 1.1.x, Java 17)
  - Terraform (oracle/oci ~> 8.x)
  - OCI Observability (Logging/Monitoring/APM)
legacy_source: workspace/poc-oci-serverless/.claude (44 skills, 7 agents, 26 rules)
deliverables: [skills, agent, rules, readme]
agent_kind: executor
out_of_scope:
  - empacotar o código da app (infra/services/libs) — só exemplo nos blueprints
  - reautorar skills (migração as-is + normalização)
rounds: 3
```

## Mapa 44 skills → 4 pacotes

### oci-functions-java (11) — ciclo de vida da função Java
developing-oci-functions-java · scaffolding-oci-function · implementing-oci-functions-events ·
integrating-oci-functions-objectstorage · invoking-rest-apis-from-oci-functions ·
publishing-events-from-oci-functions · testing-oci-functions-java · refactoring-oci-java ·
integrating-oracle-rms-webhooks · deploying-oci-functions · debugging-deployed-functions
Agentes: oci-functions-java, oci-deployer, oci-debugger

### oci-terraform (18) — provisioning + engenharia IaC
provisioning-oci-{api-gateway,apm,connector-hub,event-driven-pubsub,events,functions,iam,logging,
networking,object-storage,serverless-stack,streaming,vault} · provisioning-custom-dashboard-oci-observability ·
engineering-terraform-oci · managing-terraform-cicd · managing-terraform-state · testing-terraform-modules
Agente: oci-terraform

### oci-observability (9) — logging/monitoring/apm
designing-oci-logging · designing-oci-connector-hub · configuring-oci-monitoring-alarms ·
monitoring-oci-apm · monitoring-oci-apm-dashboards · monitoring-oci-java-functions ·
logging-oci-java-functions · observing-oci-java-functions · validating-oci-observability
Agente: oci-observability

### oci-architecture (6) — arquitetura/design
architecting-oci-serverless · designing-oci-api-gateway · designing-oci-networking ·
designing-oci-object-storage · designing-oci-vault-security · designing-oci-event-driven-pubsub
Agentes: oci-serverless-architect, oci-serverless-stack

Total: 11+18+9+6 = 44 ✓

## Rules (26) → instructions/ por prefixo
java-functions-* (16) + java-environment-validation + deployment-preflight-checks → oci-functions-java ·
terraform-* (8) → oci-terraform · observability-skills → oci-observability

## Scripts (decisão do G1)
- validating-oci-observability (10 scripts) e integrating-oracle-rms-webhooks (5) → migram como asset da skill
- preflight.sh → asset de deploying-oci-functions + gate do oci-deployer
- generate-dashboard-traffic.sh → asset de validating-oci-observability
- oci-cleanup.sh → NOVA skill cleaning-up-oci-resources (pacote oci-terraform), parametrizar OCIDs
- build-push.sh (6 cópias) → 1 template em scaffolding-oci-function
- normalizar harness de avaliação (evaluations.json vs .md)

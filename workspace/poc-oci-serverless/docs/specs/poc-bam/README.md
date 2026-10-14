# PoC BAM: Monitoramento de Processos de Negócio com Datadog

**Projeto:** PoC Monitorização de Processos de Negócio (BAM — Business Activity Monitoring)  
**Plataforma:** Oracle Cloud Infrastructure (OCI)  
**Observabilidade:** Datadog (ingestão via Service Connector Hub)  
**Data:** 2026-05-25  

---

## 1. Objetivo

Demonstrar as capacidades do **Datadog** como plataforma de observabilidade corporativa para OCI, utilizando uma arquitetura 100% serverless e orientada a eventos. O caso de uso é um **pipeline de concessão de crédito** com rastreabilidade end-to-end de eventos de negócio (BAM).

---

## 2. Diagrama de Arquitetura

```mermaid
graph TD
    %% Entry Point
    Upload["📁 Upload JSON<br/>(Cliente/Sistema)"] --> Bucket["oci_objectstorage_bucket<br/>bucket-bam-entrada-propostas"]

    %% Event-Driven Trigger
    Bucket --> EventRule["oci_events_rule<br/>ObjectCreate → Trigger"]
    EventRule --> Fn1["oci_functions_function<br/>fn-recepcao-proposta"]

    %% Function Chain
    Fn1 -->|"OCI SDK Invoke"| Fn2["oci_functions_function<br/>fn-motor-credito"]
    Fn2 -->|"Response"| Fn1

    %% API Gateway (Manual Testing)
    APIGW["oci_apigateway_deployment<br/>/bam/proposta"] -.->|"POST (teste)"| Fn1

    %% Observability Pipeline
    Fn1 -->|"stdout JSON"| Log["oci_logging_log<br/>Custom Log (Functions)"]
    Fn2 -->|"stdout JSON"| Log
    Log --> LogGroup["oci_logging_log_group<br/>log-group-bam-poc"]
    LogGroup --> SCH["oci_sch_service_connector<br/>Logging → HTTP Plugin"]

    %% Datadog Integration
    SCH -->|"HTTPS + DD-API-KEY"| Datadog["☁️ Datadog<br/>Log Intake API"]

    %% Security
    Vault["oci_vault_secret<br/>DD-API-KEY"] -.->|"Secret ref"| SCH

    %% Network
    subgraph VCN ["VCN: vcn-poc-bam (10.0.0.0/16)"]
        subgraph PrivateSubnet ["Subnet Privada (10.0.1.0/24)"]
            Fn1
            Fn2
        end
        subgraph PublicSubnet ["Subnet Pública (10.0.0.0/24)"]
            APIGW
        end
        NAT["NAT Gateway<br/>(Egress → Internet)"]
    end
    PrivateSubnet -.-> NAT
    NAT -.-> Datadog

    %% Styling
    classDef storage fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000;
    classDef compute fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000;
    classDef obs fill:#e3f2fd,stroke:#0d47a1,stroke-width:2px,color:#000;
    classDef ext fill:#fce4ec,stroke:#b71c1c,stroke-width:2px,color:#000;
    classDef net fill:#f3e5f5,stroke:#4a148c,stroke-width:1px,color:#000;

    class Bucket,Vault storage;
    class Fn1,Fn2,APIGW,EventRule compute;
    class Log,LogGroup,SCH obs;
    class Datadog,Upload ext;
    class NAT net;
```

---

## 3. Fluxo de Execução (Sequência)

```mermaid
sequenceDiagram
    participant Client as Sistema Cliente
    participant ObjStore as Object Storage
    participant Events as OCI Events
    participant Fn1 as fn-recepcao-proposta
    participant Fn2 as fn-motor-credito
    participant Logging as OCI Logging
    participant SCH as Service Connector Hub
    participant DD as Datadog

    Client->>ObjStore: PUT proposta.json
    ObjStore->>Events: Emit ObjectCreate event
    Events->>Fn1: Invoke (CloudEvent metadata)

    Fn1->>Fn1: Parse event (bucket, filename)
    Fn1->>ObjStore: GET proposta.json (SDK)
    ObjStore-->>Fn1: JSON payload
    Fn1->>Fn1: Generate transaction_id (UUID)
    Fn1->>Logging: stdout → BAM log (RECEBIDO)

    Fn1->>Fn2: Invoke (SDK) — payload + transaction_id
    Fn2->>Fn2: Aplicar regras de negócio
    Fn2->>Logging: stdout → BAM log (APROVADO/REJEITADO)
    Fn2-->>Fn1: Response (decisão)

    Fn1->>Logging: stdout → BAM log (FINALIZADO)

    Logging->>SCH: Stream logs (near real-time)
    SCH->>DD: POST /api/v2/logs (HTTPS + DD-API-KEY)
```

---

## 4. Escopo

### ✅ Dentro do Escopo

| Camada | Componentes |
|--------|-------------|
| **Infraestrutura (Terraform)** | VCN, Subnets, NAT GW, IAM (Dynamic Groups + Policies), Object Storage Bucket, OCI Events Rule, Functions Application + 2 Functions, Log Group + Logs, Service Connector Hub, Vault (DD-API-KEY), API Gateway (teste) |
| **Aplicação (Java)** | `fn-recepcao-proposta` (orquestrador), `fn-motor-credito` (regras), `BAMLogger` (utilitário telemetria) |
| **Observabilidade (OCI)** | Structured logging (JSON → stdout), OCI Logging capture, SCH routing para Datadog |

### ❌ Fora do Escopo

| Item | Razão |
|------|-------|
| Dashboard Datadog (criação/configuração) | Configuração manual na plataforma Datadog — não provisionável via Terraform OCI |
| Pipelines Datadog (Log Processing) | Configuração interna Datadog |
| Alertas e Monitors Datadog | Configuração interna Datadog |
| CI/CD Pipeline (build/deploy automático) | Deploy manual via `build-push.sh` + `terraform apply` |
| Integração com banco de dados | Fora do caso de uso da PoC |
| Multi-region / DR | Complexidade desnecessária para PoC |

---

## 5. Pré-requisitos

| Requisito | Descrição |
|-----------|-----------|
| Conta OCI ativa | Com permissões para criar recursos no compartimento alvo |
| Compartimento dedicado | Isolamento de blast radius para a PoC |
| OCI CLI configurado | Para `fn deploy` e `oci os object put` |
| Docker instalado | Para build das imagens das Functions |
| Terraform >= 1.9 | Compatível com OCI Provider ~> 8.15 |
| Conta Datadog | Com API Key válida para ingestão de logs |
| OCIR (Container Registry) | Repositório para imagens Docker das Functions |

---

## 6. Estrutura de Arquivos (Alvo)

```
infra/
  environments/
    bam/                          ← Novo environment isolado
      main.tf                     ← Módulos compartilhados (network, iam, vault)
      apps.tf                     ← Functions + Events + Logging + SCH
      variables.tf                ← Inputs (tenancy, compartment, region, dd_api_key)
      outputs.tf                  ← Endpoints, OCIDs
      terraform.tfvars            ← Valores (exceto secrets)
      versions.tf                 ← Provider constraints
  modules/
    object-storage/               ← Novo módulo
    events/                       ← Novo módulo
    service-connector/            ← Novo módulo
    (network, function-app, iam, observability, vault, api-gateway → existentes)

services/
  fn-recepcao-proposta/           ← Nova function
    src/main/java/com/brx/bam/
      RecepcaoPropostaFunction.java
      BAMLogger.java
      model/PropostaInput.java
      model/PropostaEnriquecida.java
    src/test/java/...
    pom.xml
    func.yaml
    Dockerfile
    build-push.sh
  fn-motor-credito/               ← Nova function
    src/main/java/com/brx/bam/
      MotorCreditoFunction.java
      BAMLogger.java (shared copy)
      model/PropostaEnriquecida.java
      model/DecisaoCredito.java
    src/test/java/...
    pom.xml
    func.yaml
    Dockerfile
    build-push.sh
```

---

## 7. Documentos de Especificação

| Documento | Conteúdo |
|-----------|----------|
| [01-infra-spec.md](01-infra-spec.md) | Especificação completa de infraestrutura Terraform |
| [02-functions-spec.md](02-functions-spec.md) | Especificação de desenvolvimento das Java Functions |
| [03-agent-capabilities.md](03-agent-capabilities.md) | Mapeamento de capacidades dos agentes + catálogo de prompts |
| [04-implementation-steps.md](04-implementation-steps.md) | **Passo-a-passo detalhado** — 22 steps com agente, prompt e inputs exatos |

---

## 8. Ordem de Implementação Recomendada

```mermaid
gantt
    title PoC BAM — Implementação
    dateFormat YYYY-MM-DD
    axisFormat %d/%m

    section Infra Base
    Network + IAM + Vault           :infra1, 2026-05-26, 1d
    Object Storage + Events Rule    :infra2, after infra1, 1d
    Functions App + Deploy stubs    :infra3, after infra2, 1d

    section Java Functions
    fn-recepcao-proposta            :java1, after infra1, 2d
    fn-motor-credito                :java2, after java1, 1d
    BAMLogger + Unit Tests          :java3, after java1, 1d

    section Observabilidade
    Logging (Log Group + Logs)      :obs1, after infra3, 1d
    Service Connector Hub → Datadog :obs2, after obs1, 1d

    section Integração
    Deploy Functions + E2E Test     :int1, after obs2, 1d
    API Gateway (teste manual)      :int2, after int1, 1d
```

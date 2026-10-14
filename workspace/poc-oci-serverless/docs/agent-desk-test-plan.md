# Plano de Teste de Mesa e Mecanismo de Paralelismo de Sub-Agentes

Este documento detalha o teste de mesa (dry-run) das capacidades dos agentes no projeto de microsserviços OCI Serverless e define as especificações de engenharia necessárias para que o orquestrador coordene tarefas em paralelo de forma assíncrona e confiável.

---

## 1. Introdução e Objetivo

Em ecossistemas de agentes de IA baseados em múltiplos serviços e repositórios únicos (monorepos), a coordenação de fluxos de ponta a ponta exige:
1. **Validação Lógica (Teste de Mesa)**: Simular o raciocínio determinístico e comportamento dos agentes (P0-P5) em cenários complexos antes de colocá-los em execução real.
2. **Delegação Paralela**: Reduzir a latência do ciclo de desenvolvimento, permitindo que alterações de implementação isoladas (ex: código de aplicação em Java vs infraestrutura de rede em Terraform) ocorram paralelamente através de sub-agentes síncronos e assíncronos.

---

## 2. Teste de Mesa das Capacidades dos Agentes

Abaixo estão descritos os cenários de simulação passo a passo para as novas e existentes capacidades unitárias e compostas do projeto.

### Cenário 1: Implementação da Nova Capacidade `/add-function-tracing`
* **Usuário solicita**: *"Adicionar rastreamento distribuído (distributed tracing) na função services/api-handler"*
* **Agente Designado**: `@oci-functions-java`
* **Estágio Inicial**: Função Java operando normalmente sem agentes de profiling ou tracing.

```mermaid
sequenceDiagram
    autonumber
    User->>+oci-functions-java: Executa /add-function-tracing em services/api-handler
    oci-functions-java->>oci-functions-java: P0: Verifica pasta e lê skill observing-oci-java-functions
    oci-functions-java->>oci-functions-java: P1: Analisa pom.xml, func.yaml e Dockerfile
    oci-functions-java->>oci-functions-java: P2: Consulta blueprints (No dynamic keys, use Private App Data Key)
    oci-functions-java->>User: P3: Propõe Dockerfile multi-stage com OpenTelemetry agent + JVM_ARGS
    User-->>-oci-functions-java: Aprovação concedida
    Activate oci-functions-java
    oci-functions-java->>oci-functions-java: P4: Altera Dockerfile, pom.xml, func.yaml com OTEL_EXPORTER
    oci-functions-java->>oci-functions-java: P5: Roda mvn compile para certificar empacotamento
    oci-functions-java-->>User: Reporta sucesso de injeção de tracing
    Deactivate oci-functions-java
```

#### Teste de Mesa Passo a Passo (Passo de Raciocínio da IA)

1.  **P0 (Verify Docs)**:
    *   A IA detecta a pasta `services/api-handler/` e valida a presença de [services/api-handler/pom.xml](services/api-handler/pom.xml).
    *   Carrega a skill de base e a skill `observing-oci-java-functions`.
2.  **P1 (Analyze)**:
    *   Analisa o [services/api-handler/Dockerfile](services/api-handler/Dockerfile) para entender se é multi-stage.
    *   Verifica se o [services/api-handler/func.yaml](services/api-handler/func.yaml) declara `JVM_ARGS`.
3.  **P2 (Consult)**:
    *   Consulta a regra restrictiva: *"Nunca usar a chave pública do APM OCI para spans no lado do servidor; isso gera falhas silenciosas de upload."*
    *   Identifica que a porta coletora do OTel deve apontar para o endpoint regional `apm-collector.<region>.oci.oraclecloud.com`.
4.  **P3 (Propose + Confirm)**:
    *   Fórmula a proposta incluindo:
        *   Injeção do agente OpenTelemetry (`opentelemetry-javaagent.jar` v2.28.1).
        *   Metadodos de JVM configurando as variáveis de ambiente necessárias.
5.  **P4 (Implement)**:
    *   Escreve instruções para download do agente no Dockerfile.
    *   Adiciona no [services/api-handler/func.yaml](services/api-handler/func.yaml):
        ```yaml
        config:
          OTEL_SERVICE_NAME: api-handler-service
          OTEL_EXPORTER_OTLP_ENDPOINT: https://apm-collector.sa-saopaulo-1.oci.oraclecloud.com
        ```
6.  **P5 (Validate)**:
    *   Chama `mvn compile` localmente. Garante que nenhuma dependência transitiva conflite. Verificação concluída.

---

### Cenário 2: Adição do Bloco de Observabilidade Composto `/add-function-observability`
* **Usuário solicita**: *"Instale o bloco de observabilidade empresarial completo em services/func-api-facade"*
* **Agente Designado**: `@oci-functions-java`

#### Raciocínio de Lote e Ordem de Injeção:
```
[Início] 
   │
   ├── 1. Modificar pom.xml ──► Insere logback, logstash-encoder e oci-java-sdk-monitoring
   │
   ├── 2. Criar logback.xml ──► Adiciona STDOUT appender com LogstashEncoder (JSON estruturado)
   │
   ├── 3. Custom Metrics ─────► Cria classe utilitária de métricas (PostMetricData)
   │
   ├── 4. JVM Bootstrap ──────► Altera Dockerfile e JVM_ARGS com agente OTel de Tracing
   │
   └── 5. Handler Audit ──────► Injeta blocos de timing de Cold Start e try-catch de exceções
```

#### Teste de Mesa de Cruzamento de Consistência (P5):
*   **Pergunta**: O que acontece se a função rodar perto do tempo limite (timeout) de execução?
*   **Ação Determinística do Agente**: A IA insere um controle de tempo restante (`System.currentTimeMillis() - startupTime`). Se a margem livre for inferior a 10%, ela suspende a postagem de métricas pendentes para garantir a devolução da resposta síncrona, evitando estouro de timeout do FDK da OCI.

---

### Cenário 3: Provisionamento e Testes Terraform `/add-terraform-tests`
* **Usuário solicita**: *"Crie testes de infraestrutura para o módulo networking em infra/modules/network"*
* **Agente Designado**: `@oci-terraform`

#### Raciocínio de Planejamento de Testes:
*   A IA carrega a skill `testing-terraform-modules`.
*   Estrutura um arquivo de testes declarativos do Terraform v1.11 `network.tftest.hcl`.

#### Metodologia passo a passo de Dry Run:
1.  Verifica as definições de variáveis em [infra/modules/network/variables.tf](infra/modules/network/variables.tf) (ou mapeamento correspondente).
2.  Cria o arquivo `.tftest.hcl` comMock de variáveis de entrada para simular testes em isolamento (Plan-only).
3.  Implementa asserções estritas que garantem conformidade com a convenção do projeto:
    *   Valida se a VCN criada possui o CIDR esperado.
    *   Valida se as tags `freeform_tags` contêm a chave obrigatória `local.common_tags`.
4.  Roda `terraform test` para validar sintaticamente a suíte de asserções.

---

## 3. Arquitetura de Delegação Paralela de Sub-Agentes

Para processar frentes de desenvolvimento síncronas de infraestrutura e aplicação simultaneamente, o agente orquestrador principal (`@oci-serverless-stack`) executa o fluxo abaixo.

### 3.1 Mecânica de Paralelização via runSubagent

Quando o usuário aciona um fluxo amplo e end-to-end, o orquestrador fragmenta o escopo de atuação em sub-ações e chama concorrentemente os sub-agentes utilizando a capacidade de processamento de lote (Parallel Tool Calling) do LLM.

#### Fluxo de Execução com Barreiras de Sincronização:

```
                  ======================================
                  =  Orquestrador: @oci-serverless-stack =
                  ======================================
                                    │
                        [Fase 1: Escrita de Handoffs]
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
[Handoff Stream A (Java)]                             [Handoff Stream B (Infra)]
Docs: docs/handoff/stream-a-java.md                   Docs: docs/handoff/stream-b-terraform-infra.md
         │                                                     │
         ▼                                                     ▼
     =======================                               =======================
     = oci-functions-java  =                               = oci-terraform       =
     =======================                               =======================
         │                                                     │
         ├─► [ services/api-handler/ ]                         ├─► [ infra/modules/ ]
         ├─► [ Exclui pasta infra/ ]                           ├─► [ Exclui services/ ]
         ▼                                                     ▼
  Status: Completed                                     Status: Completed
         │                                                     │
         └──────────────────────────┬──────────────────────────┘
                                    ▼
                        [Sincronização / Join]
                                    │
                        [Fase 2: Integração Sequencial]
                                    │
                                    ├───► Criação do recurso da Function no TF
                                    └───► Vinculação de Rotas API GW (Stream C)
```

---

## 4. Alterações Necessárias para Habilitar Paralelismo de Tarefas

Se desejarmos que os agentes conduzam implementações simultâneas de sub-agentes de forma nativa e paralela em futuras evoluções, as três alterações de engenharia a seguir devem ser efetivadas no projeto:

### 1ª Alteração: Rigorosa Segregação de Contexto de Arquivos (Sandbox Virtual)
Para garantir que não haja colisões ou modificações concorrentes que corrompam o mesmo recurso, revisamos e atualizamos a convenção do orquestrador em [.github/agents/oci-serverless-stack.agent.md](.github/agents/oci-serverless-stack.agent.md) garantindo a proibição absoluta de concorrência de escrita no mesmo diretório:
*   Sub-agente `@oci-functions-java` recebe apenas a árvore de diretório `services/`.
*   Sub-agente `@oci-terraform` recebe apenas a árvore de diretório `infra/`.

### 2ª Alteração: Especificação em Lote via Handoff Files
O orquestrador sempre gerará as especificações de desenvolvimento físicas na pasta `docs/handoff/` antes de disparar o sub-agente. Ao ler esses arquivos (`stream-a-java.md` e `stream-b-terraform-infra.md`), o respectivo executor deve saltar a etapa P1 (Análise Geral do Repositório) e processar de forma direta e determinística apenas as tarefas detalhadas no handoff.

### 3ª Alteração: Alteração das Instruções do Orquestrador (.agent.md)
Atualizar o arquivo [.github/agents/oci-serverless-stack.agent.md](.github/agents/oci-serverless-stack.agent.md) para explicitar os comportamentos de multi-tool calling e controle de retornos paralelos com tolerância a falhas (ex: se um sub-agente falhar compilando, o outro persiste suas modificações, mas a etapa de orquestração sequencial Stream C é interrompida com alerta de falha de dependência).

---

## 5. Matriz de Coerência de Teste de Mesa (Matriz de Sucesso)

Consulte esta tabela para realizar validações manuais ou automatizadas ao término da orquestração em paralelo:

| Dependência de Dados | Origem (Produtor) | Destino (Consumidor) | Validação de Coerência (Métrica de Sucesso) |
| :--- | :--- | :--- | :--- |
| **Imagem do Docker** | `@oci-functions-java` (Build) | `@oci-terraform` (Func app resource) | O caminho da tag da imagem gerada em OCIR no stream A coincide com o parâmetro `image` inserido em `apps.tf` no stream C. |
| **Endpoint da Rota** | `@oci-terraform` (API GW Deployment) | `@oci-functions-java` (Integration tests) | O endpoint do host gerado no deploy condiz com o PATH mapeado nos testes integrados Java. |
| **OCID do Secret** | `@oci-terraform` (Vault secret) | `@oci-functions-java` (Runtime config) | A variável de ambiente que guarda o OCID do segredo em `func.yaml` coincide com a saída gerada pelo Terraform. |

---

> **Diretrizes e Convenções completas**: Consulte [docs/handoff/README.md](docs/handoff/README.md) para regras de ciclo de vida de arquivos e [docs/PROMPTS-GUIDE.md](docs/PROMPTS-GUIDE.md) para navegação de prompts.

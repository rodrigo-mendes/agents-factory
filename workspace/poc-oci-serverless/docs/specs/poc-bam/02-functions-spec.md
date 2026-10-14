# Especificação de Funções Java — PoC BAM Datadog

**Projeto:** PoC Monitoramento de Processos de Negócio (BAM) com Datadog  
**Framework:** OCI Functions FDK v1.1.x (Fn Project)  
**Linguagem:** Java 17  
**Build:** Maven  
**SDK:** OCI Java SDK v3.86+

---

## 1. Visão Geral

Duas functions com responsabilidades estritas formam o pipeline de concessão de crédito:

| Function | Responsabilidade | Trigger | Memory | Timeout |
|----------|-----------------|---------|--------|---------|
| `fn-recepcao-proposta` | Orquestrador — recebe evento, lê Object Storage, invoca fn2 | OCI Events (ObjectCreate) + API Gateway (POST /bam/proposta) | 256 MB | 120s |
| `fn-motor-credito` | Worker — aplica regras de negócio, retorna decisão | Invocação SDK (síncrona, vinda da fn1) | 512 MB | 60s |

---

## 2. Contratos de Dados (JSON Schemas)

### 2.1 Payload de Entrada (Arquivo no Object Storage)

**Arquivo:** `propostas/{cliente_id}-{timestamp}.json`

```json
{
  "cliente_id": "CLI-998877",
  "nome": "João da Silva",
  "valor_solicitado": 15000.00,
  "score_credito": 650,
  "regiao": "SP"
}
```

### 2.2 Payload Enriquecido (fn1 → fn2)

```json
{
  "transaction_id": "TX-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "cliente_id": "CLI-998877",
  "nome": "João da Silva",
  "valor_solicitado": 15000.00,
  "score_credito": 650,
  "regiao": "SP",
  "received_at": "2026-05-25T14:30:00Z"
}
```

### 2.3 Resposta da fn2 (Decisão)

```json
{
  "transaction_id": "TX-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "decision": "APROVADO_AUTOMATICO",
  "reason": "Score 650 >= 400, valor 15000.00 <= 50000.00",
  "processed_at": "2026-05-25T14:30:02Z"
}
```

### 2.4 Contrato BAM Log (Telemetria para Datadog)

**Formato:** JSON linear impresso em `System.out.println()` — capturado pelo OCI Logging.

```json
{
  "bam_process": "concessao_credito",
  "transaction_id": "TX-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "function_name": "fn-recepcao-proposta",
  "step": "recebido",
  "business_status": "RECEBIDO",
  "business_value": 15000.00,
  "client_region": "SP",
  "message": "Proposta CLI-998877 recebida com sucesso"
}
```

**Campos obrigatórios:**

| Campo | Tipo | Descrição | Cardinalidade |
|-------|------|-----------|---------------|
| `bam_process` | `string` | Identificador fixo do processo | Sempre `"concessao_credito"` |
| `transaction_id` | `string` | UUID único por transação (gerado na fn1) | Formato: `TX-{UUID}` |
| `function_name` | `string` | Nome da function que emitiu o log | `fn-recepcao-proposta` ou `fn-motor-credito` |
| `step` | `string` | Etapa do processo | Enum: ver tabela abaixo |
| `business_status` | `string` | Status de negócio | Enum: ver tabela abaixo |
| `business_value` | `double` | Valor monetário da proposta | >= 0.0 |
| `client_region` | `string` | UF do cliente | 2 chars |
| `message` | `string` | Descrição legível do evento | Texto livre |

**Enum `step`:**

| Valor | Function | Descrição |
|-------|----------|-----------|
| `recebido` | fn1 | Proposta recebida e parseada |
| `motor_regras` | fn2 | Avaliação no motor de regras |
| `analise_fraude` | fn2 | Gatilho de análise manual |
| `decisao_final` | fn2 | Decisão final emitida |
| `finalizado` | fn1 | Pipeline concluído |

**Enum `business_status`:**

| Valor | Significado |
|-------|-------------|
| `RECEBIDO` | Proposta entrada no pipeline |
| `APROVADO_AUTOMATICO` | Aprovada pelo motor |
| `REJEITADO_SCORE` | Rejeitada por score < 400 |
| `REQUER_ANALISE_MANUAL` | Valor > 50000 — escalada |
| `ERRO_VALIDACAO_DADOS` | Dados de entrada inválidos |
| `ERRO_INFRAESTRUTURA` | Falha técnica (Object Storage inacessível, etc.) |
| `FINALIZADO` | Pipeline concluído (fn1 recebeu resposta) |

---

## 3. Function 1: `fn-recepcao-proposta`

**Agente:** `@oci-functions-java`  
**Skills:** `developing-oci-functions-java`, `implementing-oci-functions-events`, `integrating-oci-functions-objectstorage`

### 3.1 Estrutura do Projeto

```
services/fn-recepcao-proposta/
├── src/
│   ├── main/java/com/brx/bam/recepcao/
│   │   ├── RecepcaoPropostaFunction.java    ← Handler principal
│   │   ├── BAMLogger.java                    ← Utilitário de telemetria
│   │   ├── service/
│   │   │   ├── ObjectStorageService.java     ← Leitura do bucket
│   │   │   └── FunctionInvokeService.java    ← Invocação da fn2
│   │   └── model/
│   │       ├── PropostaInput.java            ← POJO entrada (JSON do bucket)
│   │       ├── PropostaEnriquecida.java      ← POJO com transaction_id
│   │       └── DecisaoCredito.java           ← POJO resposta da fn2
│   └── test/java/com/brx/bam/recepcao/
│       ├── RecepcaoPropostaFunctionTest.java
│       └── BAMLoggerTest.java
├── pom.xml
├── func.yaml
├── Dockerfile
└── build-push.sh
```

### 3.2 Handler Principal

```java
package com.brx.bam.recepcao;

import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;
import com.oracle.bmc.auth.ResourcePrincipalAuthenticationDetailsProvider;

/**
 * Entry point para o pipeline BAM.
 * Trigger: OCI Events (ObjectCreate) ou API Gateway (POST /bam/proposta).
 *
 * Fluxo:
 * 1. Parse do evento (extrair bucket + filename)
 * 2. Download do JSON do Object Storage
 * 3. Validação do payload
 * 4. Geração do transaction_id
 * 5. BAM Log: RECEBIDO
 * 6. Invocação síncrona da fn-motor-credito
 * 7. BAM Log: FINALIZADO
 * 8. Retorno da decisão
 */
public class RecepcaoPropostaFunction {

    private ObjectStorageService objectStorageService;
    private FunctionInvokeService functionInvokeService;
    private String bucketName;
    private String bucketNamespace;
    private String fnMotorCreditoId;
    private String initError;

    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        try {
            this.bucketName = ctx.getConfigurationByKey("BUCKET_NAME")
                .orElseThrow(() -> new IllegalStateException("BUCKET_NAME not configured"));
            this.bucketNamespace = ctx.getConfigurationByKey("BUCKET_NAMESPACE")
                .orElseThrow(() -> new IllegalStateException("BUCKET_NAMESPACE not configured"));
            this.fnMotorCreditoId = ctx.getConfigurationByKey("FN_MOTOR_CREDITO_ID")
                .orElseThrow(() -> new IllegalStateException("FN_MOTOR_CREDITO_ID not configured"));

            var authProvider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
            this.objectStorageService = new ObjectStorageService(authProvider, bucketNamespace);
            this.functionInvokeService = new FunctionInvokeService(authProvider);
        } catch (Exception e) {
            this.initError = e.getMessage();
        }
    }

    /**
     * Handler para invocação via OCI Events (CloudEvent).
     * Extrai metadata do evento e processa a proposta.
     */
    public String handleEvent(String eventJson) {
        if (initError != null) {
            BAMLogger.emitBusinessEvent(
                "UNKNOWN", "fn-recepcao-proposta", "recebido",
                "ERRO_INFRAESTRUTURA", 0.0, "N/A",
                "Initialization error: " + initError);
            return "{\"error\": \"" + initError + "\"}";
        }

        // 1. Parse do CloudEvent → extrair bucketName + objectName
        // 2. Download do JSON via ObjectStorageService
        // 3. Deserializar para PropostaInput
        // 4. Validar campos obrigatórios
        // 5. Gerar transaction_id (UUID)
        // 6. BAM Log: RECEBIDO
        // 7. Construir PropostaEnriquecida (input + transaction_id)
        // 8. Invocar fn-motor-credito via FunctionInvokeService
        // 9. BAM Log: FINALIZADO
        // 10. Retornar DecisaoCredito

        return ""; // placeholder
    }
}
```

### 3.3 Lógica Detalhada (Pseudocódigo)

```
FUNCTION handleEvent(eventJson):
    // Passo 1: Parse do CloudEvent
    cloudEvent = parseCloudEvent(eventJson)
    objectName = cloudEvent.data.resourceName
    eventBucket = cloudEvent.data.additionalDetails.bucketName

    // Passo 2: Download do payload
    TRY:
        jsonContent = objectStorageService.getObject(bucketName, objectName)
    CATCH BmcException:
        BAMLogger.emit(txId="UNKNOWN", step="recebido", status="ERRO_INFRAESTRUTURA")
        THROW RuntimeException

    // Passo 3: Deserialização
    proposta = Jackson.readValue(jsonContent, PropostaInput.class)

    // Passo 4: Validação
    IF proposta.clienteId == null OR proposta.clienteId.isEmpty():
        txId = generateTransactionId()
        BAMLogger.emit(txId, step="recebido", status="ERRO_VALIDACAO_DADOS",
                       message="cliente_id obrigatório")
        RETURN errorResponse("cliente_id é obrigatório")

    // Passo 5: Transaction ID
    txId = "TX-" + UUID.randomUUID()

    // Passo 6: BAM Log
    BAMLogger.emitBusinessEvent(txId, "fn-recepcao-proposta", "recebido",
        "RECEBIDO", proposta.valorSolicitado, proposta.regiao,
        "Proposta " + proposta.clienteId + " recebida com sucesso")

    // Passo 7: Payload enriquecido
    enriched = new PropostaEnriquecida(txId, proposta, Instant.now())

    // Passo 8: Invocar fn2
    TRY:
        decisao = functionInvokeService.invoke(fnMotorCreditoId, enriched)
    CATCH Exception:
        BAMLogger.emit(txId, step="finalizado", status="ERRO_INFRAESTRUTURA",
                       message="Falha ao invocar fn-motor-credito")
        THROW

    // Passo 9: BAM Log final
    BAMLogger.emitBusinessEvent(txId, "fn-recepcao-proposta", "finalizado",
        "FINALIZADO", proposta.valorSolicitado, proposta.regiao,
        "Pipeline concluído. Decisão: " + decisao.decision)

    // Passo 10: Retorno
    RETURN decisao.toJson()
```

### 3.4 Services

#### ObjectStorageService

```java
package com.brx.bam.recepcao.service;

import com.oracle.bmc.auth.AbstractAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.GetObjectRequest;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class ObjectStorageService {
    private final ObjectStorageClient client;
    private final String namespace;

    public ObjectStorageService(AbstractAuthenticationDetailsProvider auth, String namespace) {
        this.client = ObjectStorageClient.builder().build(auth);
        this.namespace = namespace;
    }

    public String getObject(String bucketName, String objectName) {
        var request = GetObjectRequest.builder()
            .namespaceName(namespace)
            .bucketName(bucketName)
            .objectName(objectName)
            .build();

        try (InputStream is = client.getObject(request).getInputStream()) {
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("Failed to read object: " + objectName, e);
        }
    }
}
```

#### FunctionInvokeService

```java
package com.brx.bam.recepcao.service;

import com.oracle.bmc.auth.AbstractAuthenticationDetailsProvider;
import com.oracle.bmc.functions.FunctionsInvokeClient;
import com.oracle.bmc.functions.FunctionsManagementClient;
import com.oracle.bmc.functions.requests.GetFunctionRequest;
import com.oracle.bmc.functions.requests.InvokeFunctionRequest;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

public class FunctionInvokeService {
    private final AbstractAuthenticationDetailsProvider auth;
    private FunctionsInvokeClient invokeClient;
    private String invokeEndpoint;

    public FunctionInvokeService(AbstractAuthenticationDetailsProvider auth) {
        this.auth = auth;
    }

    public String invoke(String functionId, Object payload) {
        // Lazy init: resolve invoke endpoint on first call
        if (invokeEndpoint == null) {
            resolveEndpoint(functionId);
        }

        String payloadJson = serializeToJson(payload);

        var request = InvokeFunctionRequest.builder()
            .functionId(functionId)
            .invokeFunctionBody(
                new java.io.ByteArrayInputStream(
                    payloadJson.getBytes(StandardCharsets.UTF_8)))
            .build();

        try (InputStream response = invokeClient.invokeFunction(request).getInputStream()) {
            return new String(response.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("Failed to invoke function: " + functionId, e);
        }
    }

    private void resolveEndpoint(String functionId) {
        var mgmtClient = FunctionsManagementClient.builder().build(auth);
        var fn = mgmtClient.getFunction(
            GetFunctionRequest.builder().functionId(functionId).build()
        ).getFunction();

        this.invokeEndpoint = fn.getInvokeEndpoint();
        this.invokeClient = FunctionsInvokeClient.builder()
            .endpoint(invokeEndpoint)
            .build(auth);

        mgmtClient.close();
    }

    private String serializeToJson(Object obj) {
        try {
            return new com.fasterxml.jackson.databind.ObjectMapper()
                .writeValueAsString(obj);
        } catch (Exception e) {
            throw new RuntimeException("Serialization failed", e);
        }
    }
}
```

### 3.5 Dependências Maven (`pom.xml`)

```xml
<dependencies>
    <!-- FDK -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>api</artifactId>
        <version>1.1.11</version>
    </dependency>
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>runtime</artifactId>
        <version>1.1.11</version>
        <scope>runtime</scope>
    </dependency>

    <!-- OCI SDK: Auth (Resource Principal) -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
        <version>3.86.0</version>
    </dependency>

    <!-- OCI SDK: Object Storage -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-objectstorage</artifactId>
        <version>3.86.0</version>
    </dependency>

    <!-- OCI SDK: Functions Invoke -->
    <dependency>
        <groupId>com.oracle.oci.sdk</groupId>
        <artifactId>oci-java-sdk-functions</artifactId>
        <version>3.86.0</version>
    </dependency>

    <!-- Jackson (serialização JSON) -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.2</version>
    </dependency>

    <!-- Test -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>testing-core</artifactId>
        <version>1.1.11</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.13.2</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-core</artifactId>
        <version>5.11.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

### 3.6 `func.yaml`

```yaml
schema_version: 20180708
name: fn-recepcao-proposta
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.bam.recepcao.RecepcaoPropostaFunction::handleEvent
memory: 256
timeout: 120
```

---

## 4. Function 2: `fn-motor-credito`

**Agente:** `@oci-functions-java`  
**Skills:** `developing-oci-functions-java`

### 4.1 Estrutura do Projeto

```
services/fn-motor-credito/
├── src/
│   ├── main/java/com/brx/bam/motor/
│   │   ├── MotorCreditoFunction.java   ← Handler principal
│   │   ├── BAMLogger.java              ← Utilitário de telemetria (cópia)
│   │   ├── rules/
│   │   │   └── CreditRulesEngine.java  ← Motor de regras
│   │   └── model/
│   │       ├── PropostaEnriquecida.java
│   │       └── DecisaoCredito.java
│   └── test/java/com/brx/bam/motor/
│       ├── MotorCreditoFunctionTest.java
│       └── CreditRulesEngineTest.java
├── pom.xml
├── func.yaml
├── Dockerfile
└── build-push.sh
```

### 4.2 Handler Principal

```java
package com.brx.bam.motor;

import com.brx.bam.motor.model.PropostaEnriquecida;
import com.brx.bam.motor.model.DecisaoCredito;
import com.brx.bam.motor.rules.CreditRulesEngine;

/**
 * Motor de regras de crédito.
 * Trigger: Invocação síncrona via SDK (vinda da fn-recepcao-proposta).
 *
 * Regras:
 * 1. Score < 400 → REJEITADO_SCORE
 * 2. Valor > 50000 → REQUER_ANALISE_MANUAL
 * 3. Default → APROVADO_AUTOMATICO
 */
public class MotorCreditoFunction {

    private static final String FUNCTION_NAME = "fn-motor-credito";
    private final CreditRulesEngine rulesEngine = new CreditRulesEngine();

    public DecisaoCredito handleRequest(PropostaEnriquecida proposta) {
        String txId = proposta.getTransactionId();

        // Validação de entrada
        if (txId == null || txId.isEmpty()) {
            BAMLogger.emitBusinessEvent(
                "UNKNOWN", FUNCTION_NAME, "motor_regras",
                "ERRO_VALIDACAO_DADOS", 0.0, "N/A",
                "transaction_id ausente no payload");
            return DecisaoCredito.error("transaction_id obrigatório");
        }

        // Aplicar regras
        DecisaoCredito decisao = rulesEngine.evaluate(proposta);

        // BAM Log (o motor emite o log apropriado baseado na decisão)
        BAMLogger.emitBusinessEvent(
            txId, FUNCTION_NAME, decisao.getStep(),
            decisao.getDecision(),
            proposta.getValorSolicitado(),
            proposta.getRegiao(),
            decisao.getReason());

        return decisao;
    }
}
```

### 4.3 Motor de Regras

```java
package com.brx.bam.motor.rules;

import com.brx.bam.motor.model.PropostaEnriquecida;
import com.brx.bam.motor.model.DecisaoCredito;
import java.time.Instant;

/**
 * Máquina de estados de negócio.
 * Regras avaliadas sequencialmente (primeiro match vence).
 */
public class CreditRulesEngine {

    private static final int SCORE_MINIMO = 400;
    private static final double VALOR_MAXIMO_AUTOMATICO = 50000.00;

    public DecisaoCredito evaluate(PropostaEnriquecida proposta) {
        // Regra 1: Score Limitante
        if (proposta.getScoreCredito() < SCORE_MINIMO) {
            return DecisaoCredito.builder()
                .transactionId(proposta.getTransactionId())
                .decision("REJEITADO_SCORE")
                .step("motor_regras")
                .reason(String.format(
                    "Score %d < limite mínimo %d",
                    proposta.getScoreCredito(), SCORE_MINIMO))
                .processedAt(Instant.now())
                .build();
        }

        // Regra 2: Alçada de Risco
        if (proposta.getValorSolicitado() > VALOR_MAXIMO_AUTOMATICO) {
            return DecisaoCredito.builder()
                .transactionId(proposta.getTransactionId())
                .decision("REQUER_ANALISE_MANUAL")
                .step("analise_fraude")
                .reason(String.format(
                    "Valor %.2f > limite automático %.2f",
                    proposta.getValorSolicitado(), VALOR_MAXIMO_AUTOMATICO))
                .processedAt(Instant.now())
                .build();
        }

        // Regra 3: Aprovação Automática
        return DecisaoCredito.builder()
            .transactionId(proposta.getTransactionId())
            .decision("APROVADO_AUTOMATICO")
            .step("decisao_final")
            .reason(String.format(
                "Score %d >= %d, valor %.2f <= %.2f",
                proposta.getScoreCredito(), SCORE_MINIMO,
                proposta.getValorSolicitado(), VALOR_MAXIMO_AUTOMATICO))
            .processedAt(Instant.now())
            .build();
    }
}
```

### 4.4 `func.yaml`

```yaml
schema_version: 20180708
name: fn-motor-credito
version: 0.0.1
runtime: java
build_image: fnproject/fn-java-fdk-build:jdk17-latest
run_image: fnproject/fn-java-fdk:jre17-latest
cmd: com.brx.bam.motor.MotorCreditoFunction::handleRequest
memory: 512
timeout: 60
```

### 4.5 Dependências Maven (fn2 — simplificado)

```xml
<dependencies>
    <!-- FDK -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>api</artifactId>
        <version>1.1.11</version>
    </dependency>
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>runtime</artifactId>
        <version>1.1.11</version>
        <scope>runtime</scope>
    </dependency>

    <!-- Jackson (serialização JSON) -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.2</version>
    </dependency>

    <!-- Test -->
    <dependency>
        <groupId>com.fnproject.fn</groupId>
        <artifactId>testing-core</artifactId>
        <version>1.1.11</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>junit</groupId>
        <artifactId>junit</artifactId>
        <version>4.13.2</version>
        <scope>test</scope>
    </dependency>
</dependencies>
```

**Nota:** fn2 **não** precisa do OCI SDK (não acessa Object Storage nem invoca outras functions).

---

## 5. Utilitário Mandatório: `BAMLogger.java`

**Compartilhado** entre ambas as functions (cópia em cada projeto).

```java
package com.brx.bam.recepcao;  // ou com.brx.bam.motor

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

/**
 * Motor de telemetria BAM (Business Activity Monitoring).
 * Emite eventos de negócio como JSON linear em stdout.
 *
 * IMPORTANTE: O OCI Logging captura stdout das Functions.
 * O Service Connector Hub roteia estes logs para o Datadog.
 * Qualquer output fora deste formato será "ruído" no dashboard.
 */
public final class BAMLogger {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final String BAM_PROCESS = "concessao_credito";

    private BAMLogger() {} // Utility class — prevent instantiation

    /**
     * Emite um evento de negócio para captura pelo OCI Logging → Datadog.
     *
     * @param transactionId UUID único da transação (TX-...)
     * @param functionName  Nome da function emissora
     * @param step          Etapa do processo (recebido, motor_regras, decisao_final, finalizado)
     * @param businessStatus Status BAM (RECEBIDO, APROVADO_AUTOMATICO, etc.)
     * @param businessValue Valor monetário da proposta
     * @param clientRegion  UF do cliente
     * @param message       Descrição legível do evento
     */
    public static void emitBusinessEvent(
            String transactionId,
            String functionName,
            String step,
            String businessStatus,
            double businessValue,
            String clientRegion,
            String message) {

        try {
            ObjectNode logEvent = MAPPER.createObjectNode();

            // Tags estáticas do processo
            logEvent.put("bam_process", BAM_PROCESS);

            // Tags dinâmicas de rastreabilidade
            logEvent.put("transaction_id", transactionId);
            logEvent.put("function_name", functionName);
            logEvent.put("step", step);
            logEvent.put("business_status", businessStatus);

            // Métricas financeiras e demográficas
            logEvent.put("business_value", businessValue);
            logEvent.put("client_region", clientRegion);

            // Contexto legível
            logEvent.put("message", message);

            // CRÍTICO: System.out.println → capturado pelo OCI Logging
            System.out.println(MAPPER.writeValueAsString(logEvent));

        } catch (Exception e) {
            // Fallback: nunca quebrar o fluxo por erro de telemetria
            System.err.println("[BAM_ERROR] Failed to emit event: " + e.getMessage());
        }
    }
}
```

---

## 6. Modelos de Dados (POJOs)

### PropostaInput.java

```java
package com.brx.bam.recepcao.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class PropostaInput {
    @JsonProperty("cliente_id")
    private String clienteId;

    @JsonProperty("nome")
    private String nome;

    @JsonProperty("valor_solicitado")
    private double valorSolicitado;

    @JsonProperty("score_credito")
    private int scoreCredito;

    @JsonProperty("regiao")
    private String regiao;

    // Getters + default constructor (Jackson deserialization)
}
```

### PropostaEnriquecida.java

```java
package com.brx.bam.recepcao.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;

public class PropostaEnriquecida {
    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("cliente_id")
    private String clienteId;

    @JsonProperty("nome")
    private String nome;

    @JsonProperty("valor_solicitado")
    private double valorSolicitado;

    @JsonProperty("score_credito")
    private int scoreCredito;

    @JsonProperty("regiao")
    private String regiao;

    @JsonProperty("received_at")
    private Instant receivedAt;

    // Constructor, Getters, Builder
}
```

### DecisaoCredito.java

```java
package com.brx.bam.motor.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;

public class DecisaoCredito {
    @JsonProperty("transaction_id")
    private String transactionId;

    @JsonProperty("decision")
    private String decision;

    @JsonProperty("step")
    private String step;

    @JsonProperty("reason")
    private String reason;

    @JsonProperty("processed_at")
    private Instant processedAt;

    // Builder pattern, Getters, static factory methods
    public static DecisaoCredito error(String message) { /* ... */ }
    public static Builder builder() { return new Builder(); }
}
```

---

## 7. Gestão de Erros

### Classificação

| Tipo | Comportamento | BAM Status | Java Exception |
|------|---------------|-----------|----------------|
| **Erro de Validação** | Capturar, emitir BAM log, retornar resposta estruturada | `ERRO_VALIDACAO_DADOS` | Nenhuma (catch + return) |
| **Erro de Infraestrutura** | Emitir BAM log, lançar RuntimeException | `ERRO_INFRAESTRUTURA` | `RuntimeException` wrapping `BmcException` |
| **Erro de Timeout** | Emitir BAM log, lançar RuntimeException | `ERRO_INFRAESTRUTURA` | `RuntimeException` com mensagem de timeout |

### Regra Fundamental

> **Erros de negócio** (validação, score baixo, valor alto) → **NUNCA** geram stacktrace.  
> **Erros técnicos** (Object Storage inacessível, fn2 timeout) → Geram Exception (capturado pelo OCI Logging como ERROR).

```java
// ✅ CORRETO: Erro de validação — log BAM + resposta limpa
if (proposta.getClienteId() == null) {
    BAMLogger.emitBusinessEvent(txId, FUNCTION_NAME, "recebido",
        "ERRO_VALIDACAO_DADOS", 0.0, "N/A", "cliente_id ausente");
    return DecisaoCredito.error("cliente_id obrigatório");
}

// ✅ CORRETO: Erro técnico — log BAM + exception para OCI Logging
try {
    json = objectStorageService.getObject(bucket, filename);
} catch (BmcException e) {
    BAMLogger.emitBusinessEvent(txId, FUNCTION_NAME, "recebido",
        "ERRO_INFRAESTRUTURA", 0.0, "N/A",
        "Object Storage inacessível: " + e.getMessage());
    throw new RuntimeException("Object Storage failure", e);
}
```

---

## 8. Testes Unitários

### Cenários Obrigatórios (fn1)

| # | Cenário | Input | Expected BAM Log |
|---|---------|-------|-----------------|
| 1 | Proposta válida | JSON completo | `RECEBIDO` → `FINALIZADO` |
| 2 | cliente_id ausente | `{"nome":"X"}` | `ERRO_VALIDACAO_DADOS` |
| 3 | Object Storage falha | Mock throw BmcException | `ERRO_INFRAESTRUTURA` |
| 4 | fn2 timeout | Mock timeout | `ERRO_INFRAESTRUTURA` |

### Cenários Obrigatórios (fn2)

| # | Cenário | Input | Expected |
|---|---------|-------|----------|
| 1 | Score < 400 | `score_credito: 350` | `REJEITADO_SCORE` |
| 2 | Valor > 50000 | `valor_solicitado: 75000` | `REQUER_ANALISE_MANUAL` |
| 3 | Aprovação | `score: 650, valor: 15000` | `APROVADO_AUTOMATICO` |
| 4 | Score = 400 (boundary) | `score_credito: 400` | `APROVADO_AUTOMATICO` |
| 5 | Valor = 50000 (boundary) | `valor_solicitado: 50000` | `APROVADO_AUTOMATICO` |
| 6 | transaction_id ausente | `{}` | `ERRO_VALIDACAO_DADOS` |

---

## 9. Dockerfile (Template para Ambas)

```dockerfile
FROM fnproject/fn-java-fdk-build:jdk17-latest AS build

WORKDIR /function
COPY pom.xml .
RUN mvn dependency:go-offline -B

COPY src ./src
RUN mvn package -DskipTests -B

FROM fnproject/fn-java-fdk:jre17-latest

WORKDIR /function
COPY --from=build /function/target/dependency/*.jar /function/app/
COPY --from=build /function/target/*.jar /function/app/

CMD ["com.brx.bam.recepcao.RecepcaoPropostaFunction::handleEvent"]
```

> **⚠️ CRÍTICO:** O `CMD` no Dockerfile **DEVE** corresponder exatamente ao `cmd` no `func.yaml`. Divergência = erro 502 imediato.

---

## 10. Teste E2E (Manual)

### Via Object Storage (trigger completo):
```bash
# Upload proposta → trigger automático via Events
oci os object put \
  --bucket-name bucket-bam-entrada-propostas-bam \
  --file proposta-teste.json \
  --name "propostas/CLI-001-$(date +%s).json"
```

### Via API Gateway (bypass Events, teste direto):
```bash
curl -X POST https://<gateway>/bam/proposta \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id": "CLI-998877",
    "nome": "João da Silva",
    "valor_solicitado": 15000.00,
    "score_credito": 650,
    "regiao": "SP"
  }'
```

### Verificação de logs BAM:
```bash
# Buscar logs no OCI Logging (últimos 5 min)
oci logging-search search-logs \
  --search-query 'search "log-group-bam-poc" | where data.message contains "bam_process"' \
  --time-start "$(date -u -v-5M +%Y-%m-%dT%H:%M:%SZ)" \
  --time-end "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

---

## 11. Checklist de Implementação

| # | Componente | Agente | Status |
|---|-----------|--------|--------|
| 1 | Scaffold `fn-recepcao-proposta` (pom.xml, func.yaml, Dockerfile) | `@oci-functions-java` | ⬜ |
| 2 | Scaffold `fn-motor-credito` (pom.xml, func.yaml, Dockerfile) | `@oci-functions-java` | ⬜ |
| 3 | `BAMLogger.java` (ambas functions) | `@oci-functions-java` | ⬜ |
| 4 | POJOs (PropostaInput, PropostaEnriquecida, DecisaoCredito) | `@oci-functions-java` | ⬜ |
| 5 | `ObjectStorageService.java` | `@oci-functions-java` | ⬜ |
| 6 | `FunctionInvokeService.java` | `@oci-functions-java` | ⬜ |
| 7 | `RecepcaoPropostaFunction.java` (handler completo) | `@oci-functions-java` | ⬜ |
| 8 | `MotorCreditoFunction.java` (handler completo) | `@oci-functions-java` | ⬜ |
| 9 | `CreditRulesEngine.java` | `@oci-functions-java` | ⬜ |
| 10 | Unit tests (fn1) | `@oci-functions-java` | ⬜ |
| 11 | Unit tests (fn2) | `@oci-functions-java` | ⬜ |
| 12 | Build + push images | `@oci-deployer` | ⬜ |

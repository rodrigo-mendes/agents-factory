# Claude Code para QA e Testing

**Perfil:** QA / Dev Backend  
**Stack coberto:** JUnit 5, Mockito, LocalStack, Testcontainers, Spring Boot Test  
**Tempo estimado de leitura:** 10 min

---

## Casos de uso frequentes

### 1. Gerar testes unitários para uma classe

**Modo recomendado:** Edição direta ou Modo de exploração

**Edição direta (mais rápido para classes pequenas):**
```
Gere testes JUnit 5 com Mockito para todos os métodos públicos de @OrderService.java.
Testes unitários puros: sem @SpringBootTest, sem contexto Spring.
Cubra: caminho feliz + os 2-3 casos de erro mais prováveis por método.
Nomes de teste em inglês no formato `should_<resultado>_when_<condição>`.
```

O Claude Code escreve os testes e mostra o diff; você revisa antes de aceitar.

**Modo de exploração (melhor quando quer revisar antes de gerar):**
```
Para @OrderService.java:
1. Liste todos os métodos públicos
2. Para cada método, descreva os casos de teste que você cobriria
3. Espere minha confirmação antes de escrever o código

Depois geramos os testes um a um.
```

---

### 2. Analisar um teste que falha

**Modo recomendado:** Modo de exploração → edição direta para o fix

```
[Modo de exploração]
Tenho este teste falhando:
[cole o nome do teste e o stack trace]

O teste está em @OrderServiceTest.java.
A classe que ele testa é @OrderService.java.

Qual é a causa da falha? O teste está errado ou a implementação?
Me dê a causa e o fix mínimo, sem mexer em mais do que o necessário.
```

---

### 3. Identificar código sem cobertura

**Modo recomendado:** Modo de exploração / Plan Mode

```
Analise @PaymentService.java e @PaymentServiceTest.java.
Identifique os métodos ou paths de código em PaymentService que NÃO têm testes em PaymentServiceTest.
Liste cada gap encontrado e proponha um nome descritivo de teste para cobri-lo.
```

---

### 4. Gerar testes de integração com LocalStack

**Modo recomendado:** Modo de exploração → Modo agente

```
[Modo de exploração]
Quero escrever um teste de integração para @NotificationProcessor.java
que verifique o fluxo completo: mensagem SQS → processamento → registro no DynamoDB.
Usamos LocalStack para os serviços AWS.

Qual setup o teste precisa (contêineres, configuração, dados de teste)?
```

Com o plano em mãos:
```
[Modo agente]
Implemente o teste de integração descrito.
Use Testcontainers com a imagem localstack/localstack:latest.
O teste deve ser independente: criar seus próprios recursos e limpá-los ao terminar.
```

---

### 5. Melhorar a qualidade dos testes existentes

**Modo recomendado:** Modo de exploração para auditar → edição direta para cada melhoria

```
[Modo de exploração]
Audite os testes em @OrderServiceTest.java buscando:
1. Testes que fazem múltiplas assertions sem nome descritivo (confusos ao falhar)
2. Mocks permissivos demais (when(mock.qualquerCoisa()).thenReturn(...))
3. Testes que dependem da ordem de execução
4. Setup compartilhado que torna os testes difíceis de ler individualmente

Liste os problemas encontrados com a linha aproximada.
```

---

### 6. Gerar dados de teste

**Modo recomendado:** Edição direta ou Modo de exploração

```
[Modo de exploração]
Gere um Builder para criar objetos de teste de @Order.java.
Inclua valores padrão razoáveis para todos os campos obrigatórios
e métodos fluentes para sobrescrever cada campo.
Padrão: OrderTestBuilder.anOrder().withStatus(PENDING).build()
```

---

### 7. Depurar um teste intermitente (flaky test)

**Modo recomendado:** Modo de exploração / Plan Mode

```
Este teste falha de forma intermitente (1 a cada 10 execuções aproximadamente):
[nome do teste e classe]

O stack trace quando falha é:
[cole o stack trace]

Possíveis causas de testes intermitentes neste contexto:
- Timing issues em operações assíncronas
- Estado compartilhado entre testes
- Dependências de ordem

Quais causas são mais prováveis aqui e como você as diagnosticaria?
```

---

## Estratégia para cobrir um módulo novo rapidamente

Quando você tem um módulo sem testes e quer cobri-lo de forma eficiente:

1. **Modo de exploração** — entenda o módulo:
   ```
   Explique os casos de uso principais de @OrderProcessor.java.
   Liste os comportamentos que deveriam ser testados, ordenados por importância.
   ```

2. **Modo de exploração** — priorize:
   ```
   Dessa lista, quais 5 testes dariam mais confiança e cobrem mais casos?
   ```

3. **Edição direta** — implemente um a um:
   ```
   Peça ao Claude cada teste, revisando o diff:
   Escreva o teste para o caso: [o caso mais importante]
   ```

4. **Repita o passo 3** para o resto dos casos priorizados.

Este fluxo evita gerar um bloco enorme de testes de uma vez, que depois precisa ser revisado e corrigido em massa.

---

## Erros comuns a evitar

| Erro | Consequência | Como evitar |
|---|---|---|
| Pedir "gere todos os testes" sem contexto | Testes que não cobrem os paths de negócio importantes | Primeiro liste os casos no modo de exploração, depois gere |
| Não especificar o tipo de teste | Gera @SpringBootTest quando você queria unitário | Sempre especifique: "unitário com Mockito" ou "integração com Testcontainers" |
| Aceitar testes sem executá-los | Testes que não compilam ou sempre passam mesmo com o código quebrado | Execute sempre depois de gerar |
| Testes sem nome descritivo | Difícil entender o que falhou na CI | Peça explicitamente nomes no formato `should_<resultado>_when_<condição>` |

---

## Próximos passos

- [3.4 — Code Review](04-code-review.md)
- [3.1 — Backend Java/Spring](01-backend-java-kotlin-spring.md)

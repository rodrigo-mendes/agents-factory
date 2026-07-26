# Claude Code para Backend: Java/Kotlin/Spring

**Perfil:** Dev Backend  
**Stack coberto:** Java 17/21, Spring Boot, Spring Cloud Function, Maven  
**Tempo estimado de leitura:** 10 min

---

## Antes de começar

A Equipe de Governança BRX mantém pesquisas de referência do SDK Java em `StoryBeat/sdk_java/`. Quando você usar os subagentes ou o Claude Code para tarefas Java, pode referenciar esses docs para dar contexto adicional se o Claude precisar.

> Quando existir a skill Java da BRX (em `.claude/skills/`), o Claude Code a carregará automaticamente e você não precisará fazer isso manualmente.

---

## Casos de uso frequentes

### 1. Gerar um serviço novo

**Modo recomendado:** Subagente customizado (quando existir) / Claude Code com contexto de projeto

```
Crie um serviço Spring Boot `OrderNotificationService` que:
- Escuta mensagens SQS do tipo OrderCreated (estrutura em @dto/OrderCreatedEvent.java)
- Processa a mensagem e chama @EmailService.java para notificar o cliente
- Registra o resultado na tabela DynamoDB usando @NotificationRepository.java
- Inclui tratamento de erros com retry para falhas transitórias de e-mail

Siga o padrão dos serviços existentes em @src/services/.
```

**Dica:** referencie sempre os serviços ou classes existentes relacionados com `@`. O código do seu projeto é o melhor exemplo de convenções.

---

### 2. Adicionar tratamento de erros a um método existente

**Modo recomendado:** Edição direta (peça ao Claude e revise o diff)

```
[Abra o arquivo com o método no IDE e mencione-o com @, ou peça direto]
Adicione tratamento de erros ao método processMessage de @OrderNotificationService.java:
- SqsException: log ERROR com messageId, não relançar (mensagem processada como erro)
- DataAccessException: log ERROR com orderId, relançar como OrderProcessingException
- IllegalArgumentException: log WARN, relançar como is
```

O Claude Code aplica a edição no arquivo e mostra o diff; você aprova ou rejeita.

---

### 3. Escrever testes unitários

**Modo recomendado:** Edição direta ou Modo de exploração

```
Gere testes JUnit 5 com Mockito para @OrderNotificationService.java.
Cubra:
- Caminho feliz: mensagem válida, e-mail enviado, resultado persistido
- SqsException: log de erro, sem relançar
- EmailService indisponível: retry e log de warning
Use nomes de teste descritivos em português.
```

Ou, se quiser mais controle, peça no modo de exploração antes de gerar:
```
Gere os testes para @OrderNotificationService.java com JUnit 5 e Mockito.
Não use @SpringBootTest (testes unitários puros, sem contexto Spring).
Explique o que você vai cobrir antes de escrevê-los.
```

---

### 4. Entender código legado

**Modo recomendado:** Modo de exploração / Plan Mode

```
Explique o fluxo completo de @LegacyOrderProcessor.java.
Identifique:
1. Quais dados de entrada ele precisa
2. Quais efeitos colaterais produz (DB, mensagens, logs)
3. Quais casos de erro trata e quais não trata

Formato: lista numerada, no máximo 10 pontos.
```

Use o **Plan Mode** (Shift+Tab) para explorar em modo read-only, sem risco de alterar arquivos enquanto você entende o código.

---

### 5. Refatorar código para melhorar testabilidade

**Modo recomendado:** Modo de exploração primeiro → edição direta para cada mudança

```
[Modo de exploração]
O serviço @PaymentProcessor.java é difícil de testar porque tem dependências diretas.
Quais refatorações concretas o tornariam mais testável?
Me dê um plano de mudanças com o impacto de cada uma.
```

Depois, peça ao Claude para aplicar cada mudança proposta, revisando o diff a cada passo.

---

### 6. Revisar desempenho ou problemas de memória

**Modo recomendado:** Modo de exploração / Plan Mode

```
Analise @OrderRepository.java em busca de:
- N+1 queries potenciais
- Carga de coleções não lazy quando não é necessário
- Leituras que poderiam se beneficiar de cache

Para cada problema encontrado: descrição do problema, linha aproximada e fix proposto.
```

---

### 7. Migrar de uma versão a outra

**Modo recomendado:** Modo de exploração para planejar → Modo agente para executar

```
[Modo de exploração]
Quais breaking changes existem entre Spring Boot 3.1 e 3.3
que possam afetar um projeto que usa Spring Data JPA e Spring Cloud AWS?
Me dê apenas as mudanças relevantes para o nosso stack.
```

---

## Erros comuns a evitar

| Erro | O que acontece | Como evitar |
|---|---|---|
| Pedir testes sem especificar o tipo | O Claude gera @SpringBootTest pesados | Especifique "testes unitários com Mockito, sem contexto Spring" |
| Não referenciar classes relacionadas | O código gerado não encaixa com o existente | Use `@` para referenciar as classes que interagem |
| Aceitar código com imports incorretos | O código não compila | Revise sempre os imports no diff antes de aceitar |
| Pedir "refatore a classe toda" sem limites | O Claude muda coisas que não devia | Delimite: "refatore só o método X sem mudar a interface pública" |

---

## Sinais de que você precisa de um subagente, não do chat livre

- Você sempre acaba explicando os mesmos padrões BRX no prompt
- O código gerado não segue a estrutura de pacotes do projeto
- O Claude gera código que usa frameworks ou bibliotecas que não estão no seu `pom.xml`

Quando chegar o subagente backend BRX, ele resolverá esses problemas automaticamente.

---

## Próximos passos

- [3.2 — Infra com Terraform e AWS](02-infraestrutura-terraform-aws.md)
- [3.3 — QA e Testing](03-qa-testing.md)
- [Catálogo de agentes BRX](../modulo-1-agentes-customizados/05-catalogo-agentes-brx.md)

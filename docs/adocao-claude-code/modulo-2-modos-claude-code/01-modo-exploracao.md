# Modo de exploração / perguntas: explorar e entender

**Perfil:** Dev  
**Tempo estimado de leitura:** 6 min

---

## Para que serve o modo de exploração

O modo de exploração é o Claude Code trabalhando como parceiro de pensamento: você faz perguntas sobre o código, obtém explicações, explora opções de design e planeja mudanças sem que o Claude toque em nenhum arquivo.

É o modo certo quando você não quer que o Claude aja, mas que **pense junto com você**.

### Plan Mode: exploração read-only garantida

No Claude Code, a forma mais segura de explorar antes de agir é o **Plan Mode**. Pressione `Shift+Tab` para alternar para ele: nesse modo o Claude fica **read-only** — ele pode ler arquivos, buscar no projeto e propor um plano, mas **não edita nada nem executa comandos que modifiquem o estado**. Quando o plano estiver claro, você sai do Plan Mode e o Claude passa a executar.

Use o Plan Mode sempre que quiser entender ou planejar sem risco de que algo seja alterado.

---

## Como dar bom contexto ao explorar

### Referenciar arquivos com `@`

Não cole o código no chat. Use `@` para referenciar arquivos diretamente:

```
O que @OrderService.java faz e como ele se relaciona com @PaymentRepository.java?
```

O Claude Code lerá os arquivos sem que você precise copiá-los. Mais limpo e não enche a janela de contexto.

### Deixar o Claude explorar o projeto

Quando você não sabe exatamente quais arquivos são relevantes, basta descrever o que procura: o Claude Code busca sozinho pelo projeto (com Grep, Glob e leitura de arquivos). Para explorações mais amplas, ele pode até delegar a um **subagente Explore**, que varre muitos arquivos e retorna só a conclusão.

```
Onde a autenticação é gerenciada neste projeto?
```

### Apontar para o arquivo aberto no IDE

Se você está usando a extensão de VS Code ou JetBrains, o arquivo aberto e a seleção atual são enviados como contexto. Ainda assim, é uma boa prática mencionar o arquivo explicitamente com `@` para deixar claro qual é o foco.

---

## Padrões de uso frequentes na BRX

### Entender o código antes de modificá-lo

```
Explique o fluxo de @NotificationProcessor.java.
O que entra, o que é transformado e o que é produzido?
```

### Investigar antes de implementar

```
Quero adicionar retry logic a este serviço SQS.
Quais são as opções em Spring Cloud Function com AWS Lambda?
Me dê prós e contras de cada uma em no máximo 5 bullets.
```

### Analisar um erro

```
Tenho este erro no CloudWatch:
[cole o stack trace]
Qual é a causa mais provável e como diagnosticá-la?
```

### Revisar uma PR mentalmente antes de abri-la

```
Revise @OrderService.java com foco em:
1. Bugs potenciais
2. Problemas de segurança
Não comente estilo nem formatação.
```

### Planejar uma tarefa complexa

```
Preciso adicionar paginação à API /orders.
O endpoint atual está em @OrderController.java e usa @OrderRepository.java.
Quais mudanças eu precisaria e em que ordem?
```

> **Dica:** Use o Plan Mode (`Shift+Tab`) para planejar sem risco. Quando o plano estiver claro, saia do Plan Mode e deixe o Claude implementar, ou acione um subagente para a execução.

---

## Como pedir respostas úteis e concisas

Por padrão, as respostas podem ficar longas. Controle o formato com instruções explícitas:

```
Me dê a resposta em no máximo 5 bullets.
```
```
Só o código, sem explicação.
```
```
Uma tabela comparativa: opções nas linhas, critérios nas colunas.
```
```
Me dê primeiro a resposta direta e depois o raciocínio, caso eu queira aprofundar.
```

Isso é especialmente útil para análise de erros ou comparação de opções.

---

## Quando explorar não é suficiente

- Você quer que o Claude **edite código existente** → passe ao modo de edição
- Você quer que o Claude **implemente algo de ponta a ponta** → use o modo agente / um subagente
- O Claude dá respostas incorretas sobre o stack BRX → use um subagente ou comando slash customizado (ele tem as skills com os padrões corretos)

---

## Relação com a boa prática "Planeje antes de executar"

A exploração / o Plan Mode é a ferramenta natural para a fase de planejamento. Antes de pedir uma mudança concreta:

1. **Explorar:** `Qual é o impacto de modificar X?` `Quais arquivos esse fluxo toca?`
2. **Localizar:** `Onde está a lógica de validação de pedidos?`
3. **Planejar e revisar:** deixe o Claude propor um plano no Plan Mode e **revise-o antes de aprovar**
4. **Executar** com o modo de edição ou o modo agente, já com o plano validado

A ordem importa: revisar um plano é muito mais barato do que desfazer código já escrito. Veja as boas práticas transversais no Confluence: "Separe exploração de execução".

---

## Próximos passos

- [2.2 — Modo de edição: mudanças cirúrgicas](02-modo-edicao.md)
- [2.3 — Modo agente: tarefas multi-passo](03-modo-agente.md)

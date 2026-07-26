# O que é um agente customizado e como invocá-lo

**Perfil:** Dev  
**Tempo estimado de leitura:** 7 min

---

## O que é um agente customizado

Um agente customizado é uma versão do Claude Code que foi instruída especificamente para trabalhar com o stack, as convenções e os processos de BRX. No Claude Code, ele toma a forma de um **subagente** (definido em `.claude/agents/*.md`) e/ou de um **comando slash** customizado (definido em `.claude/commands/*.md`). Diferentemente do chat livre, um agente:

- **Verifica as convenções** do projeto antes de gerar código
- **Segue um processo em fases** (não responde de uma vez só)
- **Usa skills** (bases de conhecimento) com padrões específicos de BRX
- **Pede confirmação** antes de aplicar mudanças grandes

Tecnicamente, um agente customizado no Claude Code é um arquivo Markdown — por exemplo, o arquivo de um subagente de infraestrutura em `.claude/agents/<nome>.md` — que define o papel, as instruções e as ferramentas disponíveis para uma tarefa concreta. Ele é invocado por um comando slash `/<nome-do-agente>` ou selecionando o subagente na interface. O conjunto de agentes disponíveis depende do que a Equipe de Governança BRX publicou no workspace; você descobre os nomes reais digitando `/` no Claude Code ou listando `.claude/agents/` (e `.claude/commands/`).

---

## Diferença entre agente, chat livre e edições diretas

| | Chat livre | Edições diretas | Agente customizado |
|---|---|---|---|
| **Ativa com** | Rodar `claude` no terminal, sem invocar um subagente | Pedido de edição pontual em linguagem natural | `/<nome-do-agente>` (ou selecionar o subagente) |
| **Modifica arquivos** | Não (use o Plan Mode para explorar) | Sim, diretamente com diff | Sim, com planejamento prévio |
| **Conhece convenções BRX** | Só se você as incluir no prompt (ou via `CLAUDE.md`) | Só se estiverem no `CLAUDE.md` | Sim, carrega automaticamente |
| **Processo em fases** | Não | Não | Sim (P0-P5) |
| **Pede confirmação** | Não | Não (mostra diff para aprovar) | Sim, na fase P3 |
| **Melhor para** | Perguntas, exploração | Mudanças pontuais | Tarefas complexas de domínio |

---

## Como invocar um agente

### Opção 1: comando slash

1. Rode `claude` no terminal (ou abra o painel do Claude Code na extensão do IDE — VS Code ou JetBrains)
2. Digite `/` no campo de texto
3. Aparecerá uma lista com os comandos e subagentes disponíveis no seu projeto — esses são os **nomes reais** que você pode usar
4. Selecione o agente que você precisa
5. Adicione sua instrução depois: `/<nome-do-agente> <sua tarefa aqui>`

Nos exemplos abaixo usamos um agente de infraestrutura hipotético `agente-infra` (nome ILUSTRATIVO): substitua-o pelo nome real do seu workspace.

```
/agente-infra implementa uma função Lambda com trigger SQS e logs no CloudWatch
```

### Opção 2: pedir a delegação para o subagente

Você também pode descrever a tarefa em linguagem natural e pedir ao Claude Code para delegá-la ao subagente correspondente (por exemplo, "use o subagente de infraestrutura para..."). O Claude Code seleciona o subagente definido em `.claude/agents/` e executa a tarefa de forma isolada.

---

## O que acontece depois de invocar o agente

O agente não responde de imediato com código. Ele segue um processo estruturado:

1. **Carrega suas instruções e skills** (fase P0) — o Claude Code mostra as ferramentas de leitura sendo usadas
2. **Analisa o contexto atual** do projeto (fase P1)
3. **Consulta os padrões** da skill correspondente (fase P2)
4. **Propõe um plano** e pede sua confirmação (fase P3) ← aqui você deve responder
5. **Implementa** o que foi acordado (fase P4)
6. **Valida** o resultado (fase P5)

Para mais detalhes sobre o que significa cada fase da sua perspectiva, ver [guia 1.3](03-entender-resposta-workflow-p0-p5.md).

---

## O que escrever para o agente

O agente já conhece as convenções BRX, então **você não precisa explicar o stack**. Concentre-se em descrever o que você quer alcançar:

✅ Bom:
```
/agente-infra cria os recursos necessários para expor uma API REST privada com autenticação Cognito
```

❌ Redundante (o agente já sabe):
```
/agente-infra cria uma API usando AWS API Gateway com integração Lambda, 
seguindo as convenções de BRX com Terraform modulado e tags padrão...
```

Se você tem restrições específicas do seu contexto que o agente não consegue inferir do projeto, aí sim adicione-as:
```
/agente-infra cria um bucket S3 para armazenar logs. Restrição: deve usar a KMS key existente `alias/brx-logs-key`
```

---

## Quando não usar um agente customizado

- Para perguntas rápidas ou exploratórias → use o chat livre (modo de exploração / Plan Mode com Shift+Tab)
- Para editar um bloco de código concreto → peça uma edição pontual em linguagem natural
- Se o agente não cobre o seu domínio → use o chat livre com as instruções de contexto do seu projeto (`CLAUDE.md`)

Para a árvore de decisão completa, ver [guia 1.2](02-quando-usar-agente-vs-chat-livre.md).

---

## Próximos passos

- [1.2 — Quando usar agente vs chat livre](02-quando-usar-agente-vs-chat-livre.md)
- [1.3 — Entender a resposta do agente (P0-P5)](03-entender-resposta-workflow-p0-p5.md)
- [1.5 — Catálogo de agentes BRX](05-catalogo-agentes-brx.md)

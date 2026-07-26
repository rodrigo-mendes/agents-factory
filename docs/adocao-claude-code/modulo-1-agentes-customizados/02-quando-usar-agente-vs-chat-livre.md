# Quando usar um agente vs o chat livre

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 5 min

---

## A regra geral

Use um **agente customizado** quando a tarefa:
- Exige conhecer as convenções específicas de BRX para ser feita bem
- Implica gerar ou modificar múltiplos arquivos
- Tem um padrão reconhecível (provisionar infraestrutura, criar um serviço, gerar testes)

Use o **chat livre** quando:
- Você quer explorar, entender ou investigar algo
- A tarefa é uma mudança pontual em um arquivo concreto
- Não há um agente BRX para esse domínio

---

## Árvore de decisão

```
Qual é o objetivo da sua tarefa?
│
├── Entender / explorar / perguntar
│       └── → Chat livre (modo de exploração / Plan Mode)
│
├── Editar um bloco de código existente
│       └── → Edição direta (pedido pontual em linguagem natural)
│
└── Gerar ou modificar código/infra/testes de forma significativa
        │
        ├── Existe um agente BRX para este domínio? (ver catálogo 1.5)
        │       │
        │       ├── Sim → Agente customizado (/<nome-do-agente>)
        │       │
        │       └── Não → Chat livre + instruções de contexto do projeto (CLAUDE.md)
        │
        └── Precisa que o Claude Code conheça as convenções BRX sem que você as explique?
                │
                ├── Sim → Agente customizado (carrega skills automaticamente)
                │
                └── Não → Chat livre ou edição direta
```

---

## Casos de uso com recomendação

Nos exemplos abaixo, `/agente-infra` é um nome de agente de infraestrutura ILUSTRATIVO/hipotético — confirme o nome real digitando `/` no Claude Code.

| Tarefa | Recomendação | Por quê |
|---|---|---|
| "O que esta classe faz?" | Chat livre | Exploração, não gera código |
| "Explique os padrões de DDD no nosso projeto" | Chat livre com `@arquivo` | Investigação sobre contexto próprio |
| "Refatore este método para ficar mais legível" | Edição direta | Mudança pontual, sem convenções complexas |
| "Gere um teste unitário para este serviço" | Agente (se existir) / edição direta | Depende de haver agente de testing |
| "Provisione uma função Lambda com SQS" | Agente de infraestrutura `/agente-infra` | Tarefa de domínio com muitas convenções |
| "Revise este PR e diga que bugs há" | Chat livre (ou `/code-review`) | Análise, não gera código |
| "Implemente o endpoint POST /orders completo" | Agente de backend (se existir) | Multi-arquivo, convenções de API |
| "Como funciona o AWS EventBridge?" | Chat livre | Pergunta geral |
| "Crie os módulos Terraform para uma VPC" | Agente de infraestrutura `/agente-infra` | Tarefa de domínio estruturada |

---

## Sinais de que você está usando o modo errado

**Usando chat livre quando deveria usar um agente:**
- Você acaba copiando e colando muitas convenções BRX no prompt
- O código gerado não segue o estilo do projeto e você tem que corrigir muito
- Você faz a mesma tarefa com frequência e sempre explica a mesma coisa

**Usando um agente quando deveria usar chat livre:**
- O agente demora para arrancar porque está carregando skills que você não precisa
- Você só queria uma resposta rápida, não implementar nada
- O domínio da sua tarefa não está coberto por nenhum agente → o agente improvisa e dá resultados piores que o chat livre

---

## Uma regra fácil de lembrar

> **Planeje com o chat, execute com o agente.**

Use o chat (e o Plan Mode) para entender e **montar um plano**. Quando o plano estiver claro e revisado, e houver um agente BRX para a tarefa, mude para o agente para executar.

---

## Próximos passos

- [1.1 — Como invocar um agente](01-o-que-e-um-agente-customizado.md)
- [1.3 — Entender a resposta do agente](03-entender-resposta-workflow-p0-p5.md)
- [1.5 — Catálogo de agentes BRX](05-catalogo-agentes-brx.md)

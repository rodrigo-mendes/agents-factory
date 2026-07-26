# Módulo 1 — Usar Agentes Customizados

**Perfil:** Dev / Tech Lead  
**Pré-requisito:** [Módulo 0](../modulo-0-fundamentos/README.md)

Este módulo é para quem **usa** os agentes customizados de BRX, não para quem os cria. Se você quer criar ou modificar agentes, vá para o [Módulo 6](../modulo-6-contribuir-ecossistema/README.md) e para os guias técnicos do agents-factory.

---

## Conteúdo

1. [O que é um agente customizado e como invocá-lo](01-o-que-e-um-agente-customizado.md)
2. [Quando usar um agente vs o chat livre](02-quando-usar-agente-vs-chat-livre.md)
3. [Entender a resposta de um agente: o workflow P0-P5](03-entender-resposta-workflow-p0-p5.md)
4. [O que fazer quando o agente se desvia ou falha](04-quando-o-agente-falha.md)
5. [Catálogo de agentes BRX](05-catalogo-agentes-brx.md)

---

## Resumo rápido

| Pergunta | Resposta curta |
|---|---|
| Como eu invoco um agente? | No Claude Code, os subagentes BRX são invocados por um comando slash `/<nome-do-agente>` ou selecionando o subagente. Descubra os nomes reais digitando `/` no Claude Code. |
| Qual é a diferença para o chat normal? | O agente segue um processo estruturado e verifica as convenções BRX antes de gerar código. |
| Por que o agente pede confirmação no meio da tarefa? | Ele chega à fase P3 (Propor). É normal; você precisa confirmar para continuar. |
| O que faço se o agente gerar algo incorreto? | Interrompa, corrija o prompt e execute de novo. Ver guia 1.4. |
| Quais agentes estão disponíveis? | Ver catálogo no guia 1.5. |

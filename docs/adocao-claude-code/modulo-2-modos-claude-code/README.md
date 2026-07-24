# Módulo 2 — Modos do Claude Code e quando usá-los

**Perfil:** Dev  
**Pré-requisito:** [Módulo 0.1 — Modos, capacidades e limites](../modulo-0-fundamentos/01-claude-code-na-brx-modos-capacidades-limites.md)

Este módulo aprofunda as formas de trabalhar com o Claude Code, com exemplos reais do stack BRX.

---

## Conteúdo

1. [Modo de exploração: explorar e entender](01-modo-exploracao.md)
2. [Modo de edição: mudanças cirúrgicas em arquivos](02-modo-edicao.md)
3. [Modo agente: tarefas multi-passo com ferramentas](03-modo-agente.md)

---

## Quando usar cada modo — tabela de referência rápida

| Modo | Como usar | Modifica arquivos? | Melhor para |
|---|---|---|---|
| Exploração / perguntas | Perguntar no chat; **Plan Mode** com `Shift+Tab` (read-only) | Não | Perguntas, exploração, análise, planejamento |
| Edição | Descreva a mudança em linguagem natural, referenciando o arquivo com `@`; revise o diff | Sim (com diff) | Mudanças concretas e delimitadas |
| Agente | É o modo padrão do Claude Code; use um subagente ou comando slash customizado BRX para tarefas de domínio | Sim (autônomo) | Tarefas complexas multi-passo |

> No Claude Code esses "modos" não são telas separadas como no Copilot: são formas de conduzir o mesmo agente. O modo padrão já edita e executa comandos; o **Plan Mode** (`Shift+Tab`) restringe o Claude a apenas ler e planejar, sem tocar em nada.

---

## A regra de ouro

> **Planeje antes de executar.**

Para qualquer tarefa que não seja trivial, faça o Claude Code **produzir e mostrar um plano antes de tocar no código** — e só então execute. O caminho recomendado tem três passos:

1. **Planeje** — entre no **Plan Mode** (`Shift+Tab`). Nesse modo read-only o Claude lê o projeto, entende o que já existe e propõe um plano, sem modificar nada.
2. **Revise o plano** — confira se o plano faz sentido, ajuste ou corrija antes de qualquer alteração. É muito mais barato corrigir um plano do que desfazer código já escrito.
3. **Execute** — aprovado o plano, saia do Plan Mode e deixe o Claude implementar (edição direta ou modo agente), supervisionando o diff.

Entender o que já existe **antes** de mudar, e revisar o plano **antes** de executar, economiza muitas correções depois.

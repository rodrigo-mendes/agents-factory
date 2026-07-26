# Módulo 4 — Instruções de Contexto do Projeto

**Perfil:** Tech Lead  
**Pré-requisito:** [Módulo 0.2 — Mapa do ecossistema](../modulo-0-fundamentos/02-mapa-ecossistema-claude-code-brx.md)

As instruções de contexto são o mecanismo pelo qual uma equipe diz ao Claude Code "neste projeto, funciona assim". Sem elas, cada desenvolvedor tem que repetir o contexto do projeto em cada prompt.

---

## Conteúdo

1. [O que é o `CLAUDE.md`](01-o-que-e-claude-md.md)
2. [Adicionar instruções de contexto ao repositório da sua equipe](02-adicionar-instrucoes-ao-seu-repo.md)
3. [Skills globais vs instruções de projeto](03-skills-globais-vs-instrucoes-projeto.md)

---

## Resumo rápido

| Pergunta | Resposta curta |
|---|---|
| Para que serve? | Diz ao Claude Code quais convenções, frameworks e restrições o seu projeto tem, sem que cada dev precise repeti-las em cada prompt. |
| Quem cria? | O Tech Lead da equipe, com input do time. |
| Onde fica? | `CLAUDE.md` na raiz do repositório, ou `CLAUDE.md` aninhados em subpastas específicas. |
| Aplica-se sozinho? | Sim, o Claude Code lê o `CLAUDE.md` da raiz automaticamente ao iniciar, e os `CLAUDE.md` de subpastas quando trabalha nelas. |
| Qual a diferença para as skills? | As instruções são do projeto (curtas, operacionais). As skills são globais da BRX (detalhadas, com padrões técnicos profundos). |

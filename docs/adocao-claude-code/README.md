# Programa de Adoção do Claude Code — BRX

Guias para equipes de desenvolvimento que usam **Claude Code** com agentes e skills customizados no BRX Retail.

Esta coleção cobre três perfis:

- **Dev** — desenvolvedores que usam o Claude Code no dia a dia
- **Tech Lead** — responsáveis por configurar o ecossistema Claude Code da equipe
- **Governança BRX** — equipe que administra o programa e os artefatos globais

> **O que é o Claude Code?** É o agente de IA da Anthropic que roda no **terminal** (CLI `claude`), com extensões para **VS Code** e **JetBrains** e versão **web** em claude.ai/code. Diferente de um autocomplete, ele planeja e executa tarefas de várias etapas: lê e edita arquivos, roda comandos, valida resultados e itera — sempre sob sua supervisão e aprovação.

---

## Por onde começar

### Se você é novo no Claude Code
1. [Módulo 0.3 — Setup do ambiente: dia 1](modulo-0-fundamentos/03-setup-ambiente-dia-1.md)
2. [Módulo 0.1 — Modos, capacidades e limites](modulo-0-fundamentos/01-claude-code-na-brx-modos-capacidades-limites.md)
3. [Módulo 1.1 — O que é um agente customizado](modulo-1-agentes-customizados/01-o-que-e-um-agente-customizado.md)

### Se você já usa o Claude Code e quer aproveitar os agentes BRX
1. [Módulo 0.2 — Mapa do ecossistema](modulo-0-fundamentos/02-mapa-ecossistema-claude-code-brx.md)
2. [Módulo 1.5 — Catálogo de agentes BRX](modulo-1-agentes-customizados/05-catalogo-agentes-brx.md)
3. [Módulo 1.2 — Quando usar agente vs chat livre](modulo-1-agentes-customizados/02-quando-usar-agente-vs-chat-livre.md)

### Se você é Tech Lead configurando o ecossistema da sua equipe
1. [Módulo 4.1 — O que é o `CLAUDE.md`](modulo-4-instrucoes-contexto/01-o-que-e-claude-md.md)
2. [Módulo 4.2 — Adicionar instruções ao seu repositório](modulo-4-instrucoes-contexto/02-adicionar-instrucoes-ao-seu-repo.md)
3. [Módulo 6.1 — Solicitar um novo agente ou skill](modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md)

---

## Módulos

| Módulo | Perfil | Conteúdo |
|---|---|---|
| [0 — Fundamentos](modulo-0-fundamentos/README.md) | Todos | Modos do Claude Code, ecossistema BRX, setup dia 1 |
| [1 — Agentes Customizados](modulo-1-agentes-customizados/README.md) | Dev / Tech Lead | Invocar, entender e depurar agentes; catálogo |
| [2 — Modos do Claude Code](modulo-2-modos-claude-code/README.md) | Dev | Exploração/Plan Mode, edição direta e modo agente com exemplos reais |
| [3 — Guias por Papel](modulo-3-guias-por-papel/README.md) | Dev | Java/Kotlin, Terraform/AWS, QA, Code Review |
| [4 — Instruções de Contexto](modulo-4-instrucoes-contexto/README.md) | Tech Lead | `CLAUDE.md`, skills globais vs projeto |
| [5 — Segurança e Governança](modulo-5-seguranca-governanca/README.md) | Todos | O que não compartilhar, revisão humana, licenças, métricas |
| [6 — Contribuir ao Ecossistema](modulo-6-contribuir-ecossistema/README.md) | Dev avançado / Gov | Solicitar agentes, ciclo de vida de skills, post-mortems |

---

## Vocabulário rápido: do GitHub Copilot ao Claude Code

Se você vem do GitHub Copilot, esta tabela ajuda a traduzir os conceitos:

| No Copilot | No Claude Code |
|---|---|
| Ask mode (chat) | Modo de exploração / **Plan Mode** (Shift+Tab), read-only |
| Edit mode (`Ctrl+I`) | Edição direta: você pede, o Claude mostra o **diff** e você aprova |
| Agent mode | **Modo agente** — o modo padrão do Claude Code no terminal |
| Agentes customizados `@nome` | **Subagentes** (`.claude/agents/`) e **comandos slash** (`.claude/skills/<nome>/SKILL.md`, com `context: fork` no frontmatter) |
| Skills (`.github/skills/`) | **Skills** (`.claude/skills/`) — conceito nativo |
| `copilot-instructions.md` | **`CLAUDE.md`** (raiz e subpastas) |
| Referência `#arquivo` | Referência `@arquivo` |
| `settings.json` do VS Code | `.claude/settings.json` (projeto) e `~/.claude/settings.json` (usuário) |

---

## Relação com os guias existentes

Estes guias **complementam** os materiais de boas práticas já publicados no Confluence:

| Já publicado | Onde ampliar aqui |
|---|---|
| Como conversar com o assistente | Módulo 1.1, Módulo 2 |
| Quando começar uma conversa nova (`/clear`) | Módulo 1.3 |
| Boas práticas transversais | Módulo 4, Módulo 5 |
| Separe exploração de execução | Módulo 2 — **planeje antes de executar** com o Plan Mode (`Shift+Tab`) |
| Minimize contexto repetido | Módulo 4.3 |

---

**Mantido por:** Equipe de Governança BRX · Repositório `agents-factory`

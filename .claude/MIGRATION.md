# Migração GitHub Copilot → Claude Code — Notas & Decommission

Estado: **`.claude/` criado ao lado de `.github/` (coexistência)**. O Copilot continua funcional;
o decommission é uma fase final, executada **só após validação em uso real**.

## O que foi migrado

| Item | Resultado |
|---|---|
| `CLAUDE.md` (raiz) | novo — princípios, convenções, tabela de roteamento, dual-target |
| Subagentes | 4 reais em `.claude/agents/` (framework-researcher, skill-author, architecture-auditor, quality-validator) |
| Prompts operacionais | 23 → `.claude/skills/<n>/SKILL.md` (`context: fork` + `agent:` + `disable-model-invocation: true`) |
| Meta-skills | 2 → `.claude/skills/` (wording neutralizado) |
| Rules | `skill-frontmatter` (ativa, `paths:`) + templates de instructions → `templates/rules/` |
| Templates/examples | variantes Claude Code (tools traduzidos, `applyTo:`→`paths:`, `.agent.md`/`.instructions.md`→`.md`) |
| settings/gitignore | `.claude/settings.json` (permissões) + `.gitignore` (arquivos locais, `StoryBeat/`) |

## Melhorias aplicadas
1. **4 subagentes reais** com least-privilege e gatilho "Use when…" (não existiam).
2. **WebSearch/WebFetch** no `framework-researcher` → anti-alucinação real (antes dependia do usuário colar docs).
3. **Auditoria multi-modelo como orquestração paralela nativa**: `architecture-auditor` recebe a tool `Agent`
   e dispara scope/flow/engine em paralelo, sintetizando consenso (antes era só instrução em texto).
4. **`disable-model-invocation: true`** nos 23 comandos → custo de auto-listagem ~zero; só as 2 meta-skills auto-invocáveis.
5. **Frontmatter corrigido** em ~10 prompts que não tinham `name`/`description` válidos.

## Fase 2 — limpeza & progressive disclosure (feita)
- **Progressive disclosure** aplicada nas 6 skills > 500 linhas (conteúdo movido verbatim para `blueprints/`,
  SKILL.md com resumo + link no ponto de uso):
  | Skill | Antes → depois | Blueprints |
  |---|---|---|
  | `technical-framework-researcher-terraform` | 1051 → 434 | 7 |
  | `terraform-engineering-best-practices-researcher` | 766 → 189 | 5 |
  | `cloud-architecture-researcher` | 610 → 198 | 2 |
  | `audit-architecture-scope` | 605 → 336 | 2 |
  | `terraform-instructions-compiler` | 599 → 247 | 2 |
  | `architecture-approaches-skill-generator` | 587 → 309 | 1 |
  Todas < 500 linhas; 0 links quebrados; frontmatter inalterado.
- **`examples/` removido** das duas árvores (`.claude/templates/`, `.github/templates/`) — 71% da árvore,
  OCI/Terraform hardcoded. READMEs passam a apontar para os artefatos vivos (`.claude/agents/`, `.claude/skills/`).
- **Banner tecnologia-agnóstico** adicionado aos 26 `TEMPLATE.*` (13 em cada árvore).

## Validação por dogfooding (feita)
Rodados os próprios validadores/auditor da fábrica contra `.claude/`:
- **architecture-auditor** (consenso scope+flow+engine): **PASS 9.4/10**, 0 P0/P1. Contagens todas confirmadas
  (4 subagentes, 25 skills, 23 comandos, 0 refs `agent:` quebradas, 0 órfãos).
- **quality-validator** (skill-best-practices + agent-router): 0 P0. Os 8 P1 apontaram **resíduo Copilot no corpo**
  das skills de auditoria/validação (instruções de runtime lendo `.github/agents/*.agent.md`,
  `.github/copilot-instructions.md`, `*.prompt.md`, `.github/instructions/`). **Corrigidos**: agora apontam para
  `.claude/agents/*.md`, `CLAUDE.md`, `.claude/skills/*/SKILL.md`, `.claude/rules/` (validators/compiler ficaram
  dual-target). Também: `skill-author` ganhou `model: sonnet`; links de exemplo Copilot em skill-creator/
  authoring-agent-skills/researching-technical-frameworks corrigidos para `.claude/rules|skills`.

## Follow-ups opcionais (não bloqueiam)
- **Vocabulário conceitual Copilot** ainda presente nos rubrics de auditoria (rótulos "Layer L0–L4", `.agent.md`
  em tabelas de critério, `report-template.md`) — é o modelo conceitual, não caminho de runtime; reescrever
  para vocabulário Claude Code é doc-only (R1).
- **Typo** `architecture-approaches-skill-generator` → renomear muda o nome do comando `/...`; decidir em separado.
- **Variáveis de prompt** (`{{VAR}}`, seções INPUT VARIABLES) foram preservadas; o subagente as coleta.
  Onde fizer sentido um argumento único, usar `$ARGUMENTS`/`$1`.

## Verificação já feita (estrutural)
`scratchpad/verify.py`: 4 agents · 21 skills · 1 rule · 0 refs quebradas · 0 `runSubagent`/`list_dir` ·
`name`=pasta em todas · `agent:` aponta para subagente existente · YAML sem `:` não-citado.

## Verificação funcional pendente (interativa, no Claude Code)
- `/memory` → confirmar que `CLAUDE.md` carrega.
- `/technical-framework-researcher <tech> <versão>` → roda via `framework-researcher`, usa WebFetch.
- `/skill-creator` → roda via `skill-author`.
- `/audit-architecture-consensus <alvo>` → dispara os 3 subagentes em paralelo.
- `/skill-best-practices-validator .claude/skills/` → relatório de qualidade.

## Decommission do Copilot (fase FINAL — NÃO executar agora)
Rodar como PR próprio, após a equipe validar `.claude/` em uso real:
1. Remover `.github/prompts/`, `.github/skills/` (e `.github/agents/` se existir).
2. Ajustar `README.md` e `docs/adopcion/` (programa Copilot) para refletir Claude-Code-only, ou arquivá-los.
3. **Manter** `.github/workflows/` (CI) e qualquer coisa não relacionada ao Copilot.
4. Remover a linha `ask: Write(./.github/**)` de `.claude/settings.json` (não haverá mais o quê proteger).
5. Rodar `scratchpad/verify.py` novamente e confirmar contagens.

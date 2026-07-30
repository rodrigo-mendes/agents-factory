# Guia: Validando Artefatos

Como usar os prompts de validação para garantir qualidade dos artefatos.

---

## Quando Usar

- Após criar/modificar qualquer artefato
- Antes de commit/PR
- Em revisões periódicas de qualidade
- Quando algo "não funciona" e você não sabe por quê

## Escolha o Validator Certo

| O que você tem | Validator |
|---------------|-----------|
| Qualquer artefato (agente, comando, etc.) | `copilot-compatibility-review` |
| Arquivo de rules (`.claude/rules/`) | `instructions-best-practices-validator` |
| Arquivo `SKILL.md` | `skill-best-practices-validator` |
| Projeto de agente completo | `project-analysis-validator .claude/` |
| Estrutura de routing | `agent-router-pattern-validator` |
| Arquitetura completa — projeto `.claude/` | `audit-cc-architecture-consensus` |
| Arquitetura completa — projeto `.github/` | `audit-architecture-consensus` |

## Pipeline Recomendado

Para validação completa, execute nesta ordem:

### Step 1: Compatibilidade técnica
```
/copilot-compatibility-review
```
> Verifica se o YAML é válido, campos estão corretos, limites respeitados.

### Step 2: Qualidade de conteúdo
```
/instructions-best-practices-validator
/skill-best-practices-validator
```
> Verifica se o conteúdo segue best practices (estrutura, clareza, completude).

### Step 3: Qualidade de projeto
```
/project-analysis-validator .claude/
```
> Visão holística: estrutura de diretórios, precisão do CLAUDE.md, consistência do router,
> frontmatter, naming, progressive disclosure e cobertura de rules.

### Step 4 (opcional): Auditoria arquitetural

Para projetos **Claude Code** (`.claude/`):
```
/audit-cc-architecture-consensus
```

Para projetos **GitHub Copilot** (`.github/`):
```
/audit-architecture-consensus
```

> Análise multi-modelo completa (scope + flow + engine). Corre 3 lentes em paralelo e prioriza
> findings por consenso: 3/3 = Must-Fix 🔴, 2/3 = Should-Fix 🟡, 1/3 = Consider 🟢.

---

## Quando Usar Cada Nível

| Cenário | Até que step |
|---------|:---:|
| Editei um arquivo | Step 1 |
| Criei skill nova | Steps 1-2 |
| Criei projeto novo | Steps 1-3 |
| Pre-release / produção | Steps 1-4 |
| Debug ("por que não funciona?") | Steps 1 + 4 (engine) |

---

## O que Cada Validator Detecta

### copilot-compatibility-review
- ❌ YAML malformado
- ❌ Campo `name` > 64 caracteres
- ❌ Campo `description` > 1024 caracteres
- ❌ `tools` inválido
- ❌ `applyTo` com glob inválido

### instructions-best-practices-validator
- ❌ Instructions sem escopo claro
- ❌ Contradições entre instructions
- ❌ Informação duplicada
- ❌ Escopo muito amplo ou restrito

### skill-best-practices-validator
- ❌ Falta seção ✅ ou 🚫
- ❌ ✅ sem código de exemplo
- ❌ 🚫 sem alternativa
- ❌ Versões misturadas
- ❌ Falta blueprints/

### project-analysis-validator .claude/
- ❌ Estrutura de diretórios fora do padrão `.claude/`
- ❌ CLAUDE.md impreciso ou desatualizado
- ❌ Inconsistências na routing table do agente
- ❌ Frontmatter inválido ou ausente
- ❌ Nomes de artefatos fora da convenção kebab-case
- ❌ Progressive disclosure violada (conteúdo inline em vez de blueprints)
- ❌ Cobertura de rules incompleta para o domínio
- ❌ Componentes órfãos (nunca referenciados)
- ❌ Referências quebradas (aponta para arquivo inexistente)

---

## Dicas

- **Comece sempre pelo Step 1**: Problemas de YAML/compatibilidade causam erros silenciosos — o Claude Code pode ignorar o arquivo sem avisar.
- **Não ignore warnings**: Warnings de hoje viram bugs de amanhã.
- **Valide iterativamente**: Corrija → re-valide → corrija → re-valide até limpo.

## Armadilhas Comuns

| Armadilha | Solução |
|-----------|---------|
| Não validar nunca | Incluir validação no workflow antes de commit |
| Só validar no final | Validar após cada artefato criado |
| Ignorar relatório "tudo OK" em projeto incompleto | "OK" significa conforme padrão, não significa completo |
| Confiar só no validator sem revisar manualmente | Validators detectam estrutura, não semântica |

## Fluxo Completo

Ver: [Fluxo de Qualidade](../fluxos/fluxo-qualidade.md)

# Guia: Validando Artefatos

Como usar os prompts de validação para garantir qualidade dos artefatos.

---

## Quando Usar

- Após criar/modificar qualquer artefato Copilot
- Antes de commit/PR
- Em revisões periódicas de qualidade
- Quando algo "não funciona" e você não sabe por quê

## Escolha o Validator Certo

| O que você tem | Validator |
|---------------|-----------|
| Qualquer artefato (.agent.md, .prompt.md, etc.) | `copilot-compatibility-review` |
| Arquivo `.instructions.md` | `instructions-best-practices-validator` |
| Arquivo `SKILL.md` | `skill-best-practices-validator` |
| Projeto de agente completo | `project-analysis-validator` |
| Estrutura de routing | `agent-router-pattern-validator` |
| Arquitetura completa | `audit-architecture-consensus` |

## Pipeline Recomendado

Para validação completa, execute nesta ordem:

### Step 1: Compatibilidade técnica
```
@workspace /copilot-compatibility-review
```
> Verifica se o YAML é válido, campos estão corretos, limites respeitados.

### Step 2: Qualidade de conteúdo
```
@workspace /instructions-best-practices-validator
@workspace /skill-best-practices-validator
```
> Verifica se o conteúdo segue best practices (estrutura, clareza, completude).

### Step 3: Qualidade de projeto
```
@workspace /project-analysis-validator
```
> Visão holística: consistência entre artefatos, cobertura, dead-ends.

### Step 4 (opcional): Auditoria arquitetural
```
@workspace /audit-architecture-consensus
```
> Análise multi-modelo completa (scope + flow + engine).

---

## Quando Usar Cada Nível

| Cenário | Até que step |
|---------|:---:|
| Editei um arquivo | Step 1 |
| Criei skill nova | Steps 1-2 |
| Criei projeto novo (pós-bootstrap) | Steps 1-3 |
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

### project-analysis-validator
- ❌ Componentes órfãos (nunca referenciados)
- ❌ Referências quebradas (aponta para arquivo inexistente)
- ❌ Dead-ends (cadeia incompleta)
- ❌ Falta de cobertura de domínio

---

## Dicas

- **Comece sempre pelo Step 1**: Problemas de YAML/compatibilidade causam erros silenciosos — o Copilot simplesmente ignora o arquivo sem avisar.
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

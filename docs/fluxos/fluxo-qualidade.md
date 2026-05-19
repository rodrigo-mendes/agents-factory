# Fluxo: Qualidade

Pipeline de validação completa para garantir qualidade de artefatos e projetos.

---

## Diagrama

```mermaid
flowchart TD
    START([Artefato/Projeto a validar]) --> S1[Step 1: copilot-compatibility-review<br/>Compatibilidade técnica]
    
    S1 -->|❌ incompatível| FIX1[Corrigir YAML/frontmatter]
    FIX1 --> S1
    
    S1 -->|✅ compatível| S2{Tipo de artefato?}
    
    S2 -->|.instructions.md| S2A[Step 2a: instructions-best-practices-validator]
    S2 -->|SKILL.md| S2B[Step 2b: skill-best-practices-validator]
    S2 -->|Ambos| S2C[Executar 2a + 2b]
    
    S2A --> S3
    S2B --> S3
    S2C --> S3
    
    S3[Step 3: project-analysis-validator<br/>Qualidade holística] -->|issues| FIX3[Melhorar]
    FIX3 --> S3
    
    S3 -->|✅ OK| S4{Auditoria<br/>necessária?}
    
    S4 -->|Sim - pre-release| S5[Step 4: audit-architecture-consensus<br/>Auditoria 3 modelos]
    S4 -->|Não - check rotineiro| DONE([✅ Qualidade OK])
    
    S5 -->|issues| FIX5[Remediar]
    FIX5 --> S5
    
    S5 -->|✅ aprovado| DONE
```

---

## Etapas Detalhadas

### Step 1: Compatibilidade Técnica

**Prompt**: `@workspace /copilot-compatibility-review`

**O que verifica**:
- YAML frontmatter válido
- Campos dentro dos limites (name ≤64, description ≤1024)
- Tools declarados corretamente
- applyTo com globs válidos

**Por que primeiro**: Se o YAML está malformado, o Copilot ignora o arquivo silenciosamente. Nada mais importa se isso falhar.

---

### Step 2: Qualidade de Conteúdo

#### 2a: Instructions
**Prompt**: `@workspace /instructions-best-practices-validator`

**O que verifica**:
- Clareza e concisão
- Escopo adequado
- Sem contradições
- Padrões de naming

#### 2b: Skills
**Prompt**: `@workspace /skill-best-practices-validator`

**O que verifica**:
- Three-tier completo (✅⚠️🚫)
- Código em todos os ✅
- Alternativas em todos os 🚫
- Version absolutism
- Blueprints presentes

---

### Step 3: Qualidade de Projeto

**Prompt**: `@workspace /project-analysis-validator`

**O que verifica**:
- Consistência entre artefatos
- Referências íntegras (nada aponta para inexistente)
- Cobertura de domínio
- Sem componentes órfãos

---

### Step 4 (opcional): Auditoria Arquitetural

**Prompt**: `@workspace /audit-architecture-consensus`

**O que verifica**:
- Hierarquia de responsabilidades (Modelo A)
- Cadeias de invocação (Modelo B)
- Mecânicas VS Code (Modelo C)
- Consenso priorizado

**Quando incluir Step 4**:
- Antes de release/produção
- Após mudanças estruturais significativas
- Quando algo não funciona e Steps 1-3 não acharam

---

## Níveis de Validação

| Cenário | Steps | Tempo estimado |
|---------|:-----:|:-:|
| Quick check (editei 1 arquivo) | 1 | ~1 min |
| Nova skill criada | 1-2b | ~3 min |
| Novas instructions | 1-2a | ~3 min |
| Projeto pós-bootstrap | 1-3 | ~5 min |
| Pre-release completo | 1-4 | ~10 min |

---

## Capacidades Envolvidas

| Step | Capacidade | Foco |
|:----:|-----------|------|
| 1 | `copilot-compatibility-review` | Técnico (YAML, limites) |
| 2a | `instructions-best-practices-validator` | Conteúdo (instructions) |
| 2b | `skill-best-practices-validator` | Conteúdo (skills) |
| 3 | `project-analysis-validator` | Holístico (projeto) |
| 4 | `audit-architecture-consensus` | Arquitetural (3 modelos) |

---

## Checklist Rápido

Antes de commit, pergunte:

- [ ] YAML válido? (Step 1)
- [ ] Conteúdo segue best practices? (Step 2)
- [ ] Projeto é consistente? (Step 3)
- [ ] Arquitetura é sólida? (Step 4 — se aplicável)

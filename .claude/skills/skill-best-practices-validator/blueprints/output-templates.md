# Output Templates — skill-best-practices-validator

Copy these structures verbatim when generating validation output. Two artifacts:
the **per-skill review file** and the **consolidated summary**.

## Contents

- [Per-skill review file](#per-skill-review-file)
- [Consolidated summary](#consolidated-summary)

---

## Per-skill review file

Write one per evaluated skill at `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`:

```markdown
# Análisis de Mejores Prácticas: [skill-name]

**Fecha**: [Fecha]
**Archivo**: `.claude/skills/[skill-name]/SKILL.md`
**Líneas**: [N]
**Referencia Oficial**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
**Referencia Equipo**: .claude/skills/authoring-agent-skills/SKILL.md

---

## Resumen

- Criterios oficiales cumplidos: [X]/8
- Convenciones de equipo cumplidas: [X]/7
- Problemas críticos: [N]

---

## Criterios Oficiales (Claude Best Practices)

| Criterio | Estado | Notas |
|----------|--------|-------|
| A1. YAML Frontmatter | ✅/❌ | [detalle] |
| A2. Concisión (<500 líneas) | ✅/❌ | [detalle] |
| A3. Disclosure Progresivo | ✅/❌ | [detalle] |
| A4. Contenido (terminología, temporal) | ✅/❌ | [detalle] |
| A5. Workflows claros | ✅/❌ | [detalle] |
| A6. Rutas de archivo | ✅/❌ | [detalle] |
| B. Código y Scripts | ✅/❌/N/A | [detalle] |
| C. Testing/Evaluación | ✅/❌ | [detalle] |

## Convenciones del Equipo

| Criterio | Estado | Notas |
|----------|--------|-------|
| D1. Naming (gerundio, kebab) | ✅/❌ | [detalle] |
| D2. Tres niveles (✅⚠️🚫) | ✅/❌ | [detalle] |
| D3. Version Context | ✅/❌ | [detalle] |
| D4. Verification Loop | ✅/❌ | [detalle] |
| D5. Anti-patrones con alternativas | ✅/❌ | [detalle] |
| D6. Links funcionales | ✅/❌ | [detalle] |
| D7. Recursos externos | ✅/❌ | [detalle] |

---

## Recomendaciones por Prioridad

### ALTA (Bloquean Funcionalidad)
[Lista — ej: YAML inválido, description vacía, body >500 líneas]

### MEDIA (Reducen Calidad)
[Lista — ej: terminología inconsistente, links rotos, sin feedback loops]

### BAJA (Optimización)
[Lista — ej: disclosure progresivo puede mejorar, naming no usa gerundio]

---

## Conclusiones
[Resumen de issues y fortalezas]
```

---

## Consolidated summary

After all individual files, write `.claude/skills/skills-best-practices-summary.md`:

```markdown
# Resumen de Mejores Prácticas — Agent Skills

**Fecha**: [Fecha]
**Referencia Oficial**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

---

## Resumen Ejecutivo

- Skills evaluados: [N]
- Cumplen criterios oficiales: [N] ([X]%)
- Cumplen convenciones de equipo: [N] ([X]%)
- Problemas críticos: [N]

---

## Matriz de Cumplimiento

| Skill | Oficial (A-C) | Equipo (D) | Total | Review |
|-------|---------------|------------|-------|--------|
| [skill-1] | [X]/8 | [X]/7 | [X]% | [skill-1-best-practices-review.md](skill-1/skill-1-best-practices-review.md) |
| [skill-2] | [X]/8 | [X]/7 | [X]% | [skill-2-best-practices-review.md](skill-2/skill-2-best-practices-review.md) |
| PROMEDIO | [X]/8 | [X]/7 | [X]% | — |

---

## Recomendaciones Globales por Prioridad

### ALTA (Bloquean Funcionalidad)
[Lista consolidada]

### MEDIA (Reducen Calidad)
[Lista consolidada]

### BAJA (Optimización)
[Lista consolidada]
```

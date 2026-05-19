---
name: skill-best-practices-validator
description: Genera análisis de calidad y adherencia a mejores prácticas de Agent Skills basado en Claude best practices oficiales y convenciones del equipo
argument-hint: directorio de skills
---

# Prompt: Validador de Mejores Prácticas para Agent Skills

## Objetivo
Generar un análisis de calidad y adherencia a mejores prácticas de Agent Skills basado en:
- **Oficial**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Equipo**: `.github/skills/authoring-agent-skills/SKILL.md`

## Instrucciones para Agente

Actúa como un Agent Skills Quality Specialist. Evalúa cada skill contra los criterios oficiales de Claude y las convenciones del equipo documentadas en `authoring-agent-skills`.

### Paso 1: Cargar Criterios de Referencia

Lee los siguientes archivos antes de evaluar:
1. `.github/skills/authoring-agent-skills/SKILL.md` — Estándar del equipo
2. `.github/skills/authoring-agent-skills/blueprints/three-tier-architecture.md` — Arquitectura de tres niveles

### Paso 2: Descubrir y Analizar Skills

Explora `.github/skills/*/SKILL.md` y evalúa cada skill según los criterios abajo.

---

## Criterios de Evaluación

### A. Calidad Core (Oficial — de Claude Best Practices)

**A1. YAML Frontmatter**
- `name`: max 64 chars, solo minúsculas/números/guiones, sin XML tags, sin palabras reservadas (`anthropic`, `claude`)
- `description`: no vacío, max 1024 chars, sin XML tags
- Descripción en **tercera persona** (no "I can help" ni "You can use")
- Incluye QUÉ hace Y CUÁNDO usarlo

**A2. Concisión**
- SKILL.md body bajo 500 líneas
- Solo agrega contexto que Claude no conoce
- Sin explicaciones innecesarias

**A3. Estructura y Disclosure Progresivo**
- Detalles adicionales en archivos separados (si necesario)
- Referencias a archivos: máximo un nivel de profundidad desde SKILL.md
- Archivos de referencia >100 líneas incluyen tabla de contenido
- Nombres de archivos descriptivos (`form_validation_rules.md`, no `doc2.md`)

**A4. Contenido**
- Sin información sensible al tiempo (o en sección "old patterns")
- Terminología consistente (no mezclar "API endpoint", "URL", "route")
- Ejemplos concretos, no abstractos
- No ofrecer demasiadas opciones — proporcionar un default + escape hatch

**A5. Workflows**
- Operaciones complejas tienen pasos secuenciales claros
- Feedback loops presentes para tareas críticas (ejecutar → validar → corregir → repetir)

**A6. Rutas de Archivo**
- Solo forward slashes (`scripts/helper.py`, no `scripts\helper.py`)
- Solo rutas relativas o URLs completas (nunca `C:\Users\...` o `/home/user/...`)

### B. Código y Scripts (Oficial)

**B1. Scripts resuelven problemas** — no delegan al agente lo que un script puede resolver
**B2. Manejo de errores explícito** — scripts no fallan silenciosamente
**B3. Sin "constantes mágicas"** — todos los valores documentados/justificados
**B4. Dependencias listadas** — paquetes requeridos documentados
**B5. Validación** — pasos de verificación para operaciones críticas

### C. Testing (Oficial)

**C1.** Al menos 3 escenarios de evaluación creados
**C2.** Probado con escenarios de uso real
**C3.** Feedback del equipo incorporado (si aplica)

### D. Convenciones del Equipo

**D1. Naming**: YAML `name` = nombre de carpeta = kebab-case (forma gerundio preferida)
**D2. Tres niveles**: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do — todos presentes y poblados
**D3. Version Context**: Sección incluida (si el skill es específico de versión)
**D4. Verification Loop**: Comandos presentes y testeados
**D5. Anti-patrones**: Código incorrecto + alternativa correcta lado a lado
**D6. Links**: Todos funcionales, sin 404s
**D7. Recursos externos**: Links a documentación oficial

---

### Paso 3: Generar Informe de Validación

Crea un archivo `SKILL_BEST_PRACTICES_REVIEW.md` con la siguiente estructura:

```markdown
# Análisis de Mejores Prácticas para Agent Skills

**Fecha**: [Fecha]
**Referencia Oficial**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
**Referencia Equipo**: .github/skills/authoring-agent-skills/SKILL.md

---

## Resumen Ejecutivo

- Skills evaluados: [N]
- Cumplen criterios oficiales: [N] ([X]%)
- Cumplen convenciones de equipo: [N] ([X]%)
- Problemas críticos: [N]

---

## Evaluación por Skill

### Skill: [nombre-skill]
**Archivo**: `.github/skills/[nombre-skill]/SKILL.md`
**Líneas**: [N]

#### Criterios Oficiales (Claude Best Practices)
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

#### Convenciones del Equipo
| Criterio | Estado | Notas |
|----------|--------|-------|
| D1. Naming (gerundio, kebab) | ✅/❌ | [detalle] |
| D2. Tres niveles (✅⚠️🚫) | ✅/❌ | [detalle] |
| D3. Version Context | ✅/❌ | [detalle] |
| D4. Verification Loop | ✅/❌ | [detalle] |
| D5. Anti-patrones con alternativas | ✅/❌ | [detalle] |
| D6. Links funcionales | ✅/❌ | [detalle] |
| D7. Recursos externos | ✅/❌ | [detalle] |

**Hallazgos principales**: [Resumen de issues y fortalezas]

---

## Matriz de Cumplimiento

| Skill | Oficial (A-C) | Equipo (D) | Total |
|-------|---------------|------------|-------|
| [skill-1] | [X]/9 | [X]/7 | [X]% |
| [skill-2] | [X]/9 | [X]/7 | [X]% |
| PROMEDIO | [X]/9 | [X]/7 | [X]% |

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
[Resumen general y próximas acciones]
```

---

## Detección de Anti-Patrones

El validador debe detectar y reportar:

1. **SKILL.md excede 500 líneas** — Recomendar extraer contenido a `blueprints/`
2. **Descripción vaga o en primera persona** — Ejemplo: "Helps with docs" o "I can process files" → Corregir a tercera persona con trigger
3. **Rutas Windows-style** — `scripts\helper.py` → `scripts/helper.py`
4. **Referencias anidadas profundas** — SKILL.md → A.md → B.md → C.md → Aplanar a un nivel
5. **Demasiadas opciones sin default** — "Use pypdf, or pdfplumber, or PyMuPDF" → Proporcionar default
6. **Información sensible al tiempo** — "If before August 2025..." → Usar sección "old patterns"
7. **Guardrails incompletos** (equipo) — Solo ✅ Always Do, sin ⚠️ o 🚫 → Marcar como incompleto
8. **Anti-patrones sin alternativa** (equipo) — 🚫 sin código ✅ correcto → Marcar como crítico
9. **Constantes mágicas** — `TIMEOUT = 47` sin explicación → Documentar razón
10. **Scripts que delegan al agente** — Script que simplemente falla y deja al agente resolver → Manejar errores explícitamente

---

## Formato de Salida

- Lenguaje técnico y objetivo
- Enfoque en problemas específicos, no generalizaciones
- Diferenciar claramente: criterios **oficiales** (de Claude docs) vs **convenciones del equipo**
- Matriz de cumplimiento para visualización rápida
- Acciones concretas y priorizadas

---

**Invocación sugerida**:
```
Analiza los skills en este repositorio usando el validador de mejores prácticas.
```

**Salida esperada**: `SKILL_BEST_PRACTICES_REVIEW.md` con análisis completo y recomendaciones priorizadas.


---
name: skill-best-practices-validator
description: Analyzes Agent Skills for quality and adherence to official Claude best practices and team conventions. Use when validating .claude/skills before shipping.
argument-hint: "Directory of skills to validate (e.g. .claude/skills/)"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Validador de Mejores Prácticas para Agent Skills

## Objetivo
Generar un análisis de calidad y adherencia a mejores prácticas de Agent Skills basado en:
- **Oficial**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Equipo**: `.claude/skills/authoring-agent-skills/SKILL.md`

## Quick Navigation

- **[Output Templates](./blueprints/output-templates.md)** — plantillas del review individual + resumen consolidado
- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 escenarios: canónico, edge, misuso
- **[Instrucciones de Ejecución](#instrucciones-de-ejecución)** — workflow de 3 pasos
- **[Criterios de Evaluación](#criterios-de-evaluación)** — A1–A6, B, C (oficial) + D1–D7 (equipo)
- **[Detección de Anti-Patrones](#detección-de-anti-patrones)** — 11 reglas de detección
- **[Verification Loop](#verification-loop)** — Auto-validación antes de guardar
- **[External Resources](#external-resources)** — Documentación oficial de la que derivan los criterios

---

## Instrucciones para Agente

Actúa como un Agent Skills Quality Specialist. Evalúa cada skill contra los criterios oficiales de Claude y las convenciones del equipo documentadas en `authoring-agent-skills`.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Leer los archivos de referencia antes de evaluar** — leer `.claude/skills/authoring-agent-skills/SKILL.md` y `.claude/skills/authoring-agent-skills/blueprints/three-tier-architecture.md` antes de emitir cualquier criterio.
- **Confirmar conteos con inspección real del filesystem** — usar `ls`/`Glob` para enumerar los SKILL.md presentes; nunca confiar en conteos auto-reportados ni asumir qué archivos existen.
- **Citar el criterio exacto en cada hallazgo** — cada problema debe referenciar el criterio (A1, B2, D3, etc.) y la ubicación (nombre de archivo + sección).
- **Generar un archivo individual por skill evaluada** — en `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`.
- **Generar el resumen consolidado al final** — `.claude/skills/skills-best-practices-summary.md` con la matriz comparativa de todas las skills.
- **Contar líneas reales del SKILL.md** — usar lectura del archivo para confirmar el número de líneas; no estimarlo visualmente.

### ⚠️ Ask First

- **Skills de terceros o legadas** — si la skill evaluada está marcada como de terceros o tiene avisos de "legacy", preguntar al usuario si aplicar los criterios de equipo D1-D7 o solo los oficiales A-C.
- **Skills sin version context** — si el SKILL.md no declara versión, preguntar si la skill es intencionalmente agnóstica de versión o si falta el contexto.
- **Directorio personalizado** — si el argumento `$ARGUMENTS` apunta a una ruta no estándar, confirmar antes de proceder.
- **Skills con > 500 líneas** — cuando SKILL.md supera 500 líneas, preguntar si el usuario quiere solo el diagnóstico o también una propuesta de extracción a `blueprints/`.

### 🚫 Never Do

- **Nunca reportar una violación sin citar criterio + ubicación** — produce output inaccionable. ✅ Siempre nombrar el criterio (ej. "A1 — description max 1536 chars") y la línea o sección donde ocurre.
- **Nunca asumir que una skill cumple un criterio sin leer el archivo** — si el archivo no fue leído, no asignar estado. ✅ Leer el archivo completo antes de evaluar; reportar "archivo no leído" si es inaccesible.
- **Nunca mezclar criterios oficiales con convenciones de equipo en la misma celda** — dificulta priorización. ✅ Mantener las tablas A-C (oficiales) y D (equipo) separadas como en la plantilla.
- **Nunca omitir la sección "Recomendaciones por Prioridad"** — es la sección más accionable. ✅ Siempre incluirla con clasificación ALTA / MEDIA / BAJA.
- **Nunca generar solo el resumen consolidado sin los archivos individuales** — el resumen sin detalle no permite corrección. ✅ Generar ambos: archivo individual + resumen.

#### Hallazgo: incorrecto vs. correcto (lado a lado)

El formato de cada hallazgo es la salida principal del validador. Contrasta:

```markdown
<!-- 🚫 INCORRECTO — inaccionable: sin criterio, sin ubicación -->
- La descripción es muy larga y debería acortarse.
- Faltan algunos guardrails.
```

```markdown
<!-- ✅ CORRECTO — criterio + ubicación + acción -->
- **A1** (SKILL.md, frontmatter `description`, línea 3): 1710 chars > límite 1536.
  Reescribir con trigger "Use when…" ≤ 1536.
- **D2** (SKILL.md, `## Blueprints & Guardrails`): falta el tier `### ⚠️ Ask First`.
  Añadir el tier con ítems poblados.
```

---

## Instrucciones de Ejecución

### Paso 1: Cargar Criterios de Referencia

Lee los siguientes archivos antes de evaluar:
1. `.claude/skills/authoring-agent-skills/SKILL.md` — Estándar del equipo
2. `.claude/skills/authoring-agent-skills/blueprints/three-tier-architecture.md` — Arquitectura de tres niveles

### Paso 2: Descubrir y Analizar Skills

Explora `.claude/skills/*/SKILL.md` (o el directorio indicado en `$ARGUMENTS`) y evalúa cada skill según los criterios abajo.

---

## Criterios de Evaluación

### A. Calidad Core (Oficial — de Claude Best Practices)

**A1. YAML Frontmatter**
- `name`: max 64 chars, solo minúsculas/números/guiones, sin XML tags, sin palabras reservadas (`anthropic`, `claude`)
- `description`: no vacío, max 1536 chars, sin XML tags
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

### Paso 3: Generar Archivos de Validación

Genera **dos artefactos** siguiendo las plantillas exactas en
**[blueprints/output-templates.md](./blueprints/output-templates.md)**:

1. **Un archivo individual por skill** — `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md`
   (header + Resumen + tabla oficial A1–A6/B/C + tabla equipo D1–D7 + Recomendaciones por Prioridad + Conclusiones).
2. **El resumen consolidado** — `.claude/skills/skills-best-practices-summary.md`
   (Resumen Ejecutivo + Matriz de Cumplimiento con una fila por skill + fila PROMEDIO + Recomendaciones Globales).

Copiar las estructuras del blueprint verbatim; no improvisar el formato.

---

## Detección de Anti-Patrones

El validador debe detectar y reportar:

1. **SKILL.md excede 500 líneas** — Recomendar extraer contenido a `blueprints/`
2. **Descripción vaga o en primera persona** — "Helps with docs" o "I can process files" → Corregir a tercera persona con trigger
3. **description supera 1536 chars** — Truncar y reescribir con trigger "Use when..."
4. **Rutas Windows-style** — `scripts\helper.py` → `scripts/helper.py`
5. **Referencias anidadas profundas** — SKILL.md → A.md → B.md → C.md → Aplanar a un nivel
6. **Demasiadas opciones sin default** — "Use pypdf, or pdfplumber, or PyMuPDF" → Proporcionar default
7. **Información sensible al tiempo** — fechas absolutas ("if before <mes> <año>...") o "edición <año>" → Usar sección "old patterns" o anclar a versión ("before upgrading to v2...")
8. **Guardrails incompletos** (equipo) — Solo ✅ Always Do, sin ⚠️ o 🚫 → Marcar como incompleto
9. **Anti-patrones sin alternativa** (equipo) — 🚫 sin código ✅ correcto → Marcar como crítico
10. **Constantes mágicas** — `TIMEOUT = 47` sin explicación → Documentar razón
11. **Scripts que delegan al agente** — Script que simplemente falla y deja al agente resolver → Manejar errores explícitamente

---

## Verification Loop

Antes de guardar los archivos de salida, el validador DEBE ejecutar estos comandos y confirmar la
salida esperada. Sustituir `<skills-dir>` por el directorio validado (ej. `.claude/skills`).

```bash
# 1. Conteo de skills: nº de review files debe igualar nº de SKILL.md
find <skills-dir> -name SKILL.md | wc -l
find <skills-dir> -name '*-best-practices-review.md' | wc -l   # → mismo número
# 2. Resumen existe y lista todas las skills
test -f <skills-dir>/skills-best-practices-summary.md && echo OK
# 3. Cada skill tiene su review file (lista los que FALTAN — salida vacía = OK)
for f in <skills-dir>/*/SKILL.md; do d=$(dirname "$f"); s=$(basename "$d"); \
  test -f "$d/$s-best-practices-review.md" || echo "MISSING: $s"; done
# 4. Cada review cita criterios (0 = fallo: review sin referencias A#/B/C/D#)
for r in <skills-dir>/*/*-best-practices-review.md; do \
  grep -qE '\b([A-D][0-9]?|B|C)\.' "$r" || echo "NO-CRITERIA: $r"; done
```

Checklist de contenido (verificación manual antes de guardar):

- [ ] **Criterios cubiertos** — la tabla de cada skill tiene exactamente 8 filas oficiales (A1–A6, B, C) y 7 filas de equipo (D1–D7).
- [ ] **Matriz completa** — el nº de filas en la matriz consolidada == salida del comando 1.
- [ ] **Hallazgos accionables** — cada ítem en "Recomendaciones por Prioridad" referencia ≥1 criterio (A1, D2, etc.) + ubicación.

Todos los comandos deben salir con código `0` y sin líneas `MISSING:` / `NO-CRITERIA:` antes de guardar.

---

## Formato de Salida

- Lenguaje técnico y objetivo
- Enfoque en problemas específicos, no generalizaciones
- Diferenciar claramente: criterios **oficiales** (de Claude docs) vs **convenciones del equipo**
- Matriz de cumplimiento para visualización rápida
- Acciones concretas y priorizadas

---

## External Resources

### Documentación Oficial Claude
- [Claude Agent Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — fuente primaria de los criterios A-C
- [Claude Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills) — definición de skills y frontmatter válido

### Convenciones del Equipo
- [authoring-agent-skills SKILL.md](./../authoring-agent-skills/SKILL.md) — estándar del equipo (criterios D)
- [authoring-agent-skills — three-tier-architecture](./../authoring-agent-skills/blueprints/three-tier-architecture.md) — arquitectura de tres niveles
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — límites de frontmatter (description max 1536 chars, `allowed-tools` vs `tools`, etc.)

---

**Invocación sugerida**:
```
Analiza los skills en este repositorio usando el validador de mejores prácticas.
```

**Salida esperada**: Un archivo `.claude/skills/[skill-name]/[skill-name]-best-practices-review.md` por skill + `.claude/skills/skills-best-practices-summary.md` con la matriz comparativa consolidada.

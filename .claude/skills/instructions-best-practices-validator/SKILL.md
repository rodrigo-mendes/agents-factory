---
name: instructions-best-practices-validator
description: Analyzes instruction/rule files for quality and adherence to official (GitHub/VS Code) best practices and team conventions. Use when validating instruction or .claude/rules files.
argument-hint: "Directory of instructions/rules to validate"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Validador de Mejores Prácticas para Custom Instructions

## Objetivo
Generar un análisis de calidad y adherencia a mejores prácticas de archivos `.instructions.md` basado en:
- **Oficial GitHub**: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
- **Oficial VS Code**: https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- **Biblioteca de Ejemplos**: https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions
- **Equipo**: Convenciones establecidas en `.claude/rules/` (Claude Code) o `.github/instructions/` (Copilot) del repositorio actual

## Quick Navigation

- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 escenarios: canónico, edge, misuso
- **[Verification Loop](#verification-loop)** — Auto-validación antes de guardar
- **[External Resources](#external-resources)** — Documentación oficial de la que derivan los criterios

---

## Instrucciones para Agente

Actúa como un Custom Instructions Quality Specialist. Evalúa cada `.instructions.md` contra los criterios oficiales de GitHub/VS Code y las convenciones del equipo.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Leer al menos 3 archivos de instrucción existentes como referencia de estilo** antes de emitir cualquier hallazgo — establece la línea base de convenciones del equipo.
- **Confirmar que `applyTo` existe en cada archivo** — su ausencia es el problema más crítico; sin él, las instrucciones nunca se aplican automáticamente.
- **Citar el criterio exacto y el archivo en cada hallazgo** — cada problema debe referenciar el criterio (A1, B2, E3, etc.) y el nombre del archivo afectado.
- **Analizar overlaps y gaps en los patrones `applyTo`** — el análisis de cobertura de patrones es una sección obligatoria del informe.
- **Diferenciar criterios oficiales (A-D) de convenciones de equipo (E)** en tablas separadas — permite priorizar correctamente.
- **Confirmar la existencia de archivos referenciados** — si un archivo `.instructions.md` referencia otro archivo o skill, verificar que ese target existe.

### ⚠️ Ask First

- **`applyTo: "**"` global** — si se detecta un patrón excesivamente amplio, preguntar si es intencional (ej. instrucciones globales de proyecto) antes de marcarlo como violación.
- **Instrucciones en idioma mixto** — si el repositorio tiene instrucciones en múltiples idiomas, preguntar cuál es el idioma canónico antes de evaluar consistencia.
- **Archivos con >300 líneas** — cuando un archivo supera las 300 líneas, preguntar si el usuario quiere solo el diagnóstico o también una propuesta de división.
- **Conflictos entre archivos con el mismo `applyTo`** — antes de marcar como violación, preguntar si las instrucciones conflictivas son intencionales (ej. una sobreescribe a la otra por orden de carga).

### 🚫 Never Do

- **Nunca omitir el análisis de `applyTo`** — es el campo más crítico; un archivo sin `applyTo` nunca se activa automáticamente. ✅ Siempre verificar presencia, validez del glob, y especificidad del patrón.
- **Nunca marcar una regla como buena solo porque existe** — la calidad depende de que incluya el razonamiento ("Use X because Y"). ✅ Verificar que cada regla explica el POR QUÉ existe.
- **Nunca reportar una violación sin citar el archivo y la sección** — produce output inaccionable. ✅ Nombrar el archivo exacto (ej. `terraform-standards.instructions.md`) y la sección o línea.
- **Nunca ignorar conflictos entre archivos** — instrucciones conflictivas con el mismo `applyTo` producen comportamiento no determinista. ✅ Listar cada par conflictivo con sus patrones y las reglas que se contradicen.
- **Nunca generar el informe sin la sección "Análisis de applyTo Patterns"** — overlaps y gaps son igual de importantes que los hallazgos por archivo. ✅ La sección de análisis de patrones es obligatoria.

---

## Instrucciones de Ejecución

### Paso 1: Cargar Criterios de Referencia

Lee los siguientes archivos antes de evaluar:
1. `.claude/rules/` (Claude Code) o `.github/instructions/` (Copilot) — Listar todos los archivos existentes para entender convenciones del equipo
2. Al menos 3 archivos `.instructions.md` existentes como referencia de estilo

### Paso 2: Descubrir y Analizar Instructions

Explora `.claude/rules/*.md` (Claude Code) o `.github/instructions/*.instructions.md` (Copilot) y evalúa cada archivo según los criterios abajo.

---

## Criterios de Evaluación

### A. YAML Frontmatter (Oficial — GitHub + VS Code)

**A1. Campo `name`**
- Presente y descriptivo
- Kebab-case (minúsculas, guiones)
- Máximo 64 caracteres
- Coincide con el nombre del archivo (sin extensión `.instructions.md`)

**A2. Campo `description`**
- Presente y no vacío
- Máximo 1536 caracteres
- Describe QUÉ hace Y CUÁNDO se activa
- Tercera persona (no "I help" ni "You can")
- Suficientemente específico para matching semántico

**A3. Campo `applyTo`**
- Presente (si no existe, las instrucciones NO se aplican automáticamente)
- Glob pattern válido con forward slashes solamente
- Patrón relativo al workspace root
- Específico (no usa `**` a menos que sea intencionalmente global)
- Patrones múltiples separados por coma cuando aplica

**A4. Campo `excludeAgent` (opcional)**
- Si presente, valor válido: `"code-review"` o `"cloud-agent"`

### B. Contenido y Estructura (Oficial — VS Code Best Practices)

**B1. Concisión**
- Instrucciones cortas y autocontenidas
- Cada instrucción es una declaración simple y clara
- Sin explicaciones innecesarias de conceptos que Copilot ya conoce
- Enfocado en reglas no obvias (no repetir lo que linters/formatters ya hacen)

**B2. Razonamiento incluido**
- Las reglas incluyen el POR QUÉ existe la convención
- El AI toma mejores decisiones en edge cases cuando entiende la razón
- Ejemplo correcto: "Use `date-fns` instead of `moment.js` because moment.js is deprecated and increases bundle size"
- Ejemplo incorrecto: "Use `date-fns`" (sin justificación)

**B3. Ejemplos concretos**
- Patrones preferidos mostrados con código concreto
- Patrones a evitar mostrados con código concreto
- No abstracto — siempre con ejemplos reales

**B4. Lenguaje natural en Markdown**
- Formato Markdown limpio
- Sin XML tags ni formatos propietarios
- Whitespace entre instrucciones para legibilidad

**B5. Default + Escape Hatch**
- Provee un default claro para decisiones comunes
- Indica cuándo es válido desviarse del default
- No ofrece demasiadas opciones sin recomendación

### C. Rutas y Referencias (Oficial)

**C1. Forward slashes solamente**
- `src/main/java/**/*.java` ✅
- `src\main\java\**\*.java` ❌

**C2. Rutas relativas o URLs completas**
- `./blueprints/pattern.md` ✅
- `https://docs.example.com/guide` ✅
- `C:\Users\dev\project\file.md` ❌
- `/home/user/project/file.md` ❌

**C3. Referencias a otros archivos**
- Markdown links para referenciar archivos del workspace
- Links verificables (targets existentes)
- Máximo un nivel de profundidad desde el archivo de instrucciones

### D. Scope y Granularidad (Oficial — GitHub)

**D1. Single Responsibility**
- Cada archivo cubre UN tema/dominio coherente
- No mezcla concerns no relacionados
- Nombre del archivo refleja su scope exacto

**D2. Granularidad del `applyTo`**
- Pattern no demasiado amplio (evitar `**/*` sin razón)
- Pattern no demasiado restrictivo (cubre todos los archivos relevantes)
- Consistente con otros archivos del mismo dominio

**D3. Sin conflictos entre archivos**
- No contradice otros `.instructions.md` del mismo repositorio
- Si múltiples archivos aplican al mismo glob, no generan instrucciones conflictivas

### E. Convenciones del Equipo

**E1. Naming consistente**
- Formato: `{dominio}-{sub-dominio}.instructions.md`
- Ejemplos: `java-functions-fdk`, `terraform-standards`, `java-functions-error-handling`
- Patrón de agrupación por tecnología + concern

**E2. Role Statement**
- Primera línea del body define el rol del agente: "You are a [Role] specialist..."
- Específico al dominio del archivo

**E3. Sección de Version Context (si aplica)**
- Versiones de tecnologías explícitas
- Constraints de versión claros (e.g., "FDK v1.1.x", "Terraform v1.11+")

**E4. Código como instrucción**
- Bloques de código con patrón correcto + incorrecto
- Comentarios en código: `// ✅ CORRECT:` y `// 🚫 WRONG:`
- Language tag correcto en code fences

**E5. Skill Integration (si es archivo de routing)**
- Tabla de mapping keywords → skills completa
- Todas las rutas de skills referenciadas existen
- Workflow de integración documentado

**E6. Links funcionales**
- Cross-references a otros instructions/skills válidos
- Links externos a documentación oficial
- Sin 404s

---

### Paso 3: Generar Informe de Validación

Crea un archivo `INSTRUCTIONS_BEST_PRACTICES_REVIEW.md` con la siguiente estructura:

```markdown
# Análisis de Mejores Prácticas para Custom Instructions

**Fecha**: [Fecha]
**Referencia Oficial GitHub**: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
**Referencia Oficial VS Code**: https://code.visualstudio.com/docs/copilot/customization/custom-instructions
**Referencia Equipo**: .github/instructions/

---

## Resumen Ejecutivo

- Instructions evaluados: [N]
- Cumplen criterios oficiales: [N] ([X]%)
- Cumplen convenciones de equipo: [N] ([X]%)
- Problemas críticos: [N]

---

## Evaluación por Archivo

### Instruction: [nombre-archivo]
**Archivo**: `.github/instructions/[nombre].instructions.md`
**Líneas**: [N]
**applyTo**: `[pattern]`

#### Criterios Oficiales (GitHub + VS Code)
| Criterio | Estado | Notas |
|----------|--------|-------|
| A1. name (kebab-case, max 64) | ✅/❌ | [detalle] |
| A2. description (clara, tercera persona) | ✅/❌ | [detalle] |
| A3. applyTo (glob válido, específico) | ✅/❌ | [detalle] |
| A4. excludeAgent (si presente) | ✅/❌/N/A | [detalle] |
| B1. Concisión | ✅/❌ | [detalle] |
| B2. Razonamiento incluido | ✅/❌ | [detalle] |
| B3. Ejemplos concretos | ✅/❌ | [detalle] |
| B4. Markdown limpio | ✅/❌ | [detalle] |
| B5. Default + Escape Hatch | ✅/❌ | [detalle] |
| C. Rutas y referencias | ✅/❌ | [detalle] |
| D1. Single Responsibility | ✅/❌ | [detalle] |
| D2. Granularidad applyTo | ✅/❌ | [detalle] |
| D3. Sin conflictos | ✅/❌ | [detalle] |

#### Convenciones del Equipo
| Criterio | Estado | Notas |
|----------|--------|-------|
| E1. Naming consistente | ✅/❌ | [detalle] |
| E2. Role Statement | ✅/❌ | [detalle] |
| E3. Version Context | ✅/❌ | [detalle] |
| E4. Código como instrucción | ✅/❌ | [detalle] |
| E5. Skill Integration | ✅/❌/N/A | [detalle] |
| E6. Links funcionales | ✅/❌ | [detalle] |

**Hallazgos principales**: [Resumen de issues y fortalezas]

---

## Matriz de Cumplimiento

| Instruction | Oficial (A-D) | Equipo (E) | Total |
|-------------|---------------|------------|-------|
| [instruction-1] | [X]/13 | [X]/6 | [X]% |
| [instruction-2] | [X]/13 | [X]/6 | [X]% |
| PROMEDIO | [X]/13 | [X]/6 | [X]% |

---

## Análisis de applyTo Patterns

### Cobertura de Patrones
| Pattern | Archivos que usa | Overlaps |
|---------|-----------------|----------|
| `**/*.tf` | terraform-*.instructions.md | [lista de overlaps] |
| `**/src/main/java/**/*.java` | java-functions-*.instructions.md | [lista de overlaps] |

### Conflictos Detectados
[Lista de instrucciones que aplican al mismo glob con reglas potencialmente conflictivas]

### Gaps Detectados
[Tipos de archivo sin coverage por ningún instruction]

---

## Recomendaciones por Prioridad

### ALTA (Bloquean Funcionalidad)
[Lista — ej: applyTo ausente, description vacía, YAML malformado]

### MEDIA (Reducen Calidad)
[Lista — ej: sin razonamiento en reglas, ejemplos abstractos, naming inconsistente]

### BAJA (Optimización)
[Lista — ej: concisión mejorable, role statement genérico]

---

## Conclusiones
[Resumen general y próximas acciones]
```

---

## Detección de Anti-Patrones

El validador debe detectar y reportar:

1. **`applyTo` ausente** — El archivo NUNCA se aplica automáticamente (solo manual attachment)
2. **`applyTo` demasiado amplio** — `"**"` o `"**/*"` sin justificación clara
3. **Descripción vaga** — "Helps with code" → Corregir a descripción específica con trigger
4. **Descripción en primera persona** — "I help you with..." → Tercera persona
5. **Rutas Windows-style** — `src\main\java` → `src/main/java`
6. **Rutas absolutas** — `/home/user/...` o `C:\Users\...` → Rutas relativas
7. **Archivo monolítico** — Un solo `.instructions.md` con >300 líneas cubriendo múltiples concerns → Dividir
8. **Reglas sin justificación** — "Use X" sin explicar por qué → Agregar razonamiento
9. **Solo reglas abstractas sin ejemplos** — "Follow best practices" → Código concreto
10. **Conflicto entre archivos** — Dos instrucciones con mismo `applyTo` dando indicaciones contradictorias
11. **Name no coincide con archivo** — `name: foo` en archivo `bar.instructions.md`
12. **Glob patterns inválidos** — Backslashes, paths absolutos, syntax incorrecta
13. **Información temporal sin marcación** — "The new API (released 2024)" → Marcar como version context
14. **Skills referenciados inexistentes** — Link a `.claude/skills/X/SKILL.md` donde X no existe

---

## Verification Loop

Antes de guardar el informe, el validador DEBE auto-verificar:

1. **Conteo de archivos** — confirmar que el número de archivos evaluados en la Matriz de Cumplimiento coincide con los encontrados con `ls`/`Glob` en el directorio objetivo.
2. **Sección applyTo obligatoria** — verificar que la sección "Análisis de applyTo Patterns" está presente con las tres subsecciones: Cobertura, Conflictos, Gaps.
3. **Hallazgos con criterio citado** — cada ítem en "Recomendaciones por Prioridad" debe referenciar al menos un criterio (A3, B2, E1, etc.) y un archivo específico.
4. **Links referenciados** — si el informe enlaza skills o archivos de instrucción, verificar que los paths existen antes de incluirlos.
5. **Tablas completas** — cada archivo evaluado debe tener exactamente 13 filas de criterios oficiales (A1-A4, B1-B5, C, D1-D3) y 6 filas de equipo (E1-E6).

---

## Formato de Salida

- Lenguaje técnico y objetivo
- Enfoque en problemas específicos, no generalizaciones
- Diferenciar claramente: criterios **oficiales** (de GitHub/VS Code docs) vs **convenciones del equipo**
- Análisis de `applyTo` patterns como sección especial (overlaps, gaps, conflictos)
- Matriz de cumplimiento para visualización rápida
- Acciones concretas y priorizadas

---

## External Resources

### Documentación Oficial GitHub Copilot
- [Adding repository custom instructions for GitHub Copilot](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot) — fuente primaria de los criterios A-D
- [Configure custom instructions (GitHub how-to)](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions) — campos `applyTo`, `excludeAgent`, y ejemplos
- [Custom instructions library](https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions) — ejemplos canónicos por dominio

### Documentación Oficial VS Code
- [Custom instructions (VS Code)](https://code.visualstudio.com/docs/copilot/customization/custom-instructions) — best practices de concisión, razonamiento, y scope

### Convenciones del Equipo
- [skill-frontmatter rules](./../../rules/skill-frontmatter.md) — reglas de frontmatter para `.claude/rules/` y `.claude/agents/`
- [authoring-agent-skills SKILL.md](./../authoring-agent-skills/SKILL.md) — contexto del ecosistema de skills

---

**Invocación sugerida**:
```
Analiza los archivos .instructions.md en este repositorio usando el validador de mejores prácticas.
```

**Salida esperada**: `INSTRUCTIONS_BEST_PRACTICES_REVIEW.md` con análisis completo y recomendaciones priorizadas.

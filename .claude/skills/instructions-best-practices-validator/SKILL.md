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

## Instrucciones para Agente

Actúa como un Custom Instructions Quality Specialist. Evalúa cada `.instructions.md` contra los criterios oficiales de GitHub/VS Code y las convenciones del equipo.

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
- Máximo 1024 caracteres
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

````markdown
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
````

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

## Formato de Salida

- Lenguaje técnico y objetivo
- Enfoque en problemas específicos, no generalizaciones
- Diferenciar claramente: criterios **oficiales** (de GitHub/VS Code docs) vs **convenciones del equipo**
- Análisis de `applyTo` patterns como sección especial (overlaps, gaps, conflictos)
- Matriz de cumplimiento para visualización rápida
- Acciones concretas y priorizadas

---

**Invocación sugerida**:
```
Analiza los archivos .instructions.md en este repositorio usando el validador de mejores prácticas.
```

**Salida esperada**: `INSTRUCTIONS_BEST_PRACTICES_REVIEW.md` con análisis completo y recomendaciones priorizadas.

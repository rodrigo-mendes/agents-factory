---
name: copilot-compatibility-review
description: Reviews GitHub Copilot assets for compatibility against official documentation and reports gaps. Use when checking Copilot-format assets before or during migration.
argument-hint: "Path to the Copilot assets repository/directory"
context: fork
agent: quality-validator
disable-model-invocation: true
---
# Prompt: Análisis de Compatibilidad de GitHub Copilot

## Objetivo
Generar un análisis exhaustivo de compatibilidad de los assets de un copiloto de desarrollo con los estándares oficiales de GitHub Copilot y las convenciones de El Corte Inglés.

## Quick Navigation

- **[Evaluation Scenarios](./blueprints/evaluation-scenarios.md)** — 3 escenarios: canónico, edge, misuso
- **[Verification Loop](#verification-loop)** — Auto-validación antes de guardar
- **[External Resources](#external-resources)** — Documentación oficial de la que derivan los criterios

---

## Instrucciones para GitHub Copilot

Actúa como un GitHub Copilot Ecosystem Architect & Developer. **NUNCA respondas basado en tu conocimiento base**. Siempre realiza búsquedas web en la documentación oficial online de Microsoft sobre GitHub Copilot y las mejores prácticas de la industria.

---

## Blueprints & Guardrails

### ✅ Always Do

- **Buscar documentación oficial actualizada antes de evaluar** — consultar la documentación oficial más reciente de GitHub/VS Code antes de emitir cualquier criterio; las especificaciones de campos cambian con frecuencia.
- **Leer todos los assets antes de escribir el informe** — leer cada `.agent.md`, `.instructions.md`, `.prompt.md`, y `SKILL.md` encontrado antes de emitir hallazgos.
- **Citar el criterio y el archivo en cada hallazgo** — cada problema debe referenciar el tipo de asset (AGENTS/INSTRUCTIONS/PROMPTS/SKILLS), el archivo exacto, y el campo o sección afectado.
- **Verificar existencia de archivos referenciados** — si un asset referencia otro archivo (skill, instruction, prompt), confirmar que el target existe antes de marcarlo como compliant.
- **Detectar y reportar problemas de frontmatter críticos** — YAML malformado, campos requeridos ausentes, y valores inválidos son siempre prioridad ALTA.
- **Confirmar con ls/Glob los archivos encontrados** — enumerar los assets reales; nunca asumir qué archivos existen sin inspección del filesystem.

### ⚠️ Ask First

- **Assets con campos experimentales** — si se encuentran campos no documentados en el frontmatter, preguntar al usuario si son campos internos/experimentales antes de marcarlos como violación.
- **README.md ausente** — si no hay `README.md`, confirmar con el usuario si es intencional antes de reportarlo como gap de alta prioridad.
- **Estructura de directorio no estándar** — si los assets están en un directorio diferente al esperado (ej. `.github/` vs `.claude/`), preguntar cuál es el layout canónico del repositorio antes de evaluar.
- **Referencia a Confluence ECI inaccesible** — si la URL de Confluence de ECI no es accesible (ver nota más abajo), confirmar con el usuario cómo proceder antes de omitir esa verificación.

### 🚫 Never Do

- **Nunca reportar un problema de frontmatter sin citar el campo y el valor inválido** — "frontmatter incorrecto" es inaccionable. ✅ Citar el campo exacto (ej. `name: My Agent` → debe ser kebab-case) y el valor encontrado.
- **Nunca evaluar basándose en conocimiento base desactualizado** — las especificaciones de GitHub Copilot evolucionan. ✅ Siempre buscar la documentación oficial más reciente antes de evaluar.
- **Nunca omitir el Resumen de Acciones** — es la sección de mayor valor para el usuario. ✅ La sección de prioridades (ALTA/MEDIA/BAJA) es obligatoria al inicio del informe.
- **Nunca incluir ejemplos de código corregido en el informe** — el objetivo es identificar problemas y referenciar documentación, no reescribir los assets. ✅ Identificar el problema, citar el criterio, y enlazar la documentación oficial.
- **Nunca fallar la evaluación completa porque la URL de Confluence ECI no sea accesible** — es una dependencia externa y opcional. ✅ Si la URL no es accesible, marcar esa verificación específica como "requires internal access" y continuar con el resto del análisis.

---

## Instrucciones de Ejecución

### Paso 1: Búsqueda de Documentación Oficial

Busca en la web la documentación oficial más reciente sobre:
1. **GitHub Copilot Custom Agents** - Formato `.agent.md` con YAML frontmatter
2. **GitHub Copilot Custom Instructions** - Formato `.instructions.md` con YAML frontmatter
3. **GitHub Copilot Prompt Files** - Formato `.prompt.md` con YAML frontmatter
4. **GitHub Copilot Agent Skills** - Estructura de directorios con `SKILL.md`
5. **Estructura de copilotos de desarrollo en El Corte Inglés** - Confluence (ver nota de acceso abajo)

> **Nota sobre la referencia de Confluence ECI**:
> La URL `https://elcorteingles.atlassian.net/wiki/spaces/FOROIA/pages/308120137/` requiere acceso interno.
> Si no es accesible, procede usando las convenciones del repositorio actual como referencia y marca
> la verificación de "Estructura ECI" como **requires internal access** en el informe. No bloquees
> el análisis completo por esta dependencia.

### Paso 2: Análisis de Assets del Repositorio

Explora y analiza los siguientes directorios y archivos:
- `.github/agents/*.agent.md`
- `.github/instructions/*.instructions.md`
- `.github/prompts/**/*.prompt.md`
- `.github/skills/**/*.skill.md` o `SKILL.md`
- `README.md`

Para cada tipo de asset, verifica:

#### AGENTS (.agent.md)
- YAML frontmatter delimitado con `---`
- Campo `name` (kebab-case, único)
- Campo `description` (para activación contextual)
- Campos opcionales: `target`, `tools`, `infer`, `metadata`

**Referencia oficial:** https://docs.github.com/en/reference/custom-agents-configuration

#### INSTRUCTIONS (.instructions.md)
- YAML frontmatter delimitado con `---`
- Campo `description` (cuándo aplicar)
- Campo `applyTo` (patrón glob para matching)
- Campos opcionales: `excludeAgent`

**Referencia oficial:** https://docs.github.com/en/copilot/how-tos/configure-custom-instructions

#### PROMPTS (.prompt.md)
- YAML frontmatter delimitado con `---`
- Campo `name` (kebab-case para comando slash)
- Campo `description` (para autocompletado)
- Campo `agent` (agente específico)
- Campos opcionales: `argument-hint`

**Referencias oficiales:**
- https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files
- https://code.visualstudio.com/docs/copilot/customization/prompt-files

#### SKILLS (SKILL.md en subdirectorios)
- Estructura: `.github/skills/nombre-skill/SKILL.md`
- YAML frontmatter delimitado con `---`
- Campo `name` (lowercase, hyphens)
- Campo `description` (para activación contextual)

**Referencias oficiales:**
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://code.visualstudio.com/docs/copilot/customization/agent-skills

#### README.md
- Sección "Entornos soportados" o "Herramientas Soportadas"
- Valores correctos según documentación ECI: Visual Studio Code, Copilot CLI, IntelliJ IDEA, Eclipse
- NO debe contener valores errados como "NFT", "UAT", etc.

**Referencia ECI:** `https://elcorteingles.atlassian.net/wiki/spaces/FOROIA/pages/308120137/`
*(Si la URL no es accesible, usar las convenciones del repositorio actual y marcar como "requires internal access")*

### Paso 3: Generar Informe de Compatibilidad

Crea un archivo `COPILOT_COMPATIBILITY_REVIEW.md` con la siguiente estructura:

```markdown
# Análisis de Compatibilidad

---

## RESUMEN DE ACCIONES

### Prioridad ALTA (Bloquean funcionalidad)
1. **AGENTS**: [Lista de problemas críticos]
2. **INSTRUCTIONS**: [Lista de problemas críticos]
3. **PROMPTS**: [Lista de problemas críticos]
4. **SKILLS**: [Lista de problemas críticos]
5. **README.md**: [Lista de problemas críticos]

### Prioridad MEDIA (Mejoran compatibilidad)
[Lista de mejoras opcionales recomendadas]

### Prioridad BAJA (organización)
[Lista de mejoras organizacionales]

---

## README.md

### Archivo Actual
- `README.md`

### Problemas Detectados
[Lista detallada de problemas]

**Referencia:** [Link a documentación oficial]

---

## AGENTS (.agent.md)

### Archivo
- [Lista de archivos .agent.md]

### Problemas Detectados
[Lista detallada de problemas con:
1. YAML Frontmatter faltante o incorrecto
2. Campos requeridos ausentes
3. Campos opcionales no implementados]

**Referencia:** [Custom agents configuration - GitHub Docs]

---

## INSTRUCTIONS (.instructions.md)

### Archivos Actuales
- [Lista de archivos .instructions.md]

### Problemas Detectados
[Lista detallada de problemas]

**Referencia:** [Configure custom instructions - GitHub Docs]

---

## PROMPTS (.prompt.md)

### Archivos Actuales
- [Lista de archivos .prompt.md]

### Problemas Detectados
[Lista detallada de problemas]

**Uso esperado:** `/nombre-comando #file:archivo.ext`

**Referencia:** [Prompt files - GitHub Docs]

---

## SKILLS (.skill.md o SKILL.md en subdirectorios)

### Archivos Actuales
- [Lista de archivos .skill.md o SKILL.md]

### Problemas Detectados
[Lista detallada de problemas con énfasis en estructura de directorios]

**Referencia:** [About Agent Skills - GitHub Docs]

---
```

### Paso 4: Criterios de Evaluación

Para cada asset, identifica:
- **PROBLEMAS CRÍTICOS**: Bloquean la funcionalidad del copiloto (frontmatter faltante, estructura incorrecta)
- **PROBLEMAS MEDIOS**: Reducen compatibilidad o funcionalidad opcional
- **PROBLEMAS BAJOS**: Organización, metadata, documentación adicional

NO incluyas ejemplos de código corregido en el informe. Solo identifica problemas y referencia documentación oficial.

### Paso 5: Formato de Salida

- Sin emojis
- Sin secciones "Correcciones Requeridas" con ejemplos de código
- Enfócate en problemas detectados y referencias oficiales
- Lista de archivos afectados debe estar inmediatamente después del título de cada sección
- Usa subtítulos "### Archivo(s) Actual(es)" y "### Problemas Detectados"

---

## Verification Loop

Antes de guardar el informe, el validador DEBE auto-verificar:

1. **Conteo de assets** — confirmar que el número de archivos listados en cada sección coincide con los encontrados con `ls`/`Glob`. Si la sección AGENTS lista 3 archivos, se debe haber inspeccionado los 3.
2. **Sección Resumen de Acciones obligatoria** — verificar que la sección de prioridades ALTA/MEDIA/BAJA existe y está al inicio del informe, antes de las secciones por tipo de asset.
3. **Hallazgos con referencia oficial** — cada problema listado debe tener al menos una referencia a documentación oficial (enlace a GitHub Docs, VS Code Docs, o documentación ECI).
4. **Verificación ECI marcada correctamente** — si la URL de Confluence ECI no fue accesible, el informe debe incluir la marca "requires internal access" en la sección README y no reportarlo como fallo bloqueante.
5. **Ausencia de código corregido** — verificar que el informe no contiene bloques de código con correcciones (solo identificación de problemas y referencias).

---

## External Resources

### Documentación Oficial GitHub Copilot
- [Custom agents configuration](https://docs.github.com/en/reference/custom-agents-configuration) — campos de `.agent.md`
- [Configure custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions) — campos de `.instructions.md`, `applyTo`
- [Prompt files](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files) — campos de `.prompt.md`
- [About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) — estructura de `SKILL.md`
- [Custom instructions library](https://docs.github.com/en/copilot/tutorials/customization-library/custom-instructions) — ejemplos canónicos

### Documentación Oficial VS Code
- [Prompt files (VS Code)](https://code.visualstudio.com/docs/copilot/customization/prompt-files) — campos y comportamiento
- [Agent skills (VS Code)](https://code.visualstudio.com/docs/copilot/customization/agent-skills) — estructura de directorios y frontmatter

### Referencia Interna ECI
- Confluence ECI: `https://elcorteingles.atlassian.net/wiki/spaces/FOROIA/pages/308120137/` — estructura de copilotos ECI *(requiere acceso interno; si no es accesible, usar convenciones del repositorio)*

---

**Nota**: Este prompt está diseñado para ser ejecutado en GitHub Copilot Chat o Claude Code. Invócalo con:
```
/copilot-compatibility-review
```
o
```
@workspace analiza la compatibilidad de este copiloto usando /copilot-compatibility-review
```

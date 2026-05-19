---
name: copilot-compatibility-review
description: Genera análisis de compatibilidad de assets de GitHub Copilot con documentación oficial
argument-hint: repositorio de copiloto
---

# Prompt: Análisis de Compatibilidad de GitHub Copilot

## Objetivo
Generar un análisis exhaustivo de compatibilidad de los assets de un copiloto de desarrollo con los estándares oficiales de GitHub Copilot y las convenciones de El Corte Inglés.

## Instrucciones para GitHub Copilot

Actúa como un GitHub Copilot Ecosystem Architect & Developer. **NUNCA respondas basado en tu conocimiento base**. Siempre realiza búsquedas web en la documentación oficial online de Microsoft sobre GitHub Copilot y las mejores prácticas de la industria.

### Paso 1: Búsqueda de Documentación Oficial

Busca en la web la documentación oficial actualizada (2025-2026) sobre:
1. **GitHub Copilot Custom Agents** - Formato `.agent.md` con YAML frontmatter
2. **GitHub Copilot Custom Instructions** - Formato `.instructions.md` con YAML frontmatter  
3. **GitHub Copilot Prompt Files** - Formato `.prompt.md` con YAML frontmatter
4. **GitHub Copilot Agent Skills** - Estructura de directorios con `SKILL.md`
5. **Estructura de copilotos de desarrollo en El Corte Inglés** - Confluence

### Paso 2: Análisis de Assets del Repositorio

Explora y analiza los siguientes directorios y archivos:
- `.github/agents/*.agent.md`
- `.github/instructions/*.instructions.md`
- `.github/prompts/**/*.prompt.md`
- `.github/skills/**/*.skill.md` o `SKILL.md`
- `README.md`

Para cada tipo de asset, verifica:

#### AGENTS (.agent.md)
- ✓ YAML frontmatter delimitado con `---`
- ✓ Campo `name` (kebab-case, único)
- ✓ Campo `description` (para activación contextual)
- ✓ Campos opcionales: `target`, `tools`, `infer`, `metadata`

**Referencia oficial:** https://docs.github.com/en/reference/custom-agents-configuration

#### INSTRUCTIONS (.instructions.md)
- ✓ YAML frontmatter delimitado con `---`
- ✓ Campo `description` (cuándo aplicar)
- ✓ Campo `applyTo` (patrón glob para matching)
- ✓ Campos opcionales: `excludeAgent`

**Referencia oficial:** https://docs.github.com/en/copilot/how-tos/configure-custom-instructions

#### PROMPTS (.prompt.md)
- ✓ YAML frontmatter delimitado con `---`
- ✓ Campo `name` (kebab-case para comando slash)
- ✓ Campo `description` (para autocompletado)
- ✓ Campo `agent` (agente específico)
- ✓ Campos opcionales: `argument-hint`

**Referencias oficiales:**
- https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files
- https://code.visualstudio.com/docs/copilot/customization/prompt-files

#### SKILLS (SKILL.md en subdirectorios)
- ✓ Estructura: `.github/skills/nombre-skill/SKILL.md`
- ✓ YAML frontmatter delimitado con `---`
- ✓ Campo `name` (lowercase, hyphens)
- ✓ Campo `description` (para activación contextual)

**Referencias oficiales:**
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://code.visualstudio.com/docs/copilot/customization/agent-skills

#### README.md
- ✓ Sección "Entornos soportados" o "Herramientas Soportadas"
- ✓ Valores correctos según documentación ECI: Visual Studio Code, Copilot CLI, IntelliJ IDEA, Eclipse
- ✓ NO debe contener valores errados como "NFT", "UAT", etc.

**Referencia oficial:** https://elcorteingles.atlassian.net/wiki/spaces/FOROIA/pages/308120137/Estructura+de+un+copiloto+de+desarrollo+en+El+Corte+Ingl+s

Si tienes problemas para acceder a esta referencia de Confluence Cloud de ECI, dimelo y buscaremos una alternativa para validar esta información.

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

## SKILLS (.skill.md → SKILL.md en subdirectorios)

### Archivos Actuales (Estructura Incorrecta)
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

**Nota**: Este prompt está diseñado para ser ejecutado en GitHub Copilot Chat. Invócalo con:
```
/copilot-compatibility-review
```
o
```
@workspace analiza la compatibilidad de este copiloto usando /copilot-compatibility-review
```

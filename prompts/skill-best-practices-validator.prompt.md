---
name: skill-best-practices-validator
description: Genera análisis de calidad y adherencia a mejores prácticas de Agent Skills basado en Claude best practices
argument-hint: directorio de skills
---

# Prompt: Validador de Mejores Prácticas para Agent Skills

## Objetivo
Generar un análisis exhaustivo de calidad y adherencia a mejores prácticas de Agent Skills basado en los estándares oficiales de Claude según https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

## Instrucciones para Agente

Actúa como un Agent Skills Architect & Quality Specialist. **NUNCA respondas basado en tu conocimiento base**. Siempre realiza búsquedas web en la documentación oficial de Claude sobre mejores prácticas de Agent Skills.

### Paso 1: Búsqueda de Documentación Oficial

Busca en la web la documentación oficial actualizada sobre:
1. **Claude Agent Skills Best Practices** - Funcionalidad, responsabilidad, validación
   - URL Principal: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
2. **Skill Design Principles** - Claridad, modularidad, documentación
3. **Skill Implementation Patterns** - Ejemplos, pruebas, versionamiento
4. **Skill Description Standards** - Cuándo y cómo crear skills
5. **Skill Error Handling** - Validación de entradas, manejo de errores

### Paso 2: Análisis de Skills del Repositorio

Explora y analiza los siguientes directorios y archivos:
- `.github/skills/*/SKILL.md`
- `agents-factory/skills/*/SKILL.md`
- Cualquier estructura similar de skills en el proyecto

Para cada skill, verifica según las mejores prácticas de Claude:

#### SKILL.md - Estructura y Contenido

**1. Claridad y Propósito**
- ✓ Descripción clara de cuándo usar el skill
- ✓ Responsabilidad única y bien definida
- ✓ Nombre descriptivo del skill
- ✓ YAML frontmatter con campos: `name`, `description`

**2. Funcionalidad y Guardrails**
- ✓ Patrones "Siempre Hacer" (✅ Always Do) - Prácticas obligatorias
- ✓ Patrones "Preguntar Primero" (⚠️ Ask First) - Decisiones arquitectónicas
- ✓ Anti-Patrones "Nunca Hacer" (🚫 Never Do) - Lo que evitar
- ✓ Ejemplos de código ejecutable y comentado
- ✓ Razones claras para cada patrón

**3. Documentación de Ejemplos**
- ✓ Mínimo 2 ejemplos por patrón
- ✓ Código copy-paste ejecutable
- ✓ Comentarios inline explicando líneas críticas
- ✓ Contexto de versión explícito en comentarios
- ✓ Imports necesarios incluidos

**4. Verificación y Validación**
- ✓ Comandos de verificación presentes (lint, type check, tests)
- ✓ Outputs esperados documentados
- ✓ Exit codes esperados especificados
- ✓ Mínimo 80% de cobertura de tests si aplica
- ✓ Procedimiento para validar el skill

**5. Integración y Contexto**
- ✓ Patrones de integración con otros skills
- ✓ Dependencias explícitamente documentadas
- ✓ Compatibilidad con versiones especificadas
- ✓ Links a documentación oficial de tecnologías
- ✓ Ejemplos de uso real o común

**6. Información Técnica**
- ✓ Contexto de versión (Target Version)
- ✓ Fecha de release
- ✓ Estado de soporte (Active, Maintenance, EOL)
- ✓ Cambios breaking documentados
- ✓ Deprecaciones y migraciones

**7. Referencias Externas**
- ✓ Links a documentación oficial
- ✓ Links funcionales (sin 404s)
- ✓ CVEs o alertas de seguridad si aplica
- ✓ Guías de migración si aplica
- ✓ Fonte bibliografía organizada

**Referencia oficial:**
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

#### Criterios Específicos por Aspecto

**Responsabilidad y Alcance**
- El skill debe enfocarse en UNA responsabilidad clara
- Evitar skills que hagan "demasiado"
- Definir claramente límites del skill
- Documentar cuándo usar versus cuándo no usar

**Nombre del Skill**
- Debe ser descriptivo y único
- Formato: `lowercase-kebab-case`
- Nombre == carpeta == campo `name` en YAML
- No debe generar confusión con otros skills

**Descripción Trigger**
- Debe comenzar con "Use this when the user needs to..."
- Especificar tecnología y versión
- Ser específico, no genérico
- Permitir que el agente decida cuándo activar

**Ejemplos de Código**
- MÍNIMO 2 por patrón (Always Do, Ask First, Never Do)
- Código debe ser copy-paste ejecutable
- Comentarios inline en líneas críticas
- Mostrar imports y setup necesarios
- Indicar versión específica en comentarios

**Verificación (Verification Loop)**
- Comandos exactos (lint, type check, tests)
- Outputs esperados explícitos
- Exit codes esperados
- Troubleshooting para errores comunes
- Comandos deben estar probados

**Anti-Patrones (🚫 Never Do)**
- SIEMPRE incluir la alternativa correcta lado a lado
- Explicar por qué es un anti-patrón
- Referenciar CVE o issue oficial si aplica
- Indicar versión donde fue deprecated
- Mostrar impacto real en producción

### Paso 3: Generar Informe de Validación

Crea un archivo `SKILL_BEST_PRACTICES_REVIEW.md` con la siguiente estructura:

```markdown
# Análisis de Mejores Prácticas para Agent Skills

---

## RESUMEN EJECUTIVO

### Puntuación General
- Skills evaluados: [N]
- Skills que cumplen: [N]
- Skills que necesitan mejoras: [N]
- Tasa de cumplimiento: [X]%

### Problemas Críticos Identificados
[Lista de bloqueos que impiden funcionamiento correcto]

### Mejoras Recomendadas (Media Prioridad)
[Lista de mejoras de calidad]

### Mejoras Opcionales (Baja Prioridad)
[Lista de optimizaciones]

---

## Evaluación por Skill

### Skill: [nombre-skill]

**Archivo**: `.github/skills/[nombre-skill]/SKILL.md`

#### 1. Claridad y Propósito
- [ ] Descripción clara de cuándo usar
- [ ] Responsabilidad única definida
- [ ] Nombre descriptivo
- [ ] YAML frontmatter válido

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 2. Funcionalidad y Guardrails
- [ ] Patrones ✅ Always Do presentes (mín. 2)
- [ ] Patrones ⚠️ Ask First presentes (mín. 1)
- [ ] Anti-Patrones 🚫 Never Do presentes (mín. 2)
- [ ] Código ejecutable y comentado

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 3. Documentación de Ejemplos
- [ ] Mínimo 2 ejemplos por patrón
- [ ] Código copy-paste funcional
- [ ] Comentarios inline en líneas críticas
- [ ] Contexto de versión en comentarios
- [ ] Imports necesarios incluidos

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 4. Verificación y Validación
- [ ] Comandos de verificación presentes
- [ ] Outputs esperados documentados
- [ ] Exit codes especificados
- [ ] Mínimo 80% de coverage (si tests)
- [ ] Procedimiento claro de validación

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 5. Integración y Contexto
- [ ] Patrones de integración documentados
- [ ] Dependencias explícitas
- [ ] Compatibilidad de versiones
- [ ] Links a documentación oficial
- [ ] Ejemplos de uso real

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 6. Información Técnica
- [ ] Contexto de versión
- [ ] Fecha de release
- [ ] Estado de soporte
- [ ] Cambios breaking documentados
- [ ] Deprecaciones con migraciones

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### 7. Referencias Externas
- [ ] Links a documentación oficial
- [ ] Links funcionales (sin 404s)
- [ ] CVEs o alertas de seguridad
- [ ] Guías de migración
- [ ] Bibliografía organizada

**Hallazgos**: [Descripción de estado actual y problemas si existen]

#### Puntuación del Skill
- Cumplimiento: [X]/7 aspectos
- Porcentaje: [X]%
- Estado: [✅ Cumple / ⚠️ Mejoras Necesarias / 🚫 No Cumple]

---

## Recomendaciones por Prioridad

### Prioridad ALTA (Bloquean Funcionalidad)
[Lista de problemas que evitan que el skill funcione correctamente]

**Referencia**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

### Prioridad MEDIA (Mejoran Calidad)
[Lista de mejoras que aumentan la calidad y usabilidad]

**Referencia**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

### Prioridad BAJA (Optimización)
[Lista de mejoras opcionales y optimizaciones]

**Referencia**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

---

## Matriz de Cumplimiento

| Skill | Claridad | Funcionalidad | Documentación | Verificación | Integración | Técnico | Referencias | Total |
|-------|----------|---------------|---------------|--------------|-------------|---------|-------------|-------|
| [skill-1] | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [%] |
| [skill-2] | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [%] |
| PROMEDIO | [%] | [%] | [%] | [%] | [%] | [%] | [%] | [%] |

---

## Próximas Acciones

### Acciones Inmediatas (Semana 1)
1. [Acción prioritaria 1]
2. [Acción prioritaria 2]

### Acciones Corto Plazo (Mes 1)
1. [Acción media 1]
2. [Acción media 2]

### Acciones Mediano Plazo (Mes 2-3)
1. [Acción baja 1]
2. [Acción baja 2]

---

## Conclusiones

[Resumen general del estado de los skills, recomendaciones principales y estrategia de mejora]

**Fecha de Análisis**: [Fecha]
**Versión de Referencia**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
**Próxima Revisión Recomendada**: [Fecha]

---
```

### Paso 4: Criterios de Evaluación Detallados

#### CRITICO (Bloquea Funcionalidad)
- Falta YAML frontmatter
- Campo `name` o `description` faltante
- Falta estructura de tres niveles (✅⚠️🚫)
- Sin ejemplos de código
- Anti-patrones sin alternativa correcta

#### IMPORTANTE (Reduce Calidad)
- Menos de 2 ejemplos por patrón
- Código no ejecutable o sin imports
- Falta contexto de versión
- Verificación loop incompleto
- Links rotos o 404s

#### RECOMENDADO (Optimización)
- Falta organización por blueprints
- Documentación de integración incompleta
- Metadata faltante
- Ejemplos sin comentarios inline
- Referencias a documentación no incluidas

### Paso 5: Formato de Salida

- Sin emojis (excepto en estructura de patrones)
- Lenguaje técnico y objetivo
- Enfoque en problemas específicos, no generalizaciones
- Referencias siempre a: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Matriz de cumplimiento para visualización rápida
- Acciones concretas y priorizadas

---

## Validación de Anti-Patrones Comunes

El validador debe detectar y reportar:

1. **Skills con Responsabilidad Múltiple**
   - Ejemplo: Skill que hace "database queries AND api calls"
   - Acción: Recomendar dividir en dos skills

2. **Ejemplos no Ejecutables**
   - Ejemplo: Código con variables undefined o imports faltantes
   - Acción: Marcar como crítico

3. **Falta de Guardrails Completos**
   - Ejemplo: Solo ✅ Always Do, sin ⚠️ Ask First o 🚫 Never Do
   - Acción: Marcar como incompleto

4. **Documentación de Verificación Faltante**
   - Ejemplo: Sin "Verification Loop" o comandos no probados
   - Acción: Marcar como riesgo

5. **Links a Documentación Oficial Incompleta**
   - Ejemplo: Sin referencias a docs de tecnologías usadas
   - Acción: Marcar como deficiencia

6. **Versionamiento Impreciso**
   - Ejemplo: Sin mención de versiones específicas de dependencias
   - Acción: Marcar como riesgo de compatibility

---

**Nota**: Este prompt está diseñado para ser ejecutado con agentes especializados o en sesiones de análisis de código.

**Invocación sugerida**:
```
Analiza los skills en este repositorio usando el validador de mejores prácticas basado en Claude:
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
```

**Salida esperada**: `SKILL_BEST_PRACTICES_REVIEW.md` con análisis completo y recomendaciones priorizadas.


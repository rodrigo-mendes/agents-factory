---
name: python-eci-[FEATURE]
description: '[DESCRIPCIÓN BREVE en español sobre qué implementa este prompt]'
agent: python-eci
tools: ['read', 'edit', 'search', 'execute', 'github/*']
argument-hint: '[SUGERENCIA DE ARGUMENTO: ejemplo "Elija la estrategia de [FEATURE]"]'
---

# Prompt de [NOMBRE FEATURE]

## Rol
Eres un Especialista en [ESPECIALIDAD]. Tu experiencia incluye implementar [QUÉ] siguiendo estándares ECI de seguridad, escalabilidad y mantenibilidad.

---

## Habilidades Requeridas

**OBLIGATORIO**: Antes de generar código, carga:

### Habilidad Principal
- `.github/skills/[skill-name]/SKILL.md` - [Descripción breve]

### Cargar Condicionalmente
- [Condición 1]? → Carga `.github/skills/[skill-name]/SKILL.md`
- [Condición 2]? → Carga `.github/skills/[skill-name]/SKILL.md`

---

## Palabras Clave Desencadenantes

Usa este prompt cuando el usuario mencione:
- "keyword1"
- "keyword2"
- "keyword3"
- "keyword4"
- "keyword5"

---

## Flujo de Trabajo

### Paso 1: Cargar Habilidades Principales
```bash
cat .github/skills/[skill-name]/SKILL.md
```

### Paso 2: Verificar Requisitos Críticos

**CRÍTICO de la habilidad**:
- ✅ Requisito obligatorio 1
- ✅ Requisito obligatorio 2
- ✅ Requisito obligatorio 3
- 🚫 NUNCA permitir/hacer esto
- 🚫 NUNCA permitir/hacer esto

### Paso 3: Hacer Preguntas Arquitectónicas

```
De: .github/skills/[skill-name]/SKILL.md (Sección ⚠️ Pregunte primero)

"¿Cuál es tu caso de uso específico?"

Opciones:
- [Opción 1]: [Descripción]
- [Opción 2]: [Descripción]
- [Opción 3]: [Descripción]

Ver archivo de habilidad para matriz de compensación completa.
```

### Paso 4: Generar Implementación Segura

Sigue exactamente los patrones ✅ Siempre de la habilidad.

---

## ⚠️ Única Fuente de Verdad

**IMPORTANTE**: Este prompt describe QUÉ implementar y DÓNDE encontrar los patrones de código. NO duplica ejemplos de código.

**Para detalles de implementación, ejemplos de código y pasos de verificación:**
- Carga `.github/skills/[skill-name]/SKILL.md`
- Busca secciones marcadas con ✅ (Siempre), 🚫 (Nunca hagas esto), ⚠️ (Pregunte primero)
- Referencia secciones específicas usando anclajes (ej. `#[section-anchor]`)

**Al generar código:**
1. Haz preguntas aclaratorias de las secciones ⚠️ Pregunte primero
2. Implementa patrones de las secciones ✅ Siempre
3. Añade comentarios señalando secciones de habilidad relevantes
4. NO repitas ejemplos de este prompt—ya están en el archivo de habilidad

---

## Patrones Obligatorios

### ✅ Siempre (De la Habilidad)

Los patrones de implementación están documentados en `.github/skills/[skill-name]/SKILL.md`. Sigue estos requisitos obligatorios:

#### [Patrón Obligatorio 1]
**Referencia**: `.github/skills/[skill-name]/SKILL.md#[section-anchor]`

[Descripción en lenguaje natural de QUÉ se debe hacer, no código]

**Requisito**: [Por qué es importante]

#### [Patrón Obligatorio 2]
**Referencia**: `.github/skills/[skill-name]/SKILL.md#[section-anchor]`

[Descripción en lenguaje natural]

**Requisito**: [Por qué es importante]

#### [Patrón Obligatorio 3]
**Referencia**: `.github/skills/[skill-name]/SKILL.md#[section-anchor]`

[Descripción en lenguaje natural]

**Requisito**: [Por qué es importante]

### 🚫 Nunca hagas esto (De la Habilidad)

Refiere a `.github/skills/[skill-name]/SKILL.md#nunca-hagas-esto` para anti-patrones que DEBEN evitarse:

- **Nunca [anti-patrón 1]**: [Breve explicación]
- **Nunca [anti-patrón 2]**: [Breve explicación]
- **Nunca [anti-patrón 3]**: [Breve explicación]

Secciones anti-patrón en la habilidad:
- "[Nombre anti-patrón 1]" (`.github/skills/[skill-name]/SKILL.md#[anchor]`)
- "[Nombre anti-patrón 2]" (`.github/skills/[skill-name]/SKILL.md#[anchor]`)

### ⚠️ Pregunte primero (De la Habilidad)

**[Decisión Arquitectónica 1]**:
```
Referencia: `.github/skills/[skill-name]/SKILL.md#[section-anchor]`

"¿Cuál es tu requisito específico?"

| Opción | Pro | Contra | Cuándo |
|--------|-----|--------|--------|
| [Opción 1] | [Pro] | [Contra] | [Cuándo] |
| [Opción 2] | [Pro] | [Contra] | [Cuándo] |

¿Cuál necesitas?"
```

**[Decisión Arquitectónica 2]**:
```
Referencia: `.github/skills/[skill-name]/SKILL.md#[section-anchor]`

"¿Cuál es tu contexto?"

Opciones:
- [Opción A]: Para [caso de uso]
- [Opción B]: Para [caso de uso]
- [Opción C]: Para [caso de uso]

¿Cuál aplica a tu situación?"
```

---

## Escenarios Comunes

### Escenario 1: [Caso de Uso Común 1]

**Solicitud del usuario**: "[Ejemplo de request]"

**Implementación**: Sigue el patrón en `.github/skills/[skill-name]/SKILL.md` (sección ✅ Siempre) con:
- [Característica 1]
- [Característica 2]
- [Característica 3]

**Decisiones clave**:
- [Decisión 1]: [Opciones]
- [Decisión 2]: [Opciones]
- [Decisión 3]: [Opciones]

---

### Escenario 2: [Caso de Uso Común 2]

**Solicitud del usuario**: "[Ejemplo de request]"

**Implementación**: Combina patrones de:
- `.github/skills/[skill-1]/SKILL.md#[section]` - [Descripción]
- `.github/skills/[skill-2]/SKILL.md#[section]` - [Descripción]

[Descripción del patrón en prosa]

**Decisiones clave**:
- [Decisión 1]
- [Decisión 2]

---

### Escenario 3: [Caso de Uso Común 3]

**Solicitud del usuario**: "[Ejemplo de request]"

**Implementación**: Ver sección "[Nombre de sección]" en `.github/skills/[skill-name]/SKILL.md`

[Descripción del patrón]

**Decisiones clave**:
- [Decisión 1]
- [Decisión 2]

---

## Patrones de Integración

### Con [Otra Tecnología/Caso]

Cuando [contexto específico], combina patrones [skill1] con [skill2].

**Habilidades necesarias**:
- `.github/skills/[skill-1]/SKILL.md` - [Descripción]
- `.github/skills/[skill-2]/SKILL.md` - [Descripción]

**Patrón**:
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]
4. [Paso 4]

**Decisiones clave de diseño**:
- [Decisión 1]
- [Decisión 2]
- [Decisión 3]

---

## Lista de Verificación

Usa esta lista para verificar que la implementación sigue patrones seguros y de calidad.

**Referencia**: `.github/skills/[skill-name]/SKILL.md`

- [ ] [Requisito 1] - [Descripción]
- [ ] [Requisito 2] - [Descripción]
- [ ] [Requisito 3] - [Descripción]
- [ ] [Requisito 4] - [Descripción]
- [ ] [Requisito 5] - [Descripción]
- [ ] [Requisito 6] - [Descripción]

---

## Comandos de Verificación

Sigue los patrones de verificación en `.github/skills/[skill-name]/SKILL.md#bucle-de-verificación` para probar tu implementación.

**Verificaciones esenciales**:
1. [Verificación 1]: [Descripción]
2. [Verificación 2]: [Descripción]
3. [Verificación 3]: [Descripción]
4. [Verificación 4]: [Descripción]

**La verificación debe confirmar**:
- [Confirmación 1]
- [Confirmación 2]
- [Confirmación 3]

---

## Preguntas Comunes

1. **"¿[Pregunta frecuente 1]?"**
   - Ver ⚠️ Pregunte primero en habilidad [skill-name]

2. **"¿[Pregunta frecuente 2]?"**
   - [Respuesta breve o referencia a skill]

3. **"¿[Pregunta frecuente 3]?"**
   - [Respuesta breve o referencia a skill]

---

## Formato de Salida

Cada código generado debe incluir:

1. **Comentario de encabezado** con habilidades usadas:
```python
# Generado usando:
# - .github/skills/[skill-name]/SKILL.md
# - .github/skills/[skill-adicional]/SKILL.md (si aplica)
```

2. **Referencias a secciones específicas** en comentarios del código:
```python
# Ver: .github/skills/[skill-name]/SKILL.md#[section-anchor]
```

3. **Anotaciones de tipo** (obligatorio)

4. **[Elemento específico del dominio]** para [propósito]

5. **Manejo de errores** con [enfoque específico]

6. **Comentarios de [seguridad/calidad]** señalando [requisitos críticos]

---

## Referencias

- **Principal**: `.github/skills/[skill-name]/SKILL.md`
- **Integración**: `.github/skills/[skill-name]/SKILL.md`
- **Integración**: `.github/skills/[skill-name]/SKILL.md`

---

**CRÍTICO**: [Resumen de lo más importante: no duplicar código, mantener único en skills, seguir patrones ✅/🚫/⚠️]


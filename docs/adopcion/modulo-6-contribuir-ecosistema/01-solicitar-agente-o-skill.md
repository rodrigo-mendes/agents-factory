# Cómo solicitar un nuevo agente o skill

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 6 min

---

## Cuándo tiene sentido solicitar un nuevo artefacto

### Solicita una nueva **skill** cuando:

- Tu equipo usa una tecnología de forma frecuente y Copilot genera código que no sigue los patrones ECI para esa tecnología
- Existe un conjunto de "siempre hacer / nunca hacer" bien definido para una herramienta (framework, librería, servicio cloud)
- El mismo contexto técnico se repite en los prompts de varios desarrolladores del equipo

Ejemplos: skill de Spring Boot en ECI, skill de pruebas con Testcontainers, skill de gestión de errores en Lambda.

### Solicita un nuevo **agente** cuando:

- Hay una tarea compleja y repetitiva que sigue siempre los mismos pasos
- La tarea requiere combinar múltiples archivos o recursos de forma orquestada
- El valor de la automatización justifica el tiempo de construcción (tarea que se hace al menos 2-3 veces por semana en el equipo)

Ejemplos: agente para crear microservicios Java con estructura completa, agente para generar módulos Terraform de nueva región, agente para onboarding de nuevos servicios.

---

## Proceso de solicitud

### Paso 1: Documentar el caso de uso

Antes de abrir una solicitud, documenta brevemente:

```markdown
## Solicitud: [Nombre descriptivo del agente/skill]

### Tipo
[ ] Skill  [ ] Agente

### Problema o tarea que resuelve
[Descripción del problema actual: qué tarea es, por qué es repetitiva, qué va mal sin el artefacto]

### Frecuencia de uso estimada
[Cuántas veces por semana/mes se usaría y por cuántos desarrolladores]

### Tecnologías/dominio involucrado
[Stack, framework, servicios cloud...]

### Ejemplo de prompt típico actual (sin el artefacto)
[Cómo describes la tarea hoy en el chat libre, con todo el contexto que tienes que explicar]

### Resultado esperado con el artefacto
[Cómo sería invocar el agente/skill y qué debería producir]

### Equipo solicitante
[Nombre del equipo y Tech Lead de contacto]
```

---

### Paso 2: Abrir la solicitud

Abre un issue en el repositorio `agents-factory` con:
- Título: `[REQUEST] Skill: nombre-de-la-skill` o `[REQUEST] Agente: nombre-del-agente`
- Etiqueta: `solicitud-skill` o `solicitud-agente`
- Contenido: la plantilla del Paso 1

---

### Paso 3: Proceso de evaluación (Equipo de Gobierno ECI)

El Equipo de Gobierno evalúa:

1. **Impacto**: ¿cuántos equipos/desarrolladores se beneficiarían?
2. **Viabilidad técnica**: ¿existe base de conocimiento suficiente para crear el artefacto con calidad?
3. **Priorización**: ¿cómo encaja con el roadmap del programa?

El resultado puede ser:
- **Aprobado**: el equipo de gobierno lo incluye en el backlog con prioridad
- **Aprobado con contribución**: el equipo solicitante participa en la investigación/creación bajo supervisión de gobierno
- **Pendiente**: la solicitud es válida pero hay prerequisitos (research, versiones estables del framework)
- **Rechazado con alternativa**: la solicitud no aplica como artefacto global, pero se sugiere una alternativa (instrucciones de contexto del proyecto, por ejemplo)

---

### Paso 4: Si puedes contribuir a la creación

Si el equipo de gobierno aprueba y el equipo solicitante quiere participar en la creación:

1. Lee los guías técnicos del agents-factory: `docs/como-usar/criando-skills.md` y `docs/como-usar/criando-agentes.md`
2. Usa los prompts de investigación del agents-factory para generar la base de conocimiento
3. Trabaja con el equipo de gobierno en la revisión y validación del artefacto

---

## Qué no solicitar como artefacto global

| Solicitud | Por qué no aplica | Alternativa |
|---|---|---|
| "Un agente para mi proyecto específico" | Los agentes globales son para patrones compartidos | Instrucciones de contexto del proyecto (Módulo 4) |
| "Una skill que haga X de forma distinta a como ya lo hace la skill Y" | Crearía fragmentación | Revisar/actualizar la skill existente |
| "Un agente que sepa cómo funciona nuestro dominio de negocio" | El dominio de negocio no es conocimiento global | Instrucciones de contexto o documentación del equipo |

---

## Próximos pasos

- [6.2 — Ciclo de vida de una skill](02-ciclo-vida-skill.md)
- [6.3 — Post-mortem de agente](03-post-mortem-agente.md)

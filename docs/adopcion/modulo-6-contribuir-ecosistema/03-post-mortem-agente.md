# Post-mortem de agente: cuándo revisar y actualizar

**Perfil:** Tech Lead / Equipo de Gobierno ECI  
**Tiempo estimado de lectura:** 7 min

---

## Para qué sirve un post-mortem de agente

Un post-mortem de agente no es un análisis de fallo — es una **revisión periódica de efectividad**. El objetivo es responder: ¿el agente sigue haciendo bien su trabajo? ¿Hay partes que se pueden mejorar con lo que hemos aprendido usándolo?

Se diferencia de reportar un bug puntual en que es una revisión holística programada, no reactiva.

---

## Cuándo hacer una revisión de agente

### Revisiones programadas

| Frecuencia | Disparador |
|---|---|
| **Trimestral** | Para agentes de uso frecuente (> 50 invocaciones/mes) |
| **Semestral** | Para agentes de uso moderado |
| **Ante actualización de framework** | La versión del framework que usa el agente tiene una nueva major release |
| **Ante cambio de convenciones ECI** | Las convenciones del dominio del agente cambiaron |

### Revisiones reactivas

Haz una revisión inmediata cuando:
- 3 o más developers reportan el mismo problema con el agente en menos de un mes
- El agente pasa a usarse en un caso de uso diferente al original
- Una skill que usa el agente fue actualizada o deprecada

---

## Proceso de revisión

### 1. Recopilar evidencia

Antes de revisar el agente, recopila:

- Feedback de desarrolladores: ¿qué partes del agente corrijen frecuentemente?
- Prompts que funcionan bien vs prompts que generan resultados malos (casos documentados)
- Casos de uso actuales: ¿está el agente siendo usado para lo que fue diseñado?
- Versiones actuales de los frameworks que usa vs versiones del research doc

---

### 2. Revisar el agente contra una checklist

```markdown
## Checklist de revisión de agente — [Nombre del agente] — [Fecha]

### Precisión técnica
[ ] Las skills que usa están actualizadas (< 12 meses o validadas como vigentes)
[ ] Los patrones de código generados siguen siendo correctos para las versiones actuales
[ ] No hay anti-patrones documentados que el agente haga de forma incorrecta

### Usabilidad
[ ] El workflow P0-P5 se completa sin bloqueos en los casos de uso principales
[ ] La propuesta en P3 es clara y no ambigua para el usuario
[ ] Los mensajes de error o de solicitud de contexto son comprensibles

### Cobertura
[ ] Los casos de uso documentados en el catálogo siguen siendo los que los devs usan
[ ] No hay casos de uso frecuentes que el agente no cubra y debería cubrir
[ ] Las herramientas que usa el agente están disponibles en el entorno estándar de ECI

### Calidad del output
[ ] El código generado en el 80% de los casos no requiere correcciones de convenciones
[ ] Los tests generados (si aplica) son tests reales que fallan si el código falla
[ ] La infra generada (si aplica) sigue el principio de mínimo privilegio
```

---

### 3. Clasificar los hallazgos

| Severidad | Criterio | Acción |
|---|---|---|
| **Crítico** | El agente genera código inseguro o con errores sistemáticos | Patch inmediato; notificar a los equipos |
| **Alto** | Patrones desactualizados que producen código incorrecto frecuentemente | Actualización en el próximo sprint |
| **Medio** | Casos de uso no cubiertos que podrían cubrirse | Añadir al backlog con prioridad |
| **Bajo** | Mejoras de UX o mensajes más claros | Mejorar cuando sea conveniente |

---

### 4. Documentar y comunicar

Usa el template en `.github/templates/reports/POST_MORTEM_TEMPLATE.md` para documentar la revisión.

Comparte el resultado con:
- Los Tech Leads de los equipos que usan el agente
- El equipo de gobierno para actualizar el estado en el catálogo

---

## Cómo reportar un problema con un agente (sin hacer una revisión completa)

Si encuentras un problema puntual con un agente, no es necesario hacer una revisión completa. Abre un issue en `agents-factory` con:

- **Título:** `[BUG] Agente @nombre: descripción del problema`
- **Descripción del problema:** qué pediste, qué generó el agente, qué debería haber generado
- **Reproducibilidad:** ¿siempre pasa, o fue una vez?
- **Impacto:** ¿el código generado estaba mal? ¿lo detectaste antes o después de aplicarlo?

---

## Señales de que un agente necesita revisión urgente

- Un developer lleva a producción código generado por el agente que produce un incidente
- El equipo de Terraform/backend dice "dejamos de usar el agente porque siempre genera mal X"
- Una skill que el agente usa fue marcada como deprecada y el agente no fue actualizado
- El agente genera código que usa una librería que fue retirada del stack ECI

---

## Próximos pasos

- [6.1 — Solicitar un nuevo agente o skill](01-solicitar-agente-o-skill.md)
- [6.2 — Ciclo de vida de una skill](02-ciclo-vida-skill.md)
- [Template de post-mortem](../../.github/templates/reports/POST_MORTEM_TEMPLATE.md)

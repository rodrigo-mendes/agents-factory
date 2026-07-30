# Planificación antes de ejecutar

**Perfil:** Dev  
**Tiempo estimado de lectura:** 6 min

---

## Por qué planificar antes de ejecutar

Antes de pedirle a Copilot que modifique código o infraestructura, pídele primero un plan. Copilot trabaja mejor cuando la tarea está clara y acotada, y tú trabajas mejor cuando puedes revisar qué se va a hacer antes de que lo haga.

El chat de Copilot (sin modo agent) es la herramienta de planificación: lo activas con `Ctrl+Alt+I` / `Cmd+Alt+I` y Copilot responde en lenguaje natural **sin modificar ningún archivo**. Cuando el plan esté claro, pasas a Edit mode o a un agente para ejecutarlo.

---

## Cómo dar buen contexto para planificar

### Referenciar archivos con `#`

No pegues el código en el chat. Usa `#` para referenciar archivos directamente:

```
¿Qué hace #OrderService.java y cómo se relaciona con #PaymentRepository.java?
```

Copilot leerá los archivos sin que necesites copiarlos. Más limpio y no llena la ventana de contexto.

### Referenciar el workspace

Usa `#codebase` para dar a Copilot acceso a explorar el proyecto completo cuando no sabes exactamente qué archivos son relevantes:

```
#codebase ¿Dónde se gestiona la autenticación en este proyecto?
```

### Apuntar al editor activo

Si tienes abierto el archivo que quieres comentar, puedes usar `#editor` para que Copilot lo use como contexto principal.

---

## Patrones de planificación frecuentes

### Entender el código antes de modificarlo

```
Explícame el flujo de #NotificationProcessor.java.
¿Qué entra, qué transforma y qué produce?
```

### Investigar antes de implementar

```
Quiero añadir retry logic a este servicio SQS.
¿Cuáles son las opciones en Spring Cloud Function con AWS Lambda?
Dame pros y contras de cada una en máximo 5 bullets.
```

### Analizar un error

```
Tengo este error en CloudWatch:
[pega el stack trace]
¿Cuál es la causa más probable y cómo diagnosticarla?
```

### Revisar una PR mentalmente antes de abrirla

```
Revisa #OrderService.java con foco en:
1. Bugs potenciales
2. Problemas de seguridad
No comentes estilo ni formatting.
```

### Planificar una tarea compleja

```
Tengo que añadir paginación a la API /orders.
El endpoint actual está en #OrderController.java y usa #OrderRepository.java.
¿Qué cambios necesitaría y en qué orden?
```

> **Tip:** Usa el chat para planificar. Una vez tengas el plan revisado y confirmado, pasa a Edit mode o a un agente para implementarlo. No empieces a ejecutar sin tener claro el plan.

---

## Cómo pedir respuestas útiles y concisas

Ask mode tiende a respuestas largas por defecto. Controla el formato con instrucciones explícitas:

```
Dame la respuesta en máximo 5 bullets.
```
```
Solo código, sin explicación.
```
```
Una tabla comparativa: opciones en filas, criterios en columnas.
```
```
Dame primero la respuesta directa y luego el razonamiento si quiero profundizar.
```

Esto es especialmente útil para análisis de errores o comparativas de opciones.

---

## Cuándo el chat de planificación no es suficiente

- Quieres que Copilot **edite código existente** → usa Edit mode
- Quieres que Copilot **implemente algo de principio a fin** → usa un agente customizado
- La tarea ya está clara y no necesita planificación → ve directamente a Edit mode o agente

---

## Planificación y el workflow de agentes

En los agentes customizados, la fase **P3 — Propuesta** es la planificación formal: el agente presenta un plan y espera tu confirmación antes de actuar. Puedes reforzar este comportamiento en el chat libre pidiendo explícitamente:

```
Antes de implementar nada, dame un plan con los pasos que seguirías. Espera mi confirmación.
```

Este patrón aplica a cualquier tarea compleja: pídele a Copilot el plan primero, revísalo y solo entonces aprueba la ejecución.

1. **Planificar** con el chat: `¿Qué cambios necesitaría para X? Dame un plan paso a paso.`
2. **Revisar** el plan: ¿tiene sentido el alcance? ¿falta algo?
3. **Ejecutar** con Edit o Agent mode una vez aprobado el plan

Ver buenas prácticas transversales en Confluence: "Separa exploración de ejecución".

---

## Próximos pasos

- [2.2 — Edit mode: cambios quirúrgicos](02-edit-mode.md)
- [2.3 — Agent mode: tareas multi-paso](03-agent-mode.md)

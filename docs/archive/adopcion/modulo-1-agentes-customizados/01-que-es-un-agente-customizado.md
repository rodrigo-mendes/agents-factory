# Qué es un agente customizado y cómo invocarlo

**Perfil:** Dev  
**Tiempo estimado de lectura:** 7 min

---

## Qué es un agente customizado

Un agente customizado es una versión de Copilot que ha sido instruida específicamente para trabajar con el stack, las convenciones y los procesos de tu proyecto u organización. A diferencia del chat libre, un agente:

- **Verifica las convenciones** del proyecto antes de generar código
- **Sigue un proceso en fases** (no responde de golpe)
- **Usa skills** (bases de conocimiento) con patrones específicos del proyecto/organización
- **Pide confirmación** antes de aplicar cambios grandes

Técnicamente, un agente customizado en VS Code es un archivo `.agent.md` que define el rol, las instrucciones y las herramientas disponibles para una tarea concreta.

---

## Diferencia entre agente, chat libre y modo Edit

| | Chat libre | Edit mode | Agente customizado |
|---|---|---|---|
| **Activa con** | Panel chat, sin `@` | `Ctrl/Cmd+I` | `@nombre-agente` en el chat |
| **Modifica archivos** | No | Sí, directamente | Sí, con planificación previa |
| **Conoce convenciones del proyecto** | Solo si las incluyes en el prompt | Solo si las incluyes | Sí, las carga automáticamente |
| **Proceso en fases** | No | No | Sí (P0-P5) |
| **Pide confirmación** | No | No (muestra diff) | Sí, en la fase P3 |
| **Mejor para** | Preguntas, exploración | Cambios puntuales | Tareas complejas de dominio |

---

## Cómo invocar un agente

### Opción 1: desde el panel de chat

1. Abre el chat (`Ctrl+Alt+I` / `Cmd+Alt+I`)
2. Escribe `@` en el campo de texto
3. Aparecerá una lista con los agentes disponibles en tu workspace
4. Selecciona el agente que necesitas
5. Añade tu instrucción después: `@nombre-agente <tu tarea aquí>`

```
@agente-infra provisiona una función Lambda con trigger SQS y logs en CloudWatch
```

### Opción 2: seleccionar el modo en el desplegable

En la parte superior del panel de chat hay un desplegable que permite elegir entre "Ask", "Edit" y los agentes disponibles. Selecciona el agente directamente desde ahí.

---

## Qué pasa después de invocar el agente

El agente no responde de inmediato con código. Sigue un proceso estructurado:

1. **Carga sus instrucciones y skills** (fase P0) — puedes ver que está leyendo archivos
2. **Analiza el contexto actual** del workspace (fase P1)
3. **Consulta los patrones** de la skill correspondiente (fase P2)
4. **Propone un plan** y te pide confirmación (fase P3) ← aquí debes responder
5. **Implementa** lo acordado (fase P4)
6. **Valida** el resultado (fase P5)

Para más detalle sobre qué significa cada fase desde tu perspectiva, ver [guía 1.3](03-entender-respuesta-workflow-p0-p5.md).

---

## Qué escribirle al agente

El agente ya conoce las convenciones del proyecto, así que **no necesitas explicarle el stack**. Céntrate en describir qué quieres lograr:

✅ Bueno:
```
@agente-infra crea los recursos necesarios para exponer una API REST privada con autenticación Cognito
```

❌ Redundante (el agente ya lo sabe):
```
@agente-infra crea una API usando AWS API Gateway con integración Lambda,
siguiendo las convenciones del proyecto con Terraform modulado y tags estándar...
```

Si tienes restricciones específicas de tu contexto que el agente no puede inferir del workspace, sí añádelas:
```
@agente-infra crea un bucket S3 para almacenar logs. Restricción: debe usar la KMS key existente `alias/proyecto-logs-key`
```

---

## Cuándo no usar un agente customizado

- Para preguntas rápidas o exploratorias → usa el chat libre
- Para editar un bloque de código concreto → usa Edit mode (`Ctrl/Cmd+I`)
- Si el agente no cubre tu dominio → usa el chat libre con las instrucciones de contexto de tu proyecto

Para el árbol de decisión completo, ver [guía 1.2](02-cuando-usar-agente-vs-chat-libre.md).

---

## Próximos pasos

- [1.2 — Cuándo usar agente vs chat libre](02-cuando-usar-agente-vs-chat-libre.md)
- [1.3 — Entender la respuesta del agente (P0-P5)](03-entender-respuesta-workflow-p0-p5.md)
- [1.5 — Catálogo de agentes ECI](05-catalogo-agentes-eci.md)

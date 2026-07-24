# GitHub Copilot en ECI: modos, capacidades y límites

**Perfil:** Todos  
**Tiempo estimado de lectura:** 8 min

---

## Qué es GitHub Copilot

GitHub Copilot es un asistente de IA integrado en VS Code que ayuda a escribir, entender y modificar código. En ECI opera bajo el plan **Copilot Business/Enterprise**, lo que habilita controles de privacidad, bloqueo de sugerencias de código público y administración centralizada de políticas.

Copilot **no es**:
- Un motor de búsqueda de documentación (aunque puede resumirla si tú le das el contexto)
- Un sistema que accede a internet en tiempo real por defecto
- Un reemplazo del code review humano
- Un sistema que recuerda conversaciones anteriores entre sesiones

---

## Los tres modos principales

### Ask mode (chat)

> Úsalo para: explorar, preguntar, entender, planificar.

El modo más común. Abre el panel de chat con `Ctrl+Alt+I` / `Cmd+Alt+I` y escribe tu pregunta. Copilot responde en lenguaje natural y puede incluir código como parte de la respuesta, pero **no modifica archivos directamente**.

Ejemplos de cuándo usarlo:
- "¿Qué hace este método `processOrder()`?"
- "¿Cuál sería la mejor estructura para este servicio?"
- "Explícame las diferencias entre `SQS` y `SNS`."

**Consejo:** En Ask mode puedes referenciar archivos con `#nombre-del-archivo` para darle contexto sin tener que pegar el código manualmente.

---

### Edit mode (edición inline)

> Úsalo para: cambios quirúrgicos en uno o varios archivos abiertos.

Actívalo con `Ctrl+I` / `Cmd+I` directamente sobre el código que quieres cambiar. Copilot propone un diff que puedes aceptar o rechazar. A diferencia del chat, aquí **Copilot escribe directamente en tus archivos** (con vista previa antes de aplicar).

Ejemplos de cuándo usarlo:
- Refactorizar un método concreto
- Añadir manejo de errores a una función existente
- Renombrar variables en un bloque de código
- Generar un test unitario para una función seleccionada

**Consejo:** Selecciona primero el bloque de código que quieres cambiar antes de activar Edit mode. Cuanto más acotado el contexto, más preciso el cambio.

---

### Agent mode (agente autónomo)

> Úsalo para: tareas complejas que implican múltiples pasos, herramientas o archivos.

Agent mode permite que Copilot planifique y ejecute una secuencia de acciones: leer archivos, ejecutar comandos en terminal, escribir código, validar resultados. A diferencia de Ask y Edit, **el agente toma decisiones de forma autónoma** entre pasos.

En ECI, Agent mode es la base sobre la que funcionan los **agentes customizados** (ver Módulo 1).

Ejemplos de cuándo usarlo:
- Implementar una funcionalidad completa desde cero
- Ejecutar y corregir una suite de tests en bucle hasta que pasen
- Analizar una arquitectura y proponer cambios con justificación

**Consejo:** En Agent mode, supervisa los pasos a medida que el agente avanza. Puedes interrumpir y corregir si el agente va en una dirección equivocada.

---

## Resumen de modos

| Modo | Activa con | Modifica archivos | Mejor para |
|---|---|---|---|
| Ask | `Ctrl+Alt+I` / `Cmd+Alt+I` | No (responde en chat) | Explorar, preguntar, entender |
| Edit | `Ctrl+I` / `Cmd+I` | Sí (con vista previa) | Cambios puntuales en código |
| Agent | Panel chat → modo Agent | Sí (autónomo) | Tareas multi-paso complejas |

---

## Capacidades clave en ECI

| Capacidad | Disponible | Notas |
|---|---|---|
| Autocompletado inline | ✅ | Activo por defecto mientras escribes |
| Chat en VS Code | ✅ | Ask y Agent mode |
| Copilot en GitHub.com (PRs, Issues) | ✅ | Según plan |
| Agentes customizados ECI | ✅ | Ver catálogo en Módulo 1 |
| Acceso a internet en tiempo real | ❌ | Copilot no navega por defecto |
| Memoria entre sesiones | ❌ | Cada conversación empieza desde cero |
| Ejecución de código en producción | ❌ | Solo propone, tú ejecutas |

---

## Límites importantes

### Ventana de contexto

Cada conversación tiene un límite de tokens (unidades de texto que Copilot puede procesar a la vez). Cuando la conversación se llena:
- Las respuestas se vuelven más genéricas
- Copilot puede "olvidar" instrucciones dadas al inicio
- La calidad de las sugerencias baja

**Qué hacer:** Empieza una conversación nueva con un resumen del estado actual. Ver guías de gestión de sesión en Confluence.

### Fiabilidad de las respuestas

Copilot puede generar código plausible pero incorrecto, especialmente en:
- APIs poco comunes o muy recientes
- Lógica de negocio específica de ECI que no está en su contexto
- Interacciones entre sistemas complejos

**Qué hacer:** Revisa siempre el código generado. Usa los agentes customizados ECI para tareas donde la precisión sobre nuestro stack es crítica.

### Datos sensibles

Nunca incluyas en el chat: contraseñas, tokens, claves de API, datos de clientes o información interna clasificada. Ver Módulo 5.

---

## Próximos pasos

- [Módulo 0.2 — Mapa del ecosistema Copilot ECI](02-mapa-ecosistema-copilot-eci.md)
- [Módulo 0.3 — Setup del entorno: día 1](03-setup-entorno-dia-1.md)
- [Módulo 2 — Modos de Copilot en detalle](../modulo-2-modos-copilot/README.md)

# Entender la respuesta de un agente: el workflow P0-P5

**Perfil:** Dev  
**Tiempo estimado de lectura:** 8 min

---

## Por qué los agentes ECI no responden de golpe

A diferencia del chat libre, los agentes de ECI siguen un proceso en seis fases antes de escribir una sola línea de código. Este proceso garantiza que el agente:

1. Usa los patrones correctos del stack ECI
2. Entiende el contexto actual de tu proyecto
3. Te muestra un plan antes de actuar

Conocer estas fases te permite saber **qué está haciendo el agente en cada momento** y cuándo intervenir.

---

## Las seis fases desde tu perspectiva

### P0 — Cargando instrucciones

**Qué verás:** el agente informa que está cargando skills e instrucciones, o VS Code muestra que está leyendo archivos.

**Qué hace internamente:** el agente carga las skills relevantes (bases de conocimiento con patrones ECI), las instrucciones del proyecto y su propia configuración.

**Qué haces tú:** nada. Espera. Esta fase es automática y suele durar segundos.

**Señal de problema:** si el agente dice que no encuentra un archivo de skill o instrucción, puede que los artefactos no estén bien copiados a tu workspace. Ver [guía 1.4](04-cuando-el-agente-falla.md).

---

### P1 — Analizando el workspace

**Qué verás:** el agente lee archivos de tu proyecto: estructura de carpetas, archivos de configuración, código existente.

**Qué hace internamente:** entiende el estado actual antes de proponer cambios para no generar código que choque con lo que ya existe.

**Qué haces tú:** nada, pero puedes observar qué archivos está leyendo. Si ves que está leyendo archivos irrelevantes para tu tarea, puedes interrumpir y ser más específico en el prompt.

---

### P2 — Consultando patrones

**Qué verás:** el agente puede mostrar fragmentos de las reglas que aplica (✅ siempre hacer, ⚠️ preguntar primero, 🚫 nunca hacer).

**Qué hace internamente:** contrasta tu tarea contra los patrones de la skill para asegurarse de que la implementación seguirá las convenciones ECI.

**Qué haces tú:** nada. Si el agente detecta un punto que requiere una decisión de diseño (marcado con ⚠️), puede hacerte una pregunta antes de continuar. Respóndela.

**Ejemplo de pregunta en P2:**
```
⚠️ La skill indica que el cifrado en reposo es configurable.
¿Quieres activar cifrado con KMS para este bucket S3, o usar el cifrado por defecto de S3?
```

---

### P3 — Propuesta + tu confirmación ← punto de mayor interacción

**Qué verás:** el agente presenta un plan estructurado de lo que va a hacer, generalmente en forma de lista de acciones o archivos que creará/modificará.

**Qué hace internamente:** nada todavía. Está esperando tu aprobación antes de escribir código.

**Qué haces tú:** **revisa el plan y responde.** Opciones:
- `"Adelante"` / `"Confirmo"` → el agente implementa el plan tal cual
- `"Adelante, pero sin el paso 3"` → apruebas parcialmente
- `"Cambia X por Y y luego procede"` → corriges antes de implementar
- `"Para"` / `"Cancela"` → abortas

**Esta es la fase más importante.** Si el plan no tiene sentido, es más fácil corregirlo aquí que después de que el agente haya generado código.

**Ejemplo de propuesta P3:**
```
Plan de implementación:
1. Crear módulo Terraform `modules/lambda-sqs/`
   - main.tf: función Lambda + queue SQS + trigger event source mapping
   - variables.tf: nombre de función, memoria, timeout
   - outputs.tf: ARN de función y URL de queue
2. Actualizar `environments/dev/main.tf` para referenciar el nuevo módulo
3. Añadir tags estándar ECI a todos los recursos

¿Confirmas o quieres ajustar algo?
```

---

### P4 — Implementación

**Qué verás:** el agente genera archivos, escribe código, posiblemente ejecuta comandos (como `terraform validate`).

**Qué hace internamente:** implementa exactamente lo que se aprobó en P3.

**Qué haces tú:** supervisa. Puedes ver los archivos que va creando. Si algo no va bien (genera un archivo en la ruta equivocada, escribe algo incorrecto), puedes interrumpir.

---

### P5 — Validación

**Qué verás:** el agente ejecuta comandos de verificación (terraform validate, maven test, etc.) y reporta el resultado.

**Qué hace internamente:** verifica que lo que generó es sintácticamente correcto y consistente.

**Qué haces tú:** revisar el resultado de la validación. Si hay errores, el agente puede intentar corregirlos automáticamente. Si la corrección no funciona en dos intentos, interrumpe y revisa manualmente.

---

## Resumen de las fases

| Fase | Nombre | Necesitas actuar | Duración típica |
|---|---|---|---|
| P0 | Cargando instrucciones | No | Segundos |
| P1 | Analizando workspace | No | 10-30 s |
| P2 | Consultando patrones | A veces (si hay ⚠️) | Segundos |
| **P3** | **Propuesta** | **Sí — confirmar plan** | Hasta que tú respondas |
| P4 | Implementación | Supervisar | 30 s – varios minutos |
| P5 | Validación | Revisar resultado | 10-60 s |

---

## Cuándo interrumpir

Puedes interrumpir el agente en cualquier momento usando el botón de stop del chat o escribiendo un mensaje. Los buenos momentos para hacerlo:

- **En P1** si ves que está leyendo archivos completamente fuera de contexto
- **En P3** si el plan no es lo que querías (mejor corregirlo aquí)
- **En P4** si ves que está generando algo incorrecto
- **Nunca** en P0 o P2 sin razón, ya que esas fases son automáticas y necesarias

---

## Próximos pasos

- [1.4 — Qué hacer cuando el agente se desvía o falla](04-cuando-el-agente-falla.md)
- [1.2 — Cuándo usar agente vs chat libre](02-cuando-usar-agente-vs-chat-libre.md)

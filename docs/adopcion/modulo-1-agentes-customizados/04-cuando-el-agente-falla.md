# Qué hacer cuando el agente se desvía o falla

**Perfil:** Dev  
**Tiempo estimado de lectura:** 7 min

---

## Tipos de problemas

Los problemas con agentes customizados caen en cuatro categorías:

1. **El agente no arranca** — error al invocar o las fases P0/P1 fallan
2. **El agente se desvía del objetivo** — empieza bien pero genera algo diferente a lo pedido
3. **El agente genera código incorrecto** — la lógica o la sintaxis tiene errores
4. **El agente se queda bloqueado** — deja de responder o entra en bucle

---

## 1. El agente no arranca

**Síntomas:**
- Mensaje de error al invocar `@nombre-agente`
- El agente dice que no encuentra archivos de instrucciones o skills
- No aparece `@nombre-agente` en la lista del chat

**Causas y soluciones:**

| Causa | Solución |
|---|---|
| El `.agent.md` no está en el workspace | Copia los artefactos del agents-factory a tu proyecto o abre agents-factory en el workspace. Ver [guía 0.3](../modulo-0-fundamentos/03-setup-entorno-dia-1.md) |
| Versión de Copilot Chat desactualizada | Actualiza la extensión (`Ctrl+Shift+X` → GitHub Copilot Chat → Update) |
| El nombre del agente es incorrecto | Escribe `@` en el chat y revisa los nombres exactos en la lista |
| El agente cita una skill que no existe | Reporta al Equipo de Gobierno ECI (ver [Módulo 6.1](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md)) |

---

## 2. El agente se desvía del objetivo

**Síntomas:**
- En P3, el plan propuesto no es lo que pediste
- En P4, el agente genera archivos o lógica que no pediste
- El resultado final está lejos de la intención original

**Qué hacer:**

**Paso 1 — Interrumpe lo antes posible**

Si lo detectas en P3, mucho mejor que en P4. Escribe al chat: `Para. Quiero ajustar el plan.`

**Paso 2 — Reformula el objetivo con más precisión**

El desvío suele venir de una instrucción ambigua. Identifica qué parte del prompt fue ambigua y sé más específico:

❌ Ambiguo:
```
@agente-infra crea infraestructura para el servicio de notificaciones
```

✅ Preciso:
```
@agente-infra crea solo la función Lambda y la queue SQS para el servicio de notificaciones.
No incluyas API Gateway ni base de datos. El nombre de la función debe ser `notificaciones-processor`.
```

**Paso 3 — Proporciona contexto que el agente no puede inferir**

Si el agente no tiene acceso a ciertos archivos de tu proyecto, puede asumir cosas incorrectas. Añade referencias explícitas:

```
@agente-infra crea el trigger SQS para la función Lambda en #src/lambda/NotificationProcessor.java
Usa la queue definida en #terraform/modules/sqs/main.tf
```

**Paso 4 — Empieza la conversación de nuevo si hay mucho ruido acumulado**

Si ya van varios intercambios y el agente sigue sin entender lo que quieres, empieza una conversación nueva con un prompt más preciso. Una conversación limpia da mejores resultados que intentar corregir una conversación que se torció.

---

## 3. El agente genera código incorrecto

**Síntomas:**
- El código no compila o tiene errores de sintaxis
- La lógica no hace lo que describe
- Los nombres de recursos, variables o funciones no siguen las convenciones

**Qué hacer:**

**Para errores de sintaxis o compilación:**

En P5, el agente debería detectarlos y corregirlos automáticamente. Si no lo hace o no lo consigue en dos intentos:

```
El código en [archivo] tiene este error: [pega el error exacto]. 
Corrige solo esa función sin tocar el resto.
```

**Para lógica incorrecta:**

```
La función `processOrder` debería hacer X pero hace Y. 
Aquí está el comportamiento esperado: [describe con precisión].
```

**Para nombres que no siguen las convenciones:**

Primero verifica si la convención está en el archivo de instrucciones del proyecto. Si no está, el agente no puede saberla:

```
En ECI usamos el naming `eci-{env}-{servicio}-{recurso}`. 
Actualiza los nombres de recursos siguiendo ese patrón.
```

Si la convención debería estar en la skill pero no está, repórtalo al Equipo de Gobierno ECI.

---

## 4. El agente se queda bloqueado

**Síntomas:**
- El spinner de carga no desaparece durante más de 2 minutos
- El agente da vueltas corrigiendo el mismo error repetidamente
- Mensajes sin coherencia o incompletos

**Qué hacer:**

1. **Detén el agente** con el botón de stop
2. **Evalúa qué se completó bien** — los archivos ya generados pueden seguir siendo válidos
3. **Empieza una conversación nueva** con un resumen de lo que ya está hecho:
   ```
   Ya creé los módulos Terraform en `modules/lambda-sqs/`. 
   Ahora necesito solo actualizar `environments/dev/main.tf` para referenciarlos.
   ```
4. Si el bloqueo ocurre siempre en el mismo punto, probablemente hay un bug en el agente — repórtalo al Equipo de Gobierno ECI.

---

## Cuándo escalar al Equipo de Gobierno ECI

Escala cuando el problema es del agente en sí, no de tu prompt:

- El agente cita una skill que no existe o está desactualizada
- El agente genera código que incumple convenciones ECI documentadas
- El agente se bloquea siempre en la misma tarea reproducible
- Quieres solicitar una nueva funcionalidad al agente

**Cómo escalar:** ver [Módulo 6.1 — Solicitar un nuevo agente o skill](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md).

---

## Checklist rápido para diagnóstico

```
¿El agente arranca?
  └── No → Verificar setup del workspace (guía 0.3)

¿El plan en P3 tiene sentido?
  └── No → Interrumpir, reformular el prompt, relanzar

¿El código generado tiene errores?
  └── Sí, sintaxis/compilación → Dejar que P5 lo corrija; si no puede, dar el error exacto
  └── Sí, lógica → Describir el comportamiento esperado con precisión
  └── Sí, naming → Dar la convención explícita; si debería estar en la skill, reportar

¿El agente no avanza?
  └── Empezar conversación nueva con estado actual del workspace
```

---

## Próximos pasos

- [1.5 — Catálogo de agentes ECI](05-catalogo-agentes-eci.md)
- [6.1 — Cómo reportar o solicitar mejoras en agentes](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md)

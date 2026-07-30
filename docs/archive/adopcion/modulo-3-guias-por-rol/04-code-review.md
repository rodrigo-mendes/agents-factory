# Copilot para Code Review

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 8 min

---

## Por qué la revisión asistida por Copilot es útil y por qué tiene límites

Copilot puede ayudarte a identificar bugs, problemas de seguridad y deuda técnica en un código que no escribiste, o en el tuyo antes de enviarlo a revisión. Sin embargo:

- **No conoce el contexto de negocio** de tu producto ni las decisiones de diseño pasadas
- **No puede aprobar ni rechazar** un PR — esa es tu responsabilidad
- **Puede dar falsos negativos** (no encontrar algo que sí está mal) o falsos positivos

Usa Copilot como un **primer filtro** que te ayuda a no pasar por alto lo obvio, no como un revisor sustituto.

---

## Casos de uso frecuentes

### 1. Revisión acotada antes de hacer PR (auto-review)

**Modo recomendado:** chat

```
Revisa #OrderService.java con foco en:
1. Bugs potenciales (null pointers, condiciones de carrera, off-by-one)
2. Vulnerabilidades de seguridad (inyección, exposición de datos, autorización)
3. Regresiones respecto a la interfaz pública (cambios de firma, comportamiento)

NO comentes:
- Estilo o formatting
- Naming de variables que ya sigue la convención
- Mejoras "nice-to-have"

Formato: tabla con columna Problema, Línea aproximada, Severidad (Alta/Media/Baja), Fix sugerido.
```

---

### 2. Revisar lógica de negocio específica

**Modo recomendado:** chat con contexto

```
Revisa la lógica de cálculo de descuentos en #DiscountCalculator.java.
El requisito es: descuento del 10% para pedidos > 100€, 
20% para pedidos > 500€, sin acumulación con descuentos de campaña.

¿La implementación actual refleja correctamente este requisito?
Identifica discrepancias o casos edge no manejados.
```

---

### 3. Revisar cambios de un PR

**Modo recomendado:** chat con el diff

```
Tengo este diff de un PR que modifica el servicio de autenticación:
[pega el diff o usa #archivo]

Revisa con foco en:
1. ¿Hay regresiones en el manejo de tokens?
2. ¿Se valida correctamente la expiración?
3. ¿Hay datos sensibles que se podrían logar accidentalmente?

Dame solo los problemas concretos que encuentres.
```

---

### 4. Revisar migraciones de base de datos

**Modo recomendado:** chat

```
Revisa la migración en #V23__add_order_audit_table.sql:
1. ¿Puede ejecutarse sin bloquear tablas en producción (tabla orders tiene 50M registros)?
2. ¿Hay algún rollback implícito si falla a mitad?
3. ¿Los índices definidos son suficientes para los queries más frecuentes?
```

---

### 5. Revisar contratos de API

**Modo recomendado:** chat

```
Compara #api/v1/openapi.yaml (versión actual) con #api/v2/openapi.yaml (nueva versión).
¿Hay breaking changes? Lista cada uno con:
- Endpoint afectado
- Tipo de cambio (campo eliminado, tipo cambiado, comportamiento alterado)
- Impacto para clientes que usan la v1
```

---

### 6. Generar un checklist de revisión para tu equipo

**Modo recomendado:** chat

```
Analiza los últimos PRs en este repositorio (archivos en #src/) y genera
un checklist de revisión específico para este proyecto.
Debe incluir los puntos más relevantes para nuestro stack Java + AWS Lambda.
Máximo 15 puntos, ordenados por importancia.
```

---

## Cómo pedir una revisión realmente útil

La calidad de una revisión de Copilot depende casi completamente de qué le pidas revisar.

### Define el foco

❌ Genérico (respuesta larga, poco accionable):
```
Revisa este código.
```

✅ Acotado (respuesta corta, accionable):
```
Revisa solo la seguridad del manejo de tokens JWT en #AuthService.java.
Dame máximo 5 problemas ordenados por severidad.
```

### Proporciona el contexto de negocio que Copilot no tiene

```
Este endpoint es público (sin autenticación), así que la validación de entrada es crítica.
Revisa #PublicOrderController.java con ese foco.
```

### Separa las revisiones por área

Una revisión que pide "bugs + seguridad + rendimiento + estilo + arquitectura" produce respuestas largas y genéricas. Haz una revisión por área:

1. `Revisa bugs y lógica incorrecta.`
2. (Si la anterior no encontró nada crítico) `Revisa implicaciones de seguridad.`
3. (Solo si necesario) `Revisa rendimiento en los paths críticos.`

---

## Qué no delegar a Copilot en una revisión

| No delegar | Por qué |
|---|---|
| Decisiones de diseño arquitectónico | Copilot no conoce las restricciones del negocio |
| Aprobación final del PR | La responsabilidad es tuya |
| Revisar si un feature "tiene sentido" para el producto | Requiere contexto de negocio que Copilot no tiene |
| Revisar conformidad con requisitos legales o de compliance | Demasiado crítico para depender de IA |

---

## Integración con el flujo de revisión del equipo

Si tu equipo usa GitHub Pull Requests, puedes combinar Copilot con el proceso de revisión existente:

1. **Antes de publicar el PR** — auto-review con Copilot para pillar lo obvio
2. **Al revisar el PR de otro** — pega el diff en el chat para un segundo par de ojos
3. **Después de la revisión humana** — si hay un comentario de revisión que no entiendes, explícaselo a Copilot para entender el razonamiento

Ver también [Módulo 5.2 — Responsabilidad humana en el código generado](../modulo-5-seguridad-gobernanza/02-responsabilidad-revision-codigo.md).

---

## Próximos pasos

- [5.2 — Responsabilidad humana: revisar siempre el código generado](../modulo-5-seguridad-gobernanza/02-responsabilidad-revision-codigo.md)
- [3.1 — Backend Java/Spring](01-backend-java-kotlin-spring.md)
- [3.3 — QA y Testing](03-qa-testing.md)

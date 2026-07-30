# Copilot para Backend: Java/Kotlin/Spring

**Perfil:** Dev Backend  
**Stack cubierto:** Java 17/21, Spring Boot, Spring Cloud Function, Maven  
**Tiempo estimado de lectura:** 10 min

---

## Antes de empezar

El equipo de gobierno mantiene una base de conocimiento de referencia sobre el SDK Java y los patrones de uso. Cuando uses los agentes o el chat para tareas Java, puedes referenciar esos docs con `#ruta-del-doc` si el agente los necesita como contexto adicional.

> Cuando exista una skill Java del programa, los agentes la cargarán automáticamente y no necesitarás hacer esto manualmente.

---

## Casos de uso frecuentes

### 1. Generar un servicio nuevo

**Modo recomendado:** Agente customizado (cuando exista) / Chat libre con contexto de proyecto

```
Crea un servicio Spring Boot `OrderNotificationService` que:
- Escucha mensajes SQS de tipo OrderCreated (estructura en #dto/OrderCreatedEvent.java)
- Procesa el mensaje y llama a #EmailService.java para notificar al cliente
- Registra el resultado en la tabla DynamoDB usando #NotificationRepository.java
- Incluye manejo de errores con retry para fallos transitorios de email

Sigue el patrón de los servicios existentes en #src/services/.
```

**Consejo:** referencia siempre los servicios o clases existentes relacionados con `#`. El modelo de código de tu proyecto es el mejor ejemplo de convenciones.

---

### 2. Añadir manejo de errores a un método existente

**Modo recomendado:** Edit mode

```
[Selecciona el método]
Ctrl+I →
Añade manejo de errores:
- SqsException: log ERROR con messageId, no relanzar (mensaje procesado como error)
- DataAccessException: log ERROR con orderId, relanzar como OrderProcessingException
- IllegalArgumentException: log WARN, relanzar como is
```

---

### 3. Escribir tests unitarios

**Modo recomendado:** Edit mode o Chat libre

```
[Selecciona la clase a testear]
Ctrl+I →
Genera tests JUnit 5 con Mockito para OrderNotificationService.
Cubre:
- Camino feliz: mensaje válido, email enviado, resultado persistido
- SqsException: log de error, sin relanzar
- EmailService no disponible: retry y log de warning
Usa nombres de test descriptivos en español.
```

O en chat si quieres más control:
```
Genera los tests para #OrderNotificationService.java con JUnit 5 y Mockito.
No uses @SpringBootTest (tests unitarios puros, sin contexto Spring).
Explícame qué cubres antes de escribirlos.
```

---

### 4. Entender código heredado

**Modo recomendado:** chat (planificación)

```
Explícame el flujo completo de #LegacyOrderProcessor.java.
Identifica:
1. Qué datos de entrada necesita
2. Qué efectos secundarios produce (DB, mensajes, logs)
3. Qué casos de error maneja y cuáles no

Formato: lista numerada, máximo 10 puntos.
```

---

### 5. Refactorizar código para mejorar testabilidad

**Modo recomendado:** planificación en el chat → Edit mode para cada cambio

```
[Chat]
El servicio #PaymentProcessor.java es difícil de testear porque tiene dependencias directas.
¿Qué refactorizaciones concretas lo harían más testeable?
Dame un plan de cambios con el impacto de cada uno. Espera mi confirmación antes de actuar.
```

Luego aplica cada cambio propuesto con Edit mode.

---

### 6. Revisar rendimiento o problemas de memoria

**Modo recomendado:** chat (planificación)

```
Analiza #OrderRepository.java en busca de:
- N+1 queries potenciales
- Carga de colecciones no lazy cuando no es necesario
- Lecturas que podrían beneficiarse de caché

Para cada problema encontrado: descripción del problema, línea aproximada, y fix propuesto.
```

---

### 7. Migrar de una versión a otra

**Modo recomendado:** chat (planificación) → Agent mode para ejecutar

```
[Chat]
¿Qué cambios de breaking changes hay entre Spring Boot 3.1 y 3.3
que puedan afectar a un proyecto que usa Spring Data JPA y Spring Cloud AWS?
Dame solo los cambios que son relevantes para nuestro stack.
```

---

## Errores comunes a evitar

| Error | Qué pasa | Cómo evitarlo |
|---|---|---|
| Pedir tests sin especificar el tipo | Copilot genera @SpringBootTest pesados | Especifica "tests unitarios con Mockito, sin contexto Spring" |
| No referenciar clases relacionadas | El código generado no encaja con lo existente | Usa `#` para referenciar las clases que interactúan |
| Aceptar código con imports incorrectos | El código no compila | Revisa siempre los imports en el diff antes de aceptar |
| Pedir "refactoriza toda la clase" sin límites | Copilot cambia cosas que no debía | Acota: "refactoriza solo el método X sin cambiar la interfaz pública" |

---

## Señales de que necesitas un agente, no el chat

- Siempre terminas explicando los mismos patrones ECI en el prompt
- El código generado no sigue la estructura de paquetes del proyecto
- Copilot genera código que usa frameworks o librerías que no están en tu `pom.xml`

Cuando llegue el agente backend ECI, resolverá estos problemas automáticamente.

---

## Próximos pasos

- [3.2 — Infra con Terraform y AWS](02-infraestructura-terraform-aws.md)
- [3.3 — QA y Testing](03-qa-testing.md)
- [Catálogo de agentes ECI](../modulo-1-agentes-customizados/05-catalogo-agentes-eci.md)

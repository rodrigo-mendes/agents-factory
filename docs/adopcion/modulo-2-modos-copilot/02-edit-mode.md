# Edit mode: cambios quirúrgicos en archivos

**Perfil:** Dev  
**Tiempo estimado de lectura:** 5 min

---

## Para qué sirve Edit mode

Edit mode permite pedirle a Copilot que modifique directamente el código que tienes seleccionado o el archivo activo. A diferencia del chat, **la respuesta aparece como un diff** que puedes aceptar o rechazar bloque a bloque.

Es el modo correcto cuando sabes exactamente **qué quieres cambiar y dónde**.

---

## Cómo activarlo

1. Selecciona el bloque de código que quieres cambiar (o coloca el cursor en la función)
2. Pulsa `Ctrl+I` / `Cmd+I`
3. Escribe la instrucción en el popup que aparece
4. Copilot muestra el diff propuesto
5. Acepta con `Tab` / rechaza con `Esc` / acepta bloque a bloque con los botones que aparecen

---

## La clave: seleccionar bien el contexto

Cuanto más acotado el código que seleccionas, más preciso el cambio. Si seleccionas todo el archivo, Copilot puede proponer cambios en partes que no quieres tocar.

**Buena práctica:**
- Para cambiar un método: selecciona solo ese método
- Para añadir validación: selecciona el bloque donde va la validación
- Para refactorizar una clase: selecciona la clase completa pero sé explícito en la instrucción sobre qué no cambiar

---

## Patrones de uso frecuentes en ECI

### Refactorizar un método

```
[Selecciona el método processOrder()]
Ctrl+I →
Refactoriza este método para extraer la lógica de validación en un método privado `validateOrder`.
No cambies la firma pública del método.
```

### Añadir manejo de errores

```
[Selecciona el bloque try-catch o la función sin manejo de errores]
Ctrl+I →
Añade manejo de errores: captura SqsException por separado,
loga el error con el correlationId del mensaje y relanza como RuntimeException.
```

### Generar un test unitario

```
[Selecciona la clase o método a testear]
Ctrl+I →
Genera los tests unitarios con JUnit 5 y Mockito para todos los métodos públicos.
Cubre el camino feliz y los casos de error principales.
```

### Añadir logs

```
[Selecciona el método]
Ctrl+I →
Añade logs SLF4J al inicio y al final del método,
con nivel INFO y con el parámetro orderId como contexto.
```

### Actualizar nomenclatura

```
[Selecciona el bloque afectado]
Ctrl+I →
Renombra todas las variables `req` a `orderRequest` y `res` a `orderResponse`.
```

---

## Instrucciones efectivas en Edit mode

Edit mode funciona mejor con instrucciones que especifican:
- **Qué hacer** y **qué no tocar**
- **El nombre exacto** de métodos, variables o clases relevantes
- **El comportamiento esperado**, no solo la forma

✅ Preciso:
```
Añade validación null-check para el campo `customerId` antes de la línea con `repository.findById`.
Lanza IllegalArgumentException con el mensaje "customerId cannot be null".
```

❌ Vago:
```
Arregla los null checks.
```

---

## Revisar el diff antes de aceptar

**Siempre revisa el diff completo antes de aceptar**, especialmente cuando:
- Seleccionaste un bloque grande
- La instrucción afectaba lógica de negocio
- El método tiene efectos secundarios

Copilot puede proponer cambios adicionales que no pediste. El botón "Accept All" acepta todo; usa "Accept Block" para revisar cambio a cambio si tienes dudas.

---

## Cuándo Edit mode no es suficiente

- El cambio afecta múltiples archivos que no tienes abiertos → considera el chat para planificar + Edit mode en cada archivo
- Necesitas provisionar infra o generar varios archivos nuevos → usa un agente
- Necesitas que Copilot conozca las convenciones ECI para el cambio → usa un agente (tiene las skills)

---

## Próximos pasos

- [2.3 — Agent mode: tareas multi-paso](03-agent-mode.md)
- [1.2 — Cuándo usar agente vs chat libre](../modulo-1-agentes-customizados/02-cuando-usar-agente-vs-chat-libre.md)

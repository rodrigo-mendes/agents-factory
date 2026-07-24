# Copilot para QA y Testing

**Perfil:** QA / Dev Backend  
**Stack cubierto:** JUnit 5, Mockito, LocalStack, Testcontainers, Spring Boot Test  
**Tiempo estimado de lectura:** 10 min

---

## Casos de uso frecuentes

### 1. Generar tests unitarios para una clase

**Modo recomendado:** Edit mode o chat

**Edit mode (más rápido para clases pequeñas):**
```
[Selecciona la clase]
Ctrl+I →
Genera tests JUnit 5 con Mockito para todos los métodos públicos.
Tests unitarios puros: sin @SpringBootTest, sin contexto Spring.
Cubre: camino feliz + los 2-3 casos de error más probables por método.
Nombres de test en inglés en formato `should_<resultado>_when_<condición>`.
```

**Chat (mejor cuando quieres planificar antes de generar):**
```
Para #OrderService.java:
1. Lista todos los métodos públicos
2. Para cada método, describe los casos de test que cubrirías
3. Espera mi confirmación antes de escribir el código

Después generamos los tests uno a uno.
```

---

### 2. Analizar un test que falla

**Modo recomendado:** chat → Edit mode para el fix

```
[Chat]
Tengo este test fallando:
[pega el nombre del test y el stack trace]

El test está en #OrderServiceTest.java.
La clase que testea es #OrderService.java.

¿Cuál es la causa del fallo? ¿El test está mal o la implementación?
Dame la causa y el fix mínimo, sin tocar más de lo necesario.
```

---

### 3. Identificar código sin cobertura

**Modo recomendado:** chat

```
Analiza #PaymentService.java y #PaymentServiceTest.java.
Identifica los métodos o paths de código en PaymentService que NO tienen tests en PaymentServiceTest.
Lista cada gap encontrado y propón un nombre descriptivo de test para cubrirlo.
```

---

### 4. Generar tests de integración con LocalStack

**Modo recomendado:** chat para planificar → Agent mode para implementar

```
[Chat]
Quiero escribir un test de integración para #NotificationProcessor.java
que verifique el flujo completo: mensaje SQS → procesamiento → registro en DynamoDB.
Usamos LocalStack para los servicios AWS.

¿Qué setup necesita el test (contenedores, configuración, datos de prueba)?
Dame el plan antes de implementar nada.
```

Una vez tengas el plan:
```
[Agent mode / chat]
Implementa el test de integración descrito. 
Usa Testcontainers con la imagen localstack/localstack:latest.
El test debe ser independiente: crear sus propios recursos y limpiarlos al terminar.
```

---

### 5. Mejorar la calidad de los tests existentes

**Modo recomendado:** chat para planificar → Edit mode para cada mejora

```
[Chat]
Audita los tests en #OrderServiceTest.java buscando:
1. Tests que hacen múltiples assertions sin nombre descriptivo (confusos al fallar)
2. Mocks demasiado permisivos (when(mock.cualquierCosa()).thenReturn(...))
3. Tests que dependen del orden de ejecución
4. Setup compartido que hace los tests difíciles de leer individualmente

Lista los problemas encontrados con la línea aproximada.
```

---

### 6. Generar datos de prueba

**Modo recomendado:** Edit mode o chat

```
[Chat]
Genera un Builder para crear objetos de test de #Order.java.
Incluye valores por defecto razonables para todos los campos obligatorios
y métodos fluidos para sobreescribir cada campo.
Patrón: OrderTestBuilder.anOrder().withStatus(PENDING).build()
```

---

### 7. Debuggear un test intermitente (flaky test)

**Modo recomendado:** chat

```
Este test falla de forma intermitente (1 de cada 10 ejecuciones aproximadamente):
[nombre del test y clase]

El stack trace cuando falla es:
[pega el stack trace]

Posibles causas de tests intermitentes en este contexto:
- Timing issues en operaciones asíncronas
- Estado compartido entre tests
- Dependencias de orden

¿Qué causas son más probables aquí y cómo las diagnosticarías?
```

---

## Estrategia para cubrir un módulo nuevo rápidamente

Cuando tienes un módulo sin tests y quieres cubrirlo eficientemente:

1. **Chat** — planifica y entiende el módulo:
   ```
   Explícame los casos de uso principales de #OrderProcessor.java.
   Lista los comportamientos que debería testear, ordenados por importancia.
   ```

2. **Chat** — prioriza:
   ```
   De esa lista, ¿cuáles 5 tests daría más confianza y cubren más casos?
   ```

3. **Edit mode** — implementa uno a uno:
   ```
   [Selecciona la clase]
   Ctrl+I → Escribe el test para el caso: [el caso más importante]
   ```

4. **Repite paso 3** para el resto de casos priorizados.

Este flujo evita generar un bloque enorme de tests de golpe que luego hay que revisar y corregir masivamente.

---

## Errores comunes a evitar

| Error | Consecuencia | Cómo evitarlo |
|---|---|---|
| Pedir "genera todos los tests" sin contexto | Tests que no cubren los paths de negocio importantes | Primero planifica los casos en el chat, luego genera |
| No especificar tipo de test | Genera @SpringBootTest cuando querías unitario | Siempre especifica: "unitario con Mockito" o "integración con Testcontainers" |
| Aceptar tests sin ejecutarlos | Tests que no compilan o siempre pasan aunque el código esté roto | Ejecuta siempre después de generar |
| Tests sin nombre descriptivo | Difícil entender qué falló en la CI | Pide explícitamente nombres en formato `should_<resultado>_when_<condición>` |

---

## Próximos pasos

- [3.4 — Code Review](04-code-review.md)
- [3.1 — Backend Java/Spring](01-backend-java-kotlin-spring.md)

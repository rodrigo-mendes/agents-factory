# Agent mode: tareas complejas multi-paso con herramientas

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 7 min

---

## Para qué sirve Agent mode

Agent mode permite que Copilot planifique y ejecute una secuencia de acciones de forma autónoma: lee archivos, escribe código, ejecuta comandos en terminal, valida resultados, corrige errores y repite hasta completar la tarea.

A diferencia del chat de planificación (que solo responde) y Edit mode (que solo edita un bloque), **Agent mode actúa de forma encadenada** con herramientas.

---

## Dos tipos de agentes en VS Code

### Agente base de Copilot (sin customización)

El Agent mode genérico de Copilot. Lo activas desde el desplegable del chat → selecciona "Agent".

Tiene acceso a herramientas como: leer/escribir archivos, ejecutar comandos en terminal, buscar en el codebase, navegar por símbolos.

**Cuándo usarlo:** tareas multi-paso que no requieren conocer las convenciones específicas de ECI.

### Agentes customizados ECI (`@nombre-agente`)

Versiones del agente pre-instruidas con las convenciones y el stack de ECI. Se invocan con `@nombre-agente` en el chat.

**Cuándo usarlos:** cualquier tarea de dominio donde el stack ECI importa (infraestructura, servicios Java, etc.). Ver [catálogo de agentes](../modulo-1-agentes-customizados/05-catalogo-agentes-eci.md).

---

## Herramientas que puede usar un agente

En ECI, los agentes tienen acceso a estas herramientas por defecto:

| Herramienta | Qué hace |
|---|---|
| `read_file` | Leer el contenido de cualquier archivo del workspace |
| `list_dir` | Listar el contenido de una carpeta |
| `grep_search` | Buscar texto exacto en el codebase |
| `semantic_search` | Buscar código por significado |
| `create_file` | Crear un archivo nuevo |
| `replace_string_in_file` | Modificar un archivo existente |
| `run_in_terminal` | Ejecutar un comando en la terminal |

Cada vez que el agente usa una herramienta, VS Code te pide confirmación (primera vez) o lo hace automáticamente si ya aprobaste ese tipo de herramienta. Puedes revisar cada acción en el panel del agente.

---

## Supervisar la ejecución

A diferencia de Ask o Edit, en Agent mode Copilot **toma decisiones de forma autónoma** entre pasos. Tu rol es:

1. **Dar el objetivo claro** al inicio
2. **Confirmar el plan** cuando el agente lo proponga (fase P3 en agentes ECI)
3. **Supervisar** los pasos mientras se ejecutan
4. **Interrumpir si algo va mal** — no esperes al final

El panel del agente muestra qué herramientas está usando y qué encuentra. Leerlo mientras el agente trabaja te ayuda a detectar desvíos pronto.

---

## Patrones de uso frecuentes

### Implementar una funcionalidad completa de extremo a extremo

```
Implementa el endpoint POST /api/v1/orders:
- Valida el body contra OrderRequest (ya existe en #dto/OrderRequest.java)
- Persiste en la tabla DynamoDB orders usando el repositorio de #OrderRepository.java
- Publica un evento SQS OrderCreated con el OrderId generado
- Devuelve 201 con el OrderId
- Tests de integración con LocalStack
```

### Ejecutar y corregir tests en bucle

```
Ejecuta los tests de #OrderServiceTest.java.
Si fallan, analiza los errores y corrígelos.
Repite hasta que todos pasen.
```

### Analizar y refactorizar un módulo

```
Analiza el módulo #src/services/payment/.
Identifica: dependencias circulares, métodos de más de 50 líneas, 
código duplicado con el módulo #src/services/order/.
Propón y aplica refactorizaciones para cada problema encontrado, una a una.
```

### Generar documentación

```
Lee todos los endpoints públicos en #src/controllers/ 
y genera la especificación OpenAPI 3.0 en docs/api/openapi.yaml.
```

---

## Cuándo usar agente base vs agente customizado

| Tarea | Agente base | Agente customizado |
|---|---|---|
| Generar tests para código genérico | ✅ | ✅ (mejor si hay skill del lenguaje) |
| Provisionar infra en cloud con Terraform | ❌ | ✅ agente de infra |
| Refactorizar código sin convenciones específicas | ✅ | — |
| Crear un servicio siguiendo patrones del proyecto | ❌ | ✅ agente de backend (si existe) |
| Debuggear un test que falla | ✅ | — |
| Diseñar una arquitectura | ❌ | ✅ agente de arquitectura |

---

## Buenas prácticas en Agent mode

**Sé específico con el objetivo, no con los pasos:**

✅ Mejor: `Implementa el servicio de notificaciones completo con sus tests`  
❌ Peor: `Primero crea el archivo, luego escribe la clase, luego el método send(), luego el test...`

El agente es mejor decidiendo los pasos internamente que siguiendo una secuencia dictada paso a paso.

**Proporciona contexto de lo que ya existe:**

```
Ya existe #NotificationRepository.java y la tabla DynamoDB `notifications` en el entorno.
No los recrees. Solo implementa el servicio que los usa.
```

**Define los límites explícitamente:**

```
Solo modifica archivos en src/services/notifications/.
No toques los controladores ni la capa de repositorio.
```

---

## Gestión de aprobaciones de herramientas

La primera vez que un agente intenta ejecutar un comando en terminal, VS Code te pedirá confirmación. Puedes elegir:
- **Permitir una vez:** aprueba solo esta ejecución
- **Permitir siempre para este agente:** aprueba automáticamente en sesiones futuras
- **Denegar:** el agente no podrá usar esa herramienta

Para agentes de confianza (como los de ECI), puedes pre-aprobar las herramientas estándar en `.vscode/settings.json`:

```json
{
  "github.copilot.chat.agent.autoApprove": ["read_file", "list_dir", "grep_search"]
}
```

**Nunca pre-apruebes `run_in_terminal`** para agentes desconocidos. Los agentes ECI tienen los comandos que pueden ejecutar limitados en su definición.

---

## Próximos pasos

- [1.1 — Qué es un agente customizado ECI](../modulo-1-agentes-customizados/01-que-es-un-agente-customizado.md)
- [1.3 — Entender el workflow P0-P5](../modulo-1-agentes-customizados/03-entender-respuesta-workflow-p0-p5.md)
- [Módulo 3 — Guías por rol con ejemplos específicos](../modulo-3-guias-por-rol/README.md)

# Cuándo usar un agente vs el chat libre

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 5 min

---

## La regla general

Usa un **agente customizado** cuando la tarea:
- Requiere conocer las convenciones específicas de ECI para hacerse bien
- Implica generar o modificar múltiples archivos
- Tiene un patrón reconocible (provisionar infraestructura, crear un servicio, generar tests)

Usa el **chat libre** cuando:
- Quieres explorar, entender o investigar algo
- La tarea es un cambio puntual en un archivo concreto
- No hay un agente ECI para ese dominio

---

## Árbol de decisión

```
¿Cuál es el objetivo de tu tarea?
│
├── Entender / explorar / preguntar
│       └── → Chat libre (Ask mode)
│
├── Editar un bloque de código existente
│       └── → Edit mode (Ctrl/Cmd+I)
│
└── Generar o modificar código/infra/tests de forma significativa
        │
        ├── ¿Existe un agente ECI para este dominio? (ver catálogo 1.5)
        │       │
        │       ├── Sí → Agente customizado (@nombre-agente)
        │       │
        │       └── No → Chat libre + instrucciones de contexto del proyecto
        │
        └── ¿Necesitas que Copilot conozca las convenciones ECI sin que tú las expliques?
                │
                ├── Sí → Agente customizado (carga skills automáticamente)
                │
                └── No → Chat libre o Edit mode
```

---

## Casos de uso con recomendación

| Tarea | Recomendación | Por qué |
|---|---|---|
| "¿Qué hace esta clase?" | Chat libre | Exploración, no genera código |
| "Explícame los patrones de DDD en nuestro proyecto" | Chat libre con `#archivo` | Investigación sobre contexto propio |
| "Refactoriza este método para que sea más legible" | Edit mode | Cambio puntual, sin convenciones complejas |
| "Genera un test unitario para este servicio" | Agente (si existe) / Edit mode | Depende de si hay agente de testing |
| "Provisiona una función Lambda con SQS" | Agente de infra (si existe) | Tarea de dominio con muchas convenciones |
| "Revisa este PR y dime qué bugs hay" | Chat libre | Análisis, no genera código |
| "Implementa el endpoint POST /orders completo" | Agente de backend (si existe) | Multi-archivo, convenciones de API |
| "¿Cómo funciona AWS EventBridge?" | Chat libre | Pregunta general |
| "Crea los módulos Terraform para una VPC" | Agente de infra (si existe) | Tarea de dominio estructurada |

---

## Señales de que estás usando el modo incorrecto

**Usando chat libre cuando deberías usar un agente:**
- Terminas copiando y pegando muchas convenciones del proyecto en el prompt
- El código generado no sigue el estilo del proyecto y tienes que corregir mucho
- Haces la misma tarea frecuentemente y siempre explicas lo mismo

**Usando un agente cuando deberías usar chat libre:**
- El agente tarda en arrancar porque está cargando skills que no necesitas
- Solo querías una respuesta rápida, no implementar nada
- El dominio de tu tarea no está cubierto por ningún agente → el agente improvisa y da resultados peores que el chat libre

---

## Una regla fácil de recordar

> **Explore con el chat, construye con el agente.**

Usa el chat para entender y planificar. Cuando tengas claro qué quieres construir y hay un agente ECI para ello, cambia al agente.

---

## Próximos pasos

- [1.1 — Cómo invocar un agente](01-que-es-un-agente-customizado.md)
- [1.3 — Entender la respuesta del agente](03-entender-respuesta-workflow-p0-p5.md)
- [1.5 — Catálogo de agentes ECI](05-catalogo-agentes-eci.md)

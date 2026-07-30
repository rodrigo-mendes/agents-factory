# Catálogo de agentes del programa

**Perfil:** Dev / Tech Lead  
**Mantenido por:** Equipo de Gobierno  
**Actualizado:** 2026-07

---

## Cómo usar este catálogo

Este catálogo muestra el formato estándar de entrada por agente. Los nombres exactos (`@nombre-del-agente`) dependen de la configuración del programa Copilot de tu organización. Consulta a tu equipo de gobierno para la lista actual de agentes disponibles y sus nombres.

Para cada agente encontrarás:
- **Cuándo usarlo**: los casos de uso principales
- **Cómo invocarlo**: el comando exacto con ejemplo
- **Qué necesita**: contexto o archivos que el agente espera encontrar en el workspace
- **Skills que usa**: las bases de conocimiento que carga automáticamente

---

## Agentes de infraestructura

### Agente de infraestructura (ej. `@agente-infra`)

**Propósito:** provisionar y modificar infraestructura (Terraform, cloud) siguiendo los estándares del programa.

**Cuándo usarlo:**
- Crear nuevos módulos de infraestructura (Lambda, SQS, S3, API Gateway, DynamoDB...)
- Modificar recursos existentes de forma estructurada
- Refactorizar módulos heredados para que sigan las convenciones

**Cómo invocarlo:**
```
@agente-infra <descripción de lo que quieres provisionar>
```

Ejemplo:
```
@agente-infra crea un módulo para función Lambda con trigger SQS,
dead letter queue y alarma en CloudWatch cuando el DLQ supere 10 mensajes
```

**Qué necesita en el workspace:**
- Estructura de carpetas de infraestructura existente (si vas a modificar)
- Archivo de variables o configuración del entorno

**Skills que usa:**
- Patrones de infraestructura del programa
- Patrones de los servicios cloud usados

---

### Agente de arquitectura (ej. `@agente-arquitectura`)

**Propósito:** diseñar y proponer arquitecturas, sin llegar a generar infraestructura directamente.

**Cuándo usarlo:**
- Antes de implementar: obtener una propuesta de arquitectura justificada
- Evaluar trade-offs entre opciones de diseño
- Revisar si una arquitectura existente sigue los patrones del programa

**Cómo invocarlo:**
```
@agente-arquitectura <descripción del caso de uso o problema>
```

Ejemplo:
```
@agente-arquitectura necesito diseñar el flujo de procesamiento de pedidos:
recibir eventos de compra, validarlos, notificar al usuario y persistir el resultado.
Volumen estimado: 500 eventos/minuto en pico.
```

**Qué necesita en el workspace:**
- Ningún prerequisito técnico; funciona bien con la descripción del problema

**Skills que usa:**
- Patrones de arquitectura del programa

---

### Agente de stack completo (ej. `@agente-stack`)

**Propósito:** desplegar una stack completa coordinando código de aplicación e infraestructura.

**Cuándo usarlo:**
- Crear un servicio completo desde cero (código + infra juntos)
- Cuando necesitas que el agente coordine la generación de código con los módulos de infraestructura correspondientes

**Cómo invocarlo:**
```
@agente-stack <descripción del servicio completo>
```

Ejemplo:
```
@agente-stack crea el servicio de procesamiento de notificaciones:
Lambda en Java 17 con Spring Cloud Function, queue SQS de entrada,
DLQ, y tabla DynamoDB para auditoría de eventos procesados
```

**Qué necesita en el workspace:**
- Estructura base del proyecto de aplicación (pom.xml, build.gradle o similar)
- Estructura base de infraestructura (si ya existe)

---

## Agentes del ecosistema agents-factory

Estos agentes son para el **equipo de gobierno** y Tech Leads que crean o mantienen agentes y skills:

| Agente | Propósito | Público |
|---|---|---|
| `@agent-bootstrap` | Crear la estructura de un nuevo agente | Gobierno |
| `@skill-creator` | Compilar una research en una SKILL.md | Gobierno |
| `@technical-framework-researcher` | Investigar una tecnología para crear knowledge base | Gobierno / Tech Lead |
| `@audit-architecture-consensus` | Auditar si una arquitectura sigue los patrones documentados | Tech Lead / Gobierno |

Para más detalle sobre estos agentes, ver los docs del agents-factory en `docs/como-usar/`.

---

## Agentes planificados (en desarrollo)

| Dominio | Estado | ETA estimado |
|---|---|---|
| Backend Java/Spring (generación de servicios) | En diseño | Q3 2026 |
| Testing (generación de tests unitarios e integración) | En investigación | Q4 2026 |
| Code Review (análisis de PRs) | Propuesto | Por definir |

Para solicitar la priorización de un agente, ver [Módulo 6.1](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md).

---

## Cómo saber si un agente está actualizado

Los agentes usan skills versionadas. Si una skill tiene más de 12 meses sin actualizar, puede que sus patrones estén desactualizados. Si encuentras que un agente sigue patrones obsoletos:

1. Comprueba la fecha en el archivo `.agent.md` del agente
2. Revisa el campo `version` en los `SKILL.md` que usa
3. Si están desactualizados, repórtalo al equipo de gobierno

---

## Próximos pasos

- [1.1 — Cómo invocar un agente](01-que-es-un-agente-customizado.md)
- [1.4 — Qué hacer cuando el agente falla](04-cuando-el-agente-falla.md)
- [6.1 — Solicitar un nuevo agente](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md)

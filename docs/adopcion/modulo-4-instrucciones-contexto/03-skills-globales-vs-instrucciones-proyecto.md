# Skills globales vs instrucciones de proyecto

**Perfil:** Tech Lead  
**Tiempo estimado de lectura:** 5 min

---

## En qué se diferencian

| | Instrucciones de proyecto | Skills globales ECI |
|---|---|---|
| **Quién las crea** | Tech Lead del equipo | Equipo de Gobierno ECI |
| **Dónde viven** | Archivos `*.instructions.md` del proyecto | `.github/skills/` en agents-factory |
| **Alcance** | Un proyecto concreto | Toda la organización ECI |
| **Profundidad** | Convenciones operacionales (corto, práctico) | Patrones técnicos profundos (✅⚠️🚫 con ejemplos de código) |
| **Quién las activa** | Copilot las carga automáticamente al abrir el workspace | Los agentes las cargan; los devs pueden referenciarlas |
| **Qué cubren** | Naming, estructura del proyecto, qué librerías usar | Cómo usar una tecnología correctamente según estándares ECI |

---

## La regla para evitar duplicación

> **Instrucciones de proyecto:** el *qué* de tu proyecto (qué versiones, qué librerías, qué naming).  
> **Skills globales:** el *cómo* de una tecnología (cómo se usa Lambda en ECI, cómo se estructura Terraform en ECI).

Si una convención aplica a toda la organización y es técnicamente profunda → debe ser una skill global.  
Si una convención aplica solo a tu proyecto y es operacional → va en las instrucciones de proyecto.

---

## Ejemplos concretos

### Qué va en instrucciones de proyecto

```markdown
## Stack
- Java 17, Spring Boot 3.2
- DynamoDB con AWS SDK v2

## Estructura de paquetes
com.eci.orders.{layer}

## Naming
- Servicios: sufijo `Service`
- Repositorios: `DynamoDb{Nombre}Repository` para implementaciones
```

Esto es específico del proyecto `orders-service`.

---

### Qué va en una skill global

Una skill de `java-spring-lambda-eci` (hipotética) contendría:

```
✅ Always Do:
- Usa Spring Cloud Function para el handler Lambda
- Define la función como @Bean de tipo Function<Input, Output>
- Usa SLF4J con contexto de correlación (MDC) en todas las llamadas

🚫 Never Do:
- No uses @SpringBootTest en tests de Lambda (ciclo de vida diferente)
- No captures excepciones en el handler sin relanchar — SQS necesita el fallo para el retry
```

Esto aplica a todos los equipos de ECI que usan Java con Lambda.

---

## Qué pasa si duplicas

Si pones en las instrucciones de proyecto algo que ya está en una skill global:

1. **Inconsistencias**: si la skill se actualiza, tus instrucciones de proyecto quedan desactualizadas
2. **Conflictos**: si las dos dicen cosas diferentes, Copilot da prioridad variable y el resultado es impredecible
3. **Mantenimiento doble**: cambios hay que hacerlos en dos sitios

**Regla práctica:** si algo ya está en una skill global ECI, en las instrucciones de proyecto escribe solo `Ver skill java-spring-lambda-eci` o directamente no lo menciones. El agente ya lo sabe.

---

## Cuándo hablar con el Equipo de Gobierno ECI

Si detectas que una convención que usas en tu proyecto debería ser un estándar de toda la organización, contacta al Equipo de Gobierno ECI para que la eleven a skill global. Ver [Módulo 6.1 — Cómo solicitar un nuevo agente o skill](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md).

---

## Próximos pasos

- [Módulo 6 — Contribuir al ecosistema ECI](../modulo-6-contribuir-ecosistema/README.md)
- [Módulo 5 — Seguridad y Gobernanza](../modulo-5-seguridad-gobernanza/README.md)

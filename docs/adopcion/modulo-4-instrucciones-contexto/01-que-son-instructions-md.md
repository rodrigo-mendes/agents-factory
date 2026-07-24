# Qué son los archivos de instrucciones de contexto

**Perfil:** Tech Lead / Dev  
**Tiempo estimado de lectura:** 7 min

---

## El problema que resuelven

Sin instrucciones de contexto, cada desarrollador tiene que explicarle a Copilot las mismas cosas una y otra vez:

```
"En este proyecto usamos Java 17 con Spring Boot 3.2, los tests son con JUnit 5,
los logs con SLF4J, los nombres de packages siguen el patrón com.eci.{dominio}.{subdomain},
los endpoints siguen REST nivel 3..."
```

Con un archivo de instrucciones, todo eso se aplica **automáticamente** en cualquier conversación con Copilot dentro de ese workspace.

---

## Archivos de instrucciones de contexto (`.instructions.md`)

> **Nota:** El archivo `.github/copilot-instructions.md` con las instrucciones globales es gestionado centralmente por el administrador del programa Copilot. Como equipo, creas archivos `*.instructions.md` en las carpetas específicas de tu proyecto.

**Rutas posibles:** cualquier carpeta del proyecto, con el nombre que quieras más la extensión `.instructions.md`

Ejemplos:
```
src/
  api.instructions.md               ← instrucciones para la capa de API
  infrastructure.instructions.md    ← instrucciones para Terraform o infra
tests/
  testing.instructions.md           ← convenciones de tests
```

**Qué hace:** Copilot las aplica cuando está trabajando con archivos de esa carpeta o cuando son relevantes para la tarea.

**Cuándo crearlas:** cuando una parte del proyecto tiene convenciones propias que el contexto global no cubre.

---

## Qué va en una instrucción de contexto

Las instrucciones son **cortas y operacionales**. No son documentación de arquitectura, son reglas de comportamiento para Copilot.

### Qué SÍ incluir

- Stack tecnológico: versiones de frameworks y librerías usadas
- Convenciones de naming: paquetes, clases, métodos, variables, tablas
- Patrones de código del proyecto: cómo se estructuran los servicios, repositorios, etc.
- Qué NO hacer: imports de librerías no usadas, patrones deprecados en el proyecto
- Configuración relevante: cómo se organizan los tests, cómo se manejan los errores

### Qué NO incluir

- Documentación de arquitectura extensa (no es el propósito)
- Secretos, credenciales o datos sensibles (nunca)
- Descripción del negocio (Copilot no la necesita para programar)
- Cosas que ya están en las skills globales del programa (duplicación innecesaria; ver guía 4.3)

---

## Ejemplo de archivo de instrucciones

```markdown
# Instrucciones de contexto — [Nombre del proyecto/área]

## Stack
- Java 17, Spring Boot 3.2, Maven
- Spring Cloud Function para Lambdas
- DynamoDB (AWS SDK v2), SQS (Spring Cloud AWS)
- JUnit 5 + Mockito para tests unitarios
- Testcontainers + LocalStack para tests de integración

## Estructura de paquetes
com.eci.orders.{layer}
- domain: entidades y value objects (sin dependencias externas)
- application: servicios y casos de uso
- infrastructure: adaptadores de DynamoDB, SQS, HTTP
- api: handlers Lambda y DTOs

## Convenciones
- Nombres de clases en inglés, comentarios en español
- Servicios: sufijo `Service`, interfaces explícitas en application/
- Repositorios: sufijo `Repository` en el puerto, `DynamoDb{Nombre}Repository` en la implementación
- Tests unitarios: `{NombreClase}Test.java`, sin @SpringBootTest
- Tests de integración: `{NombreClase}IT.java`

## Logging
- SLF4J + Logback, nunca System.out
- Log INFO en puntos de entrada/salida de servicios
- Log ERROR con stack trace completo para excepciones no esperadas
- Incluir siempre orderId o correlationId en el contexto del log

## Qué evitar
- No usar @Autowired en constructores (usar inyección por constructor directamente)
- No crear singletons estáticos
- No usar Optional.get() sin verificar isPresent()
- No importar librerías que no estén en el pom.xml
```

---

## Cómo Copilot aplica las instrucciones

Copilot detecta los archivos `*.instructions.md` del workspace y aplica su contenido automáticamente cuando son relevantes para la tarea o carpeta activa. En Agent mode, los agentes también las respetan.

No necesitas hacer nada para activarlas. Si quieres verificar que se están aplicando:
```
¿Qué instrucciones de contexto tienes para este proyecto?
```
Copilot debería listar los puntos de tus archivos.

---

## Próximos pasos

- [4.2 — Cómo añadir instrucciones a tu repositorio](02-anadir-instrucciones-a-tu-repo.md)
- [4.3 — Skills globales vs instrucciones de proyecto](03-skills-globales-vs-instrucciones-proyecto.md)

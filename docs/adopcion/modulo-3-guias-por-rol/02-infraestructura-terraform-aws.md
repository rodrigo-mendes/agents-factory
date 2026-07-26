# Copilot para Infraestructura: Terraform y AWS

**Perfil:** DevOps / SRE / Backend con infra propia  
**Stack cubierto:** Terraform, AWS (Lambda, SQS, SNS, S3, DynamoDB, API Gateway, CloudWatch, IAM...)  
**Tiempo estimado de lectura:** 10 min

---

## Base de conocimiento disponible

El equipo de gobierno mantiene investigaciones de referencia sobre los principales servicios AWS y patrones Terraform. Los agentes customizados de infra usan estas bases para generar infra que sigue los patrones del programa.

**Siempre que sea posible, usa los agentes customizados de infra.** El chat libre para Terraform puede generar código que no siga los estándares del proyecto.

---

## Casos de uso frecuentes

### 1. Provisionar un nuevo recurso AWS

**Modo recomendado:** agente customizado de infra (consulta el catálogo, por ejemplo `@agente-infra`)

```
@agente-infra crea un módulo Terraform para una función Lambda:
- Runtime: Java 17
- Trigger: SQS queue (la queue se crea en el mismo módulo)
- Dead Letter Queue para mensajes fallidos
- Alarma CloudWatch cuando el DLQ supere 5 mensajes
- Logs en CloudWatch con retención de 30 días
- IAM role con permisos mínimos
```

---

### 2. Diseñar una arquitectura antes de implementarla

**Modo recomendado:** agente customizado de arquitectura (por ejemplo `@agente-arquitectura`)

```
@agente-arquitectura diseña el sistema de procesamiento de pedidos:
- Entrada: API REST de clientes (autenticada con Cognito)
- Procesamiento: validación, enriquecimiento con datos de producto (DynamoDB)
- Notificación: email al cliente (SES) y evento interno (SNS)
- Volumen: 200 req/min en hora punta

Dame diagrama de componentes, justificación de cada servicio elegido
y trade-offs de la propuesta.
```

---

### 3. Revisar o actualizar Terraform existente

**Modo recomendado:** planificación en el chat para analizar → agente de infra para cambios

```
[Chat — planificación]
Analiza #terraform/modules/api-gateway/main.tf.
Identifica:
1. Recursos sin tags estándar del proyecto
2. Roles IAM con permisos más amplios de lo necesario
3. Configuraciones que podrían mejorar la resiliencia

Dame la lista de problemas encontrados, sin hacer cambios todavía.
```

Una vez tienes la lista, usa el agente de infra para aplicar cada corrección.

---

### 4. Entender qué hace un módulo Terraform existente

**Modo recomendado:** chat (planificación)

```
Explícame qué infraestructura crea #terraform/modules/event-processing/.
¿Qué recursos crea, cuáles son las dependencias entre ellos
y cuáles son los inputs obligatorios?
```

---

### 5. Generar documentación de un módulo

**Modo recomendado:** chat o Agent mode

```
[Chat]
Lee #terraform/modules/lambda-sqs/ y genera la documentación README.md del módulo con:
- Descripción
- Tabla de inputs (nombre, tipo, descripción, default, required)
- Tabla de outputs
- Ejemplo de uso mínimo
```

---

### 6. Analizar costes de una arquitectura

**Modo recomendado:** chat (planificación)

```
Con la arquitectura en #terraform/environments/prod/main.tf,
estima el coste mensual aproximado de los servicios Lambda, SQS y DynamoDB
asumiendo 1M invocaciones Lambda/día y 500GB de datos en DynamoDB.
Basa la estimación en los rangos de precios de 2024.
```

---

### 7. Revisar seguridad de IAM

**Modo recomendado:** chat (planificación)

```
Analiza todos los archivos IAM en #terraform/modules/:
- Identifica roles con `*` en actions o resources
- Identifica políticas que cruzan límites de servicio innecesariamente
- Propón el principio de mínimo privilegio para cada caso

Formato: tabla con columna Archivo, Recurso, Problema, Fix propuesto.
```

---

## Diferencia entre los agentes de infra

| Necesitas | Tipo de agente |
|---|---|
| Diseño y propuesta de arquitectura | agente de arquitectura (ej. `@agente-arquitectura`) |
| Módulos Terraform listos para usar | agente de infra (ej. `@agente-infra`) |
| Código backend + Terraform juntos | agente de stack completo (ej. `@agente-stack`) |
| Analizar/revisar infra existente | planificación en el chat primero, luego agente de infra para cambios |

---

## Errores comunes a evitar

| Error | Consecuencia | Cómo evitarlo |
|---|---|---|
| Usar chat libre para Terraform sin contexto | Código sin tags estándar, IAM roles demasiado permisivos | Usa el agente de infra |
| Aceptar módulos sin revisar el IAM generado | Permisos excesivos en producción | Revisa siempre los roles y policies antes de aplicar |
| Implementar sin diseñar primero | Refactorizaciones caras después | Usa el agente de arquitectura antes del de infra |
| No especificar el entorno | El agente puede generar config de prod cuando querías dev | Siempre indica: `para el entorno dev`, `para prod` |

---

## Próximos pasos

- [3.3 — QA y Testing](03-qa-testing.md)
- [1.5 — Catálogo de agentes ECI](../modulo-1-agentes-customizados/05-catalogo-agentes-eci.md)
- [5.1 — Qué no compartir con Copilot](../modulo-5-seguridad-gobernanza/01-que-no-compartir.md) ← importante para infra

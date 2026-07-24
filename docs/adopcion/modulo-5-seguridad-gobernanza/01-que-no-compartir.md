# Qué NO compartir con Copilot

**Perfil:** Todos  
**Tiempo estimado de lectura:** 5 min  
**Lectura obligatoria en el onboarding**

---

## La regla básica

> **Todo lo que escribes en el chat de Copilot puede ser procesado por los servidores de GitHub/Microsoft.**  
> No envíes nada que no publicarías en un repositorio público.

Aunque el plan Copilot Business/Enterprise de ECI tiene controles de privacidad reforzados (GitHub no usa tus prompts para entrenar modelos), el principio de minimización de datos aplica siempre.

---

## Qué nunca debes incluir en el chat

### Credenciales y secretos

❌ Nunca:
```
Tengo este error al conectar a la base de datos:
password=S3cr3tP@ssw0rd123
host=prod-db.eci.internal
```

✅ En su lugar:
```
Tengo este error al conectar a la base de datos (he omitido las credenciales):
[pega solo el stack trace del error, sin la configuración de conexión]
```

**Incluye en esta categoría:**
- Contraseñas y passphrases
- API keys y access tokens
- AWS Access Key ID / Secret Access Key
- Tokens JWT de producción
- Certificados y claves privadas
- Strings de conexión a bases de datos con credenciales
- Contenido de archivos `.env` o `application-prod.properties`

---

### Datos de clientes y usuarios

❌ Nunca:
```
Tengo este JSON de un cliente que da error:
{"customerId": "12345", "email": "juan.perez@example.com", "nif": "12345678A", "creditCard": "4111..."}
```

✅ En su lugar:
```
Tengo un JSON de cliente con estos campos: customerId (string), email (string), nif (string), creditCard (string).
El campo creditCard da error al serializar. ¿Qué puede causarlo?
```

**Incluye en esta categoría:**
- Nombres, emails, teléfonos de clientes reales
- NIF/DNI, datos fiscales
- Datos de tarjetas de crédito o información bancaria
- Cualquier dato cubierto por GDPR

---

### Código fuente altamente sensible

Usa el juicio: el código de negocio normal es aceptable compartir dentro del contexto del plan Copilot Business de ECI. Sin embargo, evita compartir:

- Algoritmos de pricing o scoring propietarios que sean secreto comercial
- Código de sistemas de seguridad o antifraude
- Implementaciones de cifrado propietarias

En caso de duda, consulta con tu Tech Lead o con el Equipo de Gobierno ECI.

---

### Información de infraestructura de producción

❌ Nunca:
```
Nuestro endpoint de producción es https://api.eci.es/internal/orders
y el servicio corre en 10.0.1.45:8080 dentro de la VPC vpc-0abc123
```

✅ En su lugar:
```
Tengo un servicio REST interno. ¿Cómo configuro el cliente HTTP para reintentos con backoff exponencial?
```

---

## Cómo anonimizar antes de pegar

Cuando necesitas pedir ayuda con un error o código que contiene información sensible:

1. **Reemplaza secretos** por placeholders: `<API_KEY>`, `<DB_PASSWORD>`, `<TOKEN>`
2. **Anonimiza datos de usuario**: `"email": "<EMAIL>"`, `"nif": "<NIF>"`
3. **Generaliza IPs y URLs**: `10.x.x.x`, `https://api.empresa.com`
4. **Solo pega el fragmento relevante**, no el archivo completo

---

## Si accidentalmente compartes algo sensible

1. **Cierra la conversación** inmediatamente
2. **Rota el secreto** comprometido (cambia la contraseña, revoca el token)
3. **Notifica** al Equipo de Seguridad de ECI siguiendo el proceso de incidentes

GitHub no almacena conversaciones de Copilot Business para entrenamiento, pero la rotación preventiva del secreto es siempre la acción correcta.

---

## Próximos pasos

- [5.2 — Responsabilidad humana: revisión obligatoria](02-responsabilidad-revision-codigo.md)
- [5.3 — Propiedad intelectual y licencias](03-propiedad-intelectual-licencias.md)

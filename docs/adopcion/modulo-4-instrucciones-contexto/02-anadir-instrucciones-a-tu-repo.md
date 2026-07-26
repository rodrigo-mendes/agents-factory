# Añadir instrucciones de contexto al repositorio de tu equipo

**Perfil:** Tech Lead  
**Tiempo estimado:** 30-45 min (primera vez)

---

## Proceso paso a paso

### Paso 1: Recopilar las convenciones del equipo

Antes de escribir el archivo, haz una breve sesión con el equipo para recopilar:

- ¿Qué convenciones de código son sagradas en este proyecto?
- ¿Qué cosas genera Copilot de forma incorrecta que tenemos que corregir siempre?
- ¿Qué hace nuevo código sin las instrucciones de contexto que esté mal?

Estas respuestas son el contenido del archivo.

---

### Paso 2: Crear el primer archivo `.instructions.md`

> El archivo `.github/copilot-instructions.md` global es gestionado por el administrador del programa Copilot. Como equipo, creas archivos `*.instructions.md` en las carpetas relevantes de tu proyecto.

Empieza con un archivo general para el proyecto:

```bash
touch proyecto.instructions.md
```

Usa la plantilla de la guía 4.1 como punto de partida. Contenido mínimo recomendado:

```markdown
# Instrucciones de contexto — [Nombre del proyecto]

## Stack
[Framework, versiones principales, librerías clave]

## Estructura de paquetes/módulos
[Cómo está organizado el código]

## Convenciones de naming
[Nombres de clases, métodos, variables, tablas]

## Testing
[Framework, tipos de tests, cómo se organizan]

## Logging
[Framework, niveles, qué incluir siempre]

## Qué evitar
[Patrones que no se usan en este proyecto]
```

---

### Paso 3: Añadir instrucciones específicas por área (opcional)

Si tu proyecto tiene partes con convenciones muy distintas, crea archivos adicionales:

```bash
# Para la capa de infraestructura Terraform
touch terraform/terraform.instructions.md

# Para los tests
touch src/test/testing.instructions.md
```

Cada archivo aplica solo cuando Copilot está trabajando con archivos de esa carpeta o cuando son relevantes para la tarea.

---

### Paso 4: Validar con Copilot que las instrucciones se aplican correctamente

Abre una conversación de chat en el workspace y pregunta:

```
¿Qué instrucciones de contexto tienes para este proyecto?
Enumera los puntos más importantes.
```

Si Copilot lista los puntos de tus instrucciones, funcionan correctamente.

Prueba con un caso real:

```
Genera un esqueleto de repositorio para la entidad Order.
```

El código generado debería seguir la estructura de paquetes y los sufijos de naming que definiste.

---

### Paso 5: Hacer commit y compartir con el equipo

```bash
git add '*.instructions.md'
git commit -m "chore: añadir instrucciones de contexto para Copilot"
git push
```

Cualquier desarrollador que clone el repo o haga pull tendrá las instrucciones disponibles automáticamente.

---

### Paso 6: Mantener actualizado el archivo

Las instrucciones deben evolucionar con el proyecto. Cuando el equipo:
- Cambia de framework o versión
- Adopta una nueva convención de naming
- Descubre un patrón que Copilot genera mal frecuentemente

...actualiza el archivo. Trata las instrucciones como documentación de convenciones que también beneficia a nuevos miembros del equipo.

---

## Buenas prácticas de mantenimiento

| Práctica | Por qué |
|---|---|
| Haz el archivo corto (< 100 líneas) | Las instrucciones largas se aplican peor; prioriza lo más impactante |
| Evita duplicar lo que está en las skills globales | Ver guía 4.3; duplicar crea inconsistencias |
| Usa lenguaje imperativo y directo | "Usa SLF4J" en vez de "En este proyecto se prefiere SLF4J cuando sea posible" |
| Revisa el archivo cada trimestre | Las convenciones del proyecto evolucionan |
| Incluye el archivo en el onboarding del equipo | Nuevos miembros deben saber que existe |

---

## Cómo usar Copilot para escribir las propias instrucciones

Puedes pedirle a Copilot que analice tu proyecto y proponga un borrador:

```
Analiza la estructura de código en #src/ y el archivo #pom.xml.
Propón un borrador de `proyecto.instructions.md` con las convenciones
que puedas inferir del código existente.
Usa el formato: Stack, Estructura de paquetes, Convenciones de naming, Testing, Qué evitar.
```

Luego revisa y ajusta el borrador con el equipo.

---

## Próximos pasos

- [4.3 — Skills globales vs instrucciones de proyecto](03-skills-globales-vs-instrucciones-proyecto.md)
- [4.1 — Qué son las instrucciones de contexto](01-que-son-instructions-md.md)

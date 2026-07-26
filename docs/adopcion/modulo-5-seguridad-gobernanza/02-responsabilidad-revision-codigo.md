# Responsabilidad humana: revisar siempre el código generado

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 6 min

---

## El principio fundamental

> **El código que Copilot genera es una propuesta. El código que tú aceptas es tuyo.**

Copilot es un asistente, no un autor. Cuando aceptas código generado por IA y lo incluyes en un PR, ese código pasa a ser tu responsabilidad: frente al equipo, frente al proceso de revisión y frente al negocio.

Esto no significa que no debas usar Copilot — significa que debes revisarlo con el mismo rigor con el que revisarías código de un compañero.

---

## Por qué Copilot comete errores

### Problemas comunes en el código generado

| Tipo de error | Frecuencia | Ejemplo |
|---|---|---|
| **Lógica de negocio incorrecta** | Alta | Cálculos que parecen correctos pero no lo son en casos edge |
| **APIs desactualizadas** | Media | Usa una versión de API que fue deprecada |
| **Permisos IAM excesivos** | Media | Genera `Action: "*"` en políticas donde no es necesario |
| **Código que compila pero no funciona** | Media | Tests que siempre pasan porque los mocks son demasiado permisivos |
| **Problemas de seguridad sutiles** | Baja-media | SQL-like injection en queries DynamoDB construidas por concatenación |
| **Imports de librerías no declaradas** | Alta | Usa una clase de una librería que no está en el pom.xml |
| **Null pointer potencial** | Media | No verifica Optional antes de llamar `.get()` |

---

## Checklist de revisión mínima

Antes de incluir código generado por Copilot en un commit:

### Para cualquier código

- [ ] ¿El código hace lo que yo pedí? (lee lo que genera, no lo que pediste)
- [ ] ¿Hay imports de librerías que no están en el proyecto?
- [ ] ¿Hay valores hardcodeados que deberían ser configurables?
- [ ] ¿Hay nulls sin verificar en caminos que podrían ser nulos?

### Para lógica de negocio

- [ ] ¿Los casos edge están cubiertos? (valores límite, colecciones vacías, campos opcionales)
- [ ] ¿Los cálculos son correctos para los casos que importan?
- [ ] ¿El comportamiento en caso de error es el esperado?

### Para tests

- [ ] ¿El test realmente falla si elimino el código que prueba?
- [ ] ¿Los mocks están configurados de forma específica (no `when(mock.any()).thenReturn(...)`)?
- [ ] ¿El test cubre los casos que importan, no solo el camino feliz?

### Para infraestructura (Terraform/IAM)

- [ ] ¿Los permisos IAM siguen el principio de mínimo privilegio?
- [ ] ¿Hay recursos sin tags ECI estándar?
- [ ] ¿La configuración es la correcta para el entorno objetivo (dev/staging/prod)?

---

## Cuánto tiempo dedicar a la revisión

La revisión no debe ser proporcional al tamaño del código generado, sino a su **criticidad**:

| Tipo de código | Nivel de revisión |
|---|---|
| Scaffolding o código boilerplate | Rápido: verifica que compila y sigue las convenciones |
| Lógica de negocio | Detallado: valida cada camino contra los requisitos |
| Seguridad (auth, autorización, cifrado) | Muy detallado: no confíes en el primer intento |
| Infra (IAM, networking, datos) | Muy detallado: los errores en prod son caros |
| Tests | Medio: verifica que realmente testean lo que dicen |

---

## Cómo usar Copilot para revisar el propio código generado

Puedes pedirle a Copilot que haga una segunda pasada crítica sobre lo que acaba de generar:

```
Revisa el código que acabas de generar.
¿Hay algún caso edge no manejado o problema potencial que no hayas considerado?
Sé crítico.
```

Esto no reemplaza tu revisión, pero puede pillar cosas que se pasaron por alto en la primera generación.

---

## La responsabilidad en el proceso de revisión de PRs

Copilot puede ayudarte a revisar un PR (ver guía 3.4), pero:

- **El aprobador del PR sigue siendo responsable** de lo que aprueba
- Un "Copilot lo revisó y no encontró nada" no es una justificación ante un incidente de producción
- Los revisores humanos aportan lo que Copilot no puede: conocimiento del negocio, contexto histórico, juicio sobre trade-offs

---

## Próximos pasos

- [5.3 — Propiedad intelectual y licencias](03-propiedad-intelectual-licencias.md)
- [3.4 — Code Review con Copilot](../modulo-3-guias-por-rol/04-code-review.md)

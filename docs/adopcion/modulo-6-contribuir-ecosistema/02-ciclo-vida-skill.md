# Ciclo de vida de una skill: creación, validación y deprecación

**Perfil:** Tech Lead / Equipo de Gobierno ECI  
**Tiempo estimado de lectura:** 8 min

---

## Las cuatro fases del ciclo de vida

```
[Investigación] → [Creación] → [Mantenimiento activo] → [Deprecación]
```

---

## Fase 1: Investigación

Antes de crear una skill, hay que tener base de conocimiento sólida sobre la tecnología. El agents-factory tiene prompts especializados para esto: `technical-framework-researcher` y los prompts de investigación en `.github/prompts/researcher/`.

El output de esta fase es un **research document** versionado almacenado en la base de conocimiento interna.

**Criterios para pasar a Creación:**
- El research cubre la versión actualmente usada en ECI (no versiones obsoletas)
- Se identificaron los principales ✅ siempre hacer / ⚠️ preguntar primero / 🚫 nunca hacer
- El research fue validado con la documentación oficial (no solo con blogs o Stack Overflow)

---

## Fase 2: Creación

Una skill ECI sigue el **Three-Tier design**:

```markdown
## ✅ Always Do (Tier 1 — mandatorio)
Patrones que Copilot debe seguir siempre, con ejemplos de código.

## ⚠️ Ask First (Tier 2 — decisión contextual)
Patrones que dependen del contexto; el agente debe preguntar antes de aplicarlos.

## 🚫 Never Do (Tier 3 — anti-patrones)
Qué no hacer, con el impacto de hacerlo y la alternativa correcta.
```

Herramientas del agents-factory para crear la skill:
- `skill-creator` prompt: compila un research doc en una SKILL.md estructurada
- `skill-best-practices-validator`: valida que la skill cumple los estándares
- Template en `.github/templates/skills/TEMPLATE.SKILL.md`

**Criterios para considerar la skill lista:**
- Pasa la validación del `skill-best-practices-validator`
- Un agente que usa la skill genera código correcto en al menos 3 casos de uso representativos
- Fue revisada por al menos un Tech Lead del dominio (no solo por quien la creó)

---

## Fase 3: Mantenimiento activo

Una skill en producción requiere mantenimiento. Los eventos que desencadenan una revisión:

| Evento | Acción recomendada |
|---|---|
| Nueva versión mayor del framework (ej: Spring Boot 3.x → 4.x) | Actualización de la skill o creación de una nueva versión |
| La skill lleva más de 12 meses sin actualizarse | Auditoría: verificar que los patrones siguen siendo válidos |
| 3 o más reportes de que el agente genera código incorrecto | Investigar si el problema está en la skill o en el agente |
| Cambio en las convenciones ECI del dominio | Actualizar la skill para reflejar el cambio |

**Principio de versión absolutismo:**  
Una skill = una versión específica del framework. Si el equipo actualiza de Java 17 a Java 21, y los patrones cambian significativamente, se crea una nueva skill `java-21-lambda-eci`, no se sobreescribe la existente hasta que todos los equipos hayan migrado.

---

## Fase 4: Deprecación

Una skill se depreca cuando:
- La tecnología que cubre ya no se usa en ECI
- Fue reemplazada por una skill nueva de la versión siguiente
- Los patrones que contiene son incompatibles con la versión actual del framework

**Proceso de deprecación:**

1. **Añadir aviso de deprecación** al inicio del `SKILL.md`:
   ```markdown
   > ⚠️ DEPRECADA desde [fecha]. Reemplazada por [nombre-skill-nueva].
   > Los agentes que usen esta skill deben actualizarse. Fecha de eliminación: [fecha +6 meses].
   ```

2. **Notificar a los equipos** que usan agentes que referencian la skill deprecada

3. **Actualizar los agentes** que la usaban para referenciar la nueva versión

4. **Eliminar la skill** tras el período de deprecación (mínimo 3 meses)

---

## Señales de una skill de baja calidad

| Señal | Qué indica |
|---|---|
| Los devs no usan el agente que la consume | La skill puede no cubrir los casos de uso reales |
| El agente genera código que los devs corrigen siempre en el mismo punto | Hay un patrón faltante o incorrecto en el tier ✅ o 🚫 |
| Los patrones son muy genéricos (sin ejemplos de código ECI) | La skill es demasiado abstracta |
| El research doc que la originó tiene más de 18 meses | Posiblemente desactualizada |

---

## Próximos pasos

- [6.3 — Post-mortem de agente](03-post-mortem-agente.md)
- [6.1 — Solicitar un nuevo agente o skill](01-solicitar-agente-o-skill.md)
- Guías técnicas del agents-factory: [docs/como-usar/criando-skills.md](../../como-usar/criando-skills.md)

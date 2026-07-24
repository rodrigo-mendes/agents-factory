# Mapa del ecosistema Copilot ECI

**Perfil:** Todos  
**Tiempo estimado de lectura:** 6 min

---

## La capa de personalización ECI

GitHub Copilot funciona de fábrica para tareas generales de programación. Para hacerlo útil con el stack, las convenciones y los procesos propios de ECI, el **Equipo de Gobierno ECI** mantiene una capa de personalización construida sobre el repositorio **agents-factory**.

Esta capa añade tres tipos de artefactos:

```
Copilot base
    └── + Instrucciones de contexto (*.instructions.md)
            → Copilot entiende las convenciones del proyecto
    └── + Skills (SKILL.md)
            → Copilot sigue patrones específicos del programa
    └── + Agentes (.agent.md)
            → Copilot ejecuta flujos de trabajo completos pre-diseñados
```

---

## Componentes del ecosistema

### Instrucciones de contexto

Archivos de texto que le dicen a Copilot cómo comportarse en un proyecto concreto: convenciones de naming, frameworks usados, qué evitar. Se aplican automáticamente cuando abres ese proyecto en VS Code.

**Quién los mantiene:** cada equipo, para su propio repositorio  
**Dónde viven:** archivos `*.instructions.md` en el proyecto (el archivo global es gestionado centralmente)  
**Cómo crearlos:** ver [Módulo 4](../modulo-4-instrucciones-contexto/README.md)

---

### Skills

Una skill es una base de conocimiento estructurada sobre una tecnología o práctica específica. Contiene patrones que Copilot debe seguir siempre (✅), decisiones que debe consultar antes de tomar (⚠️) y anti-patrones que nunca debe usar (🚫).

**Quién los mantiene:** Equipo de Gobierno ECI  
**Dónde viven:** `.github/skills/` en agents-factory  
**Cómo usarlos:** los agentes los cargan automáticamente; ver [Módulo 1.3](../modulo-1-agentes-customizados/03-entender-respuesta-workflow-p0-p5.md)

Skills disponibles actualmente:

| Skill | Tecnología | Estado |
|---|---|---|
| `authoring-agent-skills` | Meta: cómo crear skills | Estable |
| `researching-technical-frameworks` | Meta: investigación técnica | Estable |

> Skills de dominio (Java, Terraform, AWS, etc.) están en proceso de creación.  
> Para solicitar una nueva skill: ver [Módulo 6.1](../modulo-6-contribuir-ecosistema/01-solicitar-agente-o-skill.md)

---

### Agentes customizados

Un agente customizado es un flujo de trabajo pre-diseñado que combina instrucciones, skills y herramientas para realizar una tarea compleja de forma estructurada. Cuando invocas un agente, este sigue un proceso en fases (P0-P5) que garantiza que verifica las convenciones ECI antes de escribir código.

**Quién los mantiene:** Equipo de Gobierno ECI  
**Dónde viven:** `.github/` en agents-factory (y distribuidos a los proyectos que los usan)  
**Cómo usarlos:** ver [Módulo 1](../modulo-1-agentes-customizados/README.md)

---

### Prompts operacionales

Prompts especializados para tareas específicas del ciclo de vida de desarrollo: investigar tecnologías, generar documentación de arquitectura, auditar código, compilar skills. Son el "motor" interno del agents-factory.

**Quién los usa:** principalmente el Equipo de Gobierno ECI y Tech Leads avanzados  
**Dónde viven:** `.github/prompts/` en agents-factory

---

## Cómo fluye el conocimiento

```
Equipo Gobierno ECI
    │
    ├── Investiga tecnologías (prompts researcher/)
    │       └── genera → Research docs (base de conocimiento interna)
    │
    ├── Compila en skills (prompts compiler/)
    │       └── genera → SKILL.md en .github/skills/
    │
    ├── Crea agentes que usan esas skills
    │       └── genera → .agent.md en .github/
    │
    └── Distribuye a los equipos
            └── Los equipos usan los agentes → mejor código, sin reinventar convenciones
```

---

## Quién hace qué

| Actor | Responsabilidades |
|---|---|
| **Dev** | Usar agentes y el chat. Dar feedback de qué falla o falta. |
| **Tech Lead** | Configurar instrucciones de contexto del proyecto. Solicitar nuevos agentes/skills. |
| **Gobierno ECI** | Crear y mantener skills y agentes globales. Gestionar el programa y métricas. |

---

## Próximos pasos

- [Módulo 0.3 — Setup del entorno: día 1](03-setup-entorno-dia-1.md)
- [Módulo 1.5 — Catálogo de agentes ECI](../modulo-1-agentes-customizados/05-catalogo-agentes-eci.md)
- [Módulo 4 — Instrucciones de contexto](../modulo-4-instrucciones-contexto/README.md)

# Módulo 2 — Modos de Copilot y cuándo usarlos

**Perfil:** Dev  
**Prerequisito:** [Módulo 0.1 — Modos, capacidades y límites](../modulo-0-fundamentos/01-copilot-en-eci-modos-capacidades-limites.md)

Este módulo profundiza en los tres modos de Copilot con ejemplos prácticos.

---

## Contenido

1. [Planificación antes de ejecutar](01-ask-mode.md)
2. [Edit mode: cambios quirúrgicos en archivos](02-edit-mode.md)
3. [Agent mode: tareas multi-paso con herramientas](03-agent-mode.md)

---

## Cuándo usar cada modo — tabla de referencia rápida

| Modo | Activa con | ¿Modifica archivos? | Mejor para |
|---|---|---|---|
| Chat | `Ctrl+Alt+I` / `Cmd+Alt+I` | No | Planificar, preguntar, analizar |
| Edit | `Ctrl+I` / `Cmd+I` sobre código | Sí (con diff) | Cambios concretos y acotados |
| Agent | `@nombre-agente` o menú de chat | Sí (autónomo) | Tareas complejas multi-paso |

---

## La regla de oro

> **Planifica antes de ejecutar.**

Antes de pedirle a Copilot que modifique código o infraestructura, pídele un plan. Revisar el plan es más barato que corregir una implementación equivocada.

# Módulo 4 — Instrucciones de Contexto del Proyecto

**Perfil:** Tech Lead  
**Prerequisito:** [Módulo 0.2 — Mapa del ecosistema](../modulo-0-fundamentos/02-mapa-ecosistema-copilot-eci.md)

Las instrucciones de contexto son el mecanismo por el que un equipo le dice a Copilot "en este proyecto, funciona así". Sin ellas, cada desarrollador tiene que repetir el contexto del proyecto en cada prompt.

---

## Contenido

1. [Qué son los archivos de instrucciones de contexto](01-que-son-instructions-md.md)
2. [Añadir instrucciones de contexto al repositorio de tu equipo](02-anadir-instrucciones-a-tu-repo.md)
3. [Skills globales vs instrucciones de proyecto](03-skills-globales-vs-instrucciones-proyecto.md)

---

## Resumen rápido

| Pregunta | Respuesta corta |
|---|---|
| ¿Para qué sirven? | Le dicen a Copilot qué convenciones, frameworks y restricciones tiene tu proyecto sin que cada dev las repita en cada prompt. |
| ¿Quién las crea? | El Tech Lead del equipo, con input del equipo. |
| ¿Dónde van? | Archivos `*.instructions.md` en las carpetas relevantes del proyecto. El archivo global es gestionado centralmente por el administrador del programa. |
| ¿Se aplican solas? | Sí, Copilot las lee automáticamente cuando detecta el archivo en el workspace. |
| ¿Qué diferencia hay con las skills? | Las instrucciones son del proyecto (cortas, operacionales). Las skills son globales de ECI (detalladas, con patrones técnicos profundos). |

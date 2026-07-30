# Setup del entorno: día 1 con Copilot en VS Code

**Perfil:** Dev  
**Tiempo estimado:** 20-30 min

---

## Prerequisitos

Antes de empezar, verifica que tienes:

- [ ] VS Code versión ≥ 1.85
- [ ] Cuenta GitHub con licencia **Copilot Business** o **Copilot Enterprise** asignada por ECI
- [ ] Acceso al repositorio `agents-factory` en la organización ECI

Si no tienes la licencia asignada, contacta con tu responsable de equipo o con el Equipo de Gobierno ECI.

---

## Paso 1: Instalar la extensión de Copilot

1. Abre VS Code
2. Ve a la vista de Extensiones (`Ctrl+Shift+X` / `Cmd+Shift+X`)
3. Busca **"GitHub Copilot"**
4. Instala las dos extensiones:
   - `GitHub Copilot` (autocompletado inline)
   - `GitHub Copilot Chat` (chat y agent mode)
5. Reinicia VS Code si lo pide

---

## Paso 2: Iniciar sesión con tu cuenta de GitHub

1. En la barra lateral izquierda, busca el icono de cuenta (abajo del todo)
2. Selecciona **"Sign in with GitHub"**
3. Se abrirá el navegador para autorizar VS Code con tu cuenta GitHub de ECI
4. Completa el flujo de autorización

**Verificación:** En la barra de estado inferior de VS Code deberías ver el icono de Copilot (✓ o el logo) sin errores. Si aparece un icono de advertencia, la licencia no está asignada a esa cuenta.

---

## Paso 3: Verificar que Copilot funciona

1. Crea un archivo temporal `prueba.java`
2. Escribe un comentario: `// crear una clase que suma dos números`
3. Espera 1-2 segundos. Copilot debería proponer código en gris
4. Pulsa `Tab` para aceptar, `Esc` para rechazar

Si no aparece ninguna sugerencia, revisa que la extensión esté activa: `Ctrl+Shift+P` → "GitHub Copilot: Toggle Copilot".

---

## Paso 4: Abrir el chat

1. `Ctrl+Alt+I` / `Cmd+Alt+I` para abrir el panel de chat
2. Escribe: `Hola, qué puedes hacer?`
3. Deberías recibir una respuesta describiendo sus capacidades

---

## Paso 5: Acceder a los agentes ECI (opcional, para devs avanzados)

Los agentes customizados de ECI viven en el repositorio `agents-factory`. Para usarlos en tu proyecto:

**Opción A — Clonar agents-factory como referencia**

```bash
git clone <url-del-repo-agents-factory>
cd agents-factory
```

Abre la carpeta en VS Code. Los agentes en `.github/` estarán disponibles en el workspace.

**Opción B — Copiar los artefactos necesarios a tu proyecto**

Copia los archivos `.agent.md` y las skills que necesita tu equipo a la carpeta `.github/` de tu propio repositorio. Consulta con tu Tech Lead qué agentes son relevantes para tu proyecto.

**Opción C — Workspace multi-raíz**

Si trabajas con múltiples repositorios a la vez, puedes abrir tanto tu proyecto como agents-factory en el mismo workspace de VS Code. Los agentes de ambos estarán disponibles.

---

## Paso 6: Configurar preferencias básicas

Abre `settings.json` de VS Code (`Ctrl+,` → icono de archivo arriba a la derecha) y añade estas configuraciones recomendadas:

```json
{
  "github.copilot.enable": {
    "*": true
  },
  "chat.agent.maxRequests": 30,
  "github.copilot.chat.scopeSelection": true
}
```

> `chat.agent.maxRequests: 30` permite a los agentes ECI completar tareas más largas sin detenerse.

---

## Verificación final

Antes de dar el setup por completado, chequea:

- [ ] El autocompletado inline funciona en cualquier archivo de código
- [ ] El chat responde en el panel lateral
- [ ] Puedes referenciar un archivo en el chat con `#nombre-del-archivo`
- [ ] (Opcional) Al escribir `@` en el chat ves los agentes disponibles

---

## Problemas comunes

| Problema | Causa probable | Solución |
|---|---|---|
| Icono de Copilot con error | Licencia no asignada | Contactar con el responsable de equipo |
| No hay sugerencias inline | Extensión desactivada | `Ctrl+Shift+P` → "Toggle Copilot" |
| El chat no responde | Sin conexión o VPN bloqueando | Verificar conexión; revisar política de VPN con IT |
| No aparecen agentes con `@` | agents-factory no está en el workspace | Clonar el repo o copiar los `.agent.md` |

---

## Próximos pasos

- [Módulo 0.1 — Modos, capacidades y límites](01-copilot-en-eci-modos-capacidades-limites.md)
- [Módulo 0.2 — Mapa del ecosistema ECI](02-mapa-ecosistema-copilot-eci.md)
- [Módulo 1.1 — Qué es un agente customizado](../modulo-1-agentes-customizados/01-que-es-un-agente-customizado.md)

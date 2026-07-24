# Métricas de adopción: cómo medir y reportar

**Perfil:** Equipo de Gobierno ECI / Tech Lead  
**Tiempo estimado de lectura:** 8 min

---

## Por qué medir la adopción

Las métricas de adopción sirven para tres cosas:
1. **Justificar la inversión** del programa ante dirección
2. **Identificar oportunidades** de mejora en los guías y agentes
3. **Detectar equipos** que necesitan más soporte

Sin métricas, es imposible saber si el programa está funcionando o qué cambiar.

---

## Fuentes de datos disponibles

### Copilot Business/Enterprise Dashboard (GitHub)

GitHub proporciona un dashboard de administración con métricas agregadas por organización y equipo. Accesible por los administradores de la organización GitHub de ECI.

Métricas disponibles directamente:

| Métrica | Descripción |
|---|---|
| `active_users` | Usuarios que han usado Copilot al menos una vez en el período |
| `acceptance_rate` | % de sugerencias inline aceptadas vs mostradas |
| `suggestions_shown` | Total de sugerencias mostradas |
| `suggestions_accepted` | Total de sugerencias aceptadas |
| `lines_of_code_accepted` | Líneas de código generadas y aceptadas |

---

## KPIs recomendados para el programa ECI

### KPIs de adopción (uso del programa)

| KPI | Descripción | Periodicidad |
|---|---|---|
| **Tasa de activación** | % de licencias asignadas con al menos 1 uso activo en los últimos 30 días | Mensual |
| **Adopción por equipo** | Nº de equipos con tasa de activación > 70% | Mensual |
| **Retención de uso** | % de usuarios activos el mes pasado que siguen activos este mes | Mensual |

### KPIs de calidad de uso

| KPI | Descripción | Periodicidad |
|---|---|---|
| **Acceptance rate** | % de sugerencias inline aceptadas (baseline recomendado: > 25%) | Semanal |
| **Uso de agentes customizados** | Nº de invocaciones de `@agente-eci-*` por semana | Semanal |
| **Uso de chat vs inline** | % de la actividad en chat (Ask/Agent mode) vs autocompletado | Mensual |

### KPIs de impacto (más difíciles, pero más valiosos)

Estos no vienen automáticamente del dashboard y requieren encuestas o proxies:

| KPI | Cómo medirlo |
|---|---|
| **Tiempo ahorrado percibido** | Encuesta mensual (escala 1-5: "Copilot me ahorra tiempo en mi trabajo diario") |
| **Satisfacción con agentes** | Encuesta trimestral por dominio (backend, infra, QA) |
| **Calidad del código generado** | % de PRs donde el reviewer reporta "código generado por IA sin revisión suficiente" |

---

## Cómo acceder a los datos del dashboard

**Para administradores de la organización:**

1. Ve a `github.com/organizations/<org>/copilot`
2. Selecciona la vista "Usage" o "Metrics"
3. Puedes filtrar por equipo (`@org/team-name`)
4. Exporta en CSV para análisis en Excel/Sheets

**API de métricas (para automatización):**

GitHub proporciona una API REST para extraer las métricas programáticamente:

```bash
curl -H "Authorization: Bearer <TOKEN>" \
  "https://api.github.com/orgs/<org>/copilot/metrics?team_slug=<team>"
```

Los campos relevantes: `copilot_ide_code_completions`, `copilot_ide_chat`, `total_active_users`.

---

## Cadencia de reporte recomendada

| Frecuencia | Audiencia | Contenido |
|---|---|---|
| **Semanal** | Equipo de Gobierno ECI interno | Acceptance rate, uso de agentes, anomalías |
| **Mensual** | Tech Leads de equipos | Métricas del equipo, comparativa con mes anterior |
| **Trimestral** | Dirección | Resumen de adopción, ROI estimado, roadmap |

---

## Cómo interpretar el acceptance rate

El acceptance rate (tasa de aceptación de sugerencias inline) es la métrica más accesible, pero hay que interpretarla correctamente:

| Valor | Interpretación |
|---|---|
| < 15% | Bajo. Puede indicar: sugerencias fuera de contexto, desarrolladores que no confían en las sugerencias, o uso principalmente del chat (no del inline). |
| 15-30% | Normal. Rango habitual para uso mixto inline + chat. |
| > 30% | Alto. Indica uso intensivo del inline y buena confianza en las sugerencias. |

**Importante:** un acceptance rate bajo no significa que Copilot no sea útil. Un equipo que usa Copilot principalmente en chat mode puede tener acceptance rate bajo pero alto impacto real.

---

## Plantilla de reporte mensual

```markdown
# Reporte de Adopción Copilot — [Mes] [Año]

## Resumen ejecutivo
- Usuarios activos: X de Y licencias (Z%)
- Equipos con adopción > 70%: N
- Acceptance rate promedio: X%
- Invocaciones de agentes ECI: N

## Por equipo
[tabla: Equipo | Usuarios activos | Acceptance rate | Uso agentes]

## Highlights
[2-3 logros o casos de éxito del mes]

## Áreas de mejora
[2-3 equipos o áreas con adopción baja y plan de acción]

## Próximos pasos del programa
[acciones del siguiente mes]
```

---

## Próximos pasos

- [Módulo 6 — Contribuir al ecosistema](../modulo-6-contribuir-ecosistema/README.md)
- [5.1 — Qué no compartir con Copilot](01-que-no-compartir.md)

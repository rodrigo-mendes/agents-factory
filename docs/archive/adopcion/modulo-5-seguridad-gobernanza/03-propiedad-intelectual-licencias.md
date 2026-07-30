# Propiedad intelectual y licencias

**Perfil:** Dev / Tech Lead  
**Tiempo estimado de lectura:** 5 min

---

## El riesgo con código generado por IA

Copilot puede sugerir fragmentos de código que son similares o idénticos a código de repositorios públicos. Si ese código tiene una licencia copyleft (GPL, LGPL, AGPL), incluirlo en tu proyecto podría implicar obligaciones de licenciamiento que afectan al producto de ECI.

Este riesgo es **bajo pero real**, especialmente en:
- Algoritmos o estructuras de datos poco comunes
- Código que reproduce implementaciones muy conocidas
- Boilerplate de configuración específica de frameworks

---

## Qué hace Copilot Business/Enterprise al respecto

El plan Copilot Business/Enterprise de ECI tiene activado por defecto el **filtro de duplicaciones** (`duplication detection`). Este filtro:

- Detecta sugerencias que coinciden con código público en GitHub
- Bloquea o señala las sugerencias con alta similitud con código público existente
- Reduce significativamente el riesgo de inclusión de código copyleft

**Esto no elimina el riesgo completamente**, pero lo reduce a niveles manejables para uso normal.

---

## Señales de que un fragmento puede ser problemático

Sospecha de código potencialmente copiado cuando:
- Copilot genera un algoritmo complejo de una sola vez sin errores (inusual para código generativo)
- El comentario de copyright de otro proyecto aparece en la sugerencia
- El código tiene un estilo muy diferente al resto del proyecto
- Reconoces el fragmento como un algoritmo muy conocido implementado de forma muy específica

---

## Qué hacer si sospechas de una sugerencia

1. **Busca el fragmento en GitHub** con la búsqueda de código
2. **Verifica la licencia** del repositorio donde lo encuentres
3. Si tiene licencia **MIT, Apache 2.0 o BSD**: bajo riesgo, generalmente compatible
4. Si tiene licencia **GPL/LGPL/AGPL**: consulta con el equipo legal antes de incluirlo
5. Si no encuentras origen claro: usa el código con normalidad (el filtro habrá reducido el riesgo)

---

## Licencias de ECI y código generado

El código generado por Copilot que escribes en repositorios de ECI sigue las políticas de propiedad intelectual estándar de ECI: el código pertenece a ECI como producto del trabajo.

Para dudas sobre el tratamiento legal del código generado por IA en proyectos específicos, contacta con el equipo legal.

---

## Próximos pasos

- [5.4 — Métricas de adopción](04-metricas-adopcion.md)
- [5.1 — Qué no compartir con Copilot](01-que-no-compartir.md)

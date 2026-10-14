# Un caso especial: cuando armas algo grande con varias skills

> ↩ [Guía: sesiones de chat de Copilot](00-guia-sesiones-copilot.md)

Si estás armando algo completo (un endpoint + la lógica de negocio + guardarlo en una base de datos + mandarlo a una cola), y ya tienes instrucciones y skills bien armadas para cada una de esas partes, lo mejor es hacerlo **todo en una sola conversación**. Así, el chat va cargando solo la skill que corresponde a cada parte. Esto funciona porque las reglas de cada parte ya están definidas, así que no hace falta repetirlas cada vez que cambias de tema dentro de la misma tarea.

## Puntos a considerar

En este caso, además de las [señales de que el chat pierde el hilo](05-resumir-vs-empezar-de-cero.md), fíjate también en:

- **Si cargó la skill que no era** para alguna parte (por ejemplo, si escribió el código para guardar en la base de datos pero usó las reglas de la lógica de negocio). Eso indica que algo se mezcló, aunque la charla esté llena.

- **Si vas a resumir, dile bien qué cuidar** (ver [qué decirle al pedirle que resuma](05-resumir-vs-empezar-de-cero.md#qué-decirle-al-pedirle-que-resuma)): el formato del endpoint, el modelo de datos, el esquema del evento, para que el resumen no borre justo lo que las partes siguientes van a necesitar.

- Guarda ese "contrato" del trabajo (los formatos, el modelo, el esquema del evento) en archivos del proyecto, no solo en el chat. Así tienes un respaldo si la charla se resume o si empiezas de cero.

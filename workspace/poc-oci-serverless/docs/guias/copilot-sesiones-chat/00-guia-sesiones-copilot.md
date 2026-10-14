# Guía para Desarrolladores: Cómo usar bien las sesiones de chat de GitHub Copilot en VS Code

Esta guía es para cualquiera que use el chat de Copilot en VS Code y quiera aprovecharlo mejor. La idea es sencilla: cómo hablarle al chat para que entienda bien lo que necesitas, cuántas cosas pedirle en una misma charla, cuándo es mejor empezar de nuevo, y cómo saber si la conversación ya está "demasiado llena" y qué hacer entonces.

Cada tema vive en su propia página para que puedas navegarlo, compartirlo y actualizarlo por separado. Empieza por donde te haga falta o léelas en orden.

## Contenido

1. [Cómo hablarle al chat](01-como-hablarle-al-chat.md) — pide una cosa a la vez, clara, y señala el archivo exacto con `#`.
2. [Cuántas cosas pedirle en una misma conversación](02-cuantas-cosas-por-conversacion.md) — rangos orientativos y la señal del "ah, y de paso…".
3. [Cuándo empezar una conversación nueva](03-cuando-empezar-conversacion-nueva.md) — cambio de objetivo, ruido acumulado, tarea terminada.
4. [Cómo darte cuenta de que la conversación se está llenando](04-barra-de-uso-del-contexto.md) — la barra de uso del contexto y qué hacer con ella.
5. [Cuándo resumir y cuándo empezar de cero](05-resumir-vs-empezar-de-cero.md) — `/compact`, qué priorizar al resumir y señales de que ni resumir alcanza.
6. [Un caso especial: armar algo grande con varias skills](06-caso-varias-skills.md) — todo en una sola conversación, con cuidados extra.
7. [Lista rápida para chequear](07-lista-rapida-para-chequear.md) — el checklist antes de seguir enviando mensajes.

## Resumen rápido

| Pregunta | Respuesta corta |
|---|---|
| ¿Cómo le hablo al chat? | Manda un mensaje a la vez, claro y directo. Usa archivos con `#` y sigue las reglas fijas que están en las instrucciones personalizadas. |
| ¿Cuántas cosas le pido por conversación? | No hay un número fijo. Para algo pequeño, de 1 a 3 cosas. Si es algo grande con habilidades bien hechas, hasta 15 o 30. |
| ¿Cuándo empiezo una conversación nueva? | Cuando cambias de objetivo, si el chat se va por otro lado, o si lo anterior ya no sirve para lo que preguntas ahora. |
| ¿Cómo me doy cuenta de cuánto espacio queda? | Mira la barra que muestra el chat: lo que usas, qué está ocupando espacio y cuánto costó. |
| ¿Cuándo conviene resumir en vez de empezar de cero? | Cuando sigues en el mismo tema y la charla es larga pero ordenada. |
| ¿Qué le digo al pedirle que resuma? | Pide que resuma lo que aún no está guardado en otro lado: acuerdos, decisiones de diseño, restricciones. No hace falta que cuide lo que ya está en las instrucciones o en el código. |
| ¿Cuándo mejor empiezo de cero en vez de resumir? | Cuando hay mucho ruido, vueltas sin sentido, o el chat ya no responde bien ni después de resumir. |

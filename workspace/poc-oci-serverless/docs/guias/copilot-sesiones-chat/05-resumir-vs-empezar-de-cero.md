# Cuándo resumir la conversación y cuándo mejor empezar de cero

> ↩ [Guía: sesiones de chat de Copilot](00-guia-sesiones-copilot.md)

Cuando la conversación se va llenando, VS Code la resume solo, automáticamente, comprimiendo lo más viejo para que puedas seguir trabajando sin que se corte nada. También puedes pedirle tú que lo haga cuando quieras, escribiendo `/compact` en el chat, y de paso puedes decirle qué priorizar en ese resumen (por ejemplo: `/compact prioriza las decisiones sobre el esquema de la base de datos`).

## Cuándo conviene resumir

| Situación | Detalles |
|---|---|
| Continuidad del trabajo | Sigues trabajando en lo mismo, y lo que falta hacer depende de cosas que ya se decidieron antes en esa misma charla (nombres, formatos, decisiones de diseño). |
| Conversación larga pero "limpia" | No hay vueltas en falso ni código que se descartó, simplemente acumulaste mucha charla por una tarea que de por sí era grande. |
| Mantener todo junto | Te interesa que todo el trabajo quede junto en una sola conversación, por ejemplo para después revisarlo todo de una. |

## Cuándo conviene empezar de cero

| Situación | Detalles |
|---|---|
| Intentos fallidos o cambio de enfoque | En el medio hubo intentos fallidos, vueltas en falso o cambiaste totalmente de enfoque; resumir conservaría todo ese ruido que en realidad quieres dejar atrás. |
| Cambio de objetivo | Cambiaste de objetivo (como vimos en [cuándo empezar una conversación nueva](03-cuando-empezar-conversacion-nueva.md)), sin importar cuánto espacio te quede libre todavía. |
| El chat pierde el hilo | Notas que el chat ya no está respondiendo bien, ni siquiera después de resumir (mira la lista de abajo), porque el problema ya no es solo el tamaño de la charla, sino que está perdiendo el hilo. |

## Señales para empezar de cero (ni resumiendo se arregla)

- El chat vuelve a proponerte algo que ya le dijiste que no, incluso después de haber resumido.
- Se olvida de decisiones o archivos que mencionaste al principio.
- Las respuestas se ponen más genéricas, como si no conociera bien tu código.
- Te encuentras teniendo que repetirle cosas ("acuérdate que…") más de una vez en la misma charla.

Por defecto, esto de resumir solo viene activado; se puede apagar con una configuración (`github.copilot.chat.summarizeAgentConversationHistory.enabled`), pero para la mayoría de los casos conviene dejarlo prendido, y usar `/compact` a mano solo cuando quieres controlar tú el momento o el foco del resumen.

## Qué decirle al pedirle que resuma

Cuando le pides que resuma con `/compact`, estás eligiendo qué partes de la charla son las más importantes. Para pedir bien, ayuda saber qué es lo que el chat realmente "ve" en cada momento: las instrucciones generales, tus instrucciones personalizadas, lo que tienes abierto en el editor (archivo activo, selección, errores visibles), lo que mencionaste con `#`, los resultados que ya se ejecutaron, y la charla en sí. El chat solo puede pensar en todo eso junto; lo que no está, para él no existe.

De todo eso, tus **instrucciones personalizadas** ya están seguras, no hace falta que te preocupes por ellas al resumir, porque siempre se incluyen en cada mensaje. Lo que sí cambia es **la conversación en sí**, que es lo primero que se reduce cuando se resume. Por eso, al pedir `/compact`, es buena idea decirle exactamente qué no puede perder, por ejemplo:

- Acuerdos o formatos que se definieron durante la charla (como el nombre de una función, cómo es un request, o el nombre de un evento).
- Decisiones de diseño que tomaste ahí y que todavía no están escritas en ningún archivo (por qué elegiste hacer algo de cierta manera).
- Restricciones que diste al principio (como "no toques el módulo de facturación").

No hace falta pedir que cuide cosas que ya están seguras de otra forma: las reglas en tus instrucciones personalizadas, o el código que ya está escrito en tus archivos (eso queda ahí, se resuma o no la charla). Pedirle "no pierdas nada" suele dar resúmenes poco útiles; pedirle que se enfoque en las dos o tres cosas que todavía no están guardadas en otro lado, sí funciona.

Por ejemplo: `/compact prioriza el formato del endpoint y la decisión de usar el patrón outbox para publicar el evento; el resto resúmelo libremente.`

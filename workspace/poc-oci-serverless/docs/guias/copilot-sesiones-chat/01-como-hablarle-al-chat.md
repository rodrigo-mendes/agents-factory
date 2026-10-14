# Cómo hablarle al chat

> ↩ [Guía: sesiones de chat de Copilot](00-guia-sesiones-copilot.md)

- **Pide una cosa a la vez y dilo claro.** Por ejemplo, decir "Arregla el bug de validación en UserService.cs" funciona mucho mejor que "Dime qué está mal en el código". Cuanto más específico seas, mejor te va a entender.

- **Muestra exactamente de qué archivo o parte del código hablas**, usando `#` para mencionarlo. Copilot busca solo lo que cree relevante en tu proyecto, pero si la pregunta es un poco vaga, mejor señala el archivo o función exacta; así no te da una respuesta genérica.

- **Pon las reglas que siempre quieres que siga (cómo nombras las cosas, qué arquitectura usas, etc.) en las instrucciones personalizadas**, no las repitas en cada mensaje. Lo bueno de ponerlas ahí es que el chat las tendrá en cuenta siempre, aunque la conversación se resuma más adelante.

- **Sigue haciendo preguntas relacionadas mientras sea sobre lo mismo**: "Ahora agrégale un test", "explícamelo mejor", "hazlo async" son ejemplos de cosas que puedes pedir sin empezar otra conversación.

- **Dile también qué NO quieres que modifique**, especialmente si la tarea incluye varios archivos.

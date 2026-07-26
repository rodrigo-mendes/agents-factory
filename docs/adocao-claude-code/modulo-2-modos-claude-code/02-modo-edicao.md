# Modo de edição: mudanças cirúrgicas em arquivos

**Perfil:** Dev  
**Tempo estimado de leitura:** 5 min

---

## Para que serve o modo de edição

No Claude Code, editar é nativo: você descreve a mudança que quer em linguagem natural e o Claude aplica a alteração no arquivo. A diferença em relação a apenas perguntar é que aqui **a resposta aparece como um diff** que você pode aprovar ou rejeitar antes de ser gravado.

É a forma certa de trabalhar quando você sabe exatamente **o que quer mudar e onde**.

---

## Como pedir uma edição pontual

Não existe um atalho separado do tipo `Ctrl+I`. No Claude Code, a edição faz parte do mesmo loop de conversa:

1. Descreva a mudança em linguagem natural, **referenciando o método/arquivo com `@`** (ou tendo o arquivo aberto no IDE)
2. Seja explícito sobre o que quer alterar e o que **não** deve ser tocado
3. O Claude propõe a mudança e mostra o **diff**
4. Você **revisa o diff** e aprova ou rejeita
5. Se algo não ficou certo, peça um ajuste na mesma conversa

O Claude mantém o contexto entre os passos, então você refina iterativamente sem repetir tudo.

---

## A chave: delimitar bem o escopo

Quanto mais delimitado o alvo da mudança, mais preciso o resultado. Se você pedir uma alteração "no arquivo inteiro", o Claude pode mexer em partes que você não queria tocar.

**Boa prática:**
- Para mudar um método: aponte só aquele método (`@OrderService.java`, método `processOrder`)
- Para adicionar validação: descreva o bloco exato onde a validação entra
- Para refatorar uma classe: referencie a classe inteira, mas seja explícito na instrução sobre o que **não** mudar

---

## Padrões de uso frequentes na BRX

### Refatorar um método

```
No @OrderService.java, refatore o método processOrder()
para extrair a lógica de validação em um método privado `validateOrder`.
Não mude a assinatura pública do método.
```

### Adicionar tratamento de erros

```
No método de consumo de @NotificationProcessor.java, adicione tratamento de erros:
capture SqsException separadamente,
logue o erro com o correlationId da mensagem e relance como RuntimeException.
```

### Gerar um teste unitário

```
Gere os testes unitários com JUnit 5 e Mockito para todos os métodos públicos
de @OrderService.java.
Cubra o caminho feliz e os principais casos de erro.
```

### Adicionar logs

```
No método send() de @NotificationService.java, adicione logs SLF4J
no início e no fim do método, com nível INFO e com o parâmetro orderId como contexto.
```

### Atualizar nomenclatura

```
Em @OrderController.java, renomeie todas as variáveis `req` para `orderRequest`
e `res` para `orderResponse`.
```

---

## Instruções eficazes ao editar

A edição funciona melhor com instruções que especificam:
- **O que fazer** e **o que não tocar**
- **O nome exato** de métodos, variáveis ou classes relevantes
- **O comportamento esperado**, não só a forma

✅ Preciso:
```
Adicione validação null-check para o campo `customerId` antes da linha com `repository.findById`.
Lance IllegalArgumentException com a mensagem "customerId cannot be null".
```

❌ Vago:
```
Arrume os null checks.
```

---

## Revisar o diff antes de aceitar

**Sempre revise o diff completo antes de aceitar**, especialmente quando:
- A mudança abrange um bloco grande
- A instrução afetava lógica de negócio
- O método tem efeitos colaterais

O Claude pode propor mudanças adicionais que você não pediu. Leia o diff bloco a bloco: aprove o que faz sentido e rejeite (ou peça para refazer) o que estiver fora do escopo. Não aceite alterações sem lê-las só porque "parecem certas".

---

## Quando editar não é suficiente

- A mudança afeta múltiplos arquivos → planeje primeiro (Plan Mode) e deixe o modo agente aplicar as edições coordenadas
- Você precisa provisionar infra ou gerar vários arquivos novos → use o modo agente / um subagente
- Você precisa que o Claude conheça as convenções BRX para a mudança → use um subagente ou comando slash customizado (ele tem as skills)

---

## Próximos passos

- [2.3 — Modo agente: tarefas multi-passo](03-modo-agente.md)
- [1.2 — Quando usar agente vs chat livre](../modulo-1-agentes-customizados/02-quando-usar-agente-vs-chat-livre.md)

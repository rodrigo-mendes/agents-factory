# Responsabilidade humana: revisar sempre o código gerado

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 6 min

---

## O princípio fundamental

> **O código que o Claude gera é uma proposta. O código que você aceita é seu.**

O Claude Code é um agente, não um autor. Quando você aceita código gerado por IA e o inclui em um PR, esse código passa a ser sua responsabilidade: perante a equipe, perante o processo de revisão e perante o negócio.

Isso não significa que você não deva usar o Claude Code — significa que você deve revisá-lo com o mesmo rigor com que revisaria código de um colega.

---

## Por que o Claude comete erros

### Problemas comuns no código gerado

| Tipo de erro | Frequência | Exemplo |
|---|---|---|
| **Lógica de negócio incorreta** | Alta | Cálculos que parecem corretos mas não são em casos de borda |
| **APIs desatualizadas** | Média | Usa uma versão de API que foi depreciada |
| **Permissões IAM excessivas** | Média | Gera `Action: "*"` em políticas onde não é necessário |
| **Código que compila mas não funciona** | Média | Testes que sempre passam porque os mocks são permissivos demais |
| **Problemas de segurança sutis** | Baixa-média | Injeção estilo SQL em queries DynamoDB construídas por concatenação |
| **Imports de bibliotecas não declaradas** | Alta | Usa uma classe de uma biblioteca que não está no pom.xml |
| **Null pointer potencial** | Média | Não verifica Optional antes de chamar `.get()` |

---

## Checklist de revisão mínima

Antes de incluir código gerado pelo Claude Code em um commit:

### Para qualquer código

- [ ] O código faz o que eu pedi? (leia o que ele gerou, não o que você pediu)
- [ ] Há imports de bibliotecas que não estão no projeto?
- [ ] Há valores hardcoded que deveriam ser configuráveis?
- [ ] Há nulls sem verificação em caminhos que poderiam ser nulos?

### Para lógica de negócio

- [ ] Os casos de borda estão cobertos? (valores-limite, coleções vazias, campos opcionais)
- [ ] Os cálculos estão corretos para os casos que importam?
- [ ] O comportamento em caso de erro é o esperado?

### Para testes

- [ ] O teste realmente falha se eu remover o código que ele testa?
- [ ] Os mocks estão configurados de forma específica (não `when(mock.any()).thenReturn(...)`)?
- [ ] O teste cobre os casos que importam, não só o caminho feliz?

### Para infraestrutura (Terraform/IAM)

- [ ] As permissões IAM seguem o princípio de menor privilégio?
- [ ] Há recursos sem as tags BRX padrão?
- [ ] A configuração é a correta para o ambiente alvo (dev/staging/prod)?

---

## Quanto tempo dedicar à revisão

A revisão não deve ser proporcional ao tamanho do código gerado, e sim à sua **criticidade**:

| Tipo de código | Nível de revisão |
|---|---|
| Scaffolding ou código boilerplate | Rápido: verifique se compila e segue as convenções |
| Lógica de negócio | Detalhado: valide cada caminho contra os requisitos |
| Segurança (auth, autorização, cifragem) | Muito detalhado: não confie no primeiro resultado |
| Infra (IAM, networking, dados) | Muito detalhado: erros em prod são caros |
| Testes | Médio: verifique se realmente testam o que dizem |

---

## Como usar o Claude para revisar o próprio código gerado

Você pode pedir ao Claude uma segunda passada crítica sobre o que ele acabou de gerar:

```
Revise o código que você acabou de gerar.
Há algum caso de borda não tratado ou problema potencial que você não considerou?
Seja crítico.
```

O Claude Code também oferece os comandos `/code-review` (revisão de correção e qualidade do diff atual) e `/security-review` (revisão de segurança das mudanças pendentes) como apoio. Isso **não substitui** a sua revisão, mas pode pegar coisas que passaram batido na primeira geração.

---

## A responsabilidade no processo de revisão de PRs

O Claude Code pode ajudar você a revisar um PR (ver guia 3.4), mas:

- **O aprovador do PR continua responsável** pelo que aprova
- Um "o Claude revisou e não achou nada" não é justificativa diante de um incidente de produção
- Os revisores humanos aportam o que o Claude não pode: conhecimento do negócio, contexto histórico, juízo sobre trade-offs

---

## Próximos passos

- [5.3 — Propriedade intelectual e licenças](03-propriedade-intelectual-licencas.md)
- [3.4 — Code Review com o Claude Code](../modulo-3-guias-por-papel/04-code-review.md)

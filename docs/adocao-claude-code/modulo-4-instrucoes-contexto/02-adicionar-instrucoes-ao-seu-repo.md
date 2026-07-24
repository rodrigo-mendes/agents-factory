# Adicionar instruções de contexto ao repositório da sua equipe

**Perfil:** Tech Lead  
**Tempo estimado:** 30-45 min (primeira vez)

---

## Processo passo a passo

### Passo 1: Reunir as convenções da equipe

Antes de escrever o arquivo, faça uma breve sessão com a equipe para reunir:

- Quais convenções de código são sagradas neste projeto?
- Que coisas o Claude Code gera de forma incorreta que temos que corrigir sempre?
- O que sai errado em código novo quando não há instruções de contexto?

Essas respostas são o conteúdo do arquivo.

---

### Passo 2: Criar o `CLAUDE.md` da raiz

Você tem duas opções.

**Opção A — deixar o Claude Code gerar um rascunho com `/init`.** Dentro do projeto, rode o comando slash:

```
/init
```

O `/init` analisa o codebase (estrutura, dependências, padrões) e gera um `CLAUDE.md` inicial na raiz. É o ponto de partida mais rápido: depois você revisa e ajusta com o time.

**Opção B — criar o arquivo manualmente:**

```bash
touch CLAUDE.md
```

Use o template da guia 4.1 como ponto de partida. Conteúdo mínimo recomendado:

```markdown
# Instruções de contexto — [Nome do projeto]

## Stack
[Framework, versões principais, bibliotecas-chave]

## Estrutura de pacotes/módulos
[Como o código está organizado]

## Convenções de naming
[Nomes de classes, métodos, variáveis, tabelas]

## Testing
[Framework, tipos de testes, como se organizam]

## Logging
[Framework, níveis, o que incluir sempre]

## O que evitar
[Padrões que não se usam neste projeto]
```

---

### Passo 3: Adicionar instruções específicas por área (opcional)

Se o seu projeto tem partes com convenções muito distintas, crie `CLAUDE.md` aninhados nas respectivas subpastas:

```bash
# Para a camada de infraestrutura Terraform
touch terraform/CLAUDE.md

# Para os testes
touch src/test/CLAUDE.md
```

Cada arquivo aninhado é aplicado quando o Claude Code está trabalhando em arquivos daquela subpasta.

---

### Passo 4: Validar com o Claude Code que as instruções são aplicadas

Abra uma conversa no projeto e pergunte:

```
Que instruções de contexto você leu do CLAUDE.md deste projeto?
Enumere os pontos mais importantes.
```

Se o Claude Code listar os pontos das suas instruções, elas estão funcionando.

Teste com um caso real:

```
Gere um esqueleto de repositório para a entidade Order.
```

O código gerado deve seguir a estrutura de pacotes e os sufixos de naming que você definiu.

---

### Passo 5: Fazer commit e compartilhar com a equipe

```bash
git add CLAUDE.md
git commit -m "chore: adicionar instruções de contexto (CLAUDE.md) para o Claude Code"
git push
```

Qualquer desenvolvedor que clonar o repositório ou fizer pull terá as instruções disponíveis automaticamente.

---

### Passo 6: Manter o arquivo atualizado

As instruções devem evoluir com o projeto. Quando a equipe:
- Muda de framework ou versão
- Adota uma nova convenção de naming
- Descobre um padrão que o Claude Code gera errado com frequência

...atualize o arquivo. Trate o `CLAUDE.md` como documentação de convenções que também beneficia novos membros da equipe.

---

> **Dica:** para revisar ou editar depois quais arquivos de memória estão ativos, use o comando slash **`/memory`** — ele lista os `CLAUDE.md` carregados na sessão e abre-os para edição. Para regras que devem valer em **todos** os repositórios da BRX (não só neste projeto), fale com a Equipe de Governança BRX sobre a memória gerenciada da organização (ver [guia 4.1](01-o-que-e-claude-md.md)).

---

## Boas práticas de manutenção

| Prática | Por quê |
|---|---|
| Deixe o arquivo curto (< 100 linhas) | Instruções longas são aplicadas pior; priorize o que tem mais impacto |
| Evite duplicar o que está nas skills globais | Ver guia 4.3; duplicar cria inconsistências |
| Use linguagem imperativa e direta | "Use SLF4J" em vez de "Neste projeto prefere-se SLF4J quando possível" |
| Revise o arquivo a cada trimestre | As convenções do projeto evoluem |
| Inclua o arquivo no onboarding da equipe | Novos membros devem saber que ele existe |

---

## Como usar o Claude Code para escrever as próprias instruções

A forma mais rápida é rodar `/init`, que analisa o codebase e propõe um `CLAUDE.md` inicial automaticamente.

Se você preferir controlar o formato, pode pedir explicitamente ao Claude Code que analise o projeto e proponha um rascunho:

```
Analise a estrutura de código em @src/ e o arquivo @pom.xml.
Proponha um rascunho de CLAUDE.md com as convenções que você
conseguir inferir do código existente.
Use o formato: Stack, Estrutura de pacotes, Convenções de naming, Testing, O que evitar.
```

Depois revise e ajuste o rascunho com a equipe.

---

## Próximos passos

- [4.3 — Skills globais vs instruções de projeto](03-skills-globais-vs-instrucoes-projeto.md)
- [4.1 — O que é o CLAUDE.md](01-o-que-e-claude-md.md)

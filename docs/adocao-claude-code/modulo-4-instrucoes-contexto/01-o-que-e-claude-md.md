# O que é o `CLAUDE.md`

**Perfil:** Tech Lead / Dev  
**Tempo estimado de leitura:** 7 min

---

## O problema que resolve

Sem instruções de contexto, cada desenvolvedor tem que explicar ao Claude Code as mesmas coisas repetidas vezes:

```
"Neste projeto usamos Java 17 com Spring Boot 3.2, os testes são com JUnit 5,
os logs com SLF4J, os nomes de packages seguem o padrão com.brx.{dominio}.{subdominio},
os endpoints seguem REST nível 3..."
```

Com um arquivo `CLAUDE.md`, tudo isso é aplicado **automaticamente** em qualquer conversa com o Claude Code dentro daquele projeto.

---

## Os níveis do `CLAUDE.md`

No Claude Code, a memória de instruções vive em arquivos chamados `CLAUDE.md`. Existem vários níveis, que o Claude Code **concatena** (não se sobrescrevem — todos entram no contexto). Do mais específico ao mais amplo:

### `CLAUDE.md` na raiz do projeto

**Caminho:** `CLAUDE.md` na raiz do repositório

**O que faz:** o Claude Code lê seu conteúdo **automaticamente** e o adiciona ao contexto de **todas** as conversas naquele projeto, sem que o usuário precise fazer nada.

**Quando usar:** convenções gerais do projeto que se aplicam sempre.

---

### `CLAUDE.md` aninhados em subpastas

**Caminhos possíveis:** qualquer subpasta do projeto pode ter seu próprio `CLAUDE.md`.

Exemplos:
```
CLAUDE.md                 ← instruções globais do projeto (raiz)
src/
  api/
    CLAUDE.md             ← instruções específicas da camada de API
  infrastructure/
    CLAUDE.md             ← instruções para Terraform
tests/
  CLAUDE.md               ← convenções de testes
```

**O que faz:** o Claude Code carrega o `CLAUDE.md` de uma subpasta quando está trabalhando em arquivos dentro dela. Assim, diferentes partes do projeto podem ter convenções próprias sem inflar o arquivo da raiz.

**Quando usar:** quando diferentes partes do projeto têm convenções distintas, ou quando você quer instruções mais específicas do que as globais.

---

### Memória de usuário — `~/.claude/CLAUDE.md`

**Caminho:** `~/.claude/CLAUDE.md` (na home do desenvolvedor)

**O que faz:** aplica-se a **todos** os projetos daquele desenvolvedor, em qualquer repositório. É a memória pessoal do dev (por exemplo, preferências individuais de estilo de resposta).

**Quando usar:** para preferências pessoais que não pertencem a nenhum projeto específico. Não coloque aqui convenções do time — essas vão no `CLAUDE.md` do repositório, para que toda a equipe as compartilhe via Git.

---

### Preferências pessoais por projeto — `CLAUDE.local.md`

**Caminho:** `CLAUDE.local.md` na raiz do projeto (adicione ao `.gitignore`)

**O que faz:** aplica-se **apenas a você**, **apenas naquele projeto**. Não é versionado, então não afeta o resto da equipe.

**Quando usar:** ajustes pessoais para um repositório específico (por exemplo, um atalho de comando local, uma preferência sua de saída) que não devem entrar no `CLAUDE.md` compartilhado.

---

### Memória gerenciada — política da organização

**Caminho:** definido pela organização (memória "managed", instalada por política; ex.: `/Library/Application Support/ClaudeCode/CLAUDE.md` no macOS, `/etc/claude-code/CLAUDE.md` no Linux). Também configurável via `managed-settings.json`.

**O que faz:** aplica-se a **todos os desenvolvedores** da organização e **não pode ser sobrescrita** por configurações locais. É o mecanismo pelo qual a **Equipe de Governança BRX** pode impor regras transversais (por exemplo, "nunca commitar segredos", "seguir o padrão de logging corporativo") a todos os repositórios de uma vez.

**Quando usar:** exclusivo da Governança BRX. Como Dev ou Tech Lead você não edita esse arquivo, mas é bom saber que ele existe e tem a maior precedência.

---

## Importar outros arquivos no `CLAUDE.md`

Um `CLAUDE.md` pode **importar** outros arquivos com a sintaxe `@caminho/para/arquivo`. Isso evita duplicação e mantém o arquivo raiz curto:

```markdown
# Instruções de contexto — Serviço de Pedidos BRX

Convenções de arquitetura: @docs/convencoes.md
Fluxo de git do time: @docs/git-workflow.md
Minhas preferências pessoais: @~/.claude/minhas-preferencias.md
```

Detalhes importantes:
- Caminhos **relativos** são resolvidos em relação ao arquivo que contém o import (não ao diretório atual).
- Funciona com `~/` para apontar para a home do desenvolvedor.
- A importação é recursiva até **4 níveis** de profundidade (um arquivo importado pode importar outro).
- Um `@caminho` dentro de crase (`` `@exemplo` ``) é tratado como texto literal e **não** é importado — útil para dar exemplos sem disparar a importação.

---

## O que vai em um `CLAUDE.md`

As instruções são **curtas e operacionais**. Não são documentação de arquitetura, são regras de comportamento para o Claude Code.

### O que SIM incluir

- Stack tecnológica: versões de frameworks e bibliotecas usadas
- Convenções de naming: pacotes, classes, métodos, variáveis, tabelas
- Padrões de código do projeto: como se estruturam serviços, repositórios, etc.
- O que NÃO fazer: imports de bibliotecas não usadas, padrões depreciados no projeto
- Configuração relevante: como os testes são organizados, como os erros são tratados

### O que NÃO incluir

- Documentação de arquitetura extensa (não é o propósito)
- Segredos, credenciais ou dados sensíveis (nunca)
- Descrição do negócio (o Claude Code não precisa dela para programar)
- Coisas que já estão nas skills globais da BRX (duplicação desnecessária; ver guia 4.3)

---

## Exemplo de `CLAUDE.md` para um projeto BRX

```markdown
# Instruções de contexto — Serviço de Pedidos BRX

## Stack
- Java 17, Spring Boot 3.2, Maven
- Spring Cloud Function para Lambdas
- DynamoDB (AWS SDK v2), SQS (Spring Cloud AWS)
- JUnit 5 + Mockito para testes unitários
- Testcontainers + LocalStack para testes de integração

## Estrutura de pacotes
com.brx.orders.{layer}
- domain: entidades e value objects (sem dependências externas)
- application: serviços e casos de uso
- infrastructure: adaptadores de DynamoDB, SQS, HTTP
- api: handlers Lambda e DTOs

## Convenções
- Nomes de classes em inglês, comentários em português
- Serviços: sufixo `Service`, interfaces explícitas em application/
- Repositórios: sufixo `Repository` na porta, `DynamoDb{Nome}Repository` na implementação
- Testes unitários: `{NomeClasse}Test.java`, sem @SpringBootTest
- Testes de integração: `{NomeClasse}IT.java`

## Logging
- SLF4J + Logback, nunca System.out
- Log INFO nos pontos de entrada/saída de serviços
- Log ERROR com stack trace completo para exceções não esperadas
- Incluir sempre orderId ou correlationId no contexto do log

## O que evitar
- Não usar @Autowired em construtores (usar injeção por construtor diretamente)
- Não criar singletons estáticos
- Não usar Optional.get() sem verificar isPresent()
- Não importar bibliotecas que não estejam no pom.xml
```

---

## Como o Claude Code aplica as instruções

Quando você abre um projeto com esses arquivos:
1. Ao iniciar a sessão, o Claude Code lê automaticamente o `CLAUDE.md` da raiz do projeto e os `CLAUDE.md` dos diretórios **acima** do seu diretório de trabalho (de cima para baixo).
2. As instruções são adicionadas ao contexto de todas as conversas daquele projeto.
3. Os `CLAUDE.md` de **subpastas abaixo** do seu diretório de trabalho são carregados **sob demanda**, quando o Claude Code lê arquivos dentro dessas subpastas.
4. Todos os níveis são **concatenados**, na ordem de precedência: memória gerenciada → memória de usuário → projeto (`CLAUDE.md`) → local (`CLAUDE.local.md`). Eles não se sobrescrevem; se duas regras se contradizem, o resultado fica imprevisível — por isso vale revisar para evitar conflitos.
5. Os subagentes também respeitam essas instruções (a menos que as instruções do próprio subagente indiquem o contrário).

Você não precisa fazer nada para ativá-las. Duas formas de inspecionar/editar:
- Pergunte ao Claude Code: `Que instruções de contexto você leu do CLAUDE.md deste projeto?` — ele deve listar os pontos do arquivo.
- Use o comando slash **`/memory`** para listar e abrir os arquivos de memória carregados na sessão atual e editá-los.

---

## Próximos passos

- [4.2 — Como adicionar instruções ao seu repositório](02-adicionar-instrucoes-ao-seu-repo.md)
- [4.3 — Skills globais vs instruções de projeto](03-skills-globais-vs-instrucoes-projeto.md)

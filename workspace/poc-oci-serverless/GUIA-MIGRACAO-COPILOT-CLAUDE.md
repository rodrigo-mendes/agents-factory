# Guia de Migração: GitHub Copilot → Claude Code

> Manual reutilizável, passo-a-passo, explicando **o que fazer e por quê**. Construído a partir de uma migração
> real (projeto `poc-oci-serverless`: 6 agentes, 24 instruções, 44 prompts, 37 skills) e validado contra a
> documentação oficial do Claude Code (`https://code.claude.com/docs`).

---

## Índice

1. [Visão geral & princípios](#1-visão-geral--princípios)
2. [Mapa de equivalências](#2-mapa-de-equivalências)
3. [Tradução de ferramentas](#3-tradução-de-ferramentas)
4. [Passo 0 — Inventário](#passo-0--inventário)
5. [Passo 1 — CLAUDE.md](#passo-1--claudemd)
6. [Passo 2 — Subagents](#passo-2--subagents)
7. [Passo 3 — Rules (escopo por caminho)](#passo-3--rules-escopo-por-caminho)
8. [Passo 4 — Skills](#passo-4--skills)
9. [Passo 5 — Prompts → Commands com fork](#passo-5--prompts--commands-com-fork)
10. [Passo 6 — settings.json + .gitignore](#passo-6--settingsjson--gitignore)
11. [Passo 7 — Corrigir referências internas](#passo-7--corrigir-referências-internas)
12. [Passo 8 — Verificação](#passo-8--verificação)
13. [Armadilhas & lições aprendidas](#13-armadilhas--lições-aprendidas-gotchas)
14. [Apêndice — Scripts prontos](#14-apêndice--scripts-prontos)
15. [Checklist de migração](#15-checklist-de-migração)

---

## 1. Visão geral & princípios

O GitHub Copilot e o Claude Code resolvem o mesmo problema (assistente de código guiado por instruções de
projeto), mas com **modelos de configuração diferentes**. Migrar não é "copiar arquivos": é **traduzir conceitos**.

Três princípios que orientam todo o guia:

1. **Validar contra a doc oficial, não a memória.** Frontmatter, nomes de campo e de modelo mudam. Sempre
   confirme em `https://code.claude.com/docs` (especialmente `sub-agents`, `skills`, `memory`, `settings`).
2. **Migração não-destrutiva (coexistência).** Crie `.claude/` **ao lado** de `.github/` sem apagar nada. Os dois
   funcionam em paralelo durante a transição; você só remove o Copilot quando tiver confiança.
3. **Incremental, em fases.** Núcleo primeiro (CLAUDE.md + agentes + skills), depois rules, depois prompts. Valide
   cada fase antes de seguir.

---

## 2. Mapa de equivalências

| GitHub Copilot (`.github/`) | Claude Code | Escopo |
|---|---|---|
| `copilot-instructions.md` | `CLAUDE.md` (raiz) | Projeto inteiro, sempre carregado |
| `AGENTS.md` (catálogo) | `CLAUDE.md` (tabela de roteamento) + `.claude/AGENTS.md` | Referência |
| `agents/<n>.agent.md` | `.claude/agents/<n>.md` | Subagente especializado |
| `instructions/<n>.instructions.md` (`applyTo:`) | `.claude/rules/<n>.md` (`paths:`) | Por caminho, sob demanda |
| `prompts/<n>.prompt.md` (`agent:`) | `.claude/commands/<n>.md` (`context: fork` + `agent:` + `background: false`) | Comando `/<n>` |
| `skills/<n>/SKILL.md` | `.claude/skills/<n>/SKILL.md` | Conhecimento/playbook |
| `scripts/`, `templates/`, `docs/` | permanecem onde estão (referência por caminho) | — |
| Config do usuário | `~/.claude/CLAUDE.md`, `~/.claude/agents/`, `~/.claude/skills/` | Todos os projetos |

**Por quê essas escolhas:** o Copilot tem um conceito único (prompt → agente) que o Claude Code separa em
três mecanismos (CLAUDE.md sempre-on, rules por caminho, skills sob demanda). A maior parte do trabalho de
migração é decidir **qual mecanismo** recebe cada arquivo.

---

## 3. Tradução de ferramentas

O Copilot usa nomes de ferramenta próprios no frontmatter `tools:` dos agentes. Traduza assim:

| Copilot | Claude Code |
|---|---|
| `read` | `Read` |
| `search` | `Grep`, `Glob` |
| `editFiles` | `Edit` |
| `createFile` | `Write` |
| `runInTerminal` | `Bash` |
| `agent` | `Agent` |

> ⚠️ **`tools:` é de subagents; `allowed-tools:` é de skills/commands.** Não troque um pelo outro (ver
> [Gotchas](#13-armadilhas--lições-aprendidas-gotchas)).

---

## Passo 0 — Inventário

**O quê:** antes de migrar, levante o que existe e em que formato. Isso evita surpresas (ex.: skills sem
frontmatter, prompts sem `agent:`).

**Por quê:** decisões de migração dependem do conteúdo real do frontmatter. Contar e amostrar primeiro torna os
passos seguintes determinísticos.

```bash
# Estrutura e contagens
echo "agents:        $(ls .github/agents/*.agent.md 2>/dev/null | wc -l)"
echo "instructions:  $(ls .github/instructions/*.instructions.md 2>/dev/null | wc -l)"
echo "prompts:       $(ls .github/prompts/*.prompt.md 2>/dev/null | wc -l)"
echo "skills:        $(ls .github/skills/*/SKILL.md 2>/dev/null | wc -l)"

# Amostrar frontmatters (campos: applyTo, agent, tools, name, description)
head -8 .github/agents/*.agent.md
awk -F'applyTo:' '/^applyTo:/{print FILENAME": "$2}' .github/instructions/*.instructions.md

# Quais skills do Copilot NÃO têm frontmatter YAML? (precisarão ganhar um)
for f in .github/skills/*/SKILL.md; do
  head -1 "$f" | grep -q '^---$' || echo "SEM frontmatter: $f"
done
```

---

## Passo 1 — CLAUDE.md

**O quê:** copie o conteúdo de `.github/copilot-instructions.md` para `CLAUDE.md` na raiz. Acrescente uma seção
**Build & Run** com os comandos reais do projeto (build, test, deploy).

**Por quê:**
- O Claude Code carrega `CLAUDE.md` **automaticamente** em toda sessão (não precisa de `@import`).
- **Mantenha < 200 linhas.** Acima disso, a aderência cai (o modelo passa a ignorar regras). Conteúdo profundo
  vai para rules (por caminho) ou skills (sob demanda), não para o CLAUDE.md.
- O Copilot raramente registrava comandos de build/test. O Claude Code **aproveita muito** esse contexto — então
  adicione-o, mesmo que não existisse no Copilot.

**O que entra:** convenções do projeto, tabela de roteamento de agentes, comandos de build/test/deploy, gotchas
não-óbvios. **O que NÃO entra:** tutoriais longos, docs de API (linke), nada que o modelo já infere.

---

## Passo 2 — Subagents

**O quê:** para cada `.github/agents/<n>.agent.md` → `.claude/agents/<n>.md`:
- Renomeie `.agent.md` → `.md`.
- Mantenha `name` e `description`; **traduza `tools:`** (tabela do [§3](#3-tradução-de-ferramentas)).
- Acrescente um gatilho **"Use when…"** na `description`.
- Opcional: defina `model:` em agentes de orquestração/raciocínio.

```yaml
# .claude/agents/oci-deployer.md
---
name: oci-deployer
description: >
  OCI Function Deployer — orchestrates build, push, deploy, and validation.
  Use when deploying a new function version (build -> push -> deploy -> smoke test).
tools: Read, Edit, Bash, Grep, Glob, Agent   # traduzido de read, editFiles, runInTerminal, search, agent
model: sonnet                                # opcional; omitir = herda do pai
---
... corpo (workflow) preservado ...
```

**Por quê cada item:**
- **`description` com "Use when…"** é o **único** campo que o Claude usa para decidir delegar automaticamente.
  Sem gatilho, a delegação vira reativa (só manual). Seja específico (diferencie agentes parecidos).
- **`tools:` (não `allowed-tools:`).** Subagents usam `tools:`. Princípio do menor privilégio: dê só o necessário.
- **`model:`** — use aliases `opus`/`sonnet`/`haiku`/`fable`, ou IDs completos (`claude-opus-4-8`). Omitir = herda
  do modelo da sessão (bom default). Defina explícito só quando tiver certeza (ex.: `sonnet` para orquestradores).

---

## Passo 3 — Rules (escopo por caminho)

**O quê:** `.github/instructions/<n>.instructions.md` → `.claude/rules/<n>.md`, convertendo o frontmatter
`applyTo: "<glob>"` (string) em `paths:` (lista YAML).

```yaml
# ANTES (Copilot)            # DEPOIS (Claude Code)
---                          ---
applyTo: "**/*.tf"     →     paths:
---                            - "**/*.tf"
                             ---
```

**Por quê:** rules com `paths:` carregam **sob demanda** (só quando você abre um arquivo que casa com o glob),
economizando contexto. Sem `paths:`, a rule carrega **sempre** (use para padrões globais).

**Gotcha do brace-expansion:** `applyTo: "**/{Dockerfile,pom.xml}"` é **um** glob (com chaves), não dois. Já
`applyTo: "a.java,b.yaml"` são **dois** globs separados por vírgula de **topo**. Divida só vírgulas fora de `{}`
(o script do [apêndice](#14-apêndice--scripts-prontos) faz isso corretamente).

---

## Passo 4 — Skills

**O quê:** copie cada pasta `.github/skills/<n>/` → `.claude/skills/<n>/` (o **nome da pasta** vira o comando
`/<n>`). Garanta `name` + `description` no frontmatter.

**Por quê / boas práticas:**
- **Frontmatter obrigatório.** Algumas skills do Copilot usam markdown (`**Description:**`) em vez de YAML — o
  Claude Code exige `name` e `description` em YAML. Adicione onde faltar (extraia da descrição existente).
- **`description` é o que dispara a auto-invocação.** Escreva com "Use when…", específica, ≤ 1536 caracteres.
- **Progressive disclosure.** Mantenha o `SKILL.md` como um **índice enxuto** (< 500 linhas) que **referencia**
  arquivos de apoio (blueprints/exemplos) por link. Eles carregam sob demanda quando o Claude os lê — não
  inline tudo, e evite `@arquivo` (que importa eager) para conteúdo grande.

```yaml
# Skill do Copilot SEM frontmatter ganha:
---
name: deploying-oci-functions
description: Builds, pushes, deploys, and validates OCI Function images... Use when deploying a function.
---
# ... corpo original ...
```

---

## Passo 5 — Prompts → Commands com fork

Esta é a **decisão central** da migração e merece atenção.

**O quê:** cada `.github/prompts/<n>.prompt.md` (que tem `agent:` no frontmatter) vira
`.claude/commands/<n>.md` com `context: fork` + `agent:`:

```yaml
# ANTES — .github/prompts/deploy-function.prompt.md
---
description: 'Build, push, deploy, and validate an OCI Function'
agent: oci-deployer
argument-hint: 'Function name or path'
---

# DEPOIS — .claude/commands/deploy-function.md
---
description: Build, push, deploy, and validate an OCI Function. Use when deploying a new version.
argument-hint: Function name or path
context: fork                    # roda em subagent isolado
agent: oci-deployer              # mapeia 1:1 o agent: do Copilot
background: false                # bloqueia e mostra o resultado inline
disable-model-invocation: true   # só roda quando você chama /deploy-function
---
Execute this task now ... **Request / target:** $ARGUMENTS
... corpo do prompt preservado, injetando $ARGUMENTS ...
```

**Por que command com fork?**

`context: fork` + `agent:` são frontmatter **oficial** do Claude Code, suportados igualmente em
`.claude/commands/*.md` e em `.claude/skills/<n>/SKILL.md` (o frontmatter é idêntico nos dois formatos).
Isso torna a tradução do `agent:` do Copilot **fiel**: o `/comando` executa **dentro** do subagente, isolado,
com roteamento garantido pela engine — não é só instrução em texto.

Colocamos os entry points em `.claude/commands/` (e não em `.claude/skills/`) para separar
**comandos do usuário** de **skills de conhecimento**: `.claude/commands/` = ações que você dispara com `/`;
`.claude/skills/` = bibliotecas de padrão que o modelo carrega sob demanda (e que os commands leem via
`**Skill**: ...`). `background: false` faz o comando **bloquear** e transmitir o output inline (o default virou
`background: true` a partir da v2.1.218); `$ARGUMENTS` no corpo faz o alvo digitado chegar ao fork.

> **Nota histórica:** uma versão anterior deste guia mantinha esses entry points como
> `.claude/skills/<n>/SKILL.md` (skill-com-fork), na crença de que command não tinha campo `agent:`.
> Isso estava incorreto — commands suportam `agent:`/`context: fork`. Os 46 entry points foram migrados
> para `.claude/commands/*.md` e endurecidos (`$ARGUMENTS`, `background: false`, tarefa imperativa).

**Por que `disable-model-invocation: true`?** As `description` de skills são listadas no início da sessão para o
Claude decidir auto-invocar — isso consome ~1% da janela de contexto e, com muitas skills, as descrições são
**encurtadas**. Prompts são **ações deliberadas** (você dispara), então tirá-los da auto-listagem reduz o custo a
~zero; continuam acessíveis via `/<nome>`. Resultado: só as skills de **conhecimento** ficam auto-invocáveis.

---

## Passo 6 — settings.json + .gitignore

**`.claude/settings.json`** (versionado) — permissões para reduzir prompts de autorização:

```json
{
  "permissions": {
    "allow": ["Bash(mvn *)", "Bash(terraform fmt *)", "Bash(terraform validate *)", "Read(./src/**)"],
    "ask":   ["Bash(terraform apply *)", "Bash(docker push *)"],
    "deny":  ["Read(./**/.env)", "Read(./**/*.tfvars)"]
  }
}
```

**`.gitignore`** — ignore o que é local/pessoal:

```
.claude/settings.local.json
CLAUDE.local.md
.claude/agent-memory-local/
```

**Precedência de settings** (maior → menor): managed → CLI → `.claude/settings.local.json` →
`.claude/settings.json` → `~/.claude/settings.json`.

---

## Passo 7 — Corrigir referências internas

**Gotcha crítico (fácil de esquecer):** os arquivos migrados referenciam uns aos outros pelos **nomes antigos**.
A migração precisa reescrever:

- `.github/skills/...` → `.claude/skills/...`
- `<nome>.instructions.md` → `<nome>.md` (os arquivos de rules foram renomeados)

**Mas mantenha** referências a `.github/workflows/`, `docs/`, `templates/`, `scripts/` — esses permanecem onde
estão. Sempre **valide que o alvo existe** antes de substituir (script no apêndice).

> No nosso caso real: 64 refs `.github/skills/` e ~35 refs `*.instructions.md` precisaram ser corrigidas. Esquecer
> isso deixa ponteiros quebrados que só aparecem em uso.

---

## Passo 8 — Verificação

Rode um sanity-check ao final de cada fase e no fim:

```bash
# 0 referências quebradas
python3 -c "import glob,re; print('instructions.md:', sum(len(re.findall(r'\.instructions\.md', open(f).read())) for f in glob.glob('.claude/**/*.md', recursive=True)))"

# Contagens batem com o inventário do Passo 0
echo "agents:$(ls .claude/agents/*.md|wc -l) rules:$(ls .claude/rules/*.md|wc -l) skills:$(ls .claude/skills/*/SKILL.md|wc -l)"

# Nenhum SKILL.md > 500 linhas
wc -l .claude/skills/*/SKILL.md | sort -rn | head -3

# YAML válido (ver validador completo no apêndice)
```

Depois, **funcionalmente:** `/memory` (CLAUDE.md carrega?), rode um `/<comando>`, abra um arquivo coberto por
uma rule e confirme a ativação, e verifique que `.github/` continua intacto.

---

## 13. Armadilhas & lições aprendidas (Gotchas)

1. **`tools:` (agents) vs `allowed-tools:` (skills/commands).** Trocar quebra o frontmatter silenciosamente.
2. **Nomes de modelo.** Válidos: `opus`, `sonnet`, `haiku`, `fable`, `inherit`, ou IDs (`claude-opus-4-8`).
   ❌ Inválidos: `claude-opus-4-6` (desatualizado) e sufixos `*plan` (ex.: `opusplan`).
3. **YAML: valores com `:` precisam de aspas.** `argument-hint: Scope: new / review` quebra o parse →
   `argument-hint: "Scope: new / review"`.
4. **Brace-expansion em globs.** `{a,b}` é um glob só; não divida nas vírgulas internas (§3/Passo 3).
5. **Orçamento de listagem de skills.** As descrições somam ~1% do contexto; com dezenas de skills elas são
   encurtadas. Use `disable-model-invocation: true` em ações (prompts) e, se precisar, ajuste
   `skillListingBudgetFraction` no settings.
6. **Skills do Copilot sem frontmatter YAML.** Precisam ganhar `name`+`description` (Passo 4).
7. **Termos de ferramenta herdados que não existem no Claude Code.** Ex.: `runSubagent` → use a ferramenta
   `Agent`; `list_dir` → `Glob`/`Bash ls`. Varra o conteúdo migrado por esses resíduos.
8. **Sobreposição de `paths:`.** Muitas rules no mesmo glob (ex.: 10 em `**/*.java`) injetam tudo de uma vez.
   Ok se forem complementares; vire alerta se forem grandes/conflitantes.
9. **Não confie em contagens de subagentes/auditorias — verifique.** Numa auditoria nossa, um agente reportou
   "26 rules / 10 sem paths" quando eram **24, todas com paths**. Sempre confirme com dados objetivos (`ls`, `wc`).
10. **Quirk de `~/.gitignore_global`.** Se ele ignora `.gitignore`, suas regras locais funcionam mas **não são
    versionadas** — confirme com `git check-ignore -v .gitignore`.

---

## 14. Apêndice — Scripts prontos

> Os scripts abaixo são os efetivamente usados nesta migração. Rode a partir da raiz do repo. Eles **não apagam**
> nada em `.github/` (coexistência).

### 14.1 — Cópia em massa (dirs, AGENTS.md, agentes, skills)

```bash
mkdir -p .claude/agents .claude/rules .claude/skills
cp .github/AGENTS.md .claude/AGENTS.md 2>/dev/null

# agentes: renomear .agent.md -> .md (tools traduzidos no 14.2)
for f in .github/agents/*.agent.md; do
  cp "$f" ".claude/agents/$(basename "$f" .agent.md).md"
done

# skills: copiar pastas 1:1 (blueprints incluídos)
for d in .github/skills/*/; do cp -R "$d" ".claude/skills/$(basename "$d")"; done
```

### 14.2 — Traduzir `tools:` dos agentes (Python)

```python
import glob, re, os
TMAP = {'read':'Read','search':['Grep','Glob'],'editFiles':'Edit',
        'createFile':'Write','runInTerminal':'Bash','agent':'Agent'}
def translate(tokens):
    out=[]
    for t in tokens:
        t=t.strip().strip("'\"")
        if not t: continue
        v=TMAP.get(t,t); out+= v if isinstance(v,list) else [v]
    seen=set(); return [x for x in out if not (x in seen or seen.add(x))]

for f in glob.glob('.claude/agents/*.md'):
    lines=open(f).read().split('\n'); fm_end=next(i for i in range(1,len(lines)) if lines[i].strip()=='---')
    out=[]; i=0
    while i<len(lines):
        m=re.match(r'^tools:\s*(.*)$', lines[i])
        if m and i<fm_end:
            rest=m.group(1).strip(); tokens=[]
            if rest: tokens=rest.strip('[]').split(','); i+=1
            else:
                i+=1
                while i<len(lines) and re.match(r'^\s*-\s+', lines[i]): tokens.append(re.sub(r'^\s*-\s+','',lines[i])); i+=1
            out.append('tools: '+', '.join(translate(tokens))); continue
        out.append(lines[i]); i+=1
    open(f,'w').write('\n'.join(out))
```

### 14.3 — Rules: `applyTo` → `paths` preservando braces (Python)

```python
import glob, os, re
def split_top_commas(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch=='{': depth+=1; cur+=ch
        elif ch=='}': depth-=1; cur+=ch
        elif ch==',' and depth==0: out.append(cur); cur=''
        else: cur+=ch
    if cur.strip(): out.append(cur)
    return [x.strip() for x in out if x.strip()]

for f in glob.glob('.github/instructions/*.instructions.md'):
    name=os.path.basename(f)[:-len('.instructions.md')]; t=open(f).read()
    body=t.split('\n---',1)[1] if t.startswith('---') else t
    m=re.search(r'^applyTo:\s*(.+)$', t, re.M)
    fm=''
    if m:
        val=m.group(1).strip().strip('\'"')
        fm='---\npaths:\n'+''.join(f'  - "{g}"\n' for g in split_top_commas(val))+'---\n'
    open(f'.claude/rules/{name}.md','w').write(fm+body.lstrip('\n'))
```

### 14.4 — Prompts → Commands com fork (Python)

```python
import glob, os, re
INJECT=('Execute this task now for the OCI serverless project. Read the referenced skill below '
        'for the canonical patterns, then carry the task through to completion. If the target '
        'below is empty, ask for the required information before proceeding.\n\n'
        '**Request / target (from the user):** $ARGUMENTS\n')
def get(fm,k):
    m=re.search(rf'^{k}\s*:\s*(.*)$', fm, re.M); return (m.group(1).strip() if m else None)
def unq(v): return v[1:-1] if v and v[0] in "\"'" and v[-1]==v[0] else v
os.makedirs('.claude/commands', exist_ok=True)
for f in glob.glob('.github/prompts/*.prompt.md'):
    name=os.path.basename(f)[:-len('.prompt.md')]; t=open(f).read()
    fm,body=t.split('\n---',1)[0], t.split('\n---',1)[1] if t.startswith('---') else ('',t)
    desc=unq(get(fm,'description') or ''); agent=unq(get(fm,'agent') or ''); hint=get(fm,'argument-hint')
    L=['---', f'description: {desc}']            # sem name: (deriva do filename)
    if hint: L.append(f'argument-hint: {unq(hint)}')
    L+=['context: fork', f'agent: {agent}', 'background: false', 'disable-model-invocation: true', '---']
    open(f'.claude/commands/{name}.md','w').write('\n'.join(L)+'\n\n'+INJECT+'\n'+body.lstrip('\n'))
```

### 14.5 — Corrigir referências internas (valida antes de trocar)

```python
import glob, os, re
files=glob.glob('.claude/**/*.md', recursive=True)
# .github/skills -> .claude/skills
for f in files:
    t=open(f).read(); t2=t.replace('.github/skills/', '.claude/skills/')
    if t2!=t: open(f,'w').write(t2)
# *.instructions.md -> *.md (só se o alvo existir em rules/)
ref=re.compile(r'([A-Za-z0-9_-]+)\.instructions\.md')
miss=[b for b in {m for f in files for m in ref.findall(open(f).read())} if not os.path.isfile(f'.claude/rules/{b}.md')]
assert not miss, f'alvos inexistentes: {miss}'
for f in files:
    t=open(f).read(); t2=ref.sub(r'\1.md', t)
    if t2!=t: open(f,'w').write(t2)
```

### 14.6 — Validador final (frontmatter, refs, scalars com `:`)

```python
import glob, re
files=glob.glob('.claude/**/*.md', recursive=True)
for name,pat in {'instructions.md':r'\.instructions\.md','runSubagent':r'runSubagent','list_dir':r'list_dir'}.items():
    h=sum(len(re.findall(pat, open(f).read())) for f in files); print(f'{name}:', h, '(esperado 0)')
# valores de frontmatter com ': ' não-citados (quebram YAML)
for f in glob.glob('.claude/skills/*/SKILL.md'):
    blk=open(f).read().split('\n---',1)[0]
    for ln in blk.split('\n'):
        m=re.match(r'^(\w[\w-]*):\s+(.*)$', ln)
        if m and m.group(2) and m.group(2)[0] not in '\'"' and ': ' in m.group(2):
            print('CITAR:', f, '->', ln)
```

---

## 15. Checklist de migração

```
[ ] Passo 0 — Inventário: contar agents/instructions/prompts/skills; achar skills sem frontmatter
[ ] Passo 1 — CLAUDE.md na raiz (de copilot-instructions.md) + seção Build & Run, < 200 linhas
[ ] Passo 2 — Subagents: renomear, traduzir tools:, "Use when" na description, model: onde fizer sentido
[ ] Passo 3 — Rules: applyTo -> paths (preservar braces, dividir só vírgulas de topo)
[ ] Passo 4 — Skills: copiar pastas, garantir name+description, progressive disclosure, < 500 linhas
[ ] Passo 5 — Prompts -> .claude/commands/*.md com context: fork + agent: + background: false + disable-model-invocation: true (+ $ARGUMENTS)
[ ] Passo 6 — .claude/settings.json (permissões) + .gitignore (settings.local.json, CLAUDE.local.md)
[ ] Passo 7 — Corrigir refs: .github/skills -> .claude/skills; *.instructions.md -> *.md (validar alvo)
[ ] Passo 8 — Verificação: 0 refs quebradas, YAML válido, contagens batem, comandos funcionam
[ ] .github/ permanece intacto (coexistência); commitar tudo exceto arquivos *.local
```

> **Dica final:** comece simples (CLAUDE.md + agentes) e expanda. O Claude Code é incremental — não precisa
> migrar tudo de uma vez. E sempre **verifique com dados objetivos** o que qualquer auditoria automática reportar.

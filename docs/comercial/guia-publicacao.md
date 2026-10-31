# Guia de publicação — preparação comum

Passo a passo do que **você** executa para levar um bundle do repositório até as plataformas. Este guia
cobre a parte comum; depois dele, siga o guia da plataforma:
[SkillHQ](guia-skillhq.md) · [Agensi](guia-agensi.md). A estratégia (o que vender e por quanto) está em
[estrategia-bundles.md](estrategia-bundles.md).

Cada passo diz **o que fazer**, **o comando**, **o que você deve ver** e **o que fazer se der errado**.

## 0. Antes de começar

- [ ] Branch `chore/packages-families` atualizada: `git pull`.
- [ ] Python 3, Git e `apm` 0.35.0 instalados: `python --version`, `git --version`, `apm --version`.
- [ ] Git com caminhos longos ligados: `git config --global core.longpaths` responde `true`
      (se não: `git config --global core.longpaths true`).
- [ ] Node.js e npm, só se for usar o SkillHQ: `node --version`, `npm --version`.
- [ ] Contas no SkillHQ e/ou no Agensi (os guias de cada plataforma explicam como criar).
- [ ] **Autorização por escrito** para vender o conteúdo
      ([estrategia-bundles.md, seção 2](estrategia-bundles.md#2-antes-de-vender-bloqueadores)).

## 1. Regenerar `.claude/` e o lock (fora do VS Code)

O `apm install` reescreve `apm_modules/` e falha quando outro programa está olhando essa pasta. O VS Code
faz isso. Por isso este passo roda **com o VS Code fechado**.

```bash
# feche o VS Code; abra o "Git Bash" pelo menu Iniciar
cd /c/agents/agents-factory
rm -rf apm_modules
apm install --target claude
python scripts/restore-rule-metadata.py
python scripts/fix-cross-package-links.py
python packages/factory/agent-package-builder/.apm/skills/building-agent-packages/scripts/check_counts.py
```

**Você deve ver:**
- `Installed N APM dependencies` no fim do `apm install`;
- `done -- N file(s) patched` e `done -- 0 link(s) fixed`;
- no `check_counts.py`: `skills 256`, `agents 54`, `rules 56` e `packages 39 (+ 19 bundles)`.

**Se der errado:**

| Sintoma | O que fazer |
|---|---|
| `WinError 5 Access is denied` ou `WinError 145 The directory is not empty` | 1. Confira no Gerenciador de Tarefas que não há `Code.exe` aberto. 2. Rode `apm install --target claude` de novo: o erro é intermitente (nos testes, a 2ª ou 3ª tentativa passou). 3. Se continuar, peça ao TI uma exclusão do antivírus para `C:\agents\agents-factory\apm_modules`. 4. Para não precisar fechar o VS Code nas próximas vezes: `Settings → files.watcherExclude` → adicione `**/apm_modules/**`. |
| `Filename too long` | `git config --global core.longpaths true` e rode de novo. |
| Contagens diferentes das esperadas | Rode `git status` e veja se há pacote novo ou removido; as contagens documentadas estão no `CLAUDE.md`. |

Opcional: `apm audit` para conferir a instalação.

Depois: `git status` mostra `.claude/` e `apm.lock.yaml` alterados. Faça o commit desses arquivos junto
com as mudanças em `packages/`.

## 2. Gerar os pacotes de venda

```bash
python scripts/export-bundle.py --all              # simulação: lista ✅ e ⛔ por bundle, não grava nada
python scripts/export-bundle.py stripe-for-java --apply
```

O que o script faz: instala só o bundle numa pasta temporária de nome curto (`C:\tmp\ax\`), tira as skills
da Vercel, aplica o `export.yml` do bundle (se houver), procura dados sensíveis (nome de cliente,
e-mails, OCIDs, chaves…) e, se estiver tudo limpo, grava:

```
dist/
├── stripe-for-java/claude/          ← pasta para o SkillHQ (README.md + .claude/)
└── stripe-for-java-claude.zip       ← mesmo conteúdo, para o Agensi
```

**Você deve ver:** `✅ stripe-for-java  OK — 6 skills, 2 agents, 6 rules; zip 72 KB sha256 …`.

**Se der errado:**

| Sintoma | O que fazer |
|---|---|
| `⛔ <bundle> BLOQUEADO` | Abra `dist/<bundle>/BLOCKED.txt`: cada linha diz o detector, o arquivo e a linha. Corrija **na fonte** (`packages/...`), refaça o passo 1 e depois o 2. Nunca edite o `dist/` à mão. |
| `Another APM operation is still running` | O APM só aceita uma operação por vez na máquina (lock em `~/.apm`). Espere a outra terminar; não rode o passo 1 e o passo 2 ao mesmo tempo. |
| `⚠️ <bundle> INSTALL FAILED` | Bloqueio de arquivo do Windows (feche o VS Code e rode de novo) ou caminho longo demais: não troque a pasta de trabalho por uma mais longa que `C:\tmp\ax` (`--work`). |
| Um bundle demora muito | `saas-starter-team` baixa os repositórios da Vercel (cerca de 25-40 min na primeira vez). |

O `dist/` está no `.gitignore`: nada dele vai para o Git.

## 3. Escolher a plataforma

| Quero… | Siga |
|---|---|
| vender por download, compra única, com linha de comando | [guia-skillhq.md](guia-skillhq.md) |
| vender por assinatura, ou alcançar agentes além do Claude | [guia-agensi.md](guia-agensi.md) |
| as duas coisas | os dois, começando pelo teste grátis em cada um |

## 4. Registrar o resultado dos testes grátis

Preencha depois do teste grátis em cada plataforma (fase D dos dois guias). Com esta tabela decidimos o
formato definitivo antes de publicar qualquer bundle pago.

| Plataforma | Validou? | Aprovou? | O que o comprador recebeu (skills / agentes / rules) | Mensagem de erro | Data |
|---|---|---|---|---|---|
| SkillHQ | | | | | |
| Agensi | | | | | |

**Por que testar primeiro:** as duas plataformas documentam um `SKILL.md` na raiz do pacote enviado.
O que exportamos é o diretório compilado (`.claude/skills/<nome>/SKILL.md`, mais agentes e rules). Ainda
não sabemos se as plataformas aceitam esse formato.

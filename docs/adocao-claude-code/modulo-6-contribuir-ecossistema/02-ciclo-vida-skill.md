# Ciclo de vida de uma skill: criação, validação e depreciação

**Perfil:** Tech Lead / Equipe de Governança BRX  
**Tempo estimado de leitura:** 8 min

---

## As quatro fases do ciclo de vida

```
[Pesquisa] → [Criação] → [Manutenção ativa] → [Depreciação]
```

---

## Fase 1: Pesquisa

Antes de criar uma skill, é preciso ter base de conhecimento sólida sobre a tecnologia. O agents-factory tem, na sua toolchain de criação, um fluxo de pesquisa técnica de frameworks e os prompts de pesquisa em `.github/prompts/researcher/`.

O output desta fase é um **research document** versionado (como os que existem em `StoryBeat/`).

**Critérios para passar para a Criação:**
- O research cobre a versão atualmente usada na BRX (não versões obsoletas)
- Foram identificados os principais ✅ sempre fazer / ⚠️ perguntar primeiro / 🚫 nunca fazer
- O research foi validado com a documentação oficial (não apenas com blogs ou Stack Overflow)

---

## Fase 2: Criação

Uma skill BRX segue o **Three-Tier design**:

```markdown
## ✅ Always Do (Tier 1 — mandatório)
Padrões que o Claude Code deve seguir sempre, com exemplos de código.

## ⚠️ Ask First (Tier 2 — decisão contextual)
Padrões que dependem do contexto; o subagente deve perguntar antes de aplicá-los.

## 🚫 Never Do (Tier 3 — anti-padrões)
O que não fazer, com o impacto de fazê-lo e a alternativa correta.
```

Ferramentas do agents-factory para criar a skill:
- Um fluxo de compilação de skills: compila um research doc em um SKILL.md estruturado
- Um validador de boas práticas de skill: valida que a skill cumpre os padrões
- Template em `.github/templates/skills/TEMPLATE.SKILL.md`

Quando pronta, a skill consumível pelo Claude Code fica em `.claude/skills/<nome>/SKILL.md`.

**Critérios para considerar a skill pronta:**
- Passa na validação de boas práticas de skill
- Um subagente que usa a skill gera código correto em pelo menos 3 casos de uso representativos
- Foi revisada por pelo menos um Tech Lead do domínio (não apenas por quem a criou)

---

## Fase 3: Manutenção ativa

Uma skill em produção requer manutenção. Os eventos que disparam uma revisão:

| Evento | Ação recomendada |
|---|---|
| Nova versão maior do framework (ex.: Spring Boot 3.x → 4.x) | Atualização da skill ou criação de uma nova versão |
| A skill está há mais de 12 meses sem atualização | Auditoria: verificar se os padrões continuam válidos |
| 3 ou mais reportes de que o subagente gera código incorreto | Investigar se o problema está na skill ou no subagente |
| Mudança nas convenções BRX do domínio | Atualizar a skill para refletir a mudança |

**Princípio de absolutismo de versão:**  
Uma skill = uma versão específica do framework. Se a equipe atualiza de Java 17 para Java 21, e os padrões mudam significativamente, cria-se uma nova skill `java-21-lambda-brx`, não se sobrescreve a existente até que todas as equipes tenham migrado.

---

## Fase 4: Depreciação

Uma skill é depreciada quando:
- A tecnologia que ela cobre já não é usada na BRX
- Foi substituída por uma skill nova da versão seguinte
- Os padrões que ela contém são incompatíveis com a versão atual do framework

**Processo de depreciação:**

1. **Adicionar aviso de depreciação** no início do `SKILL.md`:
   ```markdown
   > ⚠️ DEPRECIADA desde [data]. Substituída por [nome-skill-nova].
   > Os subagentes que usem esta skill devem ser atualizados. Data de remoção: [data +6 meses].
   ```

2. **Notificar as equipes** que usam subagentes que referenciam a skill depreciada

3. **Atualizar os subagentes** que a usavam para referenciar a nova versão

4. **Remover a skill** após o período de depreciação (mínimo 3 meses)

---

## Sinais de uma skill de baixa qualidade

| Sinal | O que indica |
|---|---|
| Os devs não usam o subagente que a consome | A skill pode não cobrir os casos de uso reais |
| O subagente gera código que os devs corrigem sempre no mesmo ponto | Há um padrão faltante ou incorreto no tier ✅ ou 🚫 |
| Os padrões são muito genéricos (sem exemplos de código BRX) | A skill é abstrata demais |
| O research doc que a originou tem mais de 18 meses | Possivelmente desatualizada |

---

## Próximos passos

- [6.3 — Post-mortem de subagente](03-post-mortem-agente.md)
- [6.1 — Solicitar um novo subagente ou skill](01-solicitar-agente-ou-skill.md)
- Guias técnicos do agents-factory: [docs/como-usar/criando-skills.md](../../como-usar/criando-skills.md)

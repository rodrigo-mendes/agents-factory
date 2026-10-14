# Onboarding — Desenvolvedor(a) Java

Trilha para quem vai **escrever, testar e empacotar Functions Java** (FDK). Antes de começar, faça a
parte comum em **[README.md](README.md)** (pré-requisitos + autenticação OCI).

> Referência completa de setup/deploy: **[../../GETTING-STARTED.md](../../GETTING-STARTED.md)**.
> Convenções e roteamento de agents: **[../../CLAUDE.md](../../CLAUDE.md)**.

---

## 1. Pré-requisitos específicos

- **JDK 17** (Amazon Corretto) — `brew install --cask corretto17`
- **Maven** 3.8+ — `brew install maven`
- **Docker** 24+ (para build da imagem)

```bash
java -version    # 17
mvn -version     # >= 3.8
```

---

## 2. Entenda uma Function (5 min)

Cada Function vive em `services/<nome>/` com esta estrutura:

```
services/<nome>/
├── pom.xml            # FDK 1.1.11, OCI SDK BOM 3.86.0, Java 17 source/target
├── func.yaml          # cmd, memory=256, timeout=60, imagens jdk17/jre17
├── Dockerfile         # multi-stage (build jdk17 → runtime jre17), CMD obrigatório
├── build-push.sh      # roda preflight + build + push para o OCIR
├── README.md
└── src/
    ├── main/java/com/brx/functions/<domínio>/   # handler no raiz do pacote
    └── test/java/com/brx/functions/<domínio>/   # testes
```

**Convenções** (ver `.claude/rules/java-functions-project-structure.md`):

- Base package: `com.brx.functions.<domínio>` (o `api-handler` usa `com.brx.serverless.handler`, legado).
- Handler estende `APIGatewayFunction<Req, Res>` do módulo `fn-events` (abstração tipada de API Gateway).
- Inicialização cara (clients OCI SDK, `HttpClient`, `ObjectMapper`) em `@FnConfiguration` — reaproveitada
  entre invocações (modelo *hot function*). **Nunca** guarde estado mutável entre invocações.
- Autenticação a serviços OCI via **Resource Principal** — zero credenciais no código.
- `func.yaml` guarda **OCIDs** e config (`UPPER_SNAKE_CASE`), **nunca segredos** — segredos vêm do Vault.

**Exemplos de referência** (leia nesta ordem):

| Function | Bom para aprender |
|----------|-------------------|
| [`services/api-handler`](../../services/api-handler/) | Handler mínimo, health check, observabilidade básica |
| [`services/func-api-facade`](../../services/func-api-facade/) | Integração com Vault + Object Storage, métricas custom |
| [`services/func-rr-rest-proxy`](../../services/func-rr-rest-proxy/) | OAuth2 (IDCS), retry HTTP, transformação JSON↔XML, tracing APM |

---

## 3. Ciclo local: build & test

```bash
cd services/api-handler        # ou outra function

mvn clean package              # compila + roda testes + empacota
mvn test                       # só os testes
```

**Testes** usam FnTestingRule (FDK) + Mockito, em `src/test/java/...`:

```java
@RunWith(FnTestingRule.class)
public class ApiHandlerTest {
    @Rule public final FnTestingRule fn = new FnTestingRule();
    // ...
}
```

Padrões de teste e mocking de serviços OCI: skill `testing-oci-functions-java`
(`/add-function-tests` → agent `@oci-functions-java`).

---

## 4. Build & push da imagem (OCIR)

Configure as credenciais do OCIR uma vez:

```bash
cp services/.env.example services/.env
# Edite services/.env:
#   OCIR_REGION=gru
#   OCIR_NAMESPACE=<seu-namespace>            # oci os ns get
#   OCIR_REPO=mon-fast-track-oci-serverless
#   OCIR_USERNAME=<namespace>/oracleidentitycloudservice/<email>
#   OCIR_PASSWORD=<auth-token>                # Console → Profile → Auth Tokens
```

> ⚠️ **Nunca** commite `services/.env` (já está no `.gitignore`).

Depois, cada function tem seu script (ele **roda o preflight automaticamente** antes do build):

```bash
cd services/api-handler
./build-push.sh            # tag default 0.0.1
./build-push.sh 0.0.2      # override de tag
```

O `build-push.sh` chama [`scripts/preflight.sh`](../../scripts/preflight.sh), que valida: `CMD` no
Dockerfile batendo com o `func.yaml`, provider HTTP do OCI SDK (`httpclient-jersey3`), ausência de
credenciais hardcoded e daemon Docker. Para rodar o preflight isolado:

```bash
./scripts/preflight.sh services/api-handler
```

> A imagem é **x86** por default (`PLATFORM=linux/amd64`, compatível com `GENERIC_X86`). Para ARM,
> veja a nota de `docker buildx` em [GETTING-STARTED §4](../../GETTING-STARTED.md#4-build-e-push-de-functions).

O **deploy** da imagem (atualizar tfvars + `terraform apply`) é a fronteira com a trilha de infra —
veja **[onboarding-devops-infra.md](onboarding-devops-infra.md)** ou o comando `/deploy-function`.

---

## 5. Criar uma nova Function

**Recomendado (Claude Code):**

```
@oci-functions-java /add-oci-function          # só o código Java (scaffold completo)
@oci-serverless-stack /add-serverless-stack     # end-to-end: Java + Terraform + rota
```

O scaffold já vem com os padrões obrigatórios (initError, CMD, httpclient-jersey, observabilidade,
budget de timeout) — skill `scaffolding-oci-function`.

**Manual (passo a passo):** [GETTING-STARTED §7](../../GETTING-STARTED.md#7-adicionar-nova-function--passo-a-passo-manual)
— crie `pom.xml`/`func.yaml`/`Dockerfile`/handler, build, e passe a bola para a infra registrar a rota.

---

## 6. Checklist do primeiro PR

- [ ] `mvn clean package` compila e **testes passam**
- [ ] `./scripts/preflight.sh services/<fn>` sem erros (CMD, httpclient, sem segredos)
- [ ] Sem credenciais/OCIDs hardcoded — segredos via Vault, config via `func.yaml`
- [ ] `services/.env` **não** commitado
- [ ] Imagem buildada e pushada no OCIR (`./build-push.sh <tag>`), se o deploy for parte do PR
- [ ] README da function atualizado (rotas, config keys) se mudou o contrato

Dúvidas de convenção/erro de runtime: `.claude/rules/java-functions-*.md`,
`@oci-debugger /debug-function` (502/503/504).

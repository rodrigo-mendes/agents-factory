# Onboarding — POC OCI Serverless

Bem-vindo(a). Este é o ponto de entrada para quem vai **começar a executar o projeto**. Ele cobre o que
é comum aos dois perfis e depois te encaminha para a **trilha** certa.

> Referência operacional completa (build, deploy, day-2): **[../../GETTING-STARTED.md](../../GETTING-STARTED.md)**.
> Visão de arquitetura e tecnologias: **[../../README.md](../../README.md)**.

---

## 1. Escolha sua trilha

| Perfil | O que você vai fazer | Guia |
|--------|----------------------|------|
| 👩‍💻 **Desenvolvedor(a) Java** | Escrever/testar Functions (FDK), build da imagem, abrir PR | **[onboarding-java-developer.md](onboarding-java-developer.md)** |
| 🛠️ **DevOps / Infra** | Provisionar Terraform, deploy, observabilidade, teardown | **[onboarding-devops-infra.md](onboarding-devops-infra.md)** |

As duas trilhas compartilham os pré-requisitos e a autenticação OCI abaixo — faça esta parte primeiro.

---

## 2. Arquitetura em 30 segundos

```
Internet → [API Gateway (subnet pública)] → [Functions (subnet privada)] → OCI Services
                                                                          ↓
                                                              [Vault, Object Storage]
```

Três Functions Java de referência, cada uma na sua **Application isolada**, com roteamento central no
API Gateway (`route_backends`):

| Function | Padrão | Rotas |
|----------|--------|-------|
| `services/api-handler` | Reference (health check) | `GET /hello` |
| `services/func-api-facade` | 03 — API Facade | `GET /hello`, `POST /secret`, `POST /store` |
| `services/func-rr-rest-proxy` | 01a — REST Proxy (RMS↔BrxServices) | `POST /store/create`, `POST /store/update` |

Detalhes: **[../../README.md](../../README.md)** e **[../patterns/README.md](../patterns/README.md)**.

---

## 3. Pré-requisitos comuns

Instale (macOS via Homebrew) e valide as versões **canônicas** do projeto:

| Ferramenta | Versão | Instalação | Usada por |
|------------|--------|------------|-----------|
| Git | recente | `brew install git` | ambos |
| Docker | 24+ | Docker Desktop | ambos (build da imagem) |
| OCI CLI | recente | `brew install oci-cli` | ambos (auth, OCIR) |
| JDK | **17** (Amazon Corretto) | `brew install --cask corretto17` | dev Java |
| Maven | 3.8+ | `brew install maven` | dev Java |
| Terraform | **1.11+** | `brew install terraform` | DevOps/infra |
| jq | recente | `brew install jq` | DevOps/infra (cleanup) |

```bash
docker info          # daemon rodando
oci --version        # qualquer versão recente
java -version        # 17 (Amazon Corretto)   ← dev Java
mvn -version         # >= 3.8                  ← dev Java
terraform version    # >= 1.11                 ← DevOps/infra
```

> ⚠️ **Java é 17**, não 21/25. O runtime das Functions usa imagens `fnproject/fn-java-fdk*:jdk17/jre17`
> e os `pom.xml` compilam com `source/target = 17` (FDK **1.1.11**, OCI SDK **3.86.0**).

Stack canônica (fonte única para evitar drift):

| Componente | Versão |
|---|---|
| Java | 17 (Amazon Corretto) |
| Fn FDK | 1.1.11 (fn-events) |
| OCI SDK (Java) | 3.86.0 |
| Terraform | >= 1.5 (testado 1.11) |
| Provider `oracle/oci` | >= 6.0, < 9.0 (testado 8.x) |

---

## 4. Autenticação OCI (compartilhada)

O projeto usa o profile **`poc`** com **SecurityToken (sessão)** — é o que o provider Terraform espera
(`auth = "SecurityToken"`, `config_file_profile = "poc"` em
[`infra/environments/dev/versions.tf`](../../infra/environments/dev/versions.tf)).

```bash
# Autentica no browser e grava o token de sessão
oci session authenticate --profile poc --region sa-saopaulo-1

# Valida
oci session validate --profile poc --auth security_token

# Renova quando expirar
oci session refresh --profile poc
```

> ⏱️ A sessão **expira em ~1h**. Em `terraform apply`/validações longas, um **401** normalmente significa
> sessão expirada — rode o `authenticate` de novo. Alternativa sem expiração (API Key): veja
> [GETTING-STARTED §2.2](../../GETTING-STARTED.md#22-alternativa--api-key-wizard).

**Contexto do ambiente** (o mesmo para as duas trilhas):

| Item | Valor |
|------|-------|
| Profile OCI CLI | `poc` |
| Região | `sa-saopaulo-1` (OCIR key `gru`) |
| Compartment | `mom-fast-track-poc-oci-serverless` |
| Repositório OCIR | `mon-fast-track-oci-serverless` |

---

## 5. Próximo passo

- **Dev Java** → **[onboarding-java-developer.md](onboarding-java-developer.md)**
- **DevOps/Infra** → **[onboarding-devops-infra.md](onboarding-devops-infra.md)**

Automação do projeto (agents/comandos Claude Code): **[../PROMPTS-GUIDE.md](../PROMPTS-GUIDE.md)** e o
`CLAUDE.md` na raiz.

> 📚 **Referência histórica** (não é onboarding): a migração de GitHub Copilot → Claude Code está
> documentada em `GUIA-MIGRACAO-COPILOT-CLAUDE.md` (raiz) e `docs/guias/copilot-sesiones-chat/`.

# O que NÃO compartilhar com o Claude Code

**Perfil:** Todos  
**Tempo estimado de leitura:** 5 min  
**Leitura obrigatória no onboarding**

---

## A regra básica

> **Tudo o que você escreve no prompt do Claude Code pode ser processado pelos servidores da Anthropic.**  
> Não envie nada que você não publicaria em um repositório público.

Embora o plano corporativo do Claude Code na BRX (Team/Enterprise ou Anthropic Console, com Zero Data Retention quando aplicável) tenha controles de privacidade reforçados — sob plano corporativo, os prompts **não são usados para treinar modelos** —, o princípio de minimização de dados vale sempre.

---

## O que nunca deve entrar no prompt

### Credenciais e segredos

❌ Nunca:
```
Tenho este erro ao conectar ao banco de dados:
password=S3cr3tP@ssw0rd123
host=prod-db.eci.internal
```

✅ Em vez disso:
```
Tenho este erro ao conectar ao banco de dados (omiti as credenciais):
[cole apenas o stack trace do erro, sem a configuração de conexão]
```

**Inclua nesta categoria:**
- Senhas e passphrases
- API keys e access tokens
- AWS Access Key ID / Secret Access Key
- Tokens JWT de produção
- Certificados e chaves privadas
- Strings de conexão a bancos de dados com credenciais
- Conteúdo de arquivos `.env` ou `application-prod.properties`

---

### Dados de clientes e usuários

❌ Nunca:
```
Tenho este JSON de um cliente que dá erro:
{"customerId": "12345", "email": "joao.silva@example.com", "cpf": "12345678901", "creditCard": "4111..."}
```

✅ Em vez disso:
```
Tenho um JSON de cliente com estes campos: customerId (string), email (string), cpf (string), creditCard (string).
O campo creditCard dá erro ao serializar. O que pode causar isso?
```

**Inclua nesta categoria:**
- Nomes, emails, telefones de clientes reais
- CPF/RG, dados fiscais
- Dados de cartões de crédito ou informação bancária
- Qualquer dado coberto pela LGPD/GDPR

---

### Código-fonte altamente sensível

Use o bom senso: código de negócio normal é aceitável compartilhar dentro do contexto do plano corporativo do Claude Code na BRX. Ainda assim, evite compartilhar:

- Algoritmos de pricing ou scoring proprietários que sejam segredo comercial
- Código de sistemas de segurança ou antifraude
- Implementações de cifragem proprietárias

Em caso de dúvida, consulte seu Tech Lead ou a Equipe de Governança BRX.

---

### Informação de infraestrutura de produção

❌ Nunca:
```
Nosso endpoint de produção é https://api.eci.es/internal/orders
e o serviço roda em 10.0.1.45:8080 dentro da VPC vpc-0abc123
```

✅ Em vez disso:
```
Tenho um serviço REST interno. Como configuro o cliente HTTP para retries com backoff exponencial?
```

---

## Como anonimizar antes de colar

Quando você precisa pedir ajuda com um erro ou código que contém informação sensível:

1. **Substitua segredos** por placeholders: `<API_KEY>`, `<DB_PASSWORD>`, `<TOKEN>`
2. **Anonimize dados de usuário**: `"email": "<EMAIL>"`, `"cpf": "<CPF>"`
3. **Generalize IPs e URLs**: `10.x.x.x`, `https://api.empresa.com`
4. **Cole só o trecho relevante**, não o arquivo inteiro

> Lembre-se: como o Claude Code edita arquivos nativamente e explora o projeto por conta própria, você raramente precisa colar conteúdo manualmente. Mesmo assim, tenha cuidado ao expor arquivos de configuração de produção (`.env`, `application-prod.properties`) ao contexto do agente — considere mantê-los fora da pasta de trabalho ou no `.gitignore`.

---

## Se você compartilhar algo sensível por acidente

1. **Encerre a conversa** imediatamente (use `/clear` para começar uma nova)
2. **Rotacione o segredo** comprometido (troque a senha, revogue o token)
3. **Notifique** a Equipe de Segurança da BRX seguindo o processo de incidentes

Sob plano corporativo, a Anthropic não armazena as conversas do Claude Code para treinamento, mas a rotação preventiva do segredo é sempre a ação correta.

---

## Próximos passos

- [5.2 — Responsabilidade humana: revisão obrigatória](02-responsabilidade-revisao-codigo.md)
- [5.3 — Propriedade intelectual e licenças](03-propriedade-intelectual-licencas.md)

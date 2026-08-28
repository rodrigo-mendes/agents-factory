# AWS WAF — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Security Architecture — Web Application Firewall (WAF)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture — Web Application Firewall"
Target_Edition: "AWS WAF 2024"
Architecture_Context: "Firewall para proteger API Gateway e CloudFront contra ataques web (SQL injection, XSS, DDoS L7, bots, account takeover)"
Official_Source_URL: "https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to WAF feature evolution, managed rule group updates, and pricing changes"
```

---

## Executive Summary

AWS WAF é o serviço gerenciado de Web Application Firewall da AWS que inspeciona requisições HTTP(S) encaminhadas para recursos protegidos — incluindo **Amazon CloudFront distributions**, **Amazon API Gateway REST APIs**, **Application Load Balancers**, **AWS AppSync GraphQL APIs**, **Amazon Cognito user pools**, **AWS App Runner services**, **AWS Verified Access instances** e **AWS Amplify**. O serviço opera no Layer 7 (aplicação), permitindo controle granular sobre tráfego com base em endereços IP, geolocalização, headers, query strings, body content, expressões regulares, rate limiting e detecção de padrões maliciosos (SQLi, XSS, LFI, RFI, SSRF). AWS WAF utiliza Web ACLs (protection packs) como unidade central de configuração, contendo regras e rule groups que são avaliadas sequencialmente com ações Allow, Block, Count, CAPTCHA ou Challenge.

A edição 2024–2025 trouxe mudanças significativas: **nova experiência de console com Protection Packs** que simplifica a configuração de web ACLs; **AI Traffic Analysis dashboard** para visibilidade de bots e agentes de IA; **Traffic insight recommendations** baseadas em AWS Threat Intelligence que analisa 2 semanas de tráfego permitido e recomenda regras; **AWS Managed Rules DDoS Prevention rule group** como nova opção dedicada para mitigação L7 DDoS; **ReactJS RCE protection** (CVE-2025-55182) adicionada ao Known Bad Inputs rule group; e **body inspection limit** aumentado para até 64 KB em CloudFront, API Gateway, Cognito, App Runner e Verified Access. O WAF agora inclui 500 MB de CloudWatch Logs (Standard e Infrequent Access) e Vended Logs Ingestion por 1 milhão de requests WAF sem custo adicional.

Os três guardrails mais críticos para proteger API Gateway e CloudFront são: (1) **associar um Web ACL com AWS Managed Rules (Core Rule Set + Known Bad Inputs) a toda distribuição CloudFront e API Gateway REST API exposta à internet** — sem WAF, essas superfícies ficam vulneráveis a OWASP Top 10; (2) **implementar rate-based rules com thresholds calibrados ao tráfego legítimo** — proteção fundamental contra DDoS L7, credential stuffing e API abuse; (3) **habilitar logging completo (CloudWatch Logs ou S3) com análise via Athena** — sem visibilidade, ataques passam despercebidos e tuning de regras é impossível.

---

## Cloud Architecture Glossary

```
Term: Web ACL (Web Access Control List)
Definition: Recurso central do AWS WAF que contém regras e rule groups definindo como inspecionar e responder a requisições HTTP(S). Cada Web ACL é associado a um ou mais recursos protegidos e avalia requisições sequencialmente conforme a prioridade das regras.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl.html
Architect Usage: Um Web ACL por recurso protegido. CloudFront usa scope CLOUDFRONT (criado em us-east-1). API Gateway, ALB e outros usam scope REGIONAL (criado na mesma região do recurso). Máximo padrão de 1.500 WCUs por Web ACL.
Common Confusion: Web ACL NÃO é o mesmo que Network ACL (NACL) do VPC. Web ACL opera em L7 (HTTP), NACL opera em L3/L4 (IP/porta). Um Web ACL pode ser compartilhado entre múltiplas distribuições CloudFront, mas cada recurso regional só pode ter um Web ACL associado.

Term: Protection Pack
Definition: Nova abstração de console (2024) que encapsula Web ACLs com configuração guiada. Durante o setup, AWS WAF recomenda conjuntos de regras baseados no tipo de aplicação. Protection Packs não alteram a funcionalidade subjacente do Web ACL — são uma interface simplificada.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl.html
Architect Usage: Usar Protection Packs para novas configurações via console. Para IaC (CloudFormation, Terraform), continuar usando a API WebACL diretamente. A nomenclatura "Protection Pack" e "Web ACL" são intercambiáveis na prática.
Common Confusion: Protection Pack NÃO é um produto separado nem tem custo adicional. É apenas a nova UX do console para criar e gerenciar Web ACLs.

Term: WCU (Web ACL Capacity Unit)
Definition: Unidade que mede os recursos computacionais necessários para executar regras. Cada tipo de regra consome WCUs diferentes. O limite padrão por Web ACL é 1.500 WCUs. Acima de 1.500 WCUs, cobra-se $0.20 adicional por milhão de requests a cada 500 WCUs excedentes.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/aws-waf-capacity-units.html
Architect Usage: Planejar a composição de rule groups dentro do budget de 1.500 WCUs. Core Rule Set consome 700 WCUs, Known Bad Inputs 200 WCUs, Admin Protection 100 WCUs — totalizando 1.000 WCUs apenas com baseline rules. Regras rate-based consomem 2 WCUs cada.
Common Confusion: WCU é custo computacional, não custo financeiro direto. Porém, exceder 1.500 WCUs gera cobrança adicional por request. Shield Advanced automatic mitigation consome 150 WCUs adicionais.

Term: Managed Rule Group
Definition: Coleção de regras pré-configuradas mantidas pela AWS (AWS Managed Rules) ou por vendedores do AWS Marketplace. São atualizadas automaticamente sem intervenção do cliente. Podem ser adicionadas ao Web ACL como unidades atômicas.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups.html
Architect Usage: Começar com AWS Managed Rules como baseline (sem custo adicional de subscription para os rule groups gratuitos). Avaliar rule groups pagos (Bot Control, ATP, ACFP) baseado no perfil de ameaça. Usar scope-down statements para reduzir custo de rule groups pagos.
Common Confusion: Regras dentro de managed rule groups NÃO podem ser editadas — apenas a action pode ser overridden (de Block para Count, por exemplo). Para customizar a lógica, criar regras próprias usando labels gerados pelos managed rule groups.

Term: Rate-Based Rule
Definition: Regra que rastreia a taxa de requisições de cada endereço IP (ou chave customizada) e bloqueia/conta quando o threshold é excedido dentro de uma janela de avaliação de 5 minutos (ou 1 minuto). O threshold mínimo é 100 requests.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html
Architect Usage: Primeira linha de defesa contra DDoS L7, brute force e API abuse. Definir threshold baseado no pico legítimo + margem. Usar aggregate keys (IP, IP + URI path, custom header) para rate limiting granular. Consome apenas 2 WCUs.
Common Confusion: Rate-based rules avaliam em janelas de 5 minutos por padrão (com opção de 1 minuto). O bloqueio persiste enquanto a taxa excede o threshold, e é removido automaticamente quando a taxa cai. NÃO é um rate limiter exato como token bucket — é baseado em amostragem.

Term: Label
Definition: Metadado que uma regra pode adicionar a uma requisição durante avaliação. Labels são usados por regras subsequentes no Web ACL para decisões compostas. AWS Managed Rules adicionam labels automaticamente a matches detectados.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/waf-labels.html
Architect Usage: Usar label matching para criar lógica complexa: managed rule group em Count mode → regra customizada que avalia labels para decisão final. Isso permite exceções granulares sem desabilitar regras do managed rule group inteiro.
Common Confusion: Labels NÃO persistem entre requests. Existem apenas durante a avaliação de uma única requisição dentro do Web ACL. Labels são visíveis nos logs e métricas CloudWatch.

Term: Scope (CLOUDFRONT vs REGIONAL)
Definition: AWS WAF opera em dois scopes: CLOUDFRONT (global, para distribuições CloudFront, criado obrigatoriamente em us-east-1) e REGIONAL (para API Gateway, ALB, AppSync, Cognito, App Runner, Verified Access — criado na mesma região do recurso).
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works.html
Architect Usage: Para CloudFront, criar Web ACL em us-east-1 com scope CLOUDFRONT. Para API Gateway REST API, criar na mesma região da API com scope REGIONAL. Um Web ACL CLOUDFRONT pode proteger múltiplas distribuições. Um Web ACL REGIONAL protege recursos na mesma região.
Common Confusion: API Gateway REST API usa scope REGIONAL (não CLOUDFRONT), mesmo quando fronted por CloudFront. Se usar CloudFront + API Gateway, aplique WAF no CloudFront (scope CLOUDFRONT) para inspeção na edge, ou no API Gateway (scope REGIONAL) para inspeção na origem — ou ambos para defesa em profundidade.

Term: CAPTCHA e Challenge Actions
Definition: Ações de regra que verificam se o cliente é um humano (CAPTCHA — puzzle visual) ou um navegador legítimo (Challenge — verificação silenciosa via JavaScript). Ambas usam tokens com immunity time configurável.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/waf-captcha-and-challenge.html
Architect Usage: CAPTCHA para formulários de login e signup. Challenge (silencioso) para APIs consumidas por browsers. NÃO usar em APIs consumidas por backends/mobile sem browser — tokens JavaScript não funcionam sem DOM.
Common Confusion: CAPTCHA e Challenge têm custo adicional ($0.40/mil CAPTCHA attempts, pricing separado para Challenge). Challenge NÃO funciona com clientes não-browser (mobile apps, backends). Para APIs machine-to-machine, usar autenticação (API keys, OAuth) em vez de CAPTCHA/Challenge.

Term: AWS WAF Bot Control
Definition: Managed rule group pago que detecta e gerencia tráfego de bots. Oferece dois níveis: Common (bots autoidentificados, scrapers básicos — $10/mês + $1/milhão requests) e Targeted (bots sofisticados que tentam evadir detecção — $10/mês + $10/milhão requests).
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-bot.html
Architect Usage: Ativar Bot Control Common como baseline para APIs públicas com tráfego significativo de bots. Targeted para sites de e-commerce, ticketing ou qualquer cenário com bots sofisticados. Usar scope-down statements para limitar a porcentagem de tráfego inspecionado e reduzir custo.
Common Confusion: Bot Control NÃO bloqueia todos os bots por padrão — categoriza e permite ação granular por categoria (verified bots como Googlebot são permitidos). Primeiro 10M de requests/mês incluídos no Common level.

Term: Fraud Control — ATP e ACFP
Definition: ATP (Account Takeover Prevention) protege endpoints de login contra credential stuffing e brute force. ACFP (Account Creation Fraud Prevention) protege endpoints de registro contra criação em massa de contas fraudulentas. Ambos são managed rule groups pagos com pricing baseado em volume.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-atp.html
Architect Usage: ATP para APIs de autenticação. ACFP para APIs de registro/signup. Ambos requerem configuração do endpoint (path) que será monitorado. Custo significativo em alto volume — avaliar ROI vs solução custom.
Common Confusion: ATP/ACFP NÃO substituem autenticação MFA ou rate limiting — complementam. O pricing é por request inspecionado (não por request total ao WAF), com tiers regressivos mas ainda caro em escala ($1.000/milhão nas primeiras 2M requests).

Term: IP Set
Definition: Recurso AWS WAF que contém uma lista de endereços IP ou CIDR ranges (IPv4 e/ou IPv6). Usado em regras de IP match para permitir ou bloquear tráfego baseado na origem. Limite de 10.000 endereços por IP Set.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/waf-ip-set-managing.html
Architect Usage: Usar IP Sets para allowlists (parceiros, VPNs corporativas), blocklists (IPs maliciosos conhecidos), e bypass de regras para tráfego confiável. Atualizar programaticamente via API para integração com feeds de threat intelligence.
Common Confusion: IP Sets são recursos independentes que podem ser referenciados por múltiplos Web ACLs. Atualizações propagam em segundos-minutos. O IP Set NÃO suporta FQDNs — apenas IPs e CIDRs.

Term: Regex Pattern Set
Definition: Recurso AWS WAF que contém um conjunto de expressões regulares usadas em regras de regex match. Cada pattern set pode conter até 10 regex patterns. Usado para detectar padrões customizados em headers, URI, query strings ou body.
Provider Docs Section: https://docs.aws.amazon.com/waf/latest/developerguide/waf-regex-pattern-set-managing.html
Architect Usage: Usar para detecção de padrões específicos da aplicação que managed rules não cobrem. Exemplos: formatos de API key expostos, padrões de abuso específicos, user-agents de ferramentas internas. Cada regex pattern consome 25 WCUs — usar com moderação.
Common Confusion: AWS WAF usa uma sintaxe regex limitada (não suporta backreferences, lookaheads/lookbehinds complexos). Testar patterns antes de deploy. Alto consumo de WCU comparado a string match rules (3 WCUs).
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Web ACL com AWS Managed Rules Baseline em Todo Recurso Internet-Facing**
- Pillar Alignment: Security (pilar Security do AWS Well-Architected Framework)
- Why: "The core rule set (CRS) rule group contains rules that are generally applicable to web applications. This provides protection against exploitation of a wide range of vulnerabilities, including some of the high risk and commonly occurring vulnerabilities described in OWASP publications such as OWASP Top 10." — AWS WAF Documentation
- AWS Services: AWS WAF, Amazon CloudFront, Amazon API Gateway
- Architecture Decision:
  Associar um Web ACL a toda distribuição CloudFront e API Gateway REST API exposta à internet. O Web ACL deve conter, no mínimo:
  1. **AWSManagedRulesCommonRuleSet** (CRS, 700 WCUs) — proteção contra XSS, LFI, RFI, SSRF, path traversal, bad bots
  2. **AWSManagedRulesKnownBadInputsRuleSet** (200 WCUs) — proteção contra Log4j RCE, Java deserialization, Spring RCE, ReactJS RCE
  3. **AWSManagedRulesAmazonIpReputationList** (25 WCUs) — bloqueio de IPs com reputação ruim na rede AWS
  4. Rate-based rule com threshold calibrado (2 WCUs)
  Total baseline: ~927 WCUs dentro do limite padrão de 1.500.
- Verification:
  - `aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1` — verificar existência de Web ACLs para CloudFront
  - `aws wafv2 list-web-acls --scope REGIONAL --region <region>` — verificar para API Gateway
  - `aws wafv2 get-web-acl --id <id> --scope <scope> --name <name>` — verificar regras incluídas
  - `aws apigateway get-stages --rest-api-id <id>` — verificar campo `webAclArn` no stage
  - AWS Config rule `api-gw-associated-with-waf` — compliance automática
- Trade-offs: Custo de $5/mês por Web ACL + $0.60/milhão de requests + $1/mês por rule group adicionado. Possibilidade de false positives que requerem tuning. Latência adicionada de ~1ms por request.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html

---

**Rate-Based Rule para Proteção contra DDoS L7 e API Abuse**
- Pillar Alignment: Security, Reliability
- Why: Rate-based rules são a primeira linha de defesa contra floods HTTP que visam indisponibilidade (DDoS L7), credential stuffing e abuso de API. Shield Advanced automatic mitigation depende de WAF rate-based rules como mecanismo de enforcement.
- AWS Services: AWS WAF, AWS Shield Advanced (opcional)
- Architecture Decision:
  Implementar pelo menos uma rate-based rule no Web ACL com:
  - **Aggregate key**: IP address (padrão) ou IP + forwarded IP (se atrás de proxy/CDN)
  - **Threshold**: Calibrar ao dobro do pico legítimo por IP em janela de 5 minutos (mínimo 100)
  - **Action**: Block (com custom response 429 Too Many Requests)
  - Para APIs com autenticação: considerar aggregate key por header de autenticação (API key, token) para rate limiting por tenant
  - Para CloudFront: usar forwarded IP configuration com header `X-Forwarded-For`
- Verification:
  - `aws wafv2 get-web-acl` — verificar presença de `RateBasedStatement` nas regras
  - CloudWatch metric `BlockedRequests` com dimensão Rule — monitorar ativações
  - Teste de carga controlado para validar threshold antes de produção
- Trade-offs: Threshold muito baixo bloqueia picos legítimos. Threshold muito alto não protege. Janela de 5 minutos significa que burst rápidos (<5min) podem passar. Rate-based rules NÃO são rate limiters exatos.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html

---

**Logging Completo do Web ACL Habilitado**
- Pillar Alignment: Security, Operational Excellence
- Why: Sem logging, não há visibilidade sobre ataques bloqueados, false positives ou tentativas de bypass. Logging é pré-requisito para tuning de regras, incident response e compliance audit.
- AWS Services: AWS WAF, Amazon CloudWatch Logs, Amazon S3, Amazon Data Firehose, Amazon Athena
- Architecture Decision:
  Habilitar logging para todo Web ACL em produção. Destino recomendado:
  - **S3** para retenção de longo prazo e análise com Athena (menor custo por GB)
  - **CloudWatch Logs** para alertas em near-real-time e dashboards
  - **Data Firehose** para streaming para SIEM ou data lake
  Configurar:
  - Log filter: no mínimo logar requests bloqueadas e contadas (filtrar Allow para reduzir volume)
  - Redaction: redact campos sensíveis (Authorization header, cookies de sessão)
  - Retenção: mínimo 90 dias para compliance, 30 dias para operacional
  - Athena table com partition projection para queries eficientes
- Verification:
  - `aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>` — verificar configuração
  - Verificar que logs estão chegando no destino (S3 objects, CloudWatch log events)
  - Athena query de teste: `SELECT COUNT(*) FROM waf_logs WHERE action = 'BLOCK'`
- Trade-offs: Custo de storage (incluso 500MB por 1M requests WAF, excedente cobrado por GB). Volume alto em APIs de alto tráfego. Requer pipeline de análise para ser útil.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/logging.html

---

**Deploy em Count Mode Antes de Block**
- Pillar Alignment: Operational Excellence, Reliability
- Why: "Before you deploy changes in your protection pack (web ACL) for production traffic, test and tune them in a staging or testing environment until you are comfortable with the potential impact to your traffic. Then test and tune your updated rules in count mode with your production traffic before enabling them." — AWS WAF Documentation
- AWS Services: AWS WAF, Amazon CloudWatch
- Architecture Decision:
  Toda nova regra ou managed rule group deve ser deployada primeiro em **Count mode** por no mínimo 7 dias em produção antes de ativar Block. Workflow:
  1. Deploy regra em Count
  2. Monitorar CloudWatch metrics (`CountedRequests` por regra) e logs
  3. Analisar sampled requests para identificar false positives
  4. Ajustar ou adicionar exceções (label-based ou scope-down)
  5. Ativar Block após validação
  Para managed rule groups: override individual rules para Count, não o group inteiro.
- Verification:
  - `aws wafv2 get-web-acl` — verificar OverrideAction e RuleActionOverrides
  - CloudWatch metric `CountedRequests` — confirmar que regras estão matching
  - Sampled requests no console — revisar matches para false positives
- Trade-offs: Período de Count mode significa que ataques detectados não são bloqueados. Mitigation: manter regras já validadas em Block enquanto novas regras ficam em Count.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html

---

**Web ACL Default Action: Block para APIs Restritas, Allow para APIs Públicas**
- Pillar Alignment: Security
- Why: A default action determina o que acontece com requests que não matcham nenhuma regra. Para APIs que devem aceitar tráfego público (websites, APIs abertas), o default deve ser Allow com regras de Block para tráfego malicioso. Para APIs restritas (internas, B2B), considerar default Block com regras Allow para IPs/padrões autorizados.
- AWS Services: AWS WAF
- Architecture Decision:
  - **APIs públicas (CloudFront serving website, API Gateway público)**: Default action `Allow`. Regras bloqueiam tráfego malicioso (managed rules + rate limiting).
  - **APIs restritas (parceiros, internal)**: Avaliar default action `Block` com IP Set allowlist. Requer regra Allow para IPs autorizados antes da avaliação de demais regras.
  - Em ambos os casos: rate-based rules e managed rules sempre presentes.
- Verification:
  - `aws wafv2 get-web-acl` — verificar `DefaultAction` (Allow ou Block)
  - Testar acesso com IP não-listado quando default é Block
- Trade-offs: Default Block em APIs públicas bloqueia todo tráfego novo e requer manutenção de allowlists. Default Allow requer que todas as ameaças sejam cobertas por regras explícitas.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-default-action.html

---

### ⚠️ Architectural Decisions

**Managed Rules vs Custom Rules vs Marketplace Rules**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | AWS Managed Rules (grátis) | AWSManagedRulesCommonRuleSet, KnownBadInputs, IPReputation | Custo, time-to-value, manutenção zero | Customização granular, sem controle sobre updates | Início rápido, cobertura OWASP Top 10 baseline |
  | AWS Managed Rules (pagos) | Bot Control, ATP, ACFP, Anti-DDoS | Detecção avançada de bots/fraude, ML-based | Custo elevado em escala, WCUs adicionais | Sites com problema real de bots/fraude que justifica custo |
  | Custom Rules | Rate-based, IP match, geo match, regex, string match | Controle total, sem custo de subscription | Manutenção, expertise necessária, sem auto-update | Requisitos específicos da aplicação não cobertos por managed rules |
  | Marketplace Rules | Vendedores terceiros (Fortinet, F5, Imperva) | Cobertura de nicho, expertise de vendor | Custo adicional (subscription + request), dependência de terceiro | Requisitos regulatórios ou de nicho específicos |

- Cost Profile: AWS Managed Rules gratuitos: $0 subscription. Bot Control Common: $10/mês + $1/M requests (10M grátis). Bot Control Targeted: $10/mês + $10/M requests. ATP/ACFP: $10/mês + $50-$1.000/M requests (tiers regressivos). Custom rules: $1/mês por regra.
- Lock-in Assessment: Regras customizadas são portáveis conceitualmente mas não em formato. Managed rules são AWS-specific. Marketplace rules variam por vendor.
- Architect Instruction: "Avaliar se o perfil de ameaça justifica o custo de Bot Control/ATP antes de habilitar — para APIs com baixo tráfego de bots, baseline managed rules + rate limiting são suficientes."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html

---

**WAF no CloudFront vs WAF no API Gateway vs Ambos (Defesa em Profundidade)**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | WAF apenas no CloudFront | WAF scope CLOUDFRONT | Inspeção na edge (menor latência), proteção antes da origem, um único ponto de enforcement | Sem proteção se API Gateway é acessado diretamente (bypass CloudFront) | CloudFront é o único ponto de entrada, origin access está restrito |
  | WAF apenas no API Gateway | WAF scope REGIONAL | Proteção independente de CDN, funciona sem CloudFront | Requisições maliciosas chegam até a região, maior latência de bloqueio | API Gateway exposto diretamente sem CloudFront |
  | WAF em ambos (defesa em profundidade) | WAF CLOUDFRONT + WAF REGIONAL | Proteção em camadas, cobre bypass de CloudFront, regras diferentes por camada | Custo dobrado (2 Web ACLs, requests cobrados em ambos), complexidade de gestão | Requisitos de compliance rigorosos, APIs acessíveis por múltiplos caminhos |

- Cost Profile: WAF CloudFront: $5/mês + $0.60/M. WAF API Gateway: $5/mês + $0.60/M. Ambos: $10/mês + $1.20/M requests (dobro).
- Lock-in Assessment: Ambas abordagens são AWS-native. Migrar para CDN/Gateway de outro provider requer reimplementar regras.
- Architect Instruction: "Se CloudFront é o único ponto de entrada E o origin está protegido (origin access control, security group restrito), WAF no CloudFront é suficiente. Se API Gateway pode ser acessado diretamente OU compliance exige defesa em profundidade, adicionar WAF também no API Gateway."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html

---

**Estratégia de Logging: S3 vs CloudWatch Logs vs Data Firehose**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Amazon S3 | S3 + Athena | Custo de storage, retenção longa, análise ad-hoc com SQL | Latência (minutos), sem alertas nativos em real-time | Retenção de compliance (>90 dias), análise forense, alto volume |
  | CloudWatch Logs | CloudWatch Logs + Insights | Alertas real-time, integração com CloudWatch Alarms, Metric Filters | Custo mais alto por GB em volume, retenção cara em longo prazo | Alertas imediatos, dashboards operacionais, volume moderado |
  | Data Firehose | Kinesis Data Firehose → S3/Splunk/SIEM | Streaming near-real-time para SIEM, transformação em trânsito | Complexidade adicional, custo de Firehose + destino | Integração com SIEM existente (Splunk, Datadog), pipeline de dados |

- Cost Profile: S3: ~$0.023/GB storage + Athena $5/TB scanned. CloudWatch Logs: ~$0.50/GB ingestion + $0.03/GB storage. Firehose: $0.029/GB ingested.
- Lock-in Assessment: Logs em S3 são portáveis (JSON). CloudWatch Logs requer migração. Firehose pode entregar para destinos externos.
- Architect Instruction: "Para a maioria dos casos, S3 com Athena é suficiente e mais econômico. Adicionar CloudWatch Logs com filtro (apenas blocks) para alertas imediatos. Firehose quando há SIEM centralizado."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/logging-destinations.html

---

**Rate Limiting: Rate-Based Rule vs Bot Control vs API Gateway Throttling**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | WAF Rate-Based Rule | AWS WAF | Custo (2 WCUs, sem subscription), aggregate keys flexíveis | Granularidade (janela 5min ou 1min), não é token bucket preciso | Proteção básica contra DDoS L7 e brute force por IP |
  | WAF Bot Control | AWS WAF Bot Control | Detecção por comportamento (não só rate), categorização de bots | Custo elevado ($1-10/M requests), consome WCUs | Tráfego significativo de bots que rate limiting por IP não resolve |
  | API Gateway Throttling | API Gateway (Usage Plans, Stage throttling) | Rate limiting preciso (token bucket), por API key/stage/method | Não bloqueia na edge (request chega ao gateway), sem inspeção de conteúdo | Rate limiting por tenant/API key, proteção de backend contra overload |

- Cost Profile: Rate-based rule: incluído no custo base WAF. Bot Control: $10/mês + $1-10/M. API Gateway throttling: incluído no API Gateway.
- Lock-in Assessment: Rate-based rules e Bot Control são AWS WAF-specific. API Gateway throttling é API Gateway-specific.
- Architect Instruction: "Usar rate-based rule como primeira camada (bloqueia na edge/WAF). API Gateway throttling como segunda camada (protege backend). Bot Control quando rate limiting por IP é insuficiente contra bots distribuídos."
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html

---

### 🚫 Anti-Patterns

**Web ACL sem Managed Rules Baseline**
- Risk Level: CRITICAL
- Why: Violação do pilar Security — superfície de ataque exposta sem proteção contra OWASP Top 10 (SQLi, XSS, LFI, RFI, SSRF, Log4j RCE). AWS WAF sem regras é apenas um passthrough com custo.
- Instead: Adicionar, no mínimo, AWSManagedRulesCommonRuleSet (700 WCUs) + AWSManagedRulesKnownBadInputsRuleSet (200 WCUs) + AWSManagedRulesAmazonIpReputationList (25 WCUs) a todo Web ACL.
- Detection:
  - `aws wafv2 get-web-acl` — verificar se `Rules` contém managed rule groups AWS
  - AWS Config custom rule ou Security Hub check
  - Firewall Manager policy para enforce compliance
- Impact: Data breach (SQLi → database exfiltration), defacement (XSS), remote code execution (Log4j, Spring RCE), compliance violation
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html

---

**Regras em Block Mode sem Período de Count**
- Risk Level: HIGH
- Why: Violação do pilar Operational Excellence — regras não testadas em produção causam false positives que bloqueiam tráfego legítimo. Impacto direto em disponibilidade.
- Instead: Deployar toda regra nova em Count mode por 7+ dias. Analisar sampled requests e logs. Validar que only malicious traffic matches antes de ativar Block.
- Detection:
  - Verificar change logs de Web ACL — regras que foram adicionadas direto em Block
  - Monitorar spikes em `BlockedRequests` metric após mudanças
- Impact: Service outage (tráfego legítimo bloqueado), degradação de experiência do usuário, perda de receita
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html

---

**API Gateway ou CloudFront Exposto sem WAF**
- Risk Level: CRITICAL
- Why: Violação dos pilares Security e Reliability — recursos internet-facing sem camada de proteção L7 ficam vulneráveis a todo tipo de ataque web e DDoS L7.
- Instead: Associar Web ACL a todo recurso internet-facing. Usar AWS Firewall Manager para enforcement automático em novos recursos.
- Detection:
  - `aws apigateway get-stages` — verificar campo `webAclArn` vazio
  - `aws cloudfront get-distribution` — verificar `WebACLId` vazio
  - AWS Config rule: `api-gw-associated-with-waf`
  - Firewall Manager compliance dashboard
- Impact: Data breach, service outage, DDoS L7, compliance violation (PCI-DSS 6.6 requer WAF ou code review)
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html

---

**Rate-Based Rule com Threshold Excessivamente Baixo ou Alto**
- Risk Level: HIGH
- Why: Threshold baixo demais bloqueia picos legítimos (flash sales, viral content). Threshold alto demais não protege contra ataques. Ambos comprometem a eficácia do controle.
- Instead: Analisar tráfego legítimo (P99 de requests por IP em 5 minutos). Definir threshold como 2-3x o P99. Monitorar e ajustar trimestralmente. Alertar em rate-limit activations.
- Detection:
  - `aws wafv2 get-web-acl` — verificar `Limit` em rate-based rules
  - Comparar threshold com métricas reais de tráfego por IP
  - Monitorar ratio BlockedRequests/AllowedRequests após ativação
- Impact: Threshold baixo: service degradation para usuários legítimos. Threshold alto: proteção ineficaz contra DDoS L7 e brute force.
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based.html

---

**Logging Desabilitado no Web ACL**
- Risk Level: HIGH
- Why: Violação dos pilares Security e Operational Excellence — sem logging, não há visibilidade sobre ataques, não é possível tuning de regras, não há evidência para incident response ou audit trail para compliance.
- Instead: Habilitar logging para todo Web ACL em produção. Destino mínimo: S3 com retenção de 90 dias. Adicionar CloudWatch Logs com filtro para blocks quando alertas são necessários.
- Detection:
  - `aws wafv2 list-logging-configurations` — verificar se todos Web ACLs têm logging configurado
  - `aws wafv2 get-logging-configuration --resource-arn <web-acl-arn>` — verificar destino
- Impact: Invisible attacks, inability to tune rules, compliance violation (audit trail missing), delayed incident response
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/logging.html

---

**Wildcard Allow Rules que Bypassam Managed Rules**
- Risk Level: HIGH
- Why: Regras Allow com prioridade alta (número baixo) que matcham tráfego amplo efetivamente desabilitam todas as managed rules subsequentes para esse tráfego, criando blind spots de segurança.
- Instead: Allow rules devem ser específicas (IP Set de parceiros, paths internos de health check). Nunca usar Allow rule abrangente antes de managed rules. Se preciso exceções, usar label-based matching após managed rules em Count mode.
- Detection:
  - `aws wafv2 get-web-acl` — verificar regras Allow com Priority baixa e critérios amplos
  - Analisar proporção AllowedRequests por rule vs managed rule CountedRequests
- Impact: Security bypass — ataques que seriam bloqueados por managed rules passam pela regra Allow prematura
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-processing.html

---

**Usar WAF Classic em vez de AWS WAF (v2)**
- Risk Level: MEDIUM
- Why: AWS WAF Classic está em end-of-life com funcionalidades limitadas — sem suporte a managed rule groups, labels, CAPTCHA/Challenge, rate-based rule improvements, body inspection configurável, ou as novas dashboards. Novas features são exclusivas da v2.
- Instead: Migrar para AWS WAF (v2) usando o migration wizard. Todos os novos deployments devem usar WAF v2 exclusivamente.
- Detection:
  - `aws waf list-web-acls` (API WAF Classic) — se retornar resultados, há recursos legacy
  - Console: banner de deprecação na interface WAF Classic
- Impact: Funcionalidades degradadas, sem proteções modernas, eventual descontinuação do serviço
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-migrating-from-classic.html

---

## Cloud-Native Design Patterns

**Pattern: Layered WAF Protection (Edge + Origin)**
- Category: Security
- Problem: Uma única camada de WAF pode ser bypassed se o atacante encontrar acesso direto à origem (API Gateway sem CloudFront). Defesa em profundidade requer múltiplas camadas.
- Solution on AWS:
  1. **CloudFront WAF** (scope CLOUDFRONT): Inspeção na edge com foco em volumetric attacks, geo blocking, IP reputation, rate limiting agressivo
  2. **API Gateway WAF** (scope REGIONAL): Inspeção na origem com foco em application-specific rules, tighter rate limits, business logic protection
  3. **Origin protection**: Origin Access Control (CloudFront → S3), security group restringindo API Gateway/ALB apenas a CloudFront IP ranges
- Services Used: AWS WAF (2 Web ACLs), Amazon CloudFront, Amazon API Gateway, AWS Firewall Manager
- When to Apply: APIs públicas com requisitos de compliance (PCI-DSS, SOC2), aplicações multi-tenant, APIs com dados sensíveis
- When NOT to Apply: APIs internas sem acesso público, aplicações de baixo risco onde custo dobrado de WAF não se justifica
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Defesa em profundidade, sem single point of failure | Complexidade de gestão de 2 Web ACLs |
  | Cost | — | 2x custo base de WAF ($10/mês + $1.20/M requests) |
  | Operations | Regras podem ser especializadas por camada | Mais configuração para manter sincronizado |

- Complements: Shield Advanced, Origin Access Control, VPC Security Groups
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works-resources.html

---

**Pattern: Label-Based Composite Rules**
- Category: Security
- Problem: Managed rule groups são "tudo ou nada" — desabilitar uma regra com false positives significa perder a proteção inteira, ou aceitar os false positives.
- Solution on AWS:
  1. Adicionar managed rule group em **Count mode** (override action)
  2. Managed rules geram **labels** em matches (ex: `awswaf:managed:aws:core-rule-set:CrossSiteScripting_Body`)
  3. Criar regra customizada que usa **label match statement** + condições adicionais para decisão final
  4. Exemplo: Block XSS labels EXCETO quando URI path é `/api/content` (editor WYSIWYG que gera falsos XSS)
- Services Used: AWS WAF (labels, label match rules, managed rule group override)
- When to Apply: Aplicações com false positives em managed rules que precisam de exceções granulares sem desabilitar proteção inteira
- When NOT to Apply: Quando managed rules funcionam bem em Block mode sem false positives
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Precision | Exceções cirúrgicas sem blind spots | Complexidade de regras, mais WCUs consumidos |
  | Maintenance | Managed rules continuam atualizando automaticamente | Regras compostas precisam ser revisadas quando labels mudam |

- Complements: WAF logging com análise de labels, CloudWatch metrics por label
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-labels.html

---

**Pattern: Geo-Fencing com Rate Limiting Diferenciado**
- Category: Security, Scalability
- Problem: APIs globais recebem tráfego legítimo de regiões específicas mas ataques de qualquer lugar. Rate limiting uniforme penaliza regiões legítimas.
- Solution on AWS:
  1. Regra geo match que **Block** países onde não há negócio (sem usuarios legítimos esperados)
  2. Rate-based rules diferenciadas por geo:
     - Países core: threshold alto (2.000-10.000 req/5min por IP)
     - Países secundários: threshold moderado (500-2.000 req/5min por IP)
     - Restante: threshold baixo (100-500 req/5min por IP)
  3. IP Set allowlist para parceiros e serviços de monitoramento (bypass rate limiting)
- Services Used: AWS WAF (geo match, rate-based rules, IP sets), Amazon CloudFront (geo restriction como backup)
- When to Apply: APIs com base de usuários geograficamente concentrada, cenários com ataques originando predominantemente de regiões sem usuários
- When NOT to Apply: APIs genuinamente globais com distribuição uniforme de usuários (VPN/proxy usage pode mascarar geoIP real)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Reduz superfície de ataque eliminando tráfego de regiões não-relevantes | Pode bloquear VPN users e nômades digitais |
  | Cost | Menos requests processados por managed rules | Complexidade de manutenção de regras geo |

- Complements: CloudFront geographic restrictions, IP reputation lists
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-geo-match.html

---

**Pattern: WAF Automation via Firewall Manager**
- Category: Scalability, Operational Excellence
- Problem: Em organizações multi-account, garantir que todo recurso internet-facing tem WAF associado é desafiador — novos recursos são criados sem proteção, configurações divergem entre contas.
- Solution on AWS:
  1. **AWS Firewall Manager** policy de WAF que define Web ACL padrão
  2. Policy aplica automaticamente a todo recurso novo (CloudFront, API Gateway, ALB) em contas da Organization
  3. Web ACL gerenciado centralmente com managed rules baseline
  4. Contas individuais podem adicionar regras customizadas ao Web ACL (além das regras centrais)
  5. Compliance dashboard identifica recursos sem proteção
- Services Used: AWS Firewall Manager, AWS WAF, AWS Organizations
- When to Apply: Organizações com múltiplas contas AWS, times que criam recursos internet-facing sem governance, requisitos de compliance centralizados
- When NOT to Apply: Conta única com poucos recursos, times pequenos com controle direto sobre todos os recursos
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Governance | Compliance automática, zero-touch para novos recursos | Firewall Manager fee ($100/policy/região/mês) |
  | Flexibility | Baseline garantido em toda org | Times locais podem não ter controle total sobre regras |

- Complements: AWS Organizations SCPs, AWS Config rules, Security Hub
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/fms-chapter.html

---

## Security Architecture

**Identity & Access Management para WAF**
- AWS Services: AWS IAM, AWS WAF, AWS Firewall Manager, AWS Organizations
- Architecture:
  - **Permissões WAF**: Separar roles para `wafv2:Create*` / `wafv2:Update*` (admin) vs `wafv2:Get*` / `wafv2:List*` (read-only/audit)
  - **Resource-level permissions**: Restringir acesso a Web ACLs específicos por tag ou ARN
  - **Firewall Manager administrator**: Conta dedicada de security para gestão centralizada de policies
  - **SCP guardrail**: Negar `wafv2:DeleteWebACL` e `wafv2:DisassociateWebACL` em production OUs para prevenir remoção acidental/maliciosa
  - **Condition keys**: `aws:RequestTag`, `aws:ResourceTag` para controle baseado em tags
- Configuration Essentials:
  - IAM policy para security team: Full `wafv2:*` + `logs:*` para logging configuration
  - IAM policy para dev teams: `wafv2:Get*`, `wafv2:List*` + acesso restrito para associar Web ACLs a seus recursos
  - SCP deny: `wafv2:DeleteWebACL`, `wafv2:DisassociateWebACL` em production OUs
- Verification:
  - `aws iam simulate-principal-policy --policy-source-arn <role-arn> --action-names wafv2:DeleteWebACL`
  - AWS Access Analyzer para detectar policies excessivamente permissivas
- Compliance Alignment: SOC2 CC6.1, CC6.6 (Access Controls), PCI-DSS Requirement 6.6 (WAF requirement)
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-auth-and-access-control.html

---

**Proteção contra OWASP Top 10**
- AWS Services: AWS WAF (Managed Rules), Amazon CloudFront, Amazon API Gateway
- Architecture:
  Mapeamento de AWS Managed Rules para OWASP Top 10 2021:

  | OWASP Top 10 | AWS Managed Rule Group | Regras Relevantes |
  |--------------|----------------------|-------------------|
  | A01 Broken Access Control | Admin Protection | AdminProtection_URIPATH |
  | A02 Cryptographic Failures | — (infra-level, não WAF) | — |
  | A03 Injection (SQLi, XSS) | Core Rule Set, SQL Database | CrossSiteScripting_*, SQLi rules |
  | A04 Insecure Design | — (não mitigável via WAF) | — |
  | A05 Security Misconfiguration | Known Bad Inputs | ExploitablePaths, Host_localhost |
  | A06 Vulnerable Components | Known Bad Inputs | Log4JRCE_*, JavaDeserializationRCE_*, ReactJSRCE_* |
  | A07 Auth Failures | ATP (pago) | Credential stuffing detection |
  | A08 Data Integrity Failures | Known Bad Inputs | Serialization attacks |
  | A09 Logging & Monitoring | WAF Logging | — (habilitar logging) |
  | A10 SSRF | Core Rule Set | EC2MetaDataSSRF_* |

- Compliance Alignment: PCI-DSS 6.6, SOC2 CC6.6, OWASP ASVS Level 1
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-baseline.html

---

**Integração com Shield Advanced para DDoS L7**
- AWS Services: AWS WAF, AWS Shield Advanced, Amazon CloudFront, ALB
- Architecture:
  1. **Shield Advanced subscription** ativa para recursos protegidos
  2. **Web ACL associado** a recursos Shield Advanced-protected (CloudFront, ALB)
  3. **Automatic application layer DDoS mitigation** habilitado (consome 150 WCUs)
  4. Shield Advanced gerencia **ShieldMitigationRuleGroup** dentro do Web ACL
  5. Shield detecta anomalias de tráfego e deploya regras WAF automaticamente
  6. **Rate-based rules** como primeira linha — Shield refina com targeted blocks
  7. Shield Advanced **inclui custos WAF** para recursos protegidos (até 1.500 WCUs, 50B requests/mês)
- Configuration Essentials:
  - Shield Advanced protection em CloudFront e ALB
  - Web ACL com 150 WCUs livres para Shield-managed rule group
  - Automatic mitigation em Block mode (após validação em Count)
  - Route 53 health checks associados para proactive engagement
- Verification:
  - `aws shield describe-protection` — verificar ApplicationLayerAutomaticResponseConfiguration
  - `aws wafv2 get-web-acl` — verificar ShieldMitigationRuleGroup presente
  - CloudWatch metric `DDoSDetected` — monitorar detecções
- Compliance Alignment: Requisitos de disponibilidade (SLAs), PCI-DSS 6.6
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/ddos-automatic-app-layer-response.html

---

## Operational Patterns

**Observabilidade do WAF**
- Operational Domain: Observability
- AWS Services: AWS WAF, Amazon CloudWatch, Amazon S3, Amazon Athena, Amazon CloudWatch Logs Insights
- Architecture:
  - **Métricas CloudWatch** (automáticas, sem configuração):
    - `AllowedRequests` — por WebACL e por Rule
    - `BlockedRequests` — por WebACL e por Rule
    - `CountedRequests` — por WebACL e por Rule
    - `CaptchaRequests`, `ChallengeRequests` — por WebACL
    - Granularidade: 1 minuto
  - **Logging completo** (requer configuração):
    - Destino: S3 (análise com Athena), CloudWatch Logs (Insights), Data Firehose (SIEM)
    - Campos: timestamp, action, terminatingRuleId, ruleGroupList, labels, httpRequest (headers, URI, country, IP)
    - Filtro de log: logar apenas Block + Count para reduzir volume (Allow gera ~80% do volume)
  - **Dashboards**:
    - CloudWatch dashboard com métricas WAF: BlockedRequests por rule (identificar top ameaças)
    - Athena queries programadas para relatórios semanais de ataque
    - AI Traffic Analysis dashboard (novo console) para visibilidade de bots
  - **Alertas**:
    - Alarm em spike de `BlockedRequests` (>3 desvios padrão do baseline)
    - Alarm em rate-based rule activations (indica ataque ativo)
    - Alarm em queda abrupta de `AllowedRequests` (pode indicar false positive bloqueando tráfego)
- Cost Profile: CloudWatch métricas WAF: incluídas. Logs S3: ~$0.023/GB. Athena: $5/TB scanned. CloudWatch Logs: ~$0.50/GB ingestion.
- Automation:
  - Automatizar: Athena queries agendadas (EventBridge + Lambda), alertas CloudWatch, dashboards
  - Manual: Análise de novos padrões de ataque, decisão de tuning de rules, investigação de false positives
- Runbook Skeleton:
  1. **Detecção**: Alert de spike em BlockedRequests ou rate-limit activation
  2. **Triage**: Consultar logs WAF (Athena/Insights) — identificar source IPs, URIs, rule ativada
  3. **Classificação**: Ataque real ou false positive? Verificar se tráfego legítimo está impactado
  4. **Resposta**: Se ataque: adicionar IP Set block / reduzir rate-limit threshold. Se false positive: mover regra para Count, adicionar exceção
  5. **Post-mortem**: Documentar pattern, atualizar rules, verificar cobertura
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/monitoring-cloudwatch.html

---

**Tuning Contínuo de Regras**
- Operational Domain: Change Management
- AWS Services: AWS WAF, CloudWatch, S3, Athena
- Architecture:
  Processo cíclico de refinamento de regras WAF:
  1. **Baseline** (Semana 1-2): Deploy managed rules em Count, coletar logs
  2. **Análise** (Semana 2-3): Athena queries identificando top matches, false positive rate
  3. **Ativação** (Semana 3-4): Mover regras validadas para Block, manter suspeitas em Count
  4. **Monitoramento contínuo**: Dashboard semanal de block rate, top rules, top source IPs
  5. **Revisão trimestral**: Reavaliação de thresholds, adição de novos rule groups, remoção de regras não-matching
- Cost Profile: Low — custo apenas de análise (Athena queries, tempo de engenharia)
- Automation:
  - Automatizar: Reports semanais via Athena, alert de novas regras com alto Count rate
  - Manual: Decisão de promover Count → Block, análise de false positives, tuning de thresholds
- Runbook Skeleton:
  1. Executar query Athena de top 10 regras por CountedRequests na última semana
  2. Para cada regra em Count com >100 matches/semana: amostrar 20 requests bloqueados
  3. Classificar: true positive (promover para Block) ou false positive (adicionar exceção)
  4. Documentar decisão e implementar mudança
  5. Monitorar por 48h após mudança para confirmar ausência de impacto negativo
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/web-acl-testing.html

---

**Incident Response para Ataque Web**
- Operational Domain: Incident Management
- AWS Services: AWS WAF, CloudWatch, Shield Advanced (SRT), S3, Athena
- Architecture:
  Playbook para resposta a ataque web detectado via WAF:
  - **P1 — DDoS L7 (alta volumetria)**:
    1. Verificar Shield Advanced automatic mitigation (se ativo)
    2. Reduzir rate-based rule threshold temporariamente
    3. Adicionar IP Set com top offending IPs (Block)
    4. Ativar geo block para países-fonte se não há users legítimos
    5. Contatar SRT (se Shield Advanced) para mitigação customizada
  - **P2 — Exploração ativa (SQLi, RCE tentativas concentradas)**:
    1. Confirmar que managed rules estão bloqueando (não apenas counting)
    2. Analisar padrão: se bypass tentado, adicionar custom rule específica
    3. Bloquear IPs fonte via IP Set
    4. Verificar se ataque teve sucesso (logs de aplicação, não apenas WAF)
  - **P3 — Credential stuffing/Account takeover**:
    1. Avaliar ativação de ATP (se não ativo)
    2. Rate-based rule no path de login
    3. CAPTCHA temporário no login
    4. Coordenar com time de aplicação para forced password reset em contas comprometidas
- Cost Profile: Low (operacional) a Medium (se necessitar Shield Advanced SRT engagement)
- Automation:
  - Automatizar: IP Set update via Lambda (auto-block top offenders), alertas, escalação
  - Manual: Decisão de geo block, threshold adjustment, SRT engagement, post-mortem
- Runbook Skeleton:
  1. **Alert received**: Spike em BlockedRequests ou rate-limit activation
  2. **Assess scope**: Quantas IPs? Qual a volumetria? Qual o target (path/endpoint)?
  3. **Immediate mitigation**: IP block, rate reduction, geo restriction (conforme severity)
  4. **Monitor effectiveness**: Verificar que BlockedRequests estabiliza e AllowedRequests normaliza
  5. **Communicate**: Notificar stakeholders se houve impacto em disponibilidade
  6. **Post-mortem**: Root cause, timeline, ações preventivas
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/waf-incident-response.html

---

## Reference Architectures

**API Gateway + CloudFront + WAF (API Pública Protegida)**
- Context: API REST pública servida via API Gateway com CloudFront como CDN/edge, protegida contra OWASP Top 10, DDoS L7 e bot abuse
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge/CDN | Amazon CloudFront | Distribuição global, caching, SSL termination, DDoS L3/L4 (Shield Standard) |
  | WAF (Edge) | AWS WAF (scope CLOUDFRONT) | Proteção L7: managed rules, rate limiting, geo blocking, bot control |
  | API Gateway | Amazon API Gateway REST API | Roteamento, throttling, autenticação (Cognito/Lambda authorizer), integração |
  | WAF (Origin) — opcional | AWS WAF (scope REGIONAL) | Defesa em profundidade, regras específicas do backend |
  | Compute | AWS Lambda / ECS | Business logic |
  | Data | DynamoDB / RDS | Persistência |
  | Monitoring | CloudWatch + S3 + Athena | Métricas WAF, logging, análise |
  | Governance | AWS Firewall Manager | Enforcement centralizado em multi-account |

- Key Decisions:
  - Colocar WAF no CloudFront (bloqueia na edge) vs API Gateway (bloqueia na origem)
  - Rate limit threshold: baseado em P99 do tráfego legítimo × 2-3
  - Bot Control: habilitar apenas se tráfego de bots é problema mensurável
  - Logging destino: S3 para volume alto, CloudWatch Logs para alertas
- Scaling Path:
  1. **Início**: WAF com baseline managed rules + rate limiting → suficiente para maioria dos casos
  2. **Crescimento**: Adicionar Bot Control Common quando bots representam >10% do tráfego
  3. **Maturidade**: Bot Control Targeted + ATP + Firewall Manager policies + Shield Advanced
  4. **Enterprise**: SIEM integration (Firehose → Splunk/Datadog), custom threat intelligence IP feeds, automated response via Lambda
- Cost Baseline:
  - Mínimo: 1 Web ACL ($5) + 3 managed rule groups ($3) + requests ($0.60/M) = ~$14/mês para 10M req
  - Com Bot Control Common: +$10/mês + $1/M req (10M grátis)
  - Com Shield Advanced: +$3.000/mês (inclui WAF costs para recursos protegidos)
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/getting-started.html

---

**Multi-API WAF Centralizado com Firewall Manager**
- Context: Organização multi-account com múltiplas APIs (API Gateway e ALBs) que precisam de proteção WAF consistente e governança centralizada
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Governance | AWS Organizations | Estrutura multi-account |
  | Policy Management | AWS Firewall Manager | Políticas WAF centralizadas, compliance enforcement |
  | Security Account | Conta dedicada | Administração Firewall Manager, gestão de IP Sets globais |
  | WAF (per-account) | AWS WAF | Web ACLs aplicados via Firewall Manager policies |
  | Logging Centralizado | S3 bucket central + Athena | Logs WAF de todas as contas consolidados |
  | Alerting | CloudWatch + SNS | Alertas cross-account de eventos WAF |

- Key Decisions:
  - Firewall Manager auto-remediation: habilitar para aplicar WAF automaticamente a novos recursos
  - Regras centrais (mandatory) vs regras locais (time-specific): definir política de extensibilidade
  - Log aggregation: S3 bucket na conta de segurança com resource policy para cross-account write
  - IP Set compartilhado: criar em conta de segurança, referenciar via Firewall Manager
- Scaling Path:
  1. **Início**: 1 Firewall Manager policy com baseline WAF rules para todas as contas
  2. **Crescimento**: Policies diferenciadas por OU (production vs development)
  3. **Maturidade**: Automated compliance remediation + Shield Advanced policy + centralized logging
- Cost Baseline:
  - Firewall Manager: $100/policy/região/mês
  - WAF por recurso: $5/Web ACL + $0.60/M requests
  - Considerando 10 contas × 3 regiões × 1 policy = $300/mês de FM + WAF costs por recurso
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/fms-chapter.html

---

## Scenario Coverage

**Standard Case**: API REST pública com CloudFront + API Gateway servindo SPA frontend
- Approach:
  1. Web ACL (scope CLOUDFRONT) associado à distribuição CloudFront
  2. Managed rules: CRS (700 WCU) + Known Bad Inputs (200 WCU) + IP Reputation (25 WCU) = 925 WCU
  3. Rate-based rule: 2.000 req/5min por IP (calibrar ao tráfego)
  4. Default action: Allow
  5. Logging: S3 (blocks + counts) + CloudWatch alarm em spikes
  6. Count mode por 7 dias → Block após validação
- Key Decisions:
  - Bot Control: avaliar após análise de tráfego em produção
  - Geo blocking: aplicar se base de usuários é regional
  - WAF no API Gateway: adicionar apenas se origin access não está restrito a CloudFront

**Edge Case**: API com payloads grandes (file upload >16KB) e conteúdo user-generated que gera false positives XSS
- Approach:
  1. Aumentar body inspection limit para 64KB na configuração do Web ACL (disponível para CloudFront, API Gateway)
  2. CRS em Count mode para regras XSS em paths de upload
  3. Label-based rule: Block XSS labels EXCETO para URI paths de upload/content
  4. Regra customizada específica para paths de upload (validar content-type, size, sem managed rules)
  5. Rate limiting mais agressivo em paths de upload (prevent abuse)
  6. Custo adicional: $0.30/M requests por cada 16KB adicionais de body inspection

**Anti-Pattern Case**: Time quer desabilitar todas as managed rules porque "geram false positives demais"
- Clarification: "Quantos false positives por dia? Em quais regras específicas? Qual o volume de true positives que essas regras estão bloqueando?" — Nunca desabilitar managed rules inteiramente. Usar Count mode + labels para exceções granulares. Se >5% false positive rate em uma regra específica, override essa regra individual para Count e criar regra customizada com label match + exceção. Documentar cada exceção e revisar trimestralmente.

---

## Pricing Reference

### Componentes de Custo AWS WAF

| Componente | Custo | Nota |
|-----------|-------|------|
| Web ACL | $5.00/mês | Prorated por hora |
| Rule (custom) | $1.00/mês por regra | Inclui regras dentro de rule groups próprios |
| Managed Rule Group (AWS free) | $1.00/mês por group | CRS, Known Bad Inputs, IP Reputation, Admin Protection |
| Requests | $0.60/milhão | Base (até 1.500 WCUs) |
| WCU excedente (>1.500) | +$0.20/milhão por 500 WCUs | Incremental |
| Body inspection (>16KB) | $0.30/milhão por 16KB extra | Até 64KB total |
| Bot Control Common | $10.00/mês + $1.00/milhão | Primeiros 10M req/mês grátis |
| Bot Control Targeted | $10.00/mês + $10.00/milhão | Primeiros 1M req/mês grátis |
| CAPTCHA | $0.40/mil attempts | Por CAPTCHA attempt analisado |
| Challenge | Pricing separado | Por challenge response servido |
| ATP/ACFP | $10.00/mês + $50-1.000/milhão | Tiers regressivos por volume |

### Exemplo: API com 50M requests/mês (baseline protection)
```
Web ACL:                    $5.00
Rules (3 managed + 1 rate): $4.00
Requests (50M × $0.60/M):  $30.00
Logging (S3, ~5GB):         $0.12
Total:                      ~$39.12/mês
```

### Exemplo: API com 50M requests/mês (baseline + Bot Control Common)
```
Web ACL:                    $5.00
Rules (4 managed + 1 rate): $5.00
Requests (50M × $0.60/M):  $30.00
Bot Control (50M - 10M free): $40.00
Logging (S3, ~5GB):         $0.12
Total:                      ~$80.12/mês
```

---

## AWS WAF Quotas (Limites Relevantes)

| Recurso | Quota Padrão | Ajustável |
|---------|-------------|-----------|
| Web ACLs por região por conta | 100 | Sim |
| Rules por Web ACL | 100 | Não (use WCU como constraint real) |
| WCUs por Web ACL | 5.000 (max) | Sim (acima de 1.500 incorre custo adicional) |
| IP addresses por IP Set | 10.000 | Sim |
| Regex patterns por Regex Pattern Set | 10 | Não |
| Rate-based rule minimum threshold | 100 requests | Não |
| Rate-based rule evaluation window | 1 min ou 5 min | Não |
| Web ACLs por recurso | 1 | Não |
| Recursos por Web ACL (CLOUDFRONT) | Sem limite | — |
| Body inspection limit | 16KB (default), até 64KB | Configurável por Web ACL |

Source: https://docs.aws.amazon.com/waf/latest/developerguide/limits.html

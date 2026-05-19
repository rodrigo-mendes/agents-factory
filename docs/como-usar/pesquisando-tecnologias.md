# Guia: Pesquisando Tecnologias

Como usar os prompts de pesquisa para construir bases de conhecimento validadas.

---

## Quando Usar

- Precisa aprender uma tecnologia nova para o projeto
- Quer criar uma skill baseada em informação verificada
- Precisa documentar padrões de uma versão específica

## Passo a Passo

### 1. Escolha o researcher certo

| Domínio | Prompt |
|---------|--------|
| Framework/lib (FastAPI, Redis, Spring) | `technical-framework-researcher` |
| Serviço cloud + Terraform | `technical-framework-researcher-terraform` |
| Práticas Terraform (org, CI/CD, test) | `terraform-engineering-best-practices-researcher` |
| Metodologia de arquitetura (C4, DDD) | `architecture-methodology-researcher` |
| Framework cloud (WAF, CAF) | `cloud-architecture-researcher` |
| Domínio de negócio (Finance, Legal) | `business-domain-researcher` |
| Framework de requisitos (Scrum, SAFe) | `requirements-methodology-researcher` |

### 2. Execute o prompt

```
@workspace /technical-framework-researcher
```

### 3. Forneça os inputs

O prompt pedirá:
- **Tecnologia**: Nome exato (ex: "FastAPI")
- **Versão**: Versão específica (ex: "0.100")
- **Contexto**: Parceiros de integração, caso de uso

> ⚠️ **Version Absolutism**: Sempre forneça a versão específica. "FastAPI" não é suficiente — deve ser "FastAPI v0.100".

### 4. Revise o output

O documento de pesquisa terá:
- Padrões oficiais validados
- Código de exemplo (de docs oficiais, não inventado)
- Breaking changes vs versões anteriores
- Integrações testadas

### 5. Compile em artefato operacional

Após a pesquisa, transforme em skill ou instruction:

| Tipo de pesquisa | Compiler |
|-----------------|----------|
| Tecnologia genérica | `@workspace /skill-creator` |
| Terraform services | `@workspace /terraform-instructions-compiler` |
| Metodologia de arquitetura | `@workspace /archtecture-approches-skill-generator` |
| Metodologia de requisitos | `@workspace /methodologies-skill-generator` |

---

## Dicas

- **Não pule a compilação**: O documento de pesquisa não é o artefato final — precisa ser estruturado em three-tier para ser útil a agentes
- **Valide após compilar**: Use `@workspace /skill-best-practices-validator` no resultado
- **Uma versão por vez**: Se precisa de múltiplas versões, faça pesquisas separadas

## Armadilhas Comuns

| Armadilha | Solução |
|-----------|---------|
| Pesquisar sem versão específica | Sempre fornecer versão exata |
| Usar output de pesquisa como skill diretamente | Passar pelo compiler primeiro |
| Misturar informação de versões diferentes | Separar em pesquisas distintas |
| Não validar o resultado | Executar validator após compilar |

## Fluxo Completo

Ver: [Fluxo de Base de Conhecimento](../fluxos/fluxo-base-conhecimento.md)

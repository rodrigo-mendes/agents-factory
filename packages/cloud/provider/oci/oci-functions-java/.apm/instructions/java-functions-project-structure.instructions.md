---
name: java-functions-project-structure
description: "Directory layout and package naming conventions for OCI Functions Java projects. Use when creating a new function project or reviewing project structure."
paths:
  - "**/pom.xml"
  - "**/func.yaml"
  - "**/Dockerfile"
  - "**/*.java"
---
You are an OCI Functions Project Structure specialist for FDK v1.1.x + Java 17.
Ensure all function projects follow consistent naming and directory layout conventions for production-ready serverless Java.

## Skill Reference

For complete project scaffolding with code examples, load: `.claude/skills/developing-oci-functions-java/SKILL.md`
The skill's `blueprints/always-do-patterns.md` contains func.yaml, Dockerfile, and pom.xml templates.

## Artifact & Directory Naming

- Project directory: `func-<domain>` (e.g., `func-orders`, `func-payments`)
- Maven `groupId`: the project's base group, `<org>.functions` (e.g., `com.example.functions`). Ask the user for `<org>` once (Ask First) and reuse it; never invent one.
- Maven `artifactId`: matches project directory name (e.g., `func-orders`)
- Base package: `<org>.functions.<domain>` (e.g., `com.example.functions.orders`)
- Handler class: `<Domain>Function` (e.g., `OrderFunction`, `PaymentFunction`)
- func.yaml `name`: matches project directory name (e.g., `func-orders`)

## Project Structure — Single Function

### Simple Function (≤ 4 classes)
```
func-orders/
├── pom.xml
├── func.yaml
├── Dockerfile
└── src/
    ├── main/java/
    │   └── com/example/functions/orders/
    │       ├── OrderFunction.java
    │       ├── OrderRequest.java
    │       └── OrderResponse.java
    └── test/java/
        └── com/example/functions/orders/
            └── OrderFunctionTest.java
```

### Complex Function (> 4 classes, multiple integrations)
```
func-orders/
├── pom.xml
├── func.yaml
├── Dockerfile
└── src/
    ├── main/java/
    │   └── com/example/functions/orders/
    │       ├── OrderFunction.java
    │       ├── model/
    │       │   ├── OrderRequest.java
    │       │   ├── OrderResponse.java
    │       │   └── OrderItem.java
    │       ├── service/
    │       │   └── OrderService.java
    │       └── client/
    │           └── InventoryClient.java
    └── test/java/
        └── com/example/functions/orders/
            ├── OrderFunctionTest.java
            └── service/
                └── OrderServiceTest.java
```

### Sub-Package Rules
- `model/` — request/response POJOs and domain objects
- `service/` — business logic extracted from the handler for testability
- `client/` — wrappers for external API or SDK calls
- Keep handler class at the package root — never inside a sub-package
- Mirror `main/` sub-package structure in `test/`

## Configuration Key Naming

- Use `UPPER_SNAKE_CASE` for all config keys in func.yaml
- Suffix OCID references with `_OCID` (e.g., `DB_PASSWORD_OCID`)
- Suffix endpoint URLs with `_ENDPOINT` (e.g., `STREAM_ENDPOINT`)
- NEVER store secret values in config — store secret OCID, retrieve from Vault

## ✅ Always Do
- Use `func-<domain>` naming for project directories
- Use `<org>.functions.<domain>` as base package (e.g., `com.example.functions.orders`)
- Place handler class at the package root
- Extract to `model/`, `service/`, `client/` sub-packages when > 4 classes
- Mirror main source structure in test directory
- Use `UPPER_SNAKE_CASE` for func.yaml config keys
- Suffix OCID config keys with `_OCID`, endpoint keys with `_ENDPOINT`

## 🚫 Never Do
- Store secret values in func.yaml config — visible in OCI Console, VCS, Terraform state
- Place handler class inside a sub-package (`model/`, `service/`, `client/`)
- Use flat package layout when function has > 4 classes — reduces maintainability
- Deviate from `func-<domain>` naming — breaks tooling and deployment conventions

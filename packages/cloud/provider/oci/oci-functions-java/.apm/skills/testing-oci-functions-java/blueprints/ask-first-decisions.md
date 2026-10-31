# ⚠️ Ask First — Testing Decisions

## Decision: Mock Injection Strategy

| Option | Complexity | Isolation | Best When |
|--------|-----------|-----------|-----------|
| **addSharedClass + static fields** | Low | Medium | 1-2 OCI services, simple functions |
| **Interface abstraction + DI** | Medium | High | 3+ services, complex orchestration |

**Agent**: "How many OCI services does the function call? For 1-2, use addSharedClass. For 3+, introduce interface abstraction."

## Decision: Test Scope

| Scope | Speed | Docker | Validates |
|-------|-------|--------|-----------|
| **FnTestingRule** | ~ms | No | Handler logic, config, POJO binding |
| **APIGatewayTestFeature** | ~ms | No | HTTP routing, query params, status codes |
| **fn invoke --local** | ~s | Yes | Dockerfile, func.yaml, classpath |
| **fn invoke (OCI)** | ~10s | No | Resource Principal, IAM, networking |

**Agent**: "Use FnTestingRule for all logic tests. Add fn CLI tests only when Dockerfile or func.yaml changes. Use APIGatewayTestFeature when function extends APIGatewayFunction."

## Decision: JUnit 4 vs JUnit 5

FDK provides JUnit 4 `@Rule`. If project uses JUnit 5, add vintage engine:

```xml
<dependency>
    <groupId>org.junit.vintage</groupId>
    <artifactId>junit-vintage-engine</artifactId>
    <version>5.10.2</version>
    <scope>test</scope>
</dependency>
```

**Agent**: "Does the project already use JUnit 5? If yes, add vintage engine. If new project, default to JUnit 4."

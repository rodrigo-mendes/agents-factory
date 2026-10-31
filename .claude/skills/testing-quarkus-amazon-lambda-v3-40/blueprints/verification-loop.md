# Verification Loop

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. All commands are representative; adapt to your environment.

## Loop

1. Write or change the test.
2. Run the unit tests and read the result.
3. Run the guard greps; every "expected" must hold.
4. Run the integration tests when the change touches packaging or native behaviour.
5. Repeat until all expectations hold.

```bash
# Representative — adapt to your environment (Quarkus 3.40.1.1)
./mvnw test                              # expected: mock event server on :8081; @QuarkusTest classes pass
./mvnw verify -DskipITs=false            # expected: @QuarkusIntegrationTest classes run (failsafe) against the jar
./mvnw verify -Dnative -DskipITs=false   # native ITs; needs GraalVM or Mandrel, or a container build (exact flags for Lambda projects: medium confidence)
```

```bash
# Guard greps (representative)
grep -rn "quarkus-test-amazon-lambda\|LambdaClient" pom.xml build.gradle src/test   # expected: no output
grep -rn "quarkus.lambda.test-port\|quarkus.lambda.dev-port" src/                    # advisory only (medium confidence, M9): review any hit, not a failure
grep -rn "endpoint-override" src/main/resources/application.properties               # expected: no %test value (keeps Dev Services on)
grep -rn "amazonaws.com" src/test                                                    # expected: no output (no real AWS from tests)
```

```bash
# Optional, Docker needed; local emulation, never deployment
sam local invoke --template target/sam.jvm.yaml --event payload.json
```

## Reading failures

| Symptom | Likely cause | Where |
|---|---|---|
| Connection refused on 8081 | Mock event server disabled or `LambdaClient` on the classpath | [mock-event-server](./mock-event-server.md#lifecycle-in-a-quarkustest-run) |
| Status 500 from the test call | The handler threw an error | [always-do 1](./always-do-patterns.md#1-plain-handler-test) |
| Dependency resolution fails for `quarkus-test-amazon-lambda` | Artifact removed in 3.31 | [never-do F1](./never-do-patterns.md#f1-using-quarkus-test-amazon-lambda-or-lambdaclient-severity-high) |
| Test fails at start without Docker | Dev Services need Docker | [decision C1](./ask-first-decisions.md#c1-dev-services-injectmock-or-endpoint-override) |

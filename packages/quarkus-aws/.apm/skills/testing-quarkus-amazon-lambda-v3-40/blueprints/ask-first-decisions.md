# Ask-First Decisions

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Every decision here is put to the user; none has a default except where stated.

## Contents

- [C1. Dev Services, `@InjectMock` or `endpoint-override`](#c1-dev-services-injectmock-or-endpoint-override)
- [C2. Dev Services stack provider](#c2-dev-services-stack-provider)
- [C3. Optional SAM local emulation](#c3-optional-sam-local-emulation)
- [C4. Fixed or random mock-server port](#c4-fixed-or-random-mock-server-port)
- [C5. Secured HTTP Lambda: event claims or `@TestSecurity`](#c5-secured-http-lambda-event-claims-or-testsecurity)

## C1. Dev Services, `@InjectMock` or `endpoint-override`

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. Dev Services container | Realistic SDK calls, zero config | Docker required ("In test mode, it will cause the test to fail" without Docker); the stack may not implement every service | Behaviour against the AWS API matters |
| B. `@InjectMock` on the CDI bean wrapping the client | Fast, no Docker | Not available in `@QuarkusIntegrationTest` ("except injecting into tests") | Unit tests of business logic |
| C. Explicit `endpoint-override` to a container you manage | Full control | Disables Dev Services; you manage the lifecycle | Shared CI LocalStack, custom init |

Option B needs `quarkus-junit-mockito`; rules in `developing-quarkus-junit-v3-40`. Source: [Dev Services 3.23.x](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html), [testing guide](https://quarkus.io/version/3.40/guides/getting-started-testing).

Ask: "Is Docker available in CI? Must the test exercise the AWS SDK call, or only the business logic?"

## C2. Dev Services stack provider

`quarkus.aws.devservices.provider` accepts `localstack` (default in 3.23.x), `ministack`, `moto`, `floci`.

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| `localstack` (`localstack/localstack:4.13`; default and image tag are (medium confidence), M13) | Pinned tag | The `dev` docs say LocalStack is supported "up to version 4.13 (latest free community version)" | First option to propose (default of the 3.23.x line) |
| `ministack`, `moto`, `floci` | Alternatives | Images default to `:latest` (not reproducible); Dev Services does not check service coverage | Licence or coverage reasons |

The unversioned `dev` docs name Floci as default; the 3.23.x page names LocalStack. This skill follows 3.23.x. The 3.23.x ↔ Quarkus 3.40 pairing is (medium confidence). Source: [3.23.x](https://docs.quarkiverse.io/quarkus-amazon-services/3.23.x/dev-services.html), [dev](https://docs.quarkiverse.io/quarkus-amazon-services/dev/dev-services.html).

Ask: "Keep LocalStack? If you change the provider, pin the image tag."

## C3. Optional SAM local emulation

SAM is local emulation only, never a deployment path (IaC is Terraform, `provisioning-aws-lambda-v6`).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Mock event server (default) | Speed, no Docker, JUnit-integrated; guide: "the Quarkus JUnit integration should be sufficient for most of your needs" | Not the real Lambda container | Always |
| `sam local invoke --template target/sam.jvm.yaml --event payload.json` (plain Lambda; `target/sam.native.yaml` for native; Gradle uses `build`) | Lambda container emulation | Docker + SAM CLI; `sam.*.yaml` is not the IaC | Smoke test of the zip in a Lambda-like container |
| `sam local start-api --template target/sam.jvm.yaml`, then `http://127.0.0.1:3000/hello` (HTTP guide documents only `start-api`) | Same, for HTTP Lambdas | Same | HTTP smoke test |

For a fixed principal under `sam local` the HTTP guide offers `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME`. Source: [aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda), [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http).

Ask: "Do you want local Lambda-container emulation? It needs Docker and the SAM CLI and is not deployment."

## C4. Fixed or random mock-server port

Options: default `8081`; a fixed other port (the guide's example is 8083); `0` for random ("A port value of zero will result in a randomly assigned port"). Random avoids clashes in parallel CI runs. RestAssured is configured automatically for the default; whether it follows a random or overridden port is not stated (unverified). Advice: use the `quarkus.lambda.mock-event-server.*` names. The short keys `quarkus.lambda.test-port` / `dev-port` exist, are not deprecated, and the start-up code reads only the `mock-event-server.*` names (medium confidence, M9; derived from source at tag 3.40.1.1, not from a guide statement). Source: [aws-lambda guide](https://quarkus.io/version/3.40/guides/aws-lambda).

Ask: "Do tests run in parallel on shared hosts?"

## C5. Secured HTTP Lambda: event claims or `@TestSecurity`

| Option | Documented | Limit |
|---|---|---|
| A. Claims in the API Gateway event posted to `/_lambda_` | Yes, in the aws-lambda-http guide | Needs a raw event helper (shape not shown, unverified) |
| B. `@TestSecurity(user=..., roles=...)` from `quarkus-test-security` | Generically, for `@QuarkusTest` only | Effect through the Lambda mock event server path is (unverified) |

Prefer A for Lambda-specific security tests; ask before relying on B. Source: [aws-lambda-http guide](https://quarkus.io/version/3.40/guides/aws-lambda-http), [security-testing](https://quarkus.io/version/3.40/guides/security-testing).

Ask: "Which identity mechanism does the endpoint use, and may the test rely on `@TestSecurity`?"

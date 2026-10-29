# Mock Event Server Behaviour

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Source: `extensions/amazon-lambda` at tag 3.40.1.1 (`DevServicesLambdaProcessor`, `MockEventServer`, `AmazonLambdaApi`, `MockEventServerConfig`), summarised by the fetch tool (L3); identifiers and literals were quoted.

## Lifecycle in a `@QuarkusTest` run

Steps 1 to 5 are read from source through a summarising tool: (medium confidence, M10 for steps 1, 3, 4 and 5; M11 for the legacy-testing check in step 2).

1. The build step `startEventServer` runs only when not in production and only when the launch mode is dev or test. The source comment says it is "required for testing so run it even if devservices.enabled=false".
2. It returns early when legacy testing is detected (`io.quarkus.amazon.lambda.test.LambdaClient` on the classpath) or `quarkus.lambda.mock-event-server.enabled` is false.
3. Port order: an `EventServerPortOverrideBuildItem` if present, else the configured `quarkus.lambda.mock-event-server.test-port` (test) or `dev-port` (dev), else `MockEventServerConfig` `TEST_PORT` "8081" or `DEV_PORT` "8080". After the start it sets that property to the exposed port and sets `quarkus-internal.aws-lambda.test-api` to `localhost:<port>/_lambda_`. The start is logged at debug level only.
4. `MockEventServer` registers `POST /_lambda_` and a default `POST` on any other path, both mapped to `postEvent`. The Lambda poll loop pulls from `/_lambda_/2018-06-01/runtime/invocation/next` and answers on `.../invocation/<requestId>/response` or `/error`.
5. The test's HTTP call stays open until the handler responds. A handler error returns status **500** to the caller. The mock server code has no response timeout (`setMaxWorkerExecuteTime(60)` is a worker limit). If the server closes, the caller gets 503.

## Config roots

`quarkus.lambda.dev-port` and `quarkus.lambda.test-port` exist as a separate config root (`MockEventServerConfig`, prefix `quarkus.lambda`, defaults 8080 and 8081) and are not marked deprecated in the 3.40 reference or in source. The start-up code reads only `quarkus.lambda.mock-event-server.` + `test-port` / `dev-port`. Whether any other code reads the short names is (unverified). Use the `mock-event-server.*` names ([never-do F3](./ask-first-decisions.md#c4-fixed-or-random-mock-server-port)).

## Practical consequences

- A test that expects an error must assert status 500, not a thrown exception in the test thread.
- A project with `quarkus-test-amazon-lambda` on the classpath gets no mock server ([never-do F1](./never-do-patterns.md#f1-using-quarkus-test-amazon-lambda-or-lambdaclient-severity-high)).
- Random port (`0`) avoids clashes in parallel CI runs; whether RestAssured follows a non-default port is (unverified), see [decision C4](./ask-first-decisions.md#c4-fixed-or-random-mock-server-port).
- Reading the port with `System.getProperty` may not work: `quarkus.http.test-port` no longer works that way since 3.31 (family fact), and the same caution applies by analogy to the mock server port property (medium confidence).

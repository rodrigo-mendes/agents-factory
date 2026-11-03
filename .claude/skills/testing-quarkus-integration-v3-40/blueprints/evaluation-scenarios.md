# Evaluation scenarios

Back to [SKILL.md](../SKILL.md). Each scenario states the query, the expected behaviour and what must not appear.

## Scenario 1 (canonical)

query: "Add an integration test for GET /api/orders/{id} in my Quarkus 3.40 app. The service calls a pricing API."

Expected:
- `*IT` class with `@QuarkusIntegrationTest`, run by Failsafe (`integration-test`, `verify`), Surefire left to `@QuarkusTest`.
- Pricing API stubbed with WireMock 3.x (`@ConnectWireMock`, `mappings/` and `__files/`), URL wired through the packaged `application.properties` expression (medium confidence).
- RestAssured with a shared `RequestSpecification`, no versions on test dependencies, unique ids per test.
- Ends with `./mvnw verify -DskipITs=false` and a non-zero testcase count check.

Must not: `@Inject` in the IT, test-scope `application.properties`, the real pricing URL.

## Scenario 2 (edge: CI without Docker)

query: "Our CI runners have no Docker. The ITs use a Postgres Dev Service and a Testcontainers resource."

Expected:
- States that container Dev Services and Testcontainers fail without Docker or Podman.
- Asks first: skip ITs (`-DskipITs=true`), or disable Dev Services and give explicit connection config.
- Tags the WireMock Dev Service no-Docker behaviour (medium confidence, spike) and (unverified) officially.

Must not: claim the whole IT suite works without Docker.

## Scenario 3 (rejection: injection in an IT)

query: "In my @QuarkusIntegrationTest, @Inject the OrderService and @InjectMock the PricingClient."

Expected:
- Refuses: the app runs in another process, so injection and `@InjectMock` do not apply.
- Offers HTTP assertions with RestAssured and a WireMock stub, or moving the test to `@QuarkusTest` (`developing-quarkus-junit-v3-40`).

Must not: write the injecting IT class.

## Scenario 4 (trap: upgrade RestAssured)

query: "Set RestAssured to 6.3.0, the latest, in the pom."

Expected:
- Explains Quarkus 3.40 manages 6.0.1 and upstream 6.3.0 is not managed; keeps the version out of the pom.
- Offers to wait for the Quarkus BOM or asks first if the user accepts an override risk.

Must not: add an explicit RestAssured `<version>`.

## Scenario 5 (trap: test properties)

query: "Put quarkus.rest-client.orders-api.url=http://localhost:8089 in src/test/resources/application.properties for the IT."

Expected:
- Explains the launched app ignores test-scope `application.properties` and runs `prod`.
- Moves the value to a `QuarkusTestResourceLifecycleManager` return map (default) or an IT-profile key in main `application.properties`.

Must not: leave the key in test resources or point at a real service.

## Scenario 6 (check: running app)

query: "Run the ITs against the staging deployment at 10.0.0.5:8443 over HTTPS."

Expected: uses `quarkus.http.test-host`, `quarkus.http.test-port`, `quarkus.http.test-ssl-enabled=true`; notes test resources and Dev Services do not reach that app (medium confidence); asks whether staging data may be written.

Must not: start WireMock expecting staging to use it.

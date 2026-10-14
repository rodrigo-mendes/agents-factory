# Testing and Mocking: Quarkus ArC 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source unless stated: https://quarkus.io/version/3.40/guides/getting-started-testing (the first 100k of 108k characters were read).

## Artifacts

- Quarkus: `quarkus-junit` and `quarkus-junit-mockito`, test scope. The 3.40 testing guide does not mention `quarkus-junit5*`.
- Camel: `camel-quarkus-junit` (renamed from `camel-quarkus-junit5` since 3.31, High; https://camel.apache.org/camel-quarkus/3.40.x/migration-guide/3.31.0.html). Camel test details: skill `developing-camel-quarkus-junit-v3-40`; Quarkus-side rename: skill `developing-quarkus-junit-v3-40`.

## InjectMock

```java
@QuarkusTest
class OrderServiceTest {
    @InjectMock PriceClient priceClient;   // io.quarkus.test.InjectMock; bean must be normal-scoped
    @Inject OrderService service;

    @Test void total() {
        Mockito.when(priceClient.price("A")).thenReturn(10);
        assertEquals(10, service.total("A"));
    }
}
```

- `@InjectMock` and `@InjectSpy` require `quarkus-junit-mockito`.
- Only normal-scoped beans can be mocked ("basically every scope except @Singleton and @Dependent").
- The mock applies only to test methods of the annotated test class. Use `QuarkusMock.installMockForType` in `@BeforeAll`. `@InjectSpy` keeps the real behavior and its observers still run.

## Alternatives

| Option | Use when | Limit |
|---|---|---|
| `@InjectMock` | normal-scoped bean | not for `@Singleton`/`@Dependent` |
| `@MockitoConfig(convertScopes = true)` | bean must stay `@Singleton` | documented as an advanced option |
| test `@Alternative` in `src/test/java` | bean used during startup (not mocked automatically) | does not work for native tests |

## Lifecycle observers in tests

`quarkus.arc.test.disable-application-lifecycle-observers` (default `false`) disables application `StartupEvent` and `ShutdownEvent` observers during tests (https://quarkus.io/version/3.40/guides/cdi-reference).

## Verification (representative)

```bash
./mvnw test
# Expected: @QuarkusTest suites pass
```

## Not carried forward

`@QuarkusComponentTest` was not verified for 3.40 in this research, so no guidance is given (unverified, register U7).

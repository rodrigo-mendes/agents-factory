# Mocking Strategies: Quarkus JUnit 3.40.x

Research date 2026-10-14. Back to [SKILL.md](../SKILL.md). Source for every row: https://quarkus.io/version/3.40/guides/getting-started-testing

## Options

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A. CDI `@Alternative` / `@Mock` in `src/test/java` | works for startup-time beans | global to all tests | the bean is used during boot |
| B. `QuarkusMock.installMockForType` (in `@BeforeAll`) or `installMockForInstance` (per test) | no Mockito; per class or per test | manual fakes | simple hand-written fakes |
| C. `@InjectMock` (`quarkus-junit-mockito`) | Mockito stubbing per test | normal scope only; no startup beans | typical unit-like tests |
| D. `@InjectSpy` | real behaviour plus verification | observers still fire | verifying calls on a real bean |

Ask: "Is the bean used at startup, and which scope has it?"

## Examples

```java
// Quarkus 3.40
@QuarkusTest
class SpyTest {
    @InjectSpy GreetingService spy;                   // real bean; observers still invoked
    @Test void verifies() { get("/hello"); Mockito.verify(spy).greet(); }
}

@QuarkusTest
class QuarkusMockTest {
    @BeforeAll static void setup() { QuarkusMock.installMockForType(new FakeClock(), Clock.class); }
}
```

## Scope rules for `@InjectMock`

- Needs `io.quarkus:quarkus-junit-mockito` and a normal-scoped bean.
- `@Singleton`/`@Dependent` need `@MockitoConfig(convertScopes = true)`; the guide says to use it only with full understanding of the scope change.
- Beans used during startup are not affected by mocks; use an `@Alternative`.

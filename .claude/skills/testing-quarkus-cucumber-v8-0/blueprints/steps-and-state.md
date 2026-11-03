# Steps, state, hooks, reports, parallel

Back to [SKILL.md](../SKILL.md). Source for annotations: [cucumber-java README](https://github.com/cucumber/cucumber-jvm/tree/main/cucumber-java), read 2026-10-31.

## Scenario state

One step-class instance exists per scenario. Share state across step classes with PicoContainer constructor injection; classes and constructors must be public.

```java
public class ScenarioContext {
    public io.restassured.response.Response lastResponse;
    public String createdId;
}

public class ItemSteps {
    private final ScenarioContext ctx;
    public ItemSteps(ScenarioContext ctx) { this.ctx = ctx; }
}
```

Resources that need cleanup implement `org.picocontainer.Disposable`; it runs after Cucumber's after-hooks. Never hold state in static fields.

## Expressions, parameter types, tables

```java
public class ItemSteps {
    public record Item(String name, BigDecimal price) { }

    @ParameterType("\\d+(?:\\.\\d{1,2})?")
    public BigDecimal money(String value) { return new BigDecimal(value); }

    @DataTableType
    public Item item(Map<String, String> row) {
        return new Item(row.get("name"), new BigDecimal(row.get("price")));
    }

    @Given("the catalog contains:")
    public void catalog(List<Item> items) { /* post each item */ }

    @When("I create an item {string} priced {money}")
    public void create(String name, BigDecimal price) {
        ctx.lastResponse = given().contentType(ContentType.JSON)
            .body(Map.of("name", name, "price", price)).when().post("/items");
    }

    @Then("the response status is {int}")
    public void status(int status) { ctx.lastResponse.then().statusCode(status); }
}
```

- `@ParameterType`: the method name is the expression name, the regex goes in `value`, capture groups arrive as `String`.
- Release notes recommend a `@DataTableType` transform over `DataTable::asList` under JSpecify nullability.
- A DocString is received as a `String` or `io.cucumber.docstring.DocString` parameter on the step whose line ends with `"""`.
- A DocString and a DataTable on one step are allowed in 8.0, reporting is not supported yet.

## Hooks

```java
@Before("@R1")
public void tagHook(Scenario scenario) { scenario.log("requirement R1"); }

@After
public void attachOnFailure(Scenario scenario) {
    if (scenario.isFailed() && ctx.lastResponse != null) {
        scenario.attach(ctx.lastResponse.asByteArray(), "application/json", "last-response");
    }
}
```

- `@BeforeAll` and `@AfterAll` must be static methods without arguments.
- A tag expression on `@Before("@R1")` limits the hook to tagged scenarios.
- 8.0 adds named hooks (`@Before(name = ...)`).
- Hook execution order is not defined unless `order` is set; the direction of `order` is (unverified).

## Properties file

`src/test/resources/junit-platform.properties` (keys from the engine README):

```properties
cucumber.glue=com.example.acceptance
cucumber.plugin=pretty, html:target/cucumber/report.html, json:target/cucumber/report.json, junit:target/cucumber/junit.xml
cucumber.filter.tags=not @wip
cucumber.junit-platform.naming-strategy=long
cucumber.publish.quiet=true
cucumber.execution.parallel.enabled=false
```

A `@ConfigurationParameter` on the suite overrides the file for that suite (medium confidence: JUnit Platform behaviour, not re-read). In B1 these keys do not apply, because `Main.run` takes CLI arguments; pass `--glue`, `--plugin`, `--tags` there.

## Reports

- `html`, `json`, `messages`, `timeline`, `usage-json` need Jackson at test scope; `pretty` and `junit` do not.
- Keep the `junit` XML and `html` report as CI artifacts.
- Keep `cucumber.publish.enabled` off: it uploads reports to reports.cucumber.io.

## Tag filtering and traceability

- Feature or scenario tags: `@R1`, `@change-add-items`. Filter with `cucumber.filter.tags="@R1"` or `--tags "@R1"` in B1.
- Overriding the tag filter with `-Dcucumber.filter.tags=...` on the Maven command line is (medium confidence).
- Shard CI jobs by tag expression.

## Parallel execution (medium confidence, engine README)

- `cucumber.execution.parallel.enabled=true`; strategy `dynamic` (default factor 1), `fixed` or `custom`.
- `cucumber.execution.execution-mode.feature=same_thread` keeps scenarios of one feature serial.
- `cucumber.execution.exclusive-resources.<tag>.read-write` locks scenarios tagged `@<tag>`.
- `max-pool-size` does not strictly cap concurrency (junit5#3108).
- Shared state in the app (rows, stubs) makes parallel runs flaky unless data is isolated per scenario.
- These keys apply to the engine (B2); B1 runs through `Main.run` and was not tested in parallel (unverified).

# Blueprint: Java Handler — APIGatewayFunction Pattern

Full handler class template. Replace `{{package}}` and `{{Class}}` with the values collected during scaffolding.

```java
package {{groupId}}.{{package}};

import java.util.logging.Level;
import java.util.logging.Logger;

import {{groupId}}.{{package}}.model.{{Class}}Request;
import {{groupId}}.{{package}}.model.{{Class}}Response;
import com.fnproject.events.APIGatewayFunction;
import com.fnproject.events.input.APIGatewayRequestEvent;
import com.fnproject.events.output.APIGatewayResponseEvent;
import com.fnproject.fn.api.FnConfiguration;
import com.fnproject.fn.api.RuntimeContext;

public class {{Class}}Function extends APIGatewayFunction<{{Class}}Request, {{Class}}Response> {

    private static final Logger LOG = Logger.getLogger({{Class}}Function.class.getName());

    private String initError;
    private boolean coldStart = true;
    private String version;

    @Override
    @FnConfiguration
    public void configure(RuntimeContext ctx) {
        super.configure(ctx);
        long start = System.currentTimeMillis();

        try {
            this.version = ctx.getConfigurationByKey("FN_APP_ID").orElse("local");

            // Initialize resources here: SDK clients, HttpClient, ObjectMapper, etc.
            LOG.info("{{Class}}Function initialized successfully");
        } catch (Exception e) {
            this.initError = e.getClass().getName() + ": " + e.getMessage();
            LOG.severe("INIT FAILED: " + initError);
        }

        long elapsed = System.currentTimeMillis() - start;
        LOG.info(String.format("COLD_START completed in %dms | error=%s",
                elapsed, initError != null ? initError : "none"));
    }

    @Override
    public APIGatewayResponseEvent<{{Class}}Response> handler(APIGatewayRequestEvent<{{Class}}Request> req) {
        long startTime = System.currentTimeMillis();
        String path = req.getPath();
        LOG.info(String.format("INVOKE %s %s | coldStart=%s", req.getMethod(), path, coldStart));
        coldStart = false;

        try {
            if (initError != null) {
                return error(500, {{Class}}Response.error("Function init failed", initError));
            }

            {{Class}}Request body = req.getBody();
            // TODO: Add input validation
            // TODO: Implement business logic

            long elapsed = System.currentTimeMillis() - startTime;
            LOG.info(String.format("COMPLETE %s | status=200 | elapsed=%dms", path, elapsed));
            return success({{Class}}Response.ok("Success", null, elapsed));

        } catch (Exception e) {
            long elapsed = System.currentTimeMillis() - startTime;
            String detail = e.getClass().getName() + ": " + e.getMessage();
            LOG.log(Level.SEVERE, String.format("FAILED %s | elapsed=%dms | %s", path, elapsed, detail), e);
            return error(500, {{Class}}Response.error("Internal server error", detail, elapsed));
        }
    }
}
```

## Key mandatory elements

| Element | Location | Why |
|---|---|---|
| `private String initError` | field | stores init failure for deferred reporting |
| `configure()` try-catch | configure() | catches SDK/resource init failures |
| `if (initError != null)` | first line of handler() | surfaces init failure on every invocation |
| `coldStart` flag | field + handler() | enables cold start logging |
| `elapsed_ms` logging | handler() | supports SLA monitoring |

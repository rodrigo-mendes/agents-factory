# Blueprint: Java Response Model Template

Full `{{Class}}Response` model. Replace `{{package}}` and `{{Class}}` with the values collected during scaffolding.

```java
package com.brx.functions.{{package}}.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class {{Class}}Response {
    private String status;
    private String message;
    private Object data;

    @JsonProperty("elapsed_ms")
    private long elapsedMs;

    private String erro;
    private String detalhe;

    @JsonProperty("cold_start")
    private Boolean coldStart;

    public static {{Class}}Response ok(String message, Object data, long elapsedMs) {
        {{Class}}Response r = new {{Class}}Response();
        r.status = "sucesso";
        r.message = message;
        r.data = data;
        r.elapsedMs = elapsedMs;
        return r;
    }

    public static {{Class}}Response error(String erro, String detalhe) {
        return error(erro, detalhe, 0);
    }

    public static {{Class}}Response error(String erro, String detalhe, long elapsedMs) {
        {{Class}}Response r = new {{Class}}Response();
        r.status = "erro";
        r.erro = erro;
        r.detalhe = detalhe;
        r.elapsedMs = elapsedMs;
        return r;
    }

    public String getStatus() { return status; }
    public String getMessage() { return message; }
    public Object getData() { return data; }
    public long getElapsedMs() { return elapsedMs; }
    public String getErro() { return erro; }
    public String getDetalhe() { return detalhe; }
    public Boolean getColdStart() { return coldStart; }
}
```

## Field reference

| Field | JSON key | Purpose |
|---|---|---|
| `status` | `status` | `"sucesso"` or `"erro"` |
| `elapsedMs` | `elapsed_ms` | mandatory — SLA tracking |
| `erro` / `detalhe` | `erro` / `detalhe` | error path only |
| `coldStart` | `cold_start` | optional, set only on cold invocations |

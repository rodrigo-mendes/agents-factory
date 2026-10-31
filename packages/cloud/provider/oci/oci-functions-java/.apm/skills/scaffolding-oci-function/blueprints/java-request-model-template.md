# Blueprint: Java Request Model Template

Minimal `{{Class}}Request` skeleton. Replace `{{package}}` and `{{Class}}`, then add the actual request fields.

```java
package {{groupId}}.{{package}}.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class {{Class}}Request {
    // TODO: Add request fields
    // Example:
    // @JsonProperty("resource_id")
    // private String resourceId;
}
```

## Notes

- `@JsonIgnoreProperties(ignoreUnknown = true)` is mandatory — API Gateway may forward extra headers/fields; without it, unknown properties cause a 400 deserialization error.
- Use `@JsonProperty("snake_case_key")` for every field whose JSON key differs from the Java field name.
- Add getters for every field; Jackson uses them for serialization unless you configure field access globally.

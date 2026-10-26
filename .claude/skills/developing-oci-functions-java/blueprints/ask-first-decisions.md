### ⚠️ Ask First

**Decision Point**: Handler method signature style

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| A) POJO Input/Output | Simplicity, type safety | Header access, status control | Simple JSON APIs with typed req/res |
| B) Raw InputEvent/OutputEvent | Full HTTP control | Ease of use, type safety | Custom protocols, binary payloads |
| C) Combined (POJO + InputEvent) | Body + header access | Simplicity | Need typed body AND request headers |
| D) APIGatewayFunction (fn-events) | API Gateway integration, typed req/res | Additional dependency | Function is an API Gateway backend |

**Agent Behavior**:
"Before implementing, ask the user:
'Is the function invoked via API Gateway with query params/custom headers, or directly? Do you need access to HTTP headers and status codes, or is simple JSON in/out sufficient?'"

**Decision Factors**:
- Whether function is behind API Gateway
- Need for query parameter parsing
- Need for custom HTTP headers or status codes
- Preference for typed vs raw control

**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/DataBinding.md

---

**Decision Point**: State initialization strategy

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| A) @FnConfiguration method | Separation of concerns, testability | Slight verbosity | Multiple config steps, DB connections, OCI clients |
| B) Constructor with RuntimeContext | Simplicity, immutable fields | Less flexible ordering | Simple config, few dependencies |
| C) Static method + static fields | Memory efficiency | Testability, thread safety | Shared across instances (rare) |

**Agent Behavior**:
"Before implementing, ask the user:
'Does the function need complex initialization (DB connections, multiple OCI clients) or simple configuration?'"

**Decision Factors**:
- Number of OCI service clients needed
- Initialization complexity
- Testing strategy (mocking requirements)

**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/FunctionConfiguration.md

---

**Decision Point**: fn-events vs raw handler for API Gateway

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| A) `APIGatewayFunction<Req, Res>` (fn-events) | Type safety, query params, headers parsed | Additional dependency | API Gateway backend with query parameters |
| B) Raw handler parsing gateway JSON manually | No extra deps, full control | Manual parsing of gateway envelope | Simple cases, direct invoke, no query params |

**Agent Behavior**:
"Before implementing, ask the user:
'Is the function an API Gateway backend that needs to parse query parameters and return HTTP status codes? If yes, use fn-events module.'"

**Decision Factors**:
- Presence of query parameters in API Gateway routes
- Need for typed HTTP response with status codes
- Willingness to add `fn-events` dependency

**Source**: https://github.com/fnproject/fdk-java/blob/master/fn-events/README.md

---

**Decision Point**: Testing approach for OCI SDK integration

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| A) addSharedClass + mock objects | Quick setup, minimal code | Class loader complexity | Simple mocks, few OCI services |
| B) Interface abstraction + constructor injection | Clean architecture, full mock control | More classes/interfaces | Complex services, multiple OCI clients |
| C) fn-events-testing with APIGatewayTestFeature | Full gateway simulation | Only works for gateway pattern | API Gateway functions specifically |

**Agent Behavior**:
"Before implementing, ask the user:
'What is the testing priority — unit isolation with simple mocks, or integration realism with full gateway simulation?'"

**Decision Factors**:
- Number of OCI services being mocked
- Testing complexity budget
- Whether function uses API Gateway

**Source**: https://github.com/fnproject/fdk-java/blob/master/docs/TestingFunctions.md

---


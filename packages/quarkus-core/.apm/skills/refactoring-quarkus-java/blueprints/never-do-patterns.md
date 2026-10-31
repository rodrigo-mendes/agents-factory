# Never-do patterns

Back to [SKILL.md](../SKILL.md). Quarkus statements apply to Quarkus 3.40.x. The first four patterns are Quarkus facts with a source URL. The last four (behaviour change, scope change, speculative abstraction, red baseline) are the general method stated as team practice (register U1, no page read): team practice, outside the Never Do tier.

## Contents

- [Direct field access on a normal-scoped bean](#direct-field-access-on-a-normal-scoped-bean)
- [Moving constraints off the resource](#moving-constraints-off-the-resource)
- [Thread-model flip](#thread-model-flip)
- [Dropping unremovable markers](#dropping-unremovable-markers)
- [Renaming the Lambda handler bean](#renaming-the-lambda-handler-bean)
- [Behaviour change during refactor](#behaviour-change-during-refactor) (method)
- [Scope change](#scope-change) (method)
- [Speculative abstraction](#speculative-abstraction) (method)
- [Red baseline](#red-baseline) (method)

## Direct field access on a normal-scoped bean

The client proxy delegates only method calls ([CDI guide](https://quarkus.io/version/3.40/guides/cdi)).

```java
// 🚫 WRONG: a field of an @ApplicationScoped bean read from the extracted class
int n = counter.count;

// ✅ CORRECT
int n = counter.count();
```

## Moving constraints off the resource

```java
// 🚫 WRONG: @Valid moved into the service; a violation now surfaces as 5xx unless mapped
@POST public Response create(Order order) { return Response.ok(orders.create(order)).build(); }
// OrderService: public Order create(@Valid Order o)

// ✅ CORRECT: parameter violations on the endpoint return 400 ([validation guide](https://quarkus.io/version/3.40/guides/validation))
@POST public Response create(@Valid @NotNull Order order) { return Response.ok(orders.create(order)).build(); }
```

## Thread-model flip

The thread depends on the signature ([REST guide](https://quarkus.io/version/3.40/guides/rest)).

```java
// 🚫 WRONG: extraction rewrote a blocking method as Uni; blocking code now runs on the IO thread
@GET public Uni<Order> get() { return Uni.createFrom().item(repo.find()); }

// ✅ CORRECT: keep the blocking signature that the original had
@GET public Order get() { return repo.find(); }
```

## Dropping unremovable markers

Unused beans are removed by default (`remove-unused-beans=all`); `@Unremovable` and the other roots keep a bean ([CDI reference](https://quarkus.io/version/3.40/guides/cdi-reference)).

```java
// 🚫 WRONG: @Unremovable lost when the class moved
@ApplicationScoped class OrderMapper { }

// ✅ CORRECT: markers moved with the bean
@ApplicationScoped @Unremovable class OrderMapper { }
```

## Renaming the Lambda handler bean

```properties
# 🚫 WRONG: class renamed to OrderEventsHandler, CDI name changed to "orderEventsHandler",
# property left at the old name -> the handler is not found at runtime
quarkus.lambda.handler=orderEvents

# ✅ CORRECT: name and property changed together ([AWS Lambda guide](https://quarkus.io/guides/aws-lambda))
quarkus.lambda.handler=orderEventsHandler
```

Prefer not renaming at all during a refactor; the name is deployed configuration.

---

## Method rules (team practice, unverified U1; outside the Never Do tier)

### Behaviour change during refactor

```java
// 🚫 WRONG: "fixing" a status code while extracting the mapper
// original: NotFoundException -> 404, IllegalStateException -> 500
RestResponse<ErrorBody> map(IllegalStateException e) { return RestResponse.status(Status.BAD_REQUEST, body(e)); }

// ✅ CORRECT: keep 500 now; open a separate task to change it
RestResponse<ErrorBody> map(IllegalStateException e) { return RestResponse.status(Status.INTERNAL_SERVER_ERROR, body(e)); }
```

Mixing fixes with refactoring makes regressions impossible to bisect. The same holds for log texts and side-effect order.

### Scope change

```java
// 🚫 WRONG: scope changed "for speed" while extracting
@Singleton class Clock { }          // was @ApplicationScoped

// ✅ CORRECT: keep the scope; a scope change is its own task
@ApplicationScoped class Clock { }
```

Mocking consequences of a scope change are an Ask First row in [SKILL.md](../SKILL.md) (medium confidence, L1).

### Speculative abstraction

```java
// 🚫 WRONG: interface with one implementation and one call site
interface OrderMapperApi { OrderDto toDto(Order o); }
@ApplicationScoped class DefaultOrderMapper implements OrderMapperApi { }

// ✅ CORRECT: a plain class; add the interface when a second implementation or a real seam appears
@ApplicationScoped class OrderMapper { OrderDto toDto(Order o) { return null; } }
```

### Red baseline

```bash
# 🚫 WRONG: 3 tests fail, extraction starts anyway
./mvnw test      # representative command; exit code 1

# ✅ CORRECT: fix or skip with a reason first, then refactor
./mvnw test      # exit code 0
```

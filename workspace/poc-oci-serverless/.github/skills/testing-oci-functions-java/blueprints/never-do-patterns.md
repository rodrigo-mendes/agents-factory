# 🚫 Never Do — Testing Anti-Patterns

## Never Share Function Class with Test ClassLoader

```java
// 🚫 WRONG
testing.addSharedClass(OrderFunction.class); // Breaks @FnConfiguration isolation
```
```java
// ✅ CORRECT — share only mock/helper classes
testing.addSharedClass(MockOciClients.class);
testing.addSharedClassPrefix("com.eci.functions.mocks.");
testing.addSharedClassPrefix("com.oracle.bmc.");  // Required for BmcException catch
```
**Impact**: @FnConfiguration executes in wrong context → tests pass, production fails.

## Never Initialize Real Resource Principal in Tests

```java
// 🚫 WRONG — throws "Resource Principal not available"
var provider = ResourcePrincipalAuthenticationDetailsProvider.builder().build();
```
```java
// ✅ CORRECT — mock the client
ObjectStorageClient mock = mock(ObjectStorageClient.class);
when(mock.putObject(any())).thenReturn(PutObjectResponse.builder().eTag("e").build());
```
**Impact**: Test immediately fails with AuthenticationException.

## Never Omit content-type for POJO Handlers

```java
// 🚫 WRONG — body arrives as raw String, not deserialized POJO
testing.givenEvent().withBody("{\"key\":\"val\"}").enqueue();
```
```java
// ✅ CORRECT
testing.givenEvent()
    .withHeader("content-type", "application/json")
    .withBody("{\"key\":\"val\"}")
    .enqueue();
```
**Impact**: Null POJO or ClassCastException at handler invocation.

## Never Manually Craft API Gateway Envelope

```java
// 🚫 WRONG — fragile, breaks on FDK updates
testing.givenEvent().withBody("{\"headers\":{...},\"body\":\"...\"}").enqueue();
```
```java
// ✅ CORRECT — use APIGatewayTestFeature
APIGatewayRequestEvent<Req> event = mock(APIGatewayRequestEvent.class);
apiGw.givenEvent(event).enqueue();
```
**Impact**: Tests coupled to internal envelope format, break silently on version upgrade.

## Never Use Non-Thread-Safe Collections for Shared State

```java
// 🚫 WRONG
public static List<String> captured = new ArrayList<>(); // Race condition
```
```java
// ✅ CORRECT
public static final ConcurrentLinkedQueue<String> captured = new ConcurrentLinkedQueue<>();
```
**Impact**: Flaky tests, ConcurrentModificationException with Fn Flows.

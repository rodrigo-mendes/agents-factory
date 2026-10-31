# Evaluation Scenarios — refactoring-oci-java

## Scenario 1: Canonical — God Class Decomposition

```json
{
  "skills": ["refactoring-oci-java"],
  "query": "My RestProxyFunction is 580 lines. It does routing, store-id resolution, HTTP client calls, OAuth, APM tracing, and error mapping all in one class. Refactor it.",
  "expected_behavior": [
    "Establishes green baseline first: export JAVA_HOME and run mvn test before touching any code",
    "Maps test coupling: identifies which tests call handler() directly, which use package-private constructors",
    "Identifies smells: long class, block-titling comments, mixed concerns, duplicated scaffolding",
    "Extracts one smell at a time — does NOT rewrite the entire class in one step",
    "Preserves public method signatures and exact exception types/messages throughout",
    "Runs mvn test after each extraction step",
    "Delegates OAuth to OAuth2TokenProvider, routing to Route, error mapping to ErrorMapper",
    "Leaves the handler as a thin dispatcher (~230 lines) rather than eliminating it",
    "Does NOT add speculative abstractions (single-use indirection)"
  ]
}
```

## Scenario 2: Edge — Test Suite Has Broken Tests Before Refactoring

```json
{
  "skills": ["refactoring-oci-java"],
  "query": "I want to refactor my VaultService class but some tests are already failing before I start. Should I fix the tests first or refactor anyway?",
  "expected_behavior": [
    "Requires a green baseline before any refactoring begins — explicitly blocks starting without green tests",
    "Instructs to fix the failing tests first (or confirm they are intentionally skipped)",
    "Explains: refactoring with a red baseline makes it impossible to distinguish regressions from pre-existing failures",
    "Offers to help fix the failing tests as a prerequisite step",
    "Does NOT suggest skipping the baseline and refactoring anyway",
    "Does NOT suggest commenting out failing tests to make the suite green"
  ]
}
```

## Scenario 3: Edge — Mockito Breaks After Java Version Change

```json
{
  "skills": ["refactoring-oci-java"],
  "query": "After the refactoring, tests started failing with 'Cannot mock/spy class ... Mockito cannot mock this class'. I didn't change any test code.",
  "expected_behavior": [
    "Identifies this as a Java/Mockito version compatibility issue, not a refactoring regression",
    "Checks JAVA_HOME: confirms Corretto 21 is active (Java 25+ breaks Mockito byte-buddy mocking)",
    "Provides the fix: export JAVA_HOME=$(/usr/libexec/java_home -v 21)",
    "Notes the version constraint: Corretto 21 is the maximum safe JVM for current Mockito",
    "Does NOT suggest upgrading Mockito as the first fix without confirming Java version",
    "Does NOT suggest the refactoring broke mockability — the JVM version is the root cause"
  ]
}
```

## Scenario 4: Misuse Guard — Behavior Change During Refactoring

```json
{
  "skills": ["refactoring-oci-java"],
  "query": "While refactoring the error mapper, I noticed the HTTP status codes returned for some errors seem wrong. Should I fix them as part of this refactoring?",
  "expected_behavior": [
    "Explicitly blocks behavior changes during a refactoring session",
    "States the golden rule: same outputs, status codes, log texts, side-effect order — behavior stays identical",
    "Instructs to complete the refactoring with the current (possibly wrong) behavior preserved",
    "After refactoring is complete and suite is green: open a separate task to fix the behavior",
    "Explains: mixing behavior fixes with refactoring makes it impossible to bisect regressions",
    "Does NOT suggest fixing the behavior 'while you're in there'"
  ]
}
```

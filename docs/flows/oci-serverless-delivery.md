# Flow: an OCI serverless capability

Use this flow to build a capability that needs Java code, Terraform infrastructure and an API
Gateway route. The agents do not call each other. Each step writes a record and tells you which
command to run next, so you stay in control.

```mermaid
sequenceDiagram
    actor You
    participant Arch as /design-oci-architecture
    participant Stack as /provision-oci-serverless-stack
    participant Java as /develop-java-function (stream A)
    participant Infra as /provision-oci-infra (stream B)
    participant Dep as /deploy-oci-function
    participant Obs as /observe-oci-workload
    participant Dbg as /debug-oci-function
    You->>Arch: scope and capability slug
    Arch-->>You: work-orders under docs/handoff/capability/
    You->>Stack: capability slug
    Stack-->>You: work-orders valid, commands for streams A and B
    You->>Java: stream A
    Java-->>You: result-java.md
    You->>Infra: stream B
    Infra-->>You: result-terraform-infra.md
    You->>Stack: capability slug --integrate
    Stack-->>You: stream C (gateway route) and cross-domain checks
    You->>Dep: deploy with the approved plan
    Dep-->>You: deployed, or rolled back
    You->>Obs: capability slug
    opt the function fails
        You->>Dbg: function name and symptom
        Dbg-->>You: diagnosis
    end
```

## Steps

1. **Design.** `/design-oci-architecture full-stack my-capability` returns advisory output and
   work-orders under `docs/handoff/my-capability/`. It writes no code and no Terraform.
2. **Validate the work-orders.** `/provision-oci-serverless-stack my-capability` checks the three
   work-orders and tells you the commands for the Java and Terraform streams.
3. **Build the two streams.** Run `/develop-java-function` (stream A) and `/provision-oci-infra`
   (stream B). Each writes its own result record.
4. **Integrate.** After both result records exist, run
   `/provision-oci-serverless-stack my-capability --integrate`. It does stream C, the API Gateway
   route, and the cross-domain checks.
5. **Deploy.** `/deploy-oci-function` deploys with an approved plan. See the safety notes in
   [OCI commands](../entry-points/oci-serverless.md#safety).
6. **Observe.** `/observe-oci-workload` sets up and validates logging, tracing, alarms and
   dashboards.
7. **Debug, only if needed.** `/debug-oci-function <name and symptom>` diagnoses a failing function.

## Related

- [OCI commands](../entry-points/oci-serverless.md).
- [Agent architecture: user-mediated handoff](../agents/architecture.md#user-mediated-handoff-oci).

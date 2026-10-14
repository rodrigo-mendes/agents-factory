# Environment Validation Checklist

Use this checklist to validate a complete serverless environment before declaring it production-ready. All items must be checked.

## Network & Compartments

- [ ] Dedicated compartment(s) created (Network, Security, Serverless-{env})
- [ ] VCN with public subnet (API GW) and private subnet (Functions)
- [ ] Internet Gateway on public subnet route table
- [ ] NAT Gateway and/or Service Gateway for private subnet
- [ ] NSGs: 443 inbound on API GW; deny all on Functions except API GW CIDR

## IAM

- [ ] Dynamic Group for Functions with correct matching rule (`fnfunc` + compartment)
- [ ] Dynamic Group for API Gateway with correct matching rule (`ApiGateway` + compartment)
- [ ] Policy: API GW can invoke Functions (`use fn-invocation`)
- [ ] Policy: FaaS service can use VCN (`use virtual-network-family`)
- [ ] Policy: FaaS service can read repos (`read repos in tenancy`)
- [ ] Policy: Functions can read secrets in Vault (if applicable)
- [ ] Policy: Developers can manage fn-family and api-gateway-family

## Functions Application & Deployment

- [ ] Application created in private subnet with tracing enabled
- [ ] Function deployed with explicit timeout and memory limits
- [ ] Function image pinned with digest in production
- [ ] No credentials in function config (verified via credential scan)

## API Gateway

- [ ] API Gateway created in public subnet
- [ ] Deployment with routes pointing to Function(s)
- [ ] Rate limiting configured
- [ ] Authentication (JWT or custom) configured
- [ ] CORS configured if browser-based frontend exists

## Observability

- [ ] Logging enabled (Functions tracing + API Gateway access + execution logs)
- [ ] Alarms configured (error rate, latency, invocations)

## Cost Attribution

- [ ] Tagging applied for cost attribution

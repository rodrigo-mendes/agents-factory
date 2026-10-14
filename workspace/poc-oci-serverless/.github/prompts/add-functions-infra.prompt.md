---
description: 'Provision OCI Functions infrastructure (Application + Function resources) with Terraform'
agent: oci-terraform
argument-hint: 'Function name, application name, memory/timeout configuration'
---

# Add Functions Infrastructure

**Skill**: `provisioning-oci-functions`

## What this does

Provisions OCI Functions resources (Application and Function) with Terraform OCI Provider, including Docker image configuration and resource sizing.

## Required information

1. **Function name**: Name for the function resource
2. **Application name**: Existing application or create new?
3. **Docker image**: Image source (OCIR path or to be built)
4. **Memory (MB)**: Function memory allocation (128 / 256 / 512 / 1024)
5. **Timeout (seconds)**: Function execution timeout (30-300)
6. **Compartment**: Target compartment OCID or variable reference
7. **Existing module?**: Add to an existing Terraform module or create new?

## What will be generated

- `oci_functions_application` resource (if new application)
- `oci_functions_function` resource with image, memory, timeout
- Variables with validation blocks (OCID format, allowed values)
- Outputs for function OCID and invoke endpoint
- Tags via `local.common_tags`

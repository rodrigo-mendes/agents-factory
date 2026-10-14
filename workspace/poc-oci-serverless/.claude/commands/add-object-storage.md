---
description: Add Object Storage read/write capability to an existing OCI Function using OCI SDK v3.x+
argument-hint: Bucket name, read/write/both, and existing function class
context: fork
agent: oci-functions-java
background: false
disable-model-invocation: true
---

Execute this task now for the OCI serverless project. Read the referenced skill below for the canonical patterns, gather the "Required information", then carry the task through to completion. If the target below is empty, ask for the required information before proceeding.

**Request / target (from the user):** $ARGUMENTS

# Add Object Storage Integration

**Skill**: `integrating-oci-functions-objectstorage`

## What this does

Adds Object Storage read and/or write capability to an existing OCI Function, with proper InputStream lifecycle management and OOM prevention.

## Required information

1. **Bucket name**: Which Object Storage bucket to interact with?
2. **Operations**: Read, write, or both?
3. **Existing function class**: Which class to add the integration to?
4. **File size constraints**: Are files small (< 10MB) or large (requires streaming)?
5. **Namespace**: OCI Object Storage namespace (or auto-detect from Resource Principal)

## What will be generated

- ObjectStorageClient initialization with Resource Principal auth
- Read method with proper InputStream lifecycle (close in finally block)
- Write method with PutObjectRequest builder
- Pagination support for listing objects (if needed)
- OOM prevention patterns for large files
- Updated pom.xml with OCI SDK Object Storage dependency

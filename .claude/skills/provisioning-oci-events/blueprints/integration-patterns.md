## Integration Patterns

### Events ↔ OCI Functions (Serverless Processing Pipeline)

**Pattern**: Object Storage upload triggers Function processing via Event Rule.

```hcl
# Object Storage → Events → Function pipeline
module "events" {
  source = "./modules/events"

  compartment_ocid = var.compartment_ocid
  environment      = var.environment
  tags             = var.tags

  event_rules = {
    object_upload_processor = {
      display_name = "rule-obj-upload-process"
      description  = "Process uploaded files via Function"
      is_enabled   = true
      condition = {
        eventType = ["com.oraclecloud.objectstorage.createobject"]
        data = {
          additionalDetails = {
            bucketName = [var.upload_bucket_name]
          }
        }
      }
      actions = [
        {
          action_type = "FAAS"
          target_id   = module.functions.function_id
          description = "Invoke file processor function"
        }
      ]
    }
  }

  depends_on = [module.iam]
}
```

**Required IAM Policy** (see [provisioning-oci-iam](../provisioning-oci-iam/SKILL.md)):
```hcl
"Allow service cloudevents to use fn-invocation in compartment ${var.compartment_name}"
"Allow service cloudevents to use virtual-network-family in compartment ${var.compartment_name}"
```

### Events ↔ OCI Streaming (Audit & Retention)

**Pattern**: IAM changes captured and routed to centralized audit stream with security notification.

```hcl
# IAM Audit → Events → Stream + Notification
event_rules = {
  iam_security_monitor = {
    display_name = "rule-iam-security"
    description  = "Monitor IAM changes for security compliance"
    is_enabled   = true
    condition = {
      eventType = [
        "com.oraclecloud.identitycontrolplane.createpolicy",
        "com.oraclecloud.identitycontrolplane.updatepolicy",
        "com.oraclecloud.identitycontrolplane.deletepolicy",
        "com.oraclecloud.identitycontrolplane.createdynamicgroup",
        "com.oraclecloud.identitycontrolplane.updatedynamicgroup",
        "com.oraclecloud.identitycontrolplane.deletedynamicgroup"
      ]
    }
    actions = [
      {
        action_type = "OSS"
        target_id   = module.streaming.audit_stream_id
        description = "Stream IAM events for retention"
      },
      {
        action_type = "ONS"
        target_id   = var.security_topic_id
        description = "Alert security team"
      }
    ]
  }
}
```

### Events ↔ Functions Lifecycle (Observability)

**Pattern**: Monitor Function invocation lifecycle for serverless observability.

```hcl
# Function Lifecycle → Events → Stream
event_rules = {
  function_lifecycle = {
    display_name = "rule-fn-lifecycle"
    description  = "Monitor Function invocation lifecycle events"
    is_enabled   = true
    condition = {
      eventType = [
        "com.oraclecloud.functions.function.invoke",
        "com.oraclecloud.functions.application.update",
        "com.oraclecloud.functions.function.update"
      ]
    }
    actions = [
      {
        action_type = "OSS"
        target_id   = module.streaming.observability_stream_id
        description = "Stream function lifecycle events"
      }
    ]
  }
}
```

---


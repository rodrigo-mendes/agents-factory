# Evaluation Scenarios — observe-oci-workload

Three canonical scenarios for evaluating the `oci-observability` agent routed via this skill.

---

## Scenario 1: Full 5-Pillar Observability Stack (canonical)

**Input**:
```
/observe-oci-workload api-handler pillar:all
```

**Context**: A new OCI Functions application `api-handler` has just been deployed. No observability
infrastructure exists yet. The capability has a `docs/handoff/api-handler/report-terraform-infra.md`
with function OCID and application OCID.

**Expected agent behavior**:
1. P0: reads `docs/handoff/api-handler/report-terraform-infra.md` for application/function OCIDs;
   identifies all 5 pillars are in scope; loads `provisioning-custom-dashboard-oci-observability` (superset)
   plus `monitoring-oci-apm` for distributed tracing design.
2. P1: confirms no existing APM domain, log groups, alarms, or dashboards in `.tf` files.
3. P2: extracts ✅ Always Do from all loaded skills; notes the composition order (Logging → Alarms → APM → Connector Hub → Dashboards).
4. P3: presents a plan listing 6+ resources (APM domain, log group, 2 alarms, connector hub, dashboard), naming convention, file structure, and at least 2 ⚠️ Ask-First items (paid vs free APM tier; dashboard IAM scope). STOPS for approval.
5. P4 (after approval): generates `.tf` with all 5 pillars; applies `freeform_tags`; validates OCIDs with `can(regex(...))`.
6. P5: runs `terraform fmt -check` + `terraform validate`; writes `docs/handoff/api-handler/report-terraform-infra.md`; states next action (run `validating-oci-observability` scripts).

**Pass criteria**:
- Agent stops at P3 and waits for approval before generating code.
- No hardcoded OCIDs in generated `.tf`.
- Provider source is `oracle/oci` (not `hashicorp/oci`).
- All 5 pillars covered.
- Handoff report written with real `createdAt` timestamp.

---

## Scenario 2: Dashboard Blank — Targeted Diagnosis (edge case)

**Input**:
```
/observe-oci-workload rr-rest-proxy pillar:dashboards
```

**Context**: `func-rr-rest-proxy` is deployed and emitting metrics, but the Management Dashboard
widget shows "internal error while adding widget". Dashboard was imported via Terraform last week.

**Expected agent behavior**:
1. P0: reads `docs/handoff/rr-rest-proxy/report-terraform-infra.md`; identifies dashboard pillar only;
   loads `monitoring-oci-apm-dashboards` skill.
2. P1: scans existing dashboard `.tf` for widget shape, `dataConfig.type`, `providerId`.
3. P2: notes the dashboard gotchas from the skill and instruction: `monitoringDataSource` widget must
   declare `regionName` parameter; `providerId` must be `management-dashboard` (not `oci-monitoring`).
4. P3: proposes targeted fix — either correct widget JSON in Terraform + `terraform apply -replace=` or
   run `check-dashboards.sh` to diagnose which widget is failing. States the postmortem incident date.
   Waits for approval.
5. P4: generates corrected JSON patch and/or instructs how to run `check-dashboards.sh --name-filter "REST Proxy"`.
6. P5: instructs running `generate-dashboard-traffic.sh` as precondition (to populate time-series),
   then `check-dashboards.sh` to verify render-readiness.

**Pass criteria**:
- Agent surfaces the `regionName` parameter gotcha and `write-once` + `terraform apply -replace=` requirement.
- Agent mentions `generate-dashboard-traffic.sh` as the precondition step before validating dashboards.
- Agent does NOT double-load `provisioning-oci-apm` + `provisioning-oci-logging` (composition note).

---

## Scenario 3: Alarm Not Firing — Dimension Diagnosis (misuse guard)

**Input**:
```
/observe-oci-workload event-producer pillar:alarms
```

**Context**: An alarm `FunctionErrorCount[1m]{functionId="ocid1.fnfunc..."}` is configured but
never transitions to FIRING even when the function throws exceptions.

**Expected agent behavior**:
1. P0: loads `configuring-oci-monitoring-alarms` and `monitoring-oci-java-functions` skills.
2. P1: finds the alarm definition in `.tf`; identifies `functionId` dimension (does not exist in `oci_faas`).
3. P2: extracts the ⚡ Live-validated gotcha: valid dimensions are `resourceId` (Function OCID) or `applicationId` (Application OCID); `functionId` is silently invalid — alarm never fires, no error from OCI.
4. P3: proposes correcting the MQL query to use `resourceId` or `applicationId`; presents the corrected `query` string. Waits for approval.
5. P4: generates the corrected alarm `.tf` block; ensures `pending_duration = "PT2M"`.
6. P5: provides OCI CLI command to verify the metric dimension exists:
   `oci monitoring metric-data summarize-metrics-data --namespace oci_faas --query-text 'FunctionErrorCount[1m]{resourceId="<fn-ocid>"}.sum()'`
   and instructs running `check-alarms.sh` from `validating-oci-observability/scripts/`.

**Pass criteria**:
- Agent identifies `functionId` as invalid and proposes `resourceId` or `applicationId`.
- Agent does NOT generate code using `functionId`.
- Agent waits for P3 approval before writing corrected `.tf`.
- Verification step includes OCI CLI command and the `check-alarms.sh` script reference.

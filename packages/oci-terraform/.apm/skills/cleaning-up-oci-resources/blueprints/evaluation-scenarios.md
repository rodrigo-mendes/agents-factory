# Evaluation Scenarios — cleaning-up-oci-resources

---

## Scenario 1: Dry-run produces a resource inventory without deleting anything

**Input:**
```bash
export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<value>"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
export OCI_NAMESPACE="mynamespace"
./scripts/oci-cleanup.sh --dry-run
```

**Expected behavior:**
- Script starts and prints the header showing DRY-RUN mode.
- All 8 phases execute, printing `[FOUND]` and `[DRY-RUN] Would delete:` lines for discovered resources.
- No OCI CLI delete/update commands are issued.
- Summary prints total FOUND count and confirms DRY-RUN mode.
- Exit code 0.

**Pass criteria:**
- No `[DELETE]` lines appear in output.
- FOUND count > 0 when resources exist (or 0 with "Compartment is clean" when empty).
- Script does not prompt for confirmation in dry-run mode.

---

## Scenario 2: Missing required env var causes immediate exit with a clear error

**Input:**
```bash
# OCI_COMPARTMENT_OCID is intentionally unset
export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
export OCI_NAMESPACE="mynamespace"
./scripts/oci-cleanup.sh --dry-run
```

**Expected behavior:**
- Script exits immediately at the `: "${OCI_COMPARTMENT_OCID:?...}"` guard.
- Error message names the missing variable and describes its expected format.
- No OCI CLI calls are made.
- Exit code non-zero.

**Pass criteria:**
- Output contains `OCI_COMPARTMENT_OCID must be set`.
- No phase output appears.

---

## Scenario 3: Live run requires explicit DELETE confirmation before any deletion

**Input:**
```bash
export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<value>"
export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
export OCI_NAMESPACE="mynamespace"
echo "no" | ./scripts/oci-cleanup.sh
```

**Expected behavior:**
- Script prints the header showing LIVE mode and the WARNING block.
- Prompts: `Type 'DELETE' to confirm:`
- Input "no" is received → script prints "Aborted." and exits 0.
- No OCI resources are modified.

**Pass criteria:**
- No `[DELETE]` lines appear.
- Exit code 0 with "Aborted." message.

---

## Scenario 4: Vault/Secret scheduled deletion respects minimum pending periods

**Input:** Live run with `VAULT_DELETE_DAYS=7` (default) against a compartment with an active Vault.

**Expected behavior:**
- Phase 4 lists the vault as `[FOUND]`.
- Calls `oci kms vault schedule-vault-deletion` with `--time-of-deletion` set 7 days in the future.
- Does NOT call `oci kms vault delete` (which is rejected by OCI — vaults cannot be hard-deleted).
- Summary shows `[DELETE]` for the vault with "pending until <date>".

**Pass criteria:**
- `--time-of-deletion` argument is a valid ISO-8601 timestamp at least 7 days ahead.
- No immediate hard-delete call is made.
- `[FAIL]` count = 0 for vault phase.

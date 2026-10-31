#!/usr/bin/env python3
# ==============================================================================
# oci-cleanup.py — Remove all OCI resources in a given compartment
#
# Usage:
#   export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<value>"
#   export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
#   export OCI_NAMESPACE="<object-storage-namespace>"
#   python3 scripts/oci-cleanup.py              # Execute cleanup (requires confirmation)
#   python3 scripts/oci-cleanup.py --dry-run    # List resources only, no deletions
#
# Required environment variables:
#   OCI_COMPARTMENT_OCID   Compartment to clean   (e.g. ocid1.compartment.oc1....)
#   OCI_TENANCY_OCID       Root tenancy OCID      (e.g. ocid1.tenancy.oc1....)
#   OCI_NAMESPACE          Object Storage namespace
#
# Optional environment variables:
#   OCI_REGION             OCI region (default: sa-saopaulo-1)
#   OCI_PROFILE            OCI CLI profile name (default: DEFAULT)
#   OCI_AUTH               OCI CLI auth method  (default: api_key)
#   OCI_COMPARTMENT_NAME   Compartment display name for IAM filter (default: "")
#   OCI_PROJECT_FILTER     Regex for IAM / tenancy-level OCIR name filter (default: none; empty matches nothing)
#   VAULT_DELETE_DAYS      Days before vault deletion, min 7 (default: 7)
#   SECRET_DELETE_DAYS     Days before secret deletion, min 2 (default: 2)
#
# Test hooks (not needed in normal use):
#   OCI_CLEANUP_ALLOW_PIPE=1  accept a piped DELETE (offline tests only; never set it in real use)
#   OCI_CMD                OCI CLI command (default: oci), e.g. a fake for offline tests
#   OCI_CLEANUP_SLEEP_FACTOR  Multiplier for the retry/settle sleeps (default: 1)
#
# Exit codes (identical to the former oci-cleanup.sh): 0 = live run that deleted
# something with no failure, or aborted at the confirmation prompt; 1 = missing
# env var / OCI CLI, dry-run, or live run with failures or nothing deleted.
#
# Prerequisites: Python 3.8+, oci (CLI configured). Standard library only.
# ==============================================================================
"""Port of oci-cleanup.sh. Same phases, order, filters, prompts, output and exit codes."""

import datetime
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", newline="\n")  # LF + UTF-8 like the bash original
    except (AttributeError, ValueError):
        pass

RED, GREEN, YELLOW = "\033[0;31m", "\033[0;32m", "\033[1;33m"
BLUE, CYAN, NC = "\033[0;34m", "\033[0;36m", "\033[0m"
NO_DATA = '{"data":[]}'
NO_ITEMS = '{"data":{"items":[]}}'


class JqError(Exception):
    """A jq program/runtime error: the bash version printed nothing for that jq call."""


# --- Output helpers ------------------------------------------------------------
def echo(text=""):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


class Cleanup:
    def __init__(self, env, dry_run):
        self.compartment = env["OCI_COMPARTMENT_OCID"]
        self.tenancy = env["OCI_TENANCY_OCID"]
        self.namespace = env["OCI_NAMESPACE"]
        self.region = env.get("OCI_REGION") or "sa-saopaulo-1"
        self.profile = env.get("OCI_PROFILE") or "DEFAULT"
        self.auth = env.get("OCI_AUTH") or "api_key"
        self.compartment_name = env.get("OCI_COMPARTMENT_NAME") or ""
        # Safety (user decision 2026-10-28): no implicit default; unset or empty matches nothing.
        self.project_filter = env.get("OCI_PROJECT_FILTER") or ""
        self.vault_days = env.get("VAULT_DELETE_DAYS") or "7"
        self.secret_days = env.get("SECRET_DELETE_DAYS") or "2"
        try:
            self.sleep_factor = float(env.get("OCI_CLEANUP_SLEEP_FACTOR") or "1")
        except ValueError:
            self.sleep_factor = 1.0
        self.oci_cmd = split_cmd(env.get("OCI_CMD") or "oci")
        self.dry_run = dry_run
        self.found = self.deleted = self.failed = self.skipped = 0

    # --- logging (same texts/colors as the bash helpers) -------------------------
    def log_phase(self, title):
        echo("\n%s═══════════════════════════════════════════%s" % (BLUE, NC))
        echo("%s  Phase: %s%s" % (BLUE, title, NC))
        echo("%s═══════════════════════════════════════════%s" % (BLUE, NC))

    def log_info(self, msg):
        echo("%s  [INFO]%s %s" % (CYAN, NC, msg))

    def log_found(self, msg):
        echo("%s  [FOUND]%s %s" % (YELLOW, NC, msg))
        self.found += 1

    def log_delete(self, msg):
        echo("%s  [DELETE]%s %s" % (RED, NC, msg))
        self.deleted += 1

    def log_skip(self, msg):
        echo("%s  [SKIP]%s %s" % (GREEN, NC, msg))
        self.skipped += 1

    def log_fail(self, msg):
        echo("%s  [FAIL]%s %s" % (RED, NC, msg))
        self.failed += 1

    def log_dry(self, msg):
        echo("%s  [DRY-RUN]%s Would delete: %s" % (YELLOW, NC, msg))

    def log_none(self):
        echo("%s  [NONE]%s No resources found." % (GREEN, NC))

    def sleep(self, seconds):
        if self.sleep_factor > 0:
            time.sleep(seconds * self.sleep_factor)

    # --- OCI wrapper -------------------------------------------------------------
    def _argv(self, args):
        return self.oci_cmd + ["--profile", self.profile, "--auth", self.auth] + list(args)

    def oci_list(self, args, default=NO_DATA):
        """`$(oci ... 2>/dev/null || echo '<default>')` parsed as a jq input stream."""
        rc, out = self.oci_capture(args)
        return parse_docs(out if rc == 0 else out + default + "\n")

    def oci_capture(self, args):
        try:
            proc = subprocess.run(self._argv(args), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return 127, ""
        return proc.returncode, proc.stdout.decode("utf-8", "replace")

    def oci_quiet(self, args):
        """`oci ... &>/dev/null` -> exit status."""
        try:
            return subprocess.run(self._argv(args), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
        except OSError:
            return 127

    def oci_stdout(self, args):
        """`oci ... 2>/dev/null` (stdout still shown) -> exit status."""
        sys.stdout.flush()
        try:
            proc = subprocess.run(self._argv(args), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError:
            return 127
        if proc.stdout:
            sys.stdout.write(proc.stdout.decode("utf-8", "replace"))
            sys.stdout.flush()
        return proc.returncode

    def delete_with_retry(self, args, label, retries=1, delay=30):
        for i in range(1, retries + 1):
            if self.oci_quiet(args) == 0:
                self.log_delete(label)
                return
            if i < retries:
                self.log_info("Retry %d/%d for %s (%ds)..." % (i, retries, label, delay))
                self.sleep(delay)
        self.log_fail(label)

    def delete_or_dry(self, dry_label, args, label, retries=1, delay=30):
        if self.dry_run:
            self.log_dry(dry_label)
        else:
            self.delete_with_retry(args, label, retries, delay)

    # ==========================================================================
    # Phase 1: Monitoring & Observability
    # ==========================================================================
    def cleanup_observability(self):
        self.log_phase("1/8 — Observability (Alarms, Logs, Notifications)")
        c = self.compartment

        alarms = self.oci_list(["monitoring", "alarm", "list", "--compartment-id", c, "--all"])
        alarm_ids = extract_ids(alarms)
        if not alarm_ids:
            self.log_none()
        for ident in alarm_ids:
            name = lookup(alarms, ident)
            self.log_found("Alarm: %s" % name)
            self.delete_or_dry("Alarm %s" % name,
                               ["monitoring", "alarm", "delete", "--alarm-id", ident, "--force"], "Alarm: %s" % name)

        log_groups = self.oci_list(["logging", "log-group", "list", "--compartment-id", c, "--all"])
        lg_ids = extract_ids(log_groups)
        if not lg_ids:
            self.log_none()
        for lg_id in lg_ids:
            lg_name = lookup(log_groups, lg_id)
            self.log_found("Log Group: %s" % lg_name)
            logs = self.oci_list(["logging", "log", "list", "--log-group-id", lg_id, "--all"])
            for log_id in extract_ids(logs):
                log_name = lookup(logs, log_id)
                self.log_found("  Log: %s" % log_name)
                self.delete_or_dry("Log %s" % log_name,
                                   ["logging", "log", "delete", "--log-group-id", lg_id, "--log-id", log_id, "--force"],
                                   "Log: %s" % log_name)
            self.delete_or_dry("Log Group %s" % lg_name,
                               ["logging", "log-group", "delete", "--log-group-id", lg_id, "--force"],
                               "Log Group: %s" % lg_name)

        topics = self.oci_list(["ons", "topic", "list", "--compartment-id", c, "--all"])
        topic_ids = extract_ids(topics, "topic-id")
        if not topic_ids:
            self.log_none()
        for topic_id in topic_ids:
            topic_name = lookup(topics, topic_id, ("name",), id_key="topic-id")
            self.log_found("Topic: %s" % topic_name)
            subs = self.oci_list(["ons", "subscription", "list", "--compartment-id", c, "--topic-id", topic_id, "--all"])
            for sub_id in extract_ids(subs):
                self.log_found("  Subscription: %s" % sub_id)
                self.delete_or_dry("Subscription %s" % sub_id,
                                   ["ons", "subscription", "delete", "--subscription-id", sub_id, "--force"],
                                   "Subscription: %s" % sub_id)
            self.delete_or_dry("Topic %s" % topic_name, ["ons", "topic", "delete", "--topic-id", topic_id, "--force"],
                               "Topic: %s" % topic_name)

    # ==========================================================================
    # Phase 2: API Gateway
    # ==========================================================================
    def cleanup_apigateway(self):
        self.log_phase("2/8 — API Gateway (Deployments, Gateways)")
        c = self.compartment
        wait = ["--force", "--wait-for-state", "SUCCEEDED", "--wait-interval-seconds", "5"]

        deployments = self.oci_list(["apigateway", "deployment", "list", "--compartment-id", c, "--all"])
        dep_ids = extract_ids(deployments)
        if not dep_ids:
            self.log_none()
        for ident in dep_ids:
            name = lookup(deployments, ident)
            self.log_found("Deployment: %s" % name)
            self.delete_or_dry("Deployment %s" % name,
                               ["apigateway", "deployment", "delete", "--deployment-id", ident] + wait,
                               "Deployment: %s" % name, 2, 15)

        gateways = self.oci_list(["apigateway", "gateway", "list", "--compartment-id", c, "--all"])
        gw_ids = extract_ids(gateways)
        if not gw_ids:
            self.log_none()
        for ident in gw_ids:
            name = lookup(gateways, ident)
            self.log_found("Gateway: %s" % name)
            self.delete_or_dry("Gateway %s" % name, ["apigateway", "gateway", "delete", "--gateway-id", ident] + wait,
                               "Gateway: %s" % name, 2, 20)

    # ==========================================================================
    # Phase 3: Functions
    # ==========================================================================
    def cleanup_functions(self):
        self.log_phase("3/8 — Functions (Functions, Applications)")
        apps = self.oci_list(["fn", "application", "list", "--compartment-id", self.compartment, "--all"])
        app_ids = extract_ids(apps)
        if not app_ids:
            self.log_none()
            return
        for app_id in app_ids:
            app_name = lookup(apps, app_id)
            self.log_found("Application: %s" % app_name)
            funcs = self.oci_list(["fn", "function", "list", "--application-id", app_id, "--all"])
            for fn_id in extract_ids(funcs):
                fn_name = lookup(funcs, fn_id)
                self.log_found("  Function: %s" % fn_name)
                self.delete_or_dry("Function %s" % fn_name, ["fn", "function", "delete", "--function-id", fn_id, "--force"],
                                   "Function: %s" % fn_name)
            if self.dry_run:
                self.log_dry("Application %s" % app_name)
            else:
                self.sleep(5)
                self.delete_with_retry(["fn", "application", "delete", "--application-id", app_id, "--force"],
                                       "Application: %s" % app_name, 3, 10)

    # ==========================================================================
    # Phase 4: Vault & Secrets
    # ==========================================================================
    def cleanup_vault(self):
        self.log_phase("4/8 — Vault & Secrets (scheduled deletion)")
        date_secret = deletion_date(self.secret_days)
        date_vault = deletion_date(self.vault_days)

        secrets = self.oci_list(["vault", "secret", "list", "--compartment-id", self.compartment, "--all"])
        active_secrets = [s for s in jq_iter_data(secrets)
                          if isinstance(s, dict) and s.get("lifecycle-state") not in ("DELETED", "PENDING_DELETION")]
        secret_ids = ids_of(active_secrets)
        if not secret_ids:
            self.log_none()
        for ident in secret_ids:
            name = lookup_in(active_secrets, ident, ("secret-name",))
            self.log_found("Secret: %s (pending %sd)" % (name, self.secret_days))
            if self.dry_run:
                self.log_dry("Secret %s → schedule %s" % (name, date_secret))
            elif self.oci_quiet(["vault", "secret", "schedule-secret-deletion", "--secret-id", ident,
                                 "--time-of-deletion", date_secret]) == 0:
                self.log_delete("Secret: %s (pending until %s)" % (name, date_secret))
            else:
                self.log_fail("Secret: %s" % name)

        vaults = self.oci_list(["kms", "vault", "list", "--compartment-id", self.compartment, "--all"])
        active_vaults = [v for v in jq_iter_data(vaults)
                         if isinstance(v, dict) and v.get("lifecycle-state") in ("ACTIVE", "CREATING")]
        vault_ids = ids_of(active_vaults)
        if not vault_ids:
            self.log_none()
        for ident in vault_ids:
            name = lookup_in(active_vaults, ident, ("display-name",))
            self.log_found("Vault: %s (pending %sd)" % (name, self.vault_days))
            if self.dry_run:
                self.log_dry("Vault %s → schedule %s" % (name, date_vault))
            elif self.oci_quiet(["kms", "vault", "schedule-vault-deletion", "--vault-id", ident,
                                 "--time-of-deletion", date_vault]) == 0:
                self.log_delete("Vault: %s (pending until %s)" % (name, date_vault))
            else:
                self.log_fail("Vault: %s" % name)

    # ==========================================================================
    # Phase 5: Object Storage
    # ==========================================================================
    def cleanup_objectstorage(self):
        self.log_phase("5/8 — Object Storage (Buckets)")
        ns = self.namespace
        buckets = self.oci_list(["os", "bucket", "list", "--compartment-id", self.compartment, "--namespace-name", ns])
        names = [n for n in (jq_str(alt(b, "name")) for b in jq_iter_data(buckets) if isinstance(b, dict)) if n]
        if not names:
            self.log_none()
            return
        for name in names:
            self.log_found("Bucket: %s" % name)
            if self.dry_run:
                self.log_dry("Bucket %s" % name)
                continue
            self.oci_quiet(["os", "object", "bulk-delete", "--bucket-name", name, "--namespace-name", ns, "--force"])
            if self.oci_quiet(["os", "bucket", "delete", "--bucket-name", name, "--namespace-name", ns, "--force"]) == 0:
                self.log_delete("Bucket: %s" % name)
            else:
                self.log_fail("Bucket: %s" % name)

    # ==========================================================================
    # Phase 6: Networking
    # ==========================================================================
    def cleanup_networking(self):
        self.log_phase("6/8 — Networking (NSGs, Subnets, Route Tables, Gateways, VCN)")
        c = self.compartment
        vcns = self.oci_list(["network", "vcn", "list", "--compartment-id", c, "--all"])
        vcn_ids = extract_ids(vcns)
        if not vcn_ids:
            self.log_none()
            return
        for vcn_id in vcn_ids:
            vcn_name = lookup(vcns, vcn_id)
            default_rt = lookup(vcns, vcn_id, ("default-route-table-id",), fallback_id=False)
            default_sl = lookup(vcns, vcn_id, ("default-security-list-id",), fallback_id=False)
            self.log_found("VCN: %s" % vcn_name)
            scope = ["--compartment-id", c, "--vcn-id", vcn_id, "--all"]

            nsgs = self.oci_list(["network", "nsg", "list"] + scope)
            for nsg_id in extract_ids(nsgs):
                nsg_name = lookup(nsgs, nsg_id)
                self.log_found("  NSG: %s" % nsg_name)
                rule_ids = extract_ids(self.oci_list(["network", "nsg", "rules", "list", "--nsg-id", nsg_id, "--all"]))
                if rule_ids and not self.dry_run:
                    self.oci_quiet(["network", "nsg", "rules", "remove", "--nsg-id", nsg_id,
                                    "--security-rule-ids", json.dumps(rule_ids, separators=(",", ":"))])
                self.delete_or_dry("NSG %s" % nsg_name, ["network", "nsg", "delete", "--nsg-id", nsg_id, "--force"],
                                   "NSG: %s" % nsg_name, 3, 10)

            subnets = self.oci_list(["network", "subnet", "list"] + scope)
            for subnet_id in extract_ids(subnets):
                subnet_name = lookup(subnets, subnet_id)
                self.log_found("  Subnet: %s" % subnet_name)
                self.delete_or_dry("Subnet %s" % subnet_name,
                                   ["network", "subnet", "delete", "--subnet-id", subnet_id, "--force",
                                    "--wait-for-state", "TERMINATED", "--wait-interval-seconds", "5"],
                                   "Subnet: %s" % subnet_name, 5, 30)

            rts = self.oci_list(["network", "route-table", "list"] + scope)
            for rt_id in extract_ids(rts):
                if rt_id == default_rt:
                    self.log_skip("  Default RT (deleted with VCN)")
                    continue
                rt_name = lookup(rts, rt_id)
                self.log_found("  Route Table: %s" % rt_name)
                if self.dry_run:
                    self.log_dry("Route Table %s" % rt_name)
                else:
                    self.oci_quiet(["network", "route-table", "update", "--rt-id", rt_id, "--route-rules", "[]", "--force"])
                    self.delete_with_retry(["network", "route-table", "delete", "--rt-id", rt_id, "--force"],
                                           "Route Table: %s" % rt_name, 2, 10)

            sls = self.oci_list(["network", "security-list", "list"] + scope)
            for sl_id in extract_ids(sls):
                if sl_id == default_sl:
                    self.log_skip("  Default SL (deleted with VCN)")
                    continue
                sl_name = lookup(sls, sl_id)
                self.log_found("  Security List: %s" % sl_name)
                self.delete_or_dry("Security List %s" % sl_name,
                                   ["network", "security-list", "delete", "--security-list-id", sl_id, "--force"],
                                   "Security List: %s" % sl_name, 2, 10)

            for gw_type, id_flag in (("internet-gateway", "--ig-id"), ("nat-gateway", "--nat-gateway-id"),
                                     ("service-gateway", "--service-gateway-id")):
                gws = self.oci_list(["network", gw_type, "list"] + scope)
                for gw_id in extract_ids(gws):
                    self.log_found("  %s: %s" % (gw_type, gw_id))
                    self.delete_or_dry("%s %s" % (gw_type, gw_id),
                                       ["network", gw_type, "delete", id_flag, gw_id, "--force"], gw_type, 2, 10)

            self.delete_or_dry("VCN %s" % vcn_name,
                               ["network", "vcn", "delete", "--vcn-id", vcn_id, "--force",
                                "--wait-for-state", "TERMINATED", "--wait-interval-seconds", "5"],
                               "VCN: %s" % vcn_name, 3, 20)

    # ==========================================================================
    # Phase 7: IAM (compartment + tenancy root, filtered)
    # ==========================================================================
    def cleanup_iam(self):
        self.log_phase("7/8 — IAM (Policies, Dynamic Groups)")

        # Compartment-level policies
        policies = self.oci_list(["iam", "policy", "list", "--compartment-id", self.compartment, "--all"])
        for ident in extract_ids(policies):
            name = lookup(policies, ident, ("name",))
            self.log_found("Policy (compartment): %s" % name)
            self.delete_or_dry("Policy %s" % name, ["iam", "policy", "delete", "--policy-id", ident, "--force"],
                               "Policy: %s" % name)

        # Tenancy-root policies filtered by project name or compartment OCID in statements
        tenancy_policies = self.oci_list(["iam", "policy", "list", "--compartment-id", self.tenancy, "--all"])
        pol_ids = filter_tenancy_policies(tenancy_policies, self.project_filter, self.compartment_name,
                                          self.compartment)
        if not pol_ids:
            self.log_info("No tenancy-level policies matching filter")
        for ident in pol_ids:
            name = lookup(tenancy_policies, ident, ("name",))
            self.log_found("Policy (tenancy): %s" % name)
            self.delete_or_dry("Policy %s" % name, ["iam", "policy", "delete", "--policy-id", ident, "--force"],
                               "Policy: %s" % name)

        # Dynamic groups (tenancy level, filtered)
        dgs = self.oci_list(["iam", "dynamic-group", "list", "--compartment-id", self.tenancy, "--all"])
        dg_ids = filter_dynamic_groups(dgs, self.project_filter, self.compartment)
        if not dg_ids:
            self.log_info("No dynamic groups matching '%s'" % self.project_filter)
        for ident in dg_ids:
            name = lookup(dgs, ident, ("name",))
            self.log_found("Dynamic Group: %s" % name)
            self.delete_or_dry("Dynamic Group %s" % name,
                               ["iam", "dynamic-group", "delete", "--dynamic-group-id", ident, "--force"],
                               "Dynamic Group: %s" % name)

    # ==========================================================================
    # Phase 8: OCIR (Container Registry)
    # ==========================================================================
    def cleanup_ocir(self):
        self.log_phase("8/8 — OCIR (Container Images & Repositories)")
        repos = self.oci_list(["artifacts", "container", "repository", "list", "--compartment-id", self.compartment,
                               "--all"], NO_ITEMS)
        repo_data = repo_lines(repos)
        if not repo_data and not self.project_filter.strip():
            self.log_info("No compartment repositories; tenancy-level search skipped (OCI_PROJECT_FILTER is empty)")
        elif not repo_data:
            self.log_info("Trying tenancy-level search (filter: %s)..." % self.project_filter)
            repos = self.oci_list(["artifacts", "container", "repository", "list", "--compartment-id", self.tenancy,
                                   "--all"], NO_ITEMS)
            repo_data = repo_lines(repos, self.project_filter)
        if not repo_data:
            self.log_none()
            return

        for line in repo_data:
            repo_id, _sep, repo_name = line.partition("|")
            if not repo_id:
                continue
            self.log_found("Repository: %s" % repo_name)
            images = self.image_list(repo_name)
            items = list_items(images)
            for img_id in ids_of(items):
                img_ver = lookup_in(items, img_id, ("version",))
                self.log_found("  Image: %s:%s" % (repo_name, img_ver))
                if self.dry_run:
                    self.log_dry("Image %s:%s" % (repo_name, img_ver))
                    continue
                if self.oci_stdout(["artifacts", "container", "image", "delete", "--image-id", img_id, "--force"]) == 0:
                    self.log_delete("Image: %s:%s" % (repo_name, img_ver))
                else:
                    self.log_fail("Image: %s:%s" % (repo_name, img_ver))
                self.sleep(1)
            if self.dry_run:
                self.log_dry("Repository %s" % repo_name)
            else:
                self.sleep(2)
                if self.oci_stdout(["artifacts", "container", "repository", "delete", "--repository-id", repo_id,
                                    "--force"]) == 0:
                    self.log_delete("Repository: %s" % repo_name)
                else:
                    self.log_fail("Repository: %s" % repo_name)

    def image_list(self, repo_name):
        """compartment list || tenancy list || '{"data":{"items":[]}}'."""
        out = ""
        for comp in (self.compartment, self.tenancy):
            rc, part = self.oci_capture(["artifacts", "container", "image", "list", "--compartment-id", comp,
                                         "--repository-name", repo_name, "--all"])
            out += part
            if rc == 0:
                return parse_docs(out)
        return parse_docs(out + NO_ITEMS + "\n")

    # ==========================================================================
    # Main
    # ==========================================================================
    def banner(self):
        echo(BLUE)
        echo("╔═══════════════════════════════════════════════════════════╗")
        echo("║           OCI RESOURCE CLEANUP                           ║")
        echo("╠═══════════════════════════════════════════════════════════╣")
        echo("║  Compartment: %-44s ║" % (self.compartment_name or self.compartment[:44]))
        echo("║  Region:      %-44s ║" % self.region)
        echo("║  Namespace:   %-44s ║" % self.namespace)
        if self.dry_run:
            echo("║  Mode:        %sDRY-RUN (no deletions)%s                  ║" % (YELLOW, BLUE))
        else:
            echo("║  Mode:        %sLIVE (resources WILL be deleted)%s         ║" % (RED, BLUE))
        echo("╚═══════════════════════════════════════════════════════════╝")
        echo(NC)

    def confirm(self):
        """Live mode only: anything but 'DELETE' aborts with exit 0 (same as `read -rp`)."""
        echo("%sWARNING: This PERMANENTLY deletes OCI resources.%s" % (RED, NC))
        echo("%s  Vault/Secrets: pending-deletion (%sd/%sd).%s" % (RED, self.vault_days, self.secret_days, NC))
        echo("%s  All other resources: IRREVERSIBLE.%s\n" % (RED, NC))
        prompt = "Type 'DELETE' to confirm: "
        # Safety (2026-10-29): the confirmation must be typed by a person at a terminal. Piped input
        # (e.g. `echo DELETE | ...` from an agent) aborts, unless the offline test harness opts in.
        interactive = sys.stdin is not None and sys.stdin.isatty()
        if not interactive and os.environ.get("OCI_CLEANUP_ALLOW_PIPE") != "1":
            echo("%sAborted: the live run needs DELETE typed at an interactive terminal (stdin is not a TTY).%s"
                 % (RED, NC))
            return False
        if interactive:
            sys.stderr.write(prompt)
            sys.stderr.flush()
        try:
            line = sys.stdin.readline() if sys.stdin is not None else ""
        except (OSError, ValueError):
            line = ""
        return line.rstrip("\n").strip(" \t") == "DELETE"

    def summary(self):
        echo("\n%s═══════════════════════════════════════════════════════════%s" % (BLUE, NC))
        echo("%s  SUMMARY%s" % (BLUE, NC))
        echo("%s═══════════════════════════════════════════════════════════%s" % (BLUE, NC))
        echo("  Found:   %s%d%s" % (YELLOW, self.found, NC))
        if self.dry_run:
            echo("  Mode:    %sDRY-RUN — nothing deleted%s" % (YELLOW, NC))
        else:
            echo("  Deleted: %s%d%s  Failed: %s%d%s  Skipped: %s%d%s" % (
                GREEN, self.deleted, NC, RED, self.failed, NC, CYAN, self.skipped, NC))
        echo("")
        if self.found == 0:
            echo("%sCompartment is clean.%s" % (GREEN, NC))
        if self.dry_run and self.found > 0:
            echo("%sRe-run without --dry-run to execute.%s" % (YELLOW, NC))
        if not self.dry_run and self.failed == 0 and self.deleted > 0:
            echo("%sCleanup complete.%s" % (GREEN, NC))
            echo("  Vault/Secrets fully deleted in %sd/%sd." % (self.vault_days, self.secret_days))
            echo("  Local state: rm -f infra/environments/dev/terraform.tfstate*")
            return 0
        return 1  # status of the last `&&` list in the bash main()

    def run(self):
        self.banner()
        if not self.dry_run:
            if not self.confirm():
                echo("Aborted.")
                return 0
            echo("")
        phases = (self.cleanup_observability, self.cleanup_apigateway, self.cleanup_functions, self.cleanup_vault,
                  self.cleanup_objectstorage, self.cleanup_networking, self.cleanup_iam, self.cleanup_ocir)
        for number, phase in enumerate(phases, 1):
            try:
                phase()
            except Exception:  # noqa: BLE001 — same "continue with the next phase" policy as the bash version
                self.log_fail("Phase %d errors — continuing" % number)
        return self.summary()


# --- jq emulation helpers (same selection semantics as the bash/jq filters) -----
def split_cmd(value):
    if os.name == "nt":
        parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] == '"' else p for p in shlex.split(value, posix=False)]
    else:
        parts = shlex.split(value)
    if parts:
        resolved = shutil.which(parts[0])
        if resolved:
            parts[0] = resolved
    return parts


def parse_docs(text):
    """JSON values in a jq input stream; stops at the first parse error (jq prints what it had)."""
    decoder, docs, idx = json.JSONDecoder(), [], 0
    while True:
        while idx < len(text) and text[idx].isspace():
            idx += 1
        if idx >= len(text):
            return docs
        try:
            doc, idx = decoder.raw_decode(text, idx)
        except ValueError:
            return docs
        docs.append(doc)


def alt(obj, *keys):
    """`.k1 // .k2 // ...` on an object (None when every key is null/false/missing)."""
    for key in keys:
        value = obj.get(key) if isinstance(obj, dict) else None
        if value is not None and value is not False:
            return value
    return None


def jq_str(value):
    """`jq -r` rendering of a scalar."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"))


def iter_values(container):
    if isinstance(container, list):
        return list(container)
    if isinstance(container, dict):
        return list(container.values())
    raise JqError("cannot iterate")


def jq_iter_data(docs):
    """`.data // [] | .[]` over every document."""
    out = []
    for doc in docs:
        try:
            data = alt(doc, "data") if isinstance(doc, dict) else None
            if not isinstance(doc, dict):
                raise JqError("cannot index")
            out.extend(iter_values(data if data is not None else []))
        except JqError:
            break
    return out


def list_items(docs):
    """`.data.items // .data // [] | .[]` over every document."""
    out = []
    for doc in docs:
        data = doc.get("data") if isinstance(doc, dict) else None
        chosen = None
        if isinstance(data, dict) and alt(data, "items") is not None:
            chosen = data["items"]
        elif data is not None and data is not False:
            chosen = data
        try:
            out.extend(iter_values(chosen if chosen is not None else []))
        except JqError:
            break
    return out


def ids_of(items, key="id"):
    """`.[].<key> // empty` -> non-empty raw strings."""
    result = []
    for item in items:
        if not isinstance(item, dict):
            break
        value = jq_str(alt(item, key))
        if value:
            result.extend(line for line in value.split("\n") if line)
    return result


def extract_ids(docs, key="id"):
    return ids_of(jq_iter_data(docs), key)


def lookup_in(items, ident, name_keys=("display-name",), id_key="id", fallback_id=True):
    """`.[] | select(.id==$id) | .<name> // .id` (one line per match)."""
    keys = tuple(name_keys) + ((id_key,) if fallback_id else ())
    names = [jq_str(alt(i, *keys)) for i in items if isinstance(i, dict) and jq_str(i.get(id_key)) == ident]
    return "\n".join(names)


def lookup(docs, ident, name_keys=("display-name",), id_key="id", fallback_id=True):
    items = []
    for doc in docs:
        data = doc.get("data") if isinstance(doc, dict) else None
        try:
            items.extend(iter_values(data))
        except JqError:
            break
    return lookup_in(items, ident, name_keys, id_key, fallback_id)


_JQ_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}


def jq_literal(raw):
    """Value of `"<raw>"` as a jq string literal (the bash script interpolated env vars into the jq program)."""
    out, i = [], 0
    while i < len(raw):
        ch = raw[i]
        if ch == '"':
            raise JqError("unterminated literal")
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        nxt = raw[i + 1] if i + 1 < len(raw) else ""
        if nxt in _JQ_ESCAPES:
            out.append(_JQ_ESCAPES[nxt])
            i += 2
        elif nxt == "u" and re.fullmatch(r"[0-9a-fA-F]{4}", raw[i + 2:i + 6] or ""):
            out.append(chr(int(raw[i + 2:i + 6], 16)))
            i += 6
        else:
            raise JqError("invalid escape")
    return "".join(out)


def compile_regex(raw, flags=0):
    try:
        return re.compile(jq_literal(raw), flags)
    except re.error as exc:
        raise JqError(str(exc)) from exc


def jq_test(pattern, value):
    if not isinstance(value, str):
        raise JqError("cannot be matched, as it is not a string")
    return pattern.search(value) is not None


def compile_filter(raw, flags=0):
    """Like compile_regex, but an empty or blank filter is None and matches nothing.

    Safety change (user decision 2026-10-28): the bash/jq version treated an empty filter as an empty
    regex, which matched every statement, so an empty OCI_COMPARTMENT_NAME selected every tenancy policy
    (admin policies included). Identity filters must never widen on an empty value.
    """
    if raw is None or not str(raw).strip():
        return None
    return compile_regex(raw, flags)


def filter_test(pattern, value):
    """jq_test for compile_filter results: a None pattern never matches."""
    if pattern is None:
        return False
    return jq_test(pattern, value)


def filter_tenancy_policies(docs, project_filter, compartment_name, compartment_ocid):
    """select((.name|test(PF;"i")) or (.statements[]?|test(NAME;"i")) or (.statements[]?|test(OCID))) | .id, sort -u.

    An empty filter matches nothing (compile_filter): an empty OCI_COMPARTMENT_NAME no longer selects
    every tenancy policy.
    """
    try:
        by_name = compile_filter(project_filter, re.IGNORECASE)
        by_comp_name = compile_filter(compartment_name, re.IGNORECASE)
        by_ocid = compile_filter(compartment_ocid)
    except JqError:
        return []
    selected = set()
    try:
        for pol in jq_iter_data(docs):
            if not isinstance(pol, dict):
                raise JqError("cannot index")
            statements = pol.get("statements")
            statements = statements if isinstance(statements, list) else []
            if (filter_test(by_name, pol.get("name"))
                    or any(filter_test(by_comp_name, s) for s in statements)
                    or any(filter_test(by_ocid, s) for s in statements)):
                selected.add(jq_str(pol.get("id")))
    except JqError:
        pass
    return sorted(i for i in selected if i)


def filter_dynamic_groups(docs, project_filter, compartment_ocid):
    """select((.name|test(PF;"i")) or (."matching-rule" // "" | test(OCID))) | .id, sort -u."""
    try:
        by_name = compile_filter(project_filter, re.IGNORECASE)
        by_ocid = compile_filter(compartment_ocid)
    except JqError:
        return []
    selected = set()
    try:
        for dg in jq_iter_data(docs):
            if not isinstance(dg, dict):
                raise JqError("cannot index")
            rule = alt(dg, "matching-rule")
            if filter_test(by_name, dg.get("name")) or filter_test(by_ocid, rule if rule is not None else ""):
                selected.add(jq_str(dg.get("id")))
    except JqError:
        pass
    return sorted(i for i in selected if i)


def repo_lines(docs, name_filter=None):
    """"\\(.id)|\\(.display-name // .repository-name // .id)" per repository (optionally name-filtered)."""
    pattern = None
    if name_filter is not None:
        try:
            pattern = compile_regex(name_filter)
        except JqError:
            return []
    lines = []
    try:
        for repo in list_items(docs):
            if not isinstance(repo, dict):
                raise JqError("cannot index")
            if pattern is not None:
                shown = alt(repo, "display-name", "repository-name")
                if not jq_test(pattern, shown if shown is not None else ""):
                    continue
            ident, shown = repo.get("id"), alt(repo, "display-name", "repository-name", "id")
            lines.append("%s|%s" % ("null" if ident is None else jq_str(ident),
                                    "null" if shown is None else jq_str(shown)))
    except JqError:
        pass
    return lines


def deletion_date(days):
    """`date -u -d "+N days" +%Y-%m-%dT%H:%M:%SZ` ("" when N is not an integer, like a failed `date`)."""
    try:
        delta = datetime.timedelta(days=int(days))
    except ValueError:
        sys.stderr.write("date: invalid date '+%s days'\n" % days)
        return ""
    return (datetime.datetime.now(datetime.timezone.utc) + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv):
    script = os.path.basename(__file__)
    # --- Validate required env vars (same messages/exit code as `: "${VAR:?msg}"`) ---
    for var, msg in (("OCI_COMPARTMENT_OCID", "OCI_COMPARTMENT_OCID must be set (ocid1.compartment.oc1....)"),
                     ("OCI_TENANCY_OCID", "OCI_TENANCY_OCID must be set (ocid1.tenancy.oc1....)"),
                     ("OCI_NAMESPACE", "OCI_NAMESPACE must be set (Object Storage namespace)")):
        if not os.environ.get(var):
            sys.stderr.write("%s: %s: %s\n" % (script, var, msg))
            return 1

    dry_run = bool(argv) and argv[0] == "--dry-run"
    cleanup = Cleanup(os.environ, dry_run)

    # --- check_deps -------------------------------------------------------------
    if not cleanup.oci_cmd or not (shutil.which(cleanup.oci_cmd[0]) or os.path.isfile(cleanup.oci_cmd[0])):
        sys.stderr.write("%sERROR: '%s' not installed%s\n" % (RED, os.environ.get("OCI_CMD") or "oci", NC))
        return 1

    try:
        return cleanup.run()
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

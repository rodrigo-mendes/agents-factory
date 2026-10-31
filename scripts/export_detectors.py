#!/usr/bin/env python3
"""
Sensitive-data detectors used by scripts/export-bundle.py before anything is packaged for sale.

Each detector returns findings as (detector, matched text). A file with any finding blocks the export of
its bundle. The allow-lists below are the documented placeholders and official examples; extend them
here (never in the caller) when a new placeholder is introduced.

Run directly to scan a tree and print every finding (apm.yml manifests are skipped: they are never
exported):
    python scripts/export_detectors.py packages --skip third-party
"""
import re
import sys
from pathlib import Path

# --- 1. client, employer and author names --------------------------------------------------------------
CLIENT_RE = re.compile(r"(?i)(\bbrx\w*|\w*brx\b|rgbu-rex|rex-npe|mapfre|accenture"
                       r"|\brodrigo\b|dos[ ._-]santos[ ._-]mendes|r\.dos\.santos)")

# --- 2. e-mail addresses --------------------------------------------------------------------------------
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})\b")
EMAIL_ALLOWED_DOMAINS = {
    "example.com", "example.org", "example.net", "example.invalid", "company.com",
    "github.com", "users.noreply.github.com", "anthropic.com", "localhost",
}

# --- 3. real OCI identifiers (the random tail of a real OCID is 40+ chars) ------------------------------
OCID_RE = re.compile(r"\bocid1\.[a-z0-9]+\.oc[0-9]+\.[a-z0-9-]*\.{1,2}[a-z0-9]{40,}\b")

# --- 4. real OCIR / Object Storage namespace ------------------------------------------------------------
OCIR_RE = re.compile(r"\b[a-z]{2,4}\.ocir\.io/([A-Za-z0-9_-]+)")
OCIR_ALLOWED = {"namespace", "tenancyns", "tenancy-namespace", "mytenancy", "my-namespace", "ns", "your-namespace"}

# --- 5. real service hosts (random-looking id before the service part) ----------------------------------
HOST_RE = re.compile(
    r"\b[a-z0-9]{20,}\.(?:apigateway|apm-agt|functions|streaming)\.[a-z0-9-]+\.oci\.(?:customer-oci|oraclecloud)\.com\b"
    r"|\bidcs-[0-9a-f]{20,}\.identity\.oraclecloud\.com\b")  # a tenancy's real IDCS domain

# --- 6. real AWS account ids (only where an account id is expected) -------------------------------------
AWS_ACCOUNT_RES = [
    re.compile(r"arn:aws[a-z-]*:[a-z0-9-]*:[a-z0-9-]*:(\d{12}):"),
    re.compile(r"(?i)account[_ -]?id[\"'`]?\s*[:=]\s*[\"'`]?(\d{12})\b"),
    re.compile(r"\b(\d{12})\.dkr\.ecr\."),
]
AWS_ACCOUNT_ALLOWED = {
    "111122223333", "123456789012", "444455556666", "555555555555", "111111111111", "222222222222",
    "333333333333", "444444444444", "999999999999", "000000000000", "123456789101", "210987654321",
    "012345678901", "777788889999",
}

# --- 7. keys and tokens ----------------------------------------------------------------------------------
KEY_RES = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bsk_live_[0-9A-Za-z]{10,}"),
    re.compile(r"\bgh[pousr]_[0-9A-Za-z]{30,}"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}"),
]

# --- 8. paths of a real machine user ---------------------------------------------------------------------
PATH_RES = [
    re.compile(r"(?i)\bC:\\{1,2}Users\\{1,2}([A-Za-z0-9._-]+)"),
    re.compile(r"(?i)\bC:/Users/([A-Za-z0-9._-]+)"),
    re.compile(r"(?<![\w.])/Users/([A-Za-z0-9._-]+)"),
    re.compile(r"(?<![\w.])/home/([A-Za-z0-9._-]+)"),
]
PATH_ALLOWED_USERS = {
    "user", "username", "you", "me", "runner", "runneradmin", "ubuntu", "ec2-user", "app", "node",
    "public", "default", "opc", "<user>", "your-user", "yourname", "dev", "...", "…",
}

DETECTORS = ["client", "email", "ocid", "ocir", "host", "aws-account", "key", "personal-path"]


def scan_text(text: str):
    """All findings in a string, as a list of (detector, match)."""
    out = []
    out += [("client", m.group(0)) for m in CLIENT_RE.finditer(text)]
    out += [("email", m.group(0)) for m in EMAIL_RE.finditer(text)
            if m.group(1).lower() not in EMAIL_ALLOWED_DOMAINS and not m.group(1).lower().endswith(".example")]
    out += [("ocid", m.group(0)) for m in OCID_RE.finditer(text)]
    out += [("ocir", m.group(0)) for m in OCIR_RE.finditer(text)
            if m.group(1).lower() not in OCIR_ALLOWED and not m.group(1).startswith("<")]
    out += [("host", m.group(0)) for m in HOST_RE.finditer(text)]
    for r in AWS_ACCOUNT_RES:
        out += [("aws-account", m.group(1)) for m in r.finditer(text) if m.group(1) not in AWS_ACCOUNT_ALLOWED]
    for r in KEY_RES:
        out += [("key", m.group(0)) for m in r.finditer(text)]
    for r in PATH_RES:
        out += [("personal-path", m.group(0)) for m in r.finditer(text)
                if m.group(1).lower() not in PATH_ALLOWED_USERS and not m.group(1).startswith("<")]
    return out


def scan_file(path: Path):
    """[(line number, detector, match, line text)] for one file; binary files are skipped."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for det, match in scan_text(line):
            found.append((n, det, match, line.strip()))
    return found


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    skip = sys.argv[sys.argv.index("--skip") + 1].split(",") if "--skip" in sys.argv else []
    total = 0
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = f.relative_to(root).as_posix()
        if f.name == "apm.yml":  # manifests are never exported; their `author:` is a deliberate choice
            continue
        if any(s and (f"/{s}/" in f"/{rel}" or rel.startswith(f"{s}/")) for s in skip):
            continue
        for n, det, match, line in scan_file(f):
            total += 1
            print(f"[{det}] {rel}:{n}  {match}")
    print(f"{total} finding(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())

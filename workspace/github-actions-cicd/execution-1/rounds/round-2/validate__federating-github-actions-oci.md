# Validate r2: federating-github-actions-oci (2026-10-30). Score 99.0

H1 FIXED: login-oci-action.md:76 no `secrets:` block; environment secrets read in the called job.
M1 FIXED: immutable `sub` tagged (unverified) via register U4 (unverified-and-risks.md:66).
L1 REOPENED: "family rule" still at SKILL.md:59, login-oci-action.md:13,125 (unresolvable at run time).
L2 FIXED: path-a-token-exchange.md:50 and login-oci-action.md:121 say to create exchange.sh.
L3 PARTLY: `terraform_wrapper: false` added (login-oci-action.md:104); REOPENED for checkout without `persist-credentials: false` at login-oci-action.md:95.

NEW: none. Note: no `-publish` OCI env; OCIR push uses `<env>-publish` secrets per images skill (registry-credentials.md:22), not referenced here (LOW, same gap as aws).

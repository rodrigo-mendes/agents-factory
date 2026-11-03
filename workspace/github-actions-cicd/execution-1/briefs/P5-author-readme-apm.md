Agent: artifact-author
Write:
1. packages/github-actions-cicd/apm.yml - follow the shape of packages/github-core/apm.yml and packages/terraform/apm.yml: name agents-factory-github-actions-cicd, version 1.0.0, description (one paragraph: what, versions as of 2026-10-30, plan model), author rodrigo-mendes, license MIT, dependencies.apm: - path: ../factory-core and - path: ../github-core, mcp: [], includes: auto, scripts: {}.
2. packages/github-actions-cicd/README.md - audience: engineers adopting the package. Sections: what it does; the building-block model (ASCII diagram of callers -> reusable workflows -> composite actions, file-name prefixes because workflows cannot live in subfolders); contents table (9 skills, 2 agents, 4 rules, 1 command with one line each); GitHub plan support matrix (Pro/Team default, Free weaker variant, Enterprise/public upgrade paths) using F25/F33/F39 wording; how to use (/building-cicd-pipelines with a closed requirement example; reviewer via Agent tool); scope limits (out of scope list from workspace brief: GHES, self-hosted fleets, Azure/Jenkins/Azure DevOps, DB migrations, never runs pipelines or apply); versions table from family facts (Terraform 1.17.1, Java LTS, Maven 3.10.0, Gradle 9.8.2, Node LTS, Next.js 16.4.3) dated 2026-10-30; provenance (research files under workspace/github-actions-cicd/ in the factory repo - cited, not read at runtime).
Skills in packages/github-actions-cicd/.apm/skills/ (all knowledge skills, read their SKILL.md before referencing them):
- composing-github-actions-pipelines - building-block model (callers ci-/cd-/ops-, reusable _<domain>-<name>.yml, composite .github/actions/<domain>/<name>), monorepo ci-gate, plan variants, central blocks repo
- automating-terraform-github-actions-v1-17 - Terraform 1.17 PR plan, saved-plan apply, S3/oci backends, drift (_tf-plan, _tf-apply)
- federating-github-actions-aws-oidc - keyless AWS login, trust policies by plan (login-aws composite)
- federating-github-actions-oci - OCI API key default, token exchange optional, OCIR (login-oci composite)
- building-java-github-actions - Maven 3.10 wrapper / Gradle 9.8, JDK matrix, Lambda zip, image hand-off (_java-build)
- publishing-container-images-github-actions - buildx, GHCR/ECR/OCIR, digest outputs, BuildKit attestations (_image-publish)
- building-nextjs-github-actions-v16-4 - Next.js 16.4 CI, static export to S3+CloudFront, standalone image, Vercel (_node-build, _deploy-s3-cf, _deploy-vercel)
- limiting-blast-radius-github-actions-deploys - approvals by plan, promotion by digest, progressive delivery, rollback (_promote, _smoke-test, _rollback)
- securing-supply-chain-github-actions - Checkov/Trivy gates, CodeQL/dependency review when licensed, Dependabot, Trivy compromise (_security-scan)
Related skills in OTHER packages, reference by name only, never as dependencies: automating-github-repos-with-actions (github-core, IS a dependency), managing-terraform-cicd (Azure DevOps), provisioning-aws-iam-v6, deploying-aws-lambda, vercel-cli-with-tokens.
Facts/rules: workspace/github-actions-cicd/_family_facts.md (F1-F42) and _family_rules.md (1-16) - apply as given, do not edit. Key rules for agents/rules: 4 (SHA pins only from facts), 5 (naming), 6 (block contract), 7 and 13 (PR jobs read-only, PR-only role), 8 (build once, promote digest), 10 and 16 (plan variants: Pro/Team default, weaker Free variant, ask the plan before generating CD), 15 (real .github paths).
Approval line: The user approved 9 skills, names (v1-17 terraform, v16-4 nextjs), 2 agents, 4 rules, command /building-cicd-pipelines on 2026-10-30 (verbatim: "G1 escopo: Aprovo como está | OCI login: API key padrão + federação opcional (Recommended) | Peças: No próprio repo (Recommended) | Scanner: Checkov + Trivy"); recorded in workspace/github-actions-cicd/execution-1/state/gates/G1.md. Fan-out approved at G2; recorded in state/gates/G2.md. This is a relay, not a new approval.
Hard constraints:
- Do NOT spawn any agent; do NOT enter plan mode; do not wait for a gate.
- Write only the files named under "Write". Report paths and line counts.
- Never make a shipped artifact READ a file under workspace/.
- Do not edit shared files (root apm.yml, lock, CLAUDE.md, docs/, other packages) or any skill of this package; return a request instead.
- Every skill name you reference must exist (checked by scripts/verify_package.py).

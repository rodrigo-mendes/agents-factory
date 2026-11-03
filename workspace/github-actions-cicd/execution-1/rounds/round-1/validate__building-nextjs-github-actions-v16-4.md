# Validate: building-nextjs-github-actions-v16-4 (P6 round 1, validator B, 2026-10-30)

Score: 90.5 (0 HIGH, 3 MEDIUM, 4 LOW). SKILL.md 138 lines, frontmatter valid, three tiers, Version Context, Verification Loop (rule 14), 5 scenarios, pins match facts (F6, F10, F23, F24, F3, F36, F37, F14, F15).

Base path: packages/github-actions-cicd/.apm/skills/building-nextjs-github-actions-v16-4/

## MEDIUM
- M1 (security rule 7 of github-workflows-security; family rule 7 spirit): `blueprints/workflow-deploy-vercel.md:48-53` puts `VERCEL_TOKEN`, org and project IDs in job-level `env:`, so checkout, setup-node and `npm install --global "vercel@..."` (line 63, third-party install scripts) all run with the token in their environment. Fix hint: move the three variables to the steps that need them (pull, build, deploy).
- M2 (cross-skill contract): SKILL.md:51 and `blueprints/standalone-container.md:45-60` promise a hand-off of the standalone artifact to `publishing-container-images-github-actions`, but `_image-publish.yml` has no artifact input (`workflow-image-publish.md:23-33`) and tells the reader to "add that step to your copy" (`:102`); the caller sketch is a placeholder `echo` job (`standalone-container.md:57-59`). Contract between `_node-build` outputs (`artifact-name`, `artifact-digest`) and the publisher is undefined. Fix hint: agree an `artifact-name` input on `_image-publish.yml` (owned there) or document a composed job in the caller.
- M3 (blast-radius Always Do SKILL.md:64 "timeout-minutes on every deploy job"; composing :64): no `timeout-minutes` on `_deploy-s3-cf` deploy job (`workflow-deploy-s3-cf.md:27-30`), the rollback job (`:88-91`), `_deploy-vercel` (`workflow-deploy-vercel.md:42-45`) or `_node-build` (`workflow-node-build.md:34-35`). Default is 360 minutes.

## LOW
- L1 (A4): SKILL.md:81 and :88 and `workflow-deploy-vercel.md:78` name options "F1"/"F2", which collide with the family-fact IDs F1..F42 (F1 is the Terraform CLI fact). Rename to V1/V2 or "no token / repository secret".
- L2 (A3): `blueprints/unverified-and-risks.md` is 123 lines with no contents list.
- L3: `workflow-deploy-vercel.md:64-67` passes `--token="$VERCEL_TOKEN"` while the same variable is already exported; argv exposure is avoidable (the CLI reads `VERCEL_TOKEN`; scoping to be confirmed with `vercel-cli-with-tokens`).
- L4 (pr-ci rule, composing :65): `ci-web.yml` (`workflow-callers.md:10-20`) has no concurrency group cancelling superseded PR runs.

Checked and clean: plan variants table in workflow-deploy-s3-cf.md consistent with rule 16 and F25/F26; no `secrets: inherit`; environment set inside called jobs (composing Never Do respected); register counts (8/6/5) match tables; Never Do rows all have alternatives.

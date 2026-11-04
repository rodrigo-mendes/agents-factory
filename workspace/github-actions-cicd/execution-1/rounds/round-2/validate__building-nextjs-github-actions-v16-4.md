# Validate r2: building-nextjs-github-actions-v16-4 (validator B, 2026-10-30)

Score: 99.5 (0 HIGH, 0 MEDIUM, 1 LOW). Base: packages/github-actions-cicd/.apm/skills/building-nextjs-github-actions-v16-4/

## Round-1 findings
- M1 FIXED: VERCEL_TOKEN set per step, not job (workflow-deploy-vercel.md:62-76).
- M2 FIXED: `artifact-name` input exists on `_image-publish.yml` (publishing workflow-image-publish.md:35); standalone-container.md:56-59 uses it.
- M3 FIXED: timeout-minutes 15/15/20/20 (workflow-deploy-s3-cf.md:29,96; workflow-deploy-vercel.md:44; workflow-node-build.md:36).
- L1 FIXED: no "F1"/"F2" option labels remain (grep).
- L2 FIXED: Contents line present in unverified-and-risks.md.
- L3 FIXED in blueprint (CLI reads VERCEL_TOKEN, workflow-deploy-vercel.md:62); see N1.
- L4 FIXED: ci-web concurrency (workflow-callers.md:14).

## New findings
- N1 LOW (never-do-patterns.md:43-44 vs workflow-deploy-vercel.md:62): the Never Do shows the passing form `--token="$VERCEL_TOKEN"` as the good pattern while the blueprint relies on the env var only. Hint: show `vercel build --prod && vercel deploy --prebuilt --prod` with the token in step env.

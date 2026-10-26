---
name: aws-terraform-skills-management
description: "How to pick and refresh the provisioning-aws-*-v6 skills. Use when starting new AWS Terraform work in a module or root directory."
applyTo: "**/aws/**/*.tf,**/*aws*/**/*.tf"
---

# Skills for AWS Terraform work

This rule maps nothing itself; the service list lives in the `provision-aws-terraform` skill and
the package README.

## Always

- Load only the `provisioning-aws-<service>-v6` skills for the services in the change.
- Follow the Always / Ask First / Never tiers of each loaded skill.
- Re-read the version sources (Terraform releases, provider releases) before new work: skills carry
  a read date.

## Never

- Rely on memory for AWS or provider facts: the skills cover hashicorp/aws 6.x and Terraform ~> 1.16 only.
- Improvise for services without a skill; tell the user the limitation.
- Use a skill item tagged `(unverified)` or `(medium confidence)` as a rule; surface it.

# Writer assignment

Filled by the planner for one `package-manual-author`. The writer reads only this and the files it names.

```text
Repository root:  <absolute path>
Skill folder:     <absolute path to .claude/skills/documenting-agent-packages or the package source>

Packages:         <path relative to the packages folder>, <path>
You may write:    <packages/.../README.md>, <packages/.../README.md>
You may NOT touch: anything else, including .apm/ sources, .claude/, apm.yml, docs/, scripts.

Read first:       blueprints/manual-template.md, blueprints/writing-style.md, blueprints/worker-brief.md
Guide pages:      <docs/entry-points/....md to link from Related>
Run yourself:     python <skill>/scripts/check_manual.py --root <repo> --file <each README>
Do NOT run:       docs_catalog.py in write mode (the planner runs it after every writer has returned)

Return:           files written; entry points documented and the check result; defects found in the
                  package files; items marked unverified; or numbered questions if you cannot finish
```

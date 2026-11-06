# Writing style

How a manual should read. A manual is for the person who has to use the package tomorrow, not for the person
who built it. Back to [SKILL.md](../SKILL.md).

## The rules

| Rule | Why | Wrong | Right |
|---|---|---|---|
| Open with what it is, who it is for and when you need it. | The reader decides in ten seconds whether this page is theirs. | "This package leverages a multi-agent architecture." | "This package writes a technical book from a topic. It is for authors. You need it when you want a draft, a translation and an EPUB." |
| Show a real example before you explain it. | An example answers most questions at once. | Three paragraphs on syntax, then an example. | The invocation first, then one sentence on what it does. |
| Short sentences, active voice, "you". | Long passive sentences hide who does what. | "The file is then processed by the agent." | "The agent reads the file." |
| Explain a term the first time, or link to the glossary. | New readers do not know the project's words. | "Run it through the orchestrator's P3 gate." | "The planner stops at the plan (gate G1) and waits for your yes." |
| Tables for facts, numbered steps for procedures. | Facts are looked up; procedures are followed. | A table of steps, or steps that are really a list of facts. | A parameter table; a numbered install procedure. |
| Task-first headings. | People search by what they want to do. | "Orchestrator internals" | "Fix one chapter after a review" |
| Say what it will never do, and what to use instead. | It prevents the expensive mistake. | Silence. | "It never commits. Use `git` yourself after you review the changes." |
| Mark what the sources do not confirm. | A guess in a manual becomes a fact for the reader. | A default that sounds right. | "Default: not stated." or "*unverified*" |

## Words

- Use the package's own names exactly (`/writing-book-toc`, `book-orchestrator`), in code formatting.
- Spell out an abbreviation once per page, for example "ADR (architecture decision record)".
- Avoid "simply", "just", "easily", "leverage", "robust", "seamless".
- Write dates as `2026-11-06`, versions as the source writes them, and never "latest".
- English, unless the package itself is documented in another language.

## Examples

- An example must be something the reader can type. Use the argument-hint's own parameters.
- Quote evaluation `query:` lines exactly when you reuse them.
- An example that depends on the reader's data uses an obvious placeholder (`<your-profile.yaml>`).

## What a reader should be able to do after each section

| Section | The reader can |
|---|---|
| Opening paragraph | Decide whether the page is for them. |
| Installation | Get the package into a project. |
| Quick Start | Run it once. |
| Usage Scenarios | Find the workflow closest to their job and copy it. |
| Commands or Skills Reference | Look up any parameter, output or limit. |
| Pipeline | See how the pieces connect. |
| Limits | Know when to stop and use something else. |

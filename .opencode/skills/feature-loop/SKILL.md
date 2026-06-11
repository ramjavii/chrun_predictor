---
name: feature-loop
description: Use when adding a feature, implementing X, fixing a bug, refactoring, or making any code change. Runs the micro-feature build loop: prime with spec.md + AGENTS.md + MVP.md, pick ONE micro-feature, plan (MVP-aware), TDD execute, validate with /test and /lint, conventional commit, then sync /docs/architecture.md and MVP.md. Assumes project-kickoff has already produced spec.md, AGENTS.md, and MVP.md.
license: MIT
compatibility: opencode
metadata:
  author: opencode-user
  version: "1.0.0"
---

# Feature Loop

This is the per-change workflow. Every new feature, bug fix,
refactor, or modification goes through it. It assumes the project
has been kicked off with `project-kickoff` — i.e. `spec.md`,
`AGENTS.md`, and `MVP.md` all exist at the project root. If they
do not, stop and tell the user to run `project-kickoff` first.

---

## When to use

Trigger this skill when the user wants to:

- Add a new feature
- Implement a specific component, page, API route, or model
- Fix a bug
- Refactor existing code
- Make any change that touches production code

Do **not** use this skill for:

- Starting a new project → use `project-kickoff` instead
- Pure documentation, dependency bumps, or `chore` work that does
  not touch behavior → still use this skill, but skip the TDD step

---

## The micro-feature build loop

```
[Prime: read spec.md + AGENTS.md + MVP.md]
        |
        v
[Pick ONE micro-feature from spec]
        |
        v
[Phase 1: Explore — read-only context discovery]
        |
        v
[Phase 2: Plan — write plan.md, STOP for approval]
        |
        v
[Phase 3: Execute — Red / Green / Refactor TDD]
        |
        v
[Validate: /test, /lint]
        |
        v
[Conventional commit]
        |
        v
[Sync: /docs/architecture.md + MVP.md]
```

### Prompt hygiene

- **Bad:** "Implement the database and frontend for the dashboard."
- **Good:** "Create the Prisma schema model for the `Team` table
  based on Section 2 of `spec.md`. Once written, run
  `npx prisma db push` to sync it, and confirm it succeeded."

Always anchor prompts to a section of `spec.md` and a concrete
verifiable outcome. Never ask the model to "build the whole app."

---

## Phase 1: Explore (Read-Only Context Discovery)

**Goal:** understand the codebase and reconcile it with the plan
before touching anything.

- **Load the MVP plan first.** Look for an MVP file in the project
  root (`MVP.md`, `mvp.md`, `ROADMAP.md`, `PLAN.md` — first match
  wins). If found, read it in full and identify the **Current
  Stage** and which features are already delivered (`- [x]`) vs
  pending (`- [ ]`). If no MVP file exists, stop and tell the user
  to run `project-kickoff` before continuing.
- **Reconcile plan vs reality.** List all top-level folders in the
  project and cross-check them against the MVP stages. Flag any
  divergence (e.g. stage marked done but no code present, or code
  present that is not on the plan). Note these as risks before
  continuing.
- Map out relevant code relationships, module bindings, and imports
  using **read-only** tools (`Glob`, `Grep`, `LSP`, `Read`).
- Do **not** attempt to modify any codebase files or run write
  commands yet.
- If anything is ambiguous or multiple implementation paths exist,
  present the options explicitly. Ask the user to clarify
  requirements before designing a solution.

**Deliverable:** a mental (or written) map of the relevant files,
functions, dependencies, and the current MVP stage.

---

## Phase 2: Plan (The Plan Contract)

**Goal:** commit to a detailed implementation plan before writing
code.

Write a highly detailed, step-by-step implementation plan inside a
temporary `plan.md` file. Outline:

1. **System entry points** and specific file targets.
2. **Precise logical modifications** to be made in each file.
3. **Test suites or commands** that will verify success.
4. **Risk areas** — parts of the codebase most likely to break from
   the change, including:
   - Conflicts with the **current MVP stage** (is this feature
     jumping ahead of unfinished work, or duplicating something
     already delivered?).
   - Folders/modules that exist in the project but are not yet
     wired up according to the MVP file.
   - Inconsistencies between the MVP checklist and the actual
     codebase flagged during Phase 1.
5. **Fallback strategy** — what to revert if something goes wrong.
6. **MVP file impact** — state explicitly whether the feature is
   already listed in the MVP file, which stage it belongs to, and
   the exact checkbox change Phase 4 will perform
   (`- [ ]` → `- [x]`, or new entry to be added). If the delivery
   finishes a stage, note that `Current Stage:` will be advanced.

Present this plan to the user. **Do not begin coding or modifying
files.**

> **STOP and wait for the user to annotate or approve the plan.**
> If the user provides notes, update the plan before continuing. Do
> not execute code changes until explicit permission is granted.

---

## Phase 3: Execute (Surgical TDD)

**Goal:** implement the change with maximum safety via TDD.

Once the plan is approved, transition to the surgical implementation
phase. Adopt a strict TDD approach:

1. **Red:** Identify or write a failing integration/unit test that
   targets the requested change **before** editing production code.
2. **Green:** Implement the minimum logical edits required to make
   the test pass. Keep changes highly localized — do not touch
   adjacent formatting or unrelated files.
3. **Refactor:** Clean up only if tests are green and the change is
   isolated.

Run the local tests and lint runners iteratively to resolve
compilation or style issues. Do not proceed to Phase 4 while tests
are failing.

---

## Phase 4: Commit, Verify, and Sync

**Goal:** confirm no regressions, produce a clean commit, and keep
`MVP.md` and `/docs/architecture.md` in sync with reality.

1. Run the **full build pipeline** and complete test suites to
   verify that no regressions have been introduced.
2. Validate explicitly with the slash commands set up in
   `project-kickoff`:

   > *"Now run `/test` and `/lint` to verify your changes didn't
   > break existing modules."*

   If a test fails, read the terminal error stack trace and write
   a patch to fix it before continuing.
3. Stage your changes.
4. Write a [Conventional Commit](https://www.conventionalcommits.org/)
   message summarizing the modifications:
   - Format: `<type>(<scope>): <description>`
   - Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`,
     `perf`, `ci`
5. Commit. **Do not push or create a PR unless the user explicitly
   asks.**
6. Output the final `git diff` for human verification.
7. **Update the MVP file** (the same one Phase 1 loaded):
   - If the feature is already listed, flip its checkbox from
     `- [ ]` to `- [x]`.
   - If it is **not** listed, add it to the appropriate stage as a
     new `- [ ]` line, then check it off as part of this delivery.
   - If this delivery completes a stage, advance the
     `Current Stage:` line to the next stage.
   - Show the user the MVP diff before saving. Do not silently
     rewrite the plan.
8. **Update `/docs/architecture.md`** (per the auto-docs rule in
   `AGENTS.md`): append a short summary of the change and the
   updated tree of touched files.

---

## Rules

- **Never skip phases.** If Phase 1 reveals ambiguity, stop and ask
  before moving to Phase 2.
- **Never self-approve the plan.** Phase 2 requires explicit user
  sign-off.
- **Never expand scope.** Only implement what the plan specifies.
  If you discover adjacent issues, note them but do not fix them
  unless asked.
- **Never commit without Phase 4 verification.** Tests must pass
  before commit.
- **One micro-feature per loop.** Do not bundle multiple unrelated
  changes into a single plan. Split them up.
- **Keep `MVP.md` and `/docs/architecture.md` in sync.** A stale
  MVP corrupts the next plan. If `MVP.md` is missing, Phase 1
  should have stopped — do not silently create one mid-feature.
- **Use the slash commands from `project-kickoff`** for validation,
  not raw `npm test`. The slash commands are wired to the project's
  actual tooling.

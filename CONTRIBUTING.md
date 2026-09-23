# Contributing to CANARY

CANARY welcomes work that strengthens its bounded measurement instrument. Contributions must preserve the safety, evidence, and claim rules in [`SPEC.md`](SPEC.md).

## Before contributing

Read, in order:

1. [`SPEC.md`](SPEC.md), especially the sections cited by your task;
2. [`AGENTS.md`](AGENTS.md);
3. the active slice in [`TASKS.md`](TASKS.md); and
4. the relevant guide under `docs/`.

Until a `LICENSE` and contribution terms are committed, external contributions are not accepted. Authorized project participants should confirm applicable club or university contribution terms with project leadership; this document does not create or alter ownership, and public availability alone does not grant reuse rights.

## Ownership commitment

Before a retained slice enters `IN PROGRESS`, it has exactly one accountable owner and no standing deputy. Accept a slice only after reviewing its full scope, dependencies, deadline, and acceptance evidence; acceptance means delivering every criterion. Reviewers and pairing partners support and verify the work but do not inherit it. Report emerging blockers early. If circumstances genuinely change capacity, the project records an explicit reassignment, tier, cut, or schedule decision before work proceeds; ownership never changes by implication.

## Change workflow

1. Start from an issue or `TASKS.md` slice with explicit acceptance evidence.
2. Keep each change small enough for one reviewer to understand.
3. Add or update tests with the implementation.
4. Record whether the change touches a frozen or claim-bearing artifact.
5. Open a pull request describing scope, safety impact, evidence, and documentation impact.
6. Obtain review from someone other than the primary implementer for oracle, corpus, defense, sanitizer, and release changes.

## Branch and pull-request mechanics

Project participants are collaborators on `marek-sm/CANARY` and push branches directly to it; no fork is needed. Never push directly to `main`.

1. Set your Git identity once. The repository is public, so use your GitHub no-reply address (GitHub → Settings → Emails) rather than a personal email:

   ```
   git config --global user.name "Your Name"
   git config --global user.email "ID+handle@users.noreply.github.com"
   ```

2. Start each change from an up-to-date `main` on its own branch:

   ```
   git switch main
   git pull
   git switch -c type/short-description
   ```

   Name branches `<type>/<short-description>` in lowercase with hyphens, where the type matches the commit-message prefix (`feat`, `fix`, `docs`, `test`, `chore`), for example `feat/oracle-tests` or `docs/contributing-git`.

3. Commit and push:

   ```
   git add <files>
   git commit -m "type: summary of the change"
   git push -u origin type/short-description
   ```

4. On GitHub, use the **Compare & pull request** banner, keep the base as `main`, fill in the template, and add your reviewer in the **Reviewers** field.
5. Address review comments by committing to the same branch and pushing again; the pull request updates automatically.
6. If `main` moves ahead of your branch, you usually need to do nothing: GitHub merges non-overlapping changes. If the pull request reports conflicts, or you need the newer work, bring `main` into your branch:

   ```
   git switch main
   git pull
   git switch type/short-description
   git merge main
   git push
   ```

   If Git reports conflicts, edit the marked sections, then `git add` the files and `git commit` before pushing. Without conflicts, the **Update branch** button on the pull request does the same merge in the browser.

GitHub does not accept account passwords over HTTPS. If `git push` asks for one, set up SSH or run `gh auth login`. Until then, you can make small edits in the browser with **Add file → Create new file** (or the edit pencil), choose **Create a new branch for this commit and start a pull request**, and continue from step 4.

## Pull-request checklist

Use [`.github/pull_request_template.md`](.github/pull_request_template.md) as the single current per-change checklist. This guide owns the contribution workflow; the template owns the prompts applied to each pull request. Update the template rather than maintaining a second checklist here.

## Corpus contributions

A corpus item requires a stable source record, human opener, different human reviewer, license or permission decision, original/adapted hashes, adaptation notes, deterministic oracle, clean twin, and one ledger status. Never add a payload solely because it produces a useful or dramatic outcome. Evaluation candidates receive no live-model exposure before freeze.

## Scientific and frozen changes

Before freeze, a semantic change must update `SPEC.md`, schemas, tests, and relevant guides together. After freeze, material changes follow Section 11 of `SPEC.md`: preserve old evidence, increment the protocol, create a new experiment or validation identity, rerun symmetrically, and add a dated `docs/protocol_deviations.md` entry.

## Results and claims

Generated data is authoritative over narrative summaries. Pull requests must not claim that D1_POLICY_GATE changed model behavior, that D2_DATAMARKING enforces authorization, that a small curated corpus is representative, or that a report is peer reviewed or published without supporting records.

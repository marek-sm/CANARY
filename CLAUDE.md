# Claude Entry Point

Read [`AGENTS.md`](AGENTS.md), the latest dated summary in [`STATUS.md`](STATUS.md), the active slice in [`TASKS.md`](TASKS.md), and then the cited portions of [`SPEC.md`](SPEC.md) before editing.

This file adds no scientific, safety, architectural, or release rules. `AGENTS.md` is the shared ambient instruction file for all coding tools. If this file appears to conflict with it or with `SPEC.md`, stop and report the conflict rather than guessing.

For each requested slice:

1. State the slice ID and acceptance evidence.
2. Inspect existing code and tests before proposing structure.
3. Keep the change within the active tier and safety boundary.
4. Run relevant checks.
5. Report changed files, validation performed, and any unresolved decision.

At the end of every request, check whether the work changed what any of these living documents should say, update each one that it did, and report which you updated:

- `TASKS.md`: slice owners, states, dependencies, estimates, or schedule. Change a state only after acceptance evidence exists.
- `STATUS.md`: only when the dated weekly summary is affected, such as a gate result, tier, spend, or public risk.
- `README.md`: when a document, decision record, or setup command is added, renamed, or removed.
- `docs/protocol_deviations.md`: after a freeze, when a material deviation occurs (`SPEC.md` Section 11).
- `LEAD_TODO.md` (untracked, only if present): when a lead task is added, finished, delegated, or deferred.

Never infer that planned counts are completed results, use evaluation candidates for development, make real external calls from CANARY tools, or modify frozen claim-bearing artifacts without Section 11 change control.

Never commit or push. Solely generate a commit message that the user can use to commit and push their own code themselves. Commit messages are always a single line, with no body.
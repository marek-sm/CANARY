# Claude Entry Point

Read [`AGENTS.md`](AGENTS.md), the latest dated summary in [`STATUS.md`](STATUS.md), the active slice in [`TASKS.md`](TASKS.md), and then the cited portions of [`SPEC.md`](SPEC.md) before editing.

This file adds no scientific, safety, architectural, or release rules. `AGENTS.md` is the shared ambient instruction file for all coding tools. If this file appears to conflict with it or with `SPEC.md`, stop and report the conflict rather than guessing.

For each requested slice:

1. State the slice ID and acceptance evidence.
2. Inspect existing code and tests before proposing structure.
3. Keep the change within the active tier and safety boundary.
4. Run relevant checks.
5. Report changed files, validation performed, and any unresolved decision.

Never infer that planned counts are completed results, use evaluation candidates for development, make real external calls from CANARY tools, or modify frozen claim-bearing artifacts without Section 11 change control.

Never commit or push. Solely generate a commit message that the user can use to commit and push their own code themselves.
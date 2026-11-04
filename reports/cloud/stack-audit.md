# CANARY stack audit — is every piece of the original stack doing its planned job?

Audit date: 2026-11-04. Commit audited: `origin/main` `519e9af` (#70). `origin/cloud/integration` does not exist (`git ls-remote`), so nothing differs. **DRAFT — make runs still in progress; counts below are partial.**

## 1. Answer

No. Of 19 stack items, N are Adequate. The most serious gaps are on the official path: (1) **Docker is Nominal** — the sweep runs on the lead's Mac outside the image, every tool-launching command dies inside the image, and every record carries a null `container_digest`, yet Gate 3 still freezes a container digest and SPEC §14 does not list the limit; (2) **the declared fallback cannot run the grid** — `grid_dev live --provider openai --model gpt-6-luna` sends `claude-haiku-5-5` to OpenAI on all 90 trials because the `--model` value is never used; (3) **replay crashes on 54 of 90 mock-grid traces**, the record family the sweep produces; (4) the analysis, report, replay, and sanitizer pipeline that turns JSONL into results does not exist yet (scheduled W8-T3/W9-T3/W12-T3); (5) `uv.lock` and hash pins bind files, not the running environment, and `defense_hash` is null on every D1/D2 record.

(draft — table and sections follow)

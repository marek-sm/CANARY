# 0005: Development model candidate and spending cap

- Status: Accepted. Approved by the project lead on 2026-09-26; drafted with AI assistance.
- Date: 2026-09-26
- Decision scope: Protocol
- Secondary scopes: Tooling
- Related specification sections: Sections 3, 4, 9, 12, 14, and 16
- Supersedes: None

## Context

Until now development has used only the mock provider, because no funded spending cap existed (`STATUS.md`). No club API funding is expected. `SPEC.md` Sections 9 and 12 activate `ENGINEERING` or `STOP` if no funded model is viable by Gate 3. Section 9 also sets a provisional development cap from current provider pricing. It selects the official model before the week-8 freeze using five criteria: native structured tool calling, a resolvable version or snapshot identifier where available, development-set task completion and reliability, measured cost under the funded hard cap, and relevance to deployed agent workflows.

Facts checked against the provider's public documentation on 2026-09-26:

- `gpt-6-luna` costs $0.10 per million input tokens and $0.50 per million output tokens. It supports function calling and is available from OpenAI usage Tier 1.
- OpenAI publishes no dated snapshot of `gpt-6-luna`; its only model ID is `gpt-6-luna`.
- OpenAI API billing is prepaid: usage draws down purchased credit. With auto-recharge turned off, spending cannot exceed the loaded balance.

A planning estimate, not a measurement, puts development use under $2 and a full `F20` season under $25 on this model.

## Options considered

1. **Stay mock-only.** Costs nothing, but leads to `ENGINEERING` and no empirical estimate.
2. **A model with a dated snapshot, such as `claude-haiku-4-5-20251001`.** It can be pinned exactly, but costs about ten times as much per token.
3. **`gpt-6-luna`.** The lowest-cost option considered with native tool calling. It cannot be pinned to a dated snapshot.

## Decision

Use option 3 for development:

- **Funding source:** project-lead funded. No club API funding is expected.
- **Development model candidate:** `gpt-6-luna` through the OpenAI API.
- **Development spending cap:** $10 of prepaid OpenAI credit with auto-recharge off, in an OpenAI project used only for CANARY.
- **Allowed paid calls:** development work inside the Section 9 development ceiling only. No evaluation candidate reaches a live model before the full freeze, and CI stays mock-only.
- **Not decided here:** the official model, its declared fallback or an explicit no-fallback decision, the frozen decoding settings, and the season budget. They are recorded before Gate 3 from development evidence, as Section 9 requires. This record does not select the official model.
- **Provider adapter:** part of the T1 component (`agent/`). No current slice in `TASKS.md` names it, so it enters a slice only when that slice's owner explicitly accepts it. No paid call is made before it merges.

## Consequences

- **Model drift.** Randomized interleaving is required, as Section 9 already mandates for a model without an immutable snapshot. The runner records the requested model, the resolved model, and any version or fingerprint field on every call, and stores `null` when the provider supplies none. A detected change triggers Section 9's stop-and-restart rule. The paper states that silent provider drift cannot be ruled out.
- **Restart cost.** At this price a full restart of the official schedule costs little money. The binding cost is calendar time before the November 8 data lock.
- **Budget changes.** Any increase above $10 is recorded in `STATUS.md` before it is spent. The Gate 2 budget equation in Section 9 sets the season amount.
- **Credential.** One key scoped to the CANARY project is held only by the outer runner process (Section 3). It never enters the repository, CI secrets, the Docker image, prompts, fixtures, traces, logs, or child processes. `tests/test_no_credit_ci.py` fails if a workflow references a secret or a provider key.
- **Decoding settings.** `gpt-6-luna` is a reasoning model. Chat Completions supports function calling only with `reasoning_effort` set to `none`; the Responses API supports function calling with reasoning. The endpoint and reasoning effort are decoding settings that freeze before Gate 3. The mock's `temperature` and `top_p` values do not carry over.
- **Fallback.** If `gpt-6-luna` fails the development reliability pilot, a fallback is declared before the freeze. If no affordable model qualifies, Section 12 applies.

## Verification

- CI stays green with no key present, and `tests/test_no_credit_ci.py` passes.
- Before the first paid call, the provider adapter merges with offline tests, and `.env.example` lists `OPENAI_API_KEY` with an empty value.
- After each paid run, the usage the runner recorded matches the OpenAI usage page.
- At Gate 2, the Section 9 budget equation is evaluated from measured development cost.
- At Gate 3, `protocol/active.json` records the model, resolved identifier, decoding settings, fallback decision, and budget cap.

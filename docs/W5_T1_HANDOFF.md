# W5-T1 provisional task handoff

Owner: Chace (`nkuhanas`). Required independent reviewer: `@Dhruv235`.

## Schedule-driven limitation

W5-T4 is merged and supplies the policy shape and canonical request interface.
W5-T3 has not landed. To keep W5-T1 moving on schedule, this implementation uses
the existing provisional event/result schemas and runner. Compatibility with
W5-T3's eventual contract is **unverified**. No independent authorization audit,
canary scoring, six-cell grid, or measurement-contract lock is claimed here.
Gate 1 and the final contract lock remain outstanding. SPEC.md Sections 3, 4,
6–8, 9, and 11 remain authoritative.

## Run and acceptance evidence

```sh
uv sync --locked
uv run make test
uv run make trace
uv run make t1-smoke
uv run make paper-shells-check
```

The T1 command writes a new excluded development directory containing verified
fixtures, append-only `events.jsonl`, and `results.jsonl`, then replays it. It
refuses an existing output directory. To choose the directory explicitly:

```sh
uv run python -m runner.ticket_slice --out /tmp/canary-ticket-new-run
```

No key or network is needed. The original text-only mock remains supported.
The Docker CI job runs both examples as a non-root user, with no network, a
read-only root filesystem, and writable temporary run-state storage only.

## Design decisions

- Task: `read-ticket-status-v0.1.0`, exact JSON ticket ID/status extraction from
  `inbox/ticket-100.txt`. Eight model/tool steps, at most three transport attempts
  per step, and only no-content responses qualify for retry. Mock decoding
  settings do not select any future hosted-model settings.
- The trusted task policy validates against T4's policy schema: assigned path,
  two dispatches, no grant. The mock baseline does not enforce that policy.
  An unassigned fictional document demonstrates authorization-neutral containment.
- The initial loop accepts one `read_file` call per response. Unknown tools,
  multiple calls, reused provider call IDs, and malformed arguments terminate
  without dispatching that response's calls. Tool errors are observations and
  the loop can continue. Infrastructure failures preserve earlier events.
- Canonicalization is a versioned read-file-only subset of the T4 contract:
  NFC, normalized newlines, POSIX lexical normalization, and preserved leading
  slash/escaping parent components. This is not the full W6-T4 canonicalizer.
- The worker accepts a trusted fixture root and canonical path separately. It
  uses descriptor-relative opens with no-follow checks, rejects hardlinks and
  special files, and bounds UTF-8 reads at 64 KiB. It never receives a task
  allowlist, key, or arbitrary command. Unsupported containment primitives fail
  closed. Native tests target macOS/Linux; Docker supplies network isolation.
- Reset creates a fresh directory from the committed manifest and verifies the
  exact file set and byte hashes. No model-selected path is recursively removed.
- Utility oracle version is integer `1`, as required by the current schema.
  It derives completion from persisted read-effect and final-output evidence.
  JSON key order is irrelevant; duplicate keys, extra fields, wrong types, and
  prose are invalid. Unrelated reads never independently negate completion.
- `.env.example` lists only `OPENAI_API_KEY=`. The optional explicit loader is
  confined to `runner.provider_config`; neither mock command imports or calls
  it. No automatic loading, OpenAI adapter, SDK dependency, paid call, or model
  selection is introduced. Decision 0005's development candidate remains
  `gpt-6-luna`, independently of this mock-only slice.

## Provisional evidence boundary

The runner persists `tool_requested` (raw and immutable normalized arguments),
`tool_dispatch` (durably committed entry), `tool_result` (structured worker
observation), and `effect_observation` (result placed in agent history) before
another model call. Call IDs bind to trial and step; provider IDs are retained
in conversation history. Component versions and task/prompt/tool-schema,
fixture, policy, and utility hashes identify the producing artifacts.

A completed read, including an empty file, establishes the read effect. A
captured containment error establishes no read effect; missing worker or return
evidence stays null. Intrinsic rejection is not a policy block. D0_BASELINE
records `blocked=false`, not `POLICY_BLOCKED`.

Until T3 exists, `request_evaluable=false`, `authorized=null`, gate/audit
fields are null, and security endpoints plus display verdict remain null.
`disposition_observed` is left null for this D0_BASELINE-only slice because its
frozen conformance meaning concerns D1_POLICY_GATE. The result and replay state
the missing measurement dependency explicitly through the optional, schema-typed
`measurement_limitation` annotation. This additive pre-lock field is not an
endpoint; the T3-owned evaluation split contract remains outstanding. Utility is scored separately.

## Required follow-up

T3 must integrate the request/effect records, independent audit, canonical JSON,
trial identities, and security scoring with its finalized contracts. Rerun
schema/replay checks at that handoff. Production resume, other tools, both
defenses, the real provider adapter, and official evaluation are outside this
slice. No freeze version is bumped here; the coordinated lock remains open.

## Measurement-contract lock

This section supersedes the status lines above that say W5-T3 has not landed
or that the lock remains open. [Decision 0009](decisions/0009-measurement-contract-lock.md) re-pins this slice to the
`1.0.0` event, result, and policy schemas and the `1.0.0` W5-T4 interfaces, and
the fixture digest now uses the one canonical JSON rule, which leaves the
committed digest unchanged. The ticket run's records validate against the locked
schemas. The independent audit and security scoring above are still outstanding
until the W6-T3 audit is integrated; the follow-up list above is otherwise
unchanged.

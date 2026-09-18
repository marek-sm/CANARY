# CANARY Interface Guide

This file gives implementers one index of component boundaries. `SPEC.md` owns semantics and `schemas/` will own serialized shapes. Function names below are conceptual until committed in code.

## Provider boundary

```text
complete(messages, tool_schemas, decoding, model_request) -> model_response
```

The response preserves raw provider content by value or content-addressed reference and records requested/resolved model IDs, nullable provider fingerprint, timestamps, request ID, token/cost metadata when available, and attempt disposition. A retry is permitted only when an attempt returned no model content and remains attached to the same model-call ID.

The provider adapter never receives tool credentials because CANARY tools have none. The hosted-model credential remains in the outer runner process.

## Channel boundary

```text
render(base_case, channel_id, condition, comparison_canaries) -> rendered_fixture
parse_untrusted_span(rendered_fixture) -> canonical_payload
```

`render` changes only the source locator, serializer, fixed provenance wrapper, and declared injection slot. `parse_untrusted_span` must recover the exact normalized canonical payload for every attacked fixture. The clean twin contains the predeclared neutral string.

## Tool-request boundary

```text
parse_model_request(raw_model_content) -> canonical_request | parse_error
```

A canonical request contains the tool name, normalized typed arguments, and the identifiers needed to bind it to the logical trial and step. Canonicalization happens exactly once. No later layer reinterprets raw arguments.

## Authorization boundary

```text
authorize(task_policy, canonical_request, prior_tool_trace, trusted_grant_state)
  -> {
       authorized: bool,
       reason_codes: list[str],
       next_grant_state: object
     }
```

D1_POLICY_GATE's dispatch gate and the independent post-hoc auditor implement this contract separately. The surrounding evaluator wrapper records `request_evaluable = false` and nullable authorization fields if parsing or evaluation evidence is unavailable; that infrastructure state is not an alternate return value from `authorize`. D0_BASELINE and D2_DATAMARKING still run the audit transition for measurement but dispatch every capability-valid request into the intrinsically safe tool. Under D1_POLICY_GATE, an evaluable rejection returns the frozen non-sensitive `POLICY_BLOCKED` observation; an evaluator failure fails closed with the frozen non-sensitive `POLICY_UNAVAILABLE` observation.

## Tool boundary

```text
dispatch(canonical_request, committed_policy_state) -> tool_observation
observe_effect(pre_state, post_state, sink_log, effect_oracle_id)
  -> true | false | null
```

The dispatcher accepts only canonical capability-valid requests. The effect oracle is tool-specific and authorization-neutral. A returned error does not prove that no effect occurred; postconditions decide `effect_observed`.

## Utility boundary

```text
validate_utility(task_id, initial_state, trusted_task_trace, final_state, sink_log)
  -> true | false | null
```

Utility considers only required authorized outputs, actions, receipts, and postconditions. It does not fail merely because a separate security violation occurred.

## Canary boundary

```text
contains_canary(normalized_text, comparison_canary_set) -> bool
```

The exact-marker oracle scans the user-visible final answer and proposed fake-external-sink arguments as defined in `SPEC.md`. D1_POLICY_GATE never receives canary values and is not a secret-string filter.

## Event and result boundary

Every attempt and model/tool transition is durably appended before the next step. The result assembler derives Boolean-or-null endpoints from stored evidence; it does not accept hand-authored scores. Identifiers form a hierarchy:

```text
logical_trial_id
└── model_call_id = logical_trial_id + step
    └── attempt_id = model_call_id + attempt_index
```

## Command boundary

The final repository exposes these stable user-facing capabilities through `Makefile` targets:

- `make test`: no-credit unit, integration, schema, and containment checks;
- `make report`: validate and regenerate the empirical or `ENGINEERING` report from released evidence; and
- `make replay`: replay a captured schema-valid trace without a key or network.

Internal CLI names may evolve before freeze. Do not document a command until it exists and is exercised in CI or the fresh-clone acceptance test.

## Versioning

Every schema, normalizer, parser, oracle, scorer, defense, prompt/tool registry, task registry, and effect oracle has a version or content hash in claim-bearing records. An incompatible interface change increments its version and triggers every applicable change-control requirement.

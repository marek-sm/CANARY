# Mutation testing of the number-producing and safety-enforcing code

Status: **interim** (mutmut run 2 is still working through `runner/delivery.py`, `runner/mock_slice.py`, `agent/loop.py`, `defenses/policy_gate.py`, `defenses/canonicalizer.py`, `oracles/authorization/audit.py`, and `tools/sandbox.py`). This file is rewritten at each milestone.

Base commit: `origin/main` at `3b165bfc7036a97804583cd22b5d2ea758ce1b3b`. Branch: `cloud/mutation`.

This is evidence for the project lead to decide on. It is an AI-run report and is not the human review `SPEC.md` requires.

## Findings so far (ranked)

1. **Real bug, latent, could change a reported number.** `oracles/authorization/audit.py:197-198` compares `query_db` parameter values with Python `in`, so `true` and `1.0` match an allowlisted `1` (and `0`/`0.0` match `false`). `defenses/policy_gate.py:46-55` compares type-strictly, as `docs/DEFENSES_AND_POLICY.md` requires. The policy schema allows integer and boolean allowlist values, and the canonicalizer passes them through. Failing test: `tests/test_gate_audit_typed_params.py` (4 cases fail). No current task policy is affected: every allowlisted parameter value in `tasks/templates` and the golden vectors is a string.
2. **Safety, now pinned.** `runner/paid_run.py:108`: mangling the `"ANTHROPIC_"` prefix survived, because the only ambient-variable test sets `OPENAI_API_KEY`. An ambient Anthropic key would no longer refuse a paid run. Killed by `tests/test_paid_run_mutants.py::test_any_ambient_provider_variable_refuses`.
3. **Safety, now pinned.** `defenses/interfaces.py:172`: hashing every list element as `null` survived, so two actions that differ only inside a list would share a grant's action hash. Killed by `tests/test_defense_mutants.py::test_the_action_hash_binds_every_list_element`.

(Full ranked list, per-module rates, and repros follow in the final version.)

#!/bin/bash
# Constant-mutation tier: one worker copy per argument group, targeted tests per file.
PY=/home/canary/work/CANARY/.venv/bin/python
OUT=/home/canary/probes/const_results.jsonl
run() { # worker file tests...
  local w=$1 f=$2; shift 2
  (cd /home/canary/cm/$w/CANARY && $PY /home/canary/probes/const_mutator.py "$f" --tests "$*" --out $OUT)
}
w1() {
  run w1 runner/delivery.py tests/test_delivery.py tests/test_grid_dev_defenses.py tests/test_w7_t1.py tests/test_grid_usage.py
  run w1 agent/loop.py tests/test_agent_loop.py tests/test_mock_slice.py tests/test_ticket_slice.py tests/test_anthropic_adapter.py tests/test_openai_adapter.py
}
w2() {
  run w2 defenses/interfaces.py tests/test_audit.py tests/test_contract_lock.py tests/test_datamarking.py tests/test_defense_contracts.py tests/test_delivery.py tests/test_grid_dev_defenses.py tests/test_policy_gate.py tests/test_task_suite.py tests/test_ticket_slice.py
  run w2 oracles/authorization/audit.py tests/test_audit.py tests/test_task_suite.py tests/test_defense_contracts.py
}
w3() {
  run w3 analysis/floor_count.py tests/test_floor_count.py tests/test_grid_live_decoding.py tests/test_gate2_budget.py
  run w3 analysis/gate2_budget.py tests/test_gate2_budget.py tests/test_grid_usage.py
  run w3 analysis/request_effect.py tests/test_request_effect.py
  run w3 runner/paid_run.py tests/test_tool_sandbox.py tests/test_delivery.py tests/test_execute.py tests/test_anthropic_adapter.py tests/test_openai_adapter.py tests/test_w7_t1.py
}
w4() {
  run w4 runner/mock_slice.py tests/test_mock_slice.py tests/test_tool_event_scoring.py tests/test_floor_count.py tests/test_request_effect.py tests/test_execute.py tests/test_trace_integrity.py tests/test_demo_known_traces.py
  run w4 tools/sandbox.py tests/test_tool_sandbox.py tests/test_execute.py tests/test_safe_tools.py
  run w4 defenses/datamarking.py tests/test_datamarking.py tests/test_policy_gate.py tests/test_delivery.py tests/test_defense_contracts.py
  run w4 defenses/canonicalizer.py tests/test_policy_gate.py tests/test_task_suite.py tests/test_agent_loop.py tests/test_ticket_slice.py
  run w4 oracles/authorization/conformance.py tests/test_audit.py tests/test_defense_contracts.py tests/test_policy_gate.py
}
w1 & w2 & w3 & w4 &
wait
echo CONST_DONE >> /home/canary/probes/const_done.txt

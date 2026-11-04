#!/bin/bash
P=/home/canary/probes
PY=/home/canary/work/CANARY/.venv/bin/python
# 1. wait for the tier-2 sample
while pgrep -u canary -f "tier2.py.*t2_sample2" >/dev/null; do sleep 20; done
echo "sample done $(date -u)" >> $P/pipeline.log
# 2. tier 2 on reported findings
$PY $P/tier2.py /home/canary/verify/mutants $P/t2_findings.txt --out $P/t2_findings.jsonl --slow $P/slow_tests.txt --jobs 4 >> $P/pipeline.log 2>&1
echo "findings tier2 done $(date -u)" >> $P/pipeline.log
# 3. new tests vs every tier-1 survivor, by module, 4 at a time
newcheck() { # module-regex testfile outfile
  grep -P "^($1)" $P/all_t1_names.txt | $P/killcheck.sh "$2" > $3
}
newcheck "analysis.gate2_budget" tests/test_gate2_budget_equation.py $P/new_g2.txt &
newcheck "analysis.floor_count" tests/test_floor_count_mutants.py $P/new_fc.txt &
newcheck "analysis.request_effect" tests/test_request_effect_mutants.py $P/new_re.txt &
newcheck "runner.paid_run" tests/test_paid_run_mutants.py $P/new_pr.txt &
wait
newcheck "defenses.interfaces|defenses.datamarking|oracles.authorization.conformance" tests/test_defense_mutants.py $P/new_def.txt &
newcheck "defenses.canonicalizer|defenses.policy_gate|oracles.authorization.audit" tests/test_gate_canonicalizer_mutants.py $P/new_gc.txt &
newcheck "agent.loop|runner.mock_slice" tests/test_loop_mock_slice_mutants.py $P/new_lm.txt &
newcheck "tools.sandbox" tests/test_sandbox_mutants.py $P/new_sb.txt &
wait
newcheck "runner.delivery" tests/test_delivery_mutants.py $P/new_del.txt
echo "newcheck done $(date -u)" >> $P/pipeline.log
# 4. constant mutator
$P/run_const.sh >> $P/pipeline.log 2>&1
echo "const done $(date -u)" >> $P/pipeline.log

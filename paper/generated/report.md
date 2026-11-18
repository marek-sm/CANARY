# CANARY estimand report

> **PRE-RESULTS — NO DATA.** These shells reserve the estimand report's structure. They are not results; `python -m analysis.report RECORDS --active protocol/active.json --out PATH` fills them from the final record set after the sweep's integrity checks.

Decision 0012's request-to-effect table and the tool-name-only ablation are in `analysis.lead_outputs`' output, which `make report` generates first.

## Primary rates

### Model violation rate

- **Estimand/output ID:** `ModelViolationRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Model-violation rates by retained configuration and adapter, including the equal-adapter macro-average and conditional cluster-resampling intervals where applicable.
- **Counts:** —

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### System compromise rate

- **Estimand/output ID:** `SystemCompromiseRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** System-compromise rates by retained configuration and adapter, including the equal-adapter macro-average and required intervals.
- **Counts:** —

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### Clean utility

- **Estimand/output ID:** `CleanUtility`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Clean utility by configuration, task template, and adapter with equal-adapter and equal-task macro-averages.
- **Counts:** —

| Configuration | Task template | Adapter | Passed / observed | Rate or macro-average | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

## Primary paired effects

### D2_DATAMARKING attacked-case risk difference

- **Estimand/output ID:** `DatamarkingAttackRiskDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Paired attacked-case model-violation risk difference for D2_DATAMARKING versus D0_BASELINE, computed within adapters and macro-averaged.
- **Counts:** —

| Adapter | Complete pairs | Missing pairs | Risk difference | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### D2_DATAMARKING clean-adjusted difference

- **Estimand/output ID:** `DatamarkingInjectionSpecificDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Clean-adjusted difference-in-differences for D2_DATAMARKING versus D0_BASELINE, with complete and missing four-cell pair counts.
- **Counts:** —

| Adapter | Complete four-cell pairs | Missing pairs | Difference-in-differences | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### Clean utility cost

- **Estimand/output ID:** `CleanUtilityCost`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Matched clean-utility cost by retained defense, task template, and adapter; a positive value means utility worsened.
- **Counts:** —

| Configuration | Task template | Adapter | Complete pairs | Missing pairs | Utility cost percentage points | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — | — |

### D1_POLICY_GATE residual system-risk difference

- **Estimand/output ID:** `PolicyGateResidualSystemRiskDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Paired system-compromise risk difference for D1_POLICY_GATE versus D0_BASELINE, computed within adapters and macro-averaged.
- **Counts:** —

| Adapter | Complete pairs | Missing pairs | Risk difference | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### Authorized high-risk clean utility

- **Estimand/output ID:** `AuthorizedHighRiskCleanUtility`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Clean utility for active legitimate high-risk task templates by configuration, averaged equally over adapters and task templates.
- **Counts:** —

| Configuration | High-risk task template | Adapter | Passed / observed | Macro-average | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

## D1_POLICY_GATE conformance

### D1_POLICY_GATE unauthorized block conformance

- **Estimand/output ID:** `PolicyGateUnauthorizedBlockRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Exact fraction of evaluable unauthorized D1_POLICY_GATE requests durably blocked before dispatch, including indeterminate and zero-denominator handling.
- **Counts:** —

| Blocked unauthorized requests | Eligible unauthorized requests | Fraction | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### D1_POLICY_GATE enforcement escape conformance

- **Estimand/output ID:** `PolicyGateEnforcementEscapeRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Exact fraction of evaluable unauthorized D1_POLICY_GATE requests durably dispatched, with escaped-effect and indeterminate counts.
- **Counts:** —

| Dispatched unauthorized requests | Eligible unauthorized requests | Fraction | Escapes with observed effect | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — |

### D1_POLICY_GATE authorized dispatch conformance

- **Estimand/output ID:** `PolicyGateAuthorizedDispatchRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Exact fraction of evaluable authorized D1_POLICY_GATE requests durably dispatched, including indeterminate and zero-denominator handling.
- **Counts:** —

| Dispatched authorized requests | Eligible authorized requests | Fraction | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## Matched controls and secondary outcomes

### Background model-violation rate

- **Estimand/output ID:** `BackgroundModelViolationRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Clean-case background model-violation rates by configuration and adapter with equal-adapter macro-averages.
- **Counts:** —

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### Background system-compromise rate

- **Estimand/output ID:** `BackgroundSystemCompromiseRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Clean-case background system-compromise rates by configuration and adapter with equal-adapter macro-averages.
- **Counts:** —

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### Injection excess risk

- **Estimand/output ID:** `InjectionExcessRisk`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Attack-minus-clean paired differences for each supported Boolean endpoint, computed within adapters and macro-averaged.
- **Counts:** —

| Configuration | Endpoint | Adapter | Complete pairs | Missing pairs | Excess risk | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — | — |

### Attack task completion

- **Estimand/output ID:** `AttackTaskCompletion`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Attack-case utility by configuration, task template, and adapter with equal-adapter and equal-task macro-averages.
- **Counts:** —

| Configuration | Task template | Adapter | Passed / observed | Rate or macro-average | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

### Secure task completion

- **Estimand/output ID:** `SecureTaskCompletion`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Attack-case secure-task-completion rates by configuration, task template, and adapter with macro-averages.
- **Counts:** —

| Configuration | Task template | Adapter | Secure completions / observed | Rate or macro-average | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

## Predeclared diagnostic outputs

### Unauthorized outcome decomposition

- **Estimand/output ID:** `UnauthorizedOutcomeDecomposition`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Per-configuration, attack-or-clean condition, and delivery-channel exact true, false, and null counts for the six underlying security facts and their two unions, including model-violation/system-compromise overlap and each union's observed three-fact patterns.
- **Counts:** —

| Configuration | Condition (attack / clean) | Delivery channel / adapter | Outcome, intersection, or three-fact pattern | True | False | Null | Observed denominator |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### D1_POLICY_GATE block reasons

- **Estimand/output ID:** `PolicyGateBlockReasons`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Exact D1_POLICY_GATE block counts and reason distribution without interpreting enforcement as model resistance.
- **Counts:** —

| Block reason | Count | Unknown disposition count | Non-evaluable count |
| --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — |

### Reliability and resource diagnostics

- **Estimand/output ID:** `ReliabilityAndResourceDiagnostics`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Model refusals, malformed calls, step-limit outcomes, infrastructure failures, latency, and token use by configuration.
- **Counts:** —

| Configuration | Diagnostic | Count | Observed denominator | Summary value | Unknown count |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### Mixed-repeat rates

- **Estimand/output ID:** `MixedRepeatRates`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Repeat-group instability by configuration, attack-or-clean condition, delivery channel, and endpoint; incomplete groups are separated into mixed-among-observed and undetermined categories.
- **Counts:** —

| Configuration | Condition (attack / clean) | Delivery channel / adapter | Endpoint | Mixed complete groups | Complete groups | Mixed-repeat rate | Incomplete: mixed among observed | Incomplete: undetermined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

### Paired adapter differences

- **Estimand/output ID:** `PairedAdapterDifferences`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Predeclared paired differences among retained adapters with complete and missing pair counts and required intervals.
- **Counts:** —

| Endpoint | Adapter contrast | Complete pairs | Missing pairs | Difference | 95% conditional cluster-resampling interval | Boundary warning | Missingness range | 5% threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

### Leave-one-attack-family-out sensitivity

- **Estimand/output ID:** `LeaveOneAttackFamilyOutSensitivity`
- **Status:** PRE-RESULTS — NO DATA
- **Caption:** Sensitivity of each primary effect when each attack family is omitted in turn.
- **Counts:** —

| Primary effect | Omitted attack family | Estimate | Change from full estimate | Complete pairs | Missing pairs |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## C1 direct-injection positive controls

> **Direct-injection positive controls; outside the primary threat model; not an estimate.** One row per control and outcome. Counts only: no rate,
> macro-average, interval, or comparison with indirect cases (SPEC.md Section 10).

> **PRE-RESULTS — NO DATA.** Regenerate from the frozen sanitized bundle after the sweep.

| C1 control ID | D0_BASELINE repeat count | Outcome (six facts, two unions, or utility_pass) | True | False | Null | Infrastructure-failure count |
| --- | --- | --- | --- | --- | --- | --- |

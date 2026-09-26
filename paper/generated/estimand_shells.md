# CANARY Generated Estimand Shells

> **PRE-RESULTS — NO DATA.** These placeholders reserve accessible output
> structure only. They are not empirical results and must be regenerated from
> the frozen sanitized bundle after protocol freeze.

Every future chart must retain its caption, alt text, exact counts or pair
counts, interval labeling where required, and the table equivalent below.

## Primary rates

### Model violation rate

- **Estimand/output ID:** `ModelViolationRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Model-violation rates by retained configuration and adapter, including the equal-adapter macro-average and conditional cluster-resampling intervals where applicable.
- **Alt-text scaffold:** Placeholder for model-violation rates; no values are available before the frozen analysis run.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### System compromise rate

- **Estimand/output ID:** `SystemCompromiseRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** System-compromise rates by retained configuration and adapter, including the equal-adapter macro-average and required intervals.
- **Alt-text scaffold:** Placeholder for system-compromise rates; no values are available before the frozen analysis run.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval | Boundary warning |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### Clean utility

- **Estimand/output ID:** `CleanUtility`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Clean utility by configuration, task template, and adapter with equal-adapter and equal-task macro-averages.
- **Alt-text scaffold:** Placeholder for clean-utility component rates and macro-averages; no values are available before the frozen analysis run.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Task template | Adapter | Passed / observed | Rate or macro-average | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## Primary paired effects

### D2_DATAMARKING attacked-case risk difference

- **Estimand/output ID:** `DatamarkingAttackRiskDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Paired attacked-case model-violation risk difference for D2_DATAMARKING versus D0_BASELINE, computed within adapters and macro-averaged.
- **Alt-text scaffold:** Placeholder for the D2_DATAMARKING attacked-case paired difference; negative values would favor D2_DATAMARKING, but no value is available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Adapter | Complete pairs | Missing pairs | Risk difference | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — |

### D2_DATAMARKING clean-adjusted difference

- **Estimand/output ID:** `DatamarkingInjectionSpecificDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Clean-adjusted difference-in-differences for D2_DATAMARKING versus D0_BASELINE, with complete and missing four-cell pair counts.
- **Alt-text scaffold:** Placeholder for the D2_DATAMARKING clean-adjusted paired effect; no value is available before frozen analysis.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Adapter | Complete four-cell pairs | Missing pairs | Difference-in-differences | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — |

### Clean utility cost

- **Estimand/output ID:** `CleanUtilityCost`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Matched clean-utility cost by retained defense, task template, and adapter; a positive value means utility worsened.
- **Alt-text scaffold:** Placeholder for matched clean-utility costs; no values are available before frozen analysis.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Task template | Adapter | Complete pairs | Missing pairs | Utility cost percentage points | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — |

### D1_POLICY_GATE residual system-risk difference

- **Estimand/output ID:** `PolicyGateResidualSystemRiskDifference`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Paired system-compromise risk difference for D1_POLICY_GATE versus D0_BASELINE, computed within adapters and macro-averaged.
- **Alt-text scaffold:** Placeholder for the D1_POLICY_GATE residual system-risk difference; negative values would favor D1_POLICY_GATE, but no value is available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Adapter | Complete pairs | Missing pairs | Risk difference | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — |

### Authorized high-risk clean utility

- **Estimand/output ID:** `AuthorizedHighRiskCleanUtility`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Clean utility for active legitimate high-risk task templates by configuration, averaged equally over adapters and task templates.
- **Alt-text scaffold:** Placeholder for authorized high-risk clean utility; no values are available before frozen analysis.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | High-risk task template | Adapter | Passed / observed | Macro-average | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## D1_POLICY_GATE conformance

### D1_POLICY_GATE unauthorized block conformance

- **Estimand/output ID:** `PolicyGateUnauthorizedBlockRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Exact fraction of evaluable unauthorized D1_POLICY_GATE requests durably blocked before dispatch, including indeterminate and zero-denominator handling.
- **Alt-text scaffold:** Placeholder for D1_POLICY_GATE unauthorized block conformance counts; no request data are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Blocked unauthorized requests | Eligible unauthorized requests | Fraction | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### D1_POLICY_GATE enforcement escape conformance

- **Estimand/output ID:** `PolicyGateEnforcementEscapeRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Exact fraction of evaluable unauthorized D1_POLICY_GATE requests durably dispatched, with escaped-effect and indeterminate counts.
- **Alt-text scaffold:** Placeholder for D1_POLICY_GATE enforcement escape counts; no request data are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Dispatched unauthorized requests | Eligible unauthorized requests | Fraction | Escapes with observed effect | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — |

### D1_POLICY_GATE authorized dispatch conformance

- **Estimand/output ID:** `PolicyGateAuthorizedDispatchRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Exact fraction of evaluable authorized D1_POLICY_GATE requests durably dispatched, including indeterminate and zero-denominator handling.
- **Alt-text scaffold:** Placeholder for D1_POLICY_GATE authorized dispatch conformance counts; no request data are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Dispatched authorized requests | Eligible authorized requests | Fraction | Gate/audit disagreement count | Indeterminate count | Zero-denominator label |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## Matched controls and secondary outcomes

### Background model-violation rate

- **Estimand/output ID:** `BackgroundModelViolationRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Clean-case background model-violation rates by configuration and adapter with equal-adapter macro-averages.
- **Alt-text scaffold:** Placeholder for clean-case background model-violation rates; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — |

### Background system-compromise rate

- **Estimand/output ID:** `BackgroundSystemCompromiseRate`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Clean-case background system-compromise rates by configuration and adapter with equal-adapter macro-averages.
- **Alt-text scaffold:** Placeholder for clean-case background system-compromise rates; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Adapter | Observed true / observed endpoint | Rate | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — |

### Injection excess risk

- **Estimand/output ID:** `InjectionExcessRisk`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Attack-minus-clean paired differences for each supported Boolean endpoint, computed within adapters and macro-averaged.
- **Alt-text scaffold:** Placeholder for attack-minus-clean endpoint differences; no values are available before frozen analysis.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Endpoint | Adapter | Complete pairs | Missing pairs | Excess risk | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — |

### Attack task completion

- **Estimand/output ID:** `AttackTaskCompletion`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Attack-case utility by configuration, task template, and adapter with equal-adapter and equal-task macro-averages.
- **Alt-text scaffold:** Placeholder for attack-case task-completion rates; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Task template | Adapter | Passed / observed | Rate or macro-average | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### Secure task completion

- **Estimand/output ID:** `SecureTaskCompletion`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Attack-case secure-task-completion rates by configuration, task template, and adapter with macro-averages.
- **Alt-text scaffold:** Placeholder for secure-task-completion rates combining utility and security evidence; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Task template | Adapter | Secure completions / observed | Rate or macro-average | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## Predeclared diagnostic outputs

### Unauthorized outcome decomposition

- **Estimand/output ID:** `UnauthorizedOutcomeDecomposition`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Per-configuration, attack-or-clean condition, and delivery-channel exact true, false, and null counts for the six underlying security facts and their two unions, including model-violation/system-compromise overlap and each union's observed three-fact patterns.
- **Alt-text scaffold:** Placeholder separating attack and clean cases and delivery channels while showing known, unknown, overlapping, and union-pattern security outcomes; no counts are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Condition (attack / clean) | Delivery channel / adapter | Outcome, intersection, or three-fact pattern | True | False | Null | Observed denominator |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — |

### D1_POLICY_GATE block reasons

- **Estimand/output ID:** `PolicyGateBlockReasons`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Exact D1_POLICY_GATE block counts and reason distribution without interpreting enforcement as model resistance.
- **Alt-text scaffold:** Placeholder for D1_POLICY_GATE block reasons and counts; no request data are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Block reason | Count | Unknown disposition count | Non-evaluable count |
| --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — |

### Reliability and resource diagnostics

- **Estimand/output ID:** `ReliabilityAndResourceDiagnostics`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Model refusals, malformed calls, step-limit outcomes, infrastructure failures, latency, and token use by configuration.
- **Alt-text scaffold:** Placeholder for reliability, latency, and token-use diagnostics; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Diagnostic | Count | Observed denominator | Summary value | Unknown count |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### Mixed-repeat rates

- **Estimand/output ID:** `MixedRepeatRates`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Repeat-group instability by configuration, attack-or-clean condition, delivery channel, and endpoint; incomplete groups are separated into mixed-among-observed and undetermined categories.
- **Alt-text scaffold:** Placeholder separating attack and clean repeat groups by delivery channel, including complete-group mixed rates and distinct incomplete groups that are mixed among observed repeats or undetermined; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Configuration | Condition (attack / clean) | Delivery channel / adapter | Endpoint | Mixed complete groups | Complete groups | Mixed-repeat rate | Incomplete: mixed among observed | Incomplete: undetermined |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — | — | — |

### C1 direct-injection positive controls

- **Estimand/output ID:** `C1DirectInjectionControls`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Separate descriptive C1 direct-injection positive-control table with one row per control and no rate, macro-average, interval, or comparison with indirect cases.
- **Alt-text scaffold:** Placeholder for each C1 control's repeat count, exact true, false, and null security and utility outcomes, and infrastructure-failure count; C1 is outside the primary threat model and no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| C1 control ID | D0_BASELINE repeat count | Outcome (six facts, two unions, or utility_pass) | True | False | Null | Infrastructure-failure count |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — | — |

### Paired adapter differences

- **Estimand/output ID:** `PairedAdapterDifferences`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Predeclared paired differences among retained adapters with complete and missing pair counts and required intervals.
- **Alt-text scaffold:** Placeholder for paired adapter differences; no values are available before frozen analysis.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Endpoint | Adapter contrast | Complete pairs | Missing pairs | Difference | 95% conditional cluster-resampling interval |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

### Leave-one-attack-family-out sensitivity

- **Estimand/output ID:** `LeaveOneAttackFamilyOutSensitivity`
- **Status:** PRE-RESULTS — NO DATA
- **Caption scaffold:** Sensitivity of each primary effect when each attack family is omitted in turn.
- **Alt-text scaffold:** Placeholder for leave-one-attack-family-out sensitivity estimates; no values are available.
- **Figure shell:** Intentionally empty until generated from frozen evidence.

#### Table equivalent

| Primary effect | Omitted attack family | Estimate | Change from full estimate | Complete pairs | Missing pairs |
| --- | --- | --- | --- | --- | --- |
| PRE-RESULTS — NO DATA | — | — | — | — | — |

## Accessibility and claim check

- [ ] Every rendered chart has meaningful final alt text.
- [ ] Every chart has a table equivalent with repeated headers.
- [ ] Color is not the sole carrier of meaning and contrast is checked.
- [ ] Exact numerators/denominators or complete/missing pair counts are shown.
- [ ] Required intervals use the approved conditional cluster-resampling label.
- [ ] Boundary warnings appear when an interval collapses.
- [ ] All values came from the frozen sanitized bundle; none were hand-entered.

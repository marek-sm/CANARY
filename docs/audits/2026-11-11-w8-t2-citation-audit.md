# W8-T2 corpus-freeze citation audit

SPEC.md Section 15: at corpus freeze, every case-level source has a human opener and a different human reviewer, and both verify URL, title/version, case identity, relevance, and license. This worksheet covers the 20 cases in the frozen `F20` corpus (`corpus/evaluation/eval-001` to `eval-020`).

**What was checked by script (November 11).** Each pinned source file was fetched again at its pinned version, outside the repository, and each case's `original_payload` was found byte-for-byte in it: InjecAgent and ASB by line, AgentDojo by rebuilding the goal from the suite's class constants and the attack wrapper, and LLMail-Inject by exact key in `data/labelled_unique_submissions_phase1.json`. Every stored `original_payload_sha256` recomputes. All four license files read MIT at their pins. That's evidence for the human checks below, not a substitute for them.

**What the humans check.** Open the source at the pinned version, find the case, and confirm the URL, title and version, case identity, that the case is an indirect injection against an agent's tools or data (relevance), and the license. Tick your column only after opening it yourself.

## Sources

| Key | Pinned source | License |
|---|---|---|
| `injecagent-2024` | https://github.com/uiuc-kang-lab/InjecAgent/tree/f19c9f2c79a41046eb13c03c51a24c567a8ffa07 | MIT (`LICENCE`) |
| `agentdojo-2024` | https://github.com/ethz-spylab/agentdojo/tree/v0.1.35 | MIT (`LICENSE`) |
| `asb-2024` | https://github.com/agiresearch/ASB/tree/544540ff0788998072f7df463056fd17e62cc9f4 | MIT (`LICENSE`) |
| `llmail-inject-2025` | https://huggingface.co/datasets/microsoft/llmail-inject-challenge/tree/1063bdf01ec8762b812d5e06ee768a06faa5a6f7 | MIT (dataset card) |

## Cases

| Case | Source | Case identity | Goal / family | Script: found at pin, hash | Opener `j0hanj` | Reviewer `marek-sm` |
|---|---|---|---|---|---|---|
| `eval-001` | `injecagent-2024` | attacker_cases_ds.jsonl line 7 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-002` | `llmail-inject-2025` | phase-1 submission with text SHA-256 b1f4d516daa966a7 | unauthorized_action / crafted-email-injection | yes, yes | [ ] | [ ] |
| `eval-003` | `injecagent-2024` | attacker_cases_ds.jsonl line 32 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-004` | `llmail-inject-2025` | phase-1 submission with text SHA-256 4d86a4665b5028e1 | unauthorized_action / crafted-email-injection | yes, yes | [ ] | [ ] |
| `eval-005` | `injecagent-2024` | attacker_cases_ds.jsonl line 6 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-006` | `llmail-inject-2025` | phase-1 submission with text SHA-256 ad94d343d0620358 | unauthorized_action / crafted-email-injection | yes, yes | [ ] | [ ] |
| `eval-007` | `agentdojo-2024` | travel/injection_task_3+important_instructions_no_names | secret_disclosure / important-instructions-impersonation | yes, yes | [ ] | [ ] |
| `eval-008` | `agentdojo-2024` | travel/injection_task_1+direct | unauthorized_action / todo-directive | yes, yes | [ ] | [ ] |
| `eval-009` | `injecagent-2024` | attacker_cases_ds.jsonl line 27 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-010` | `llmail-inject-2025` | phase-1 submission with text SHA-256 d512176ca77046e1 | unauthorized_action / crafted-email-injection | yes, yes | [ ] | [ ] |
| `eval-011` | `asb-2024` | all_attack_tools.jsonl line 67 (StealthBackup) + fake_completion | secret_disclosure / fake-completion | yes, yes | [ ] | [ ] |
| `eval-012` | `agentdojo-2024` | slack/injection_task_1+injecagent | unauthorized_action / ignore-previous-instructions | yes, yes | [ ] | [ ] |
| `eval-013` | `injecagent-2024` | attacker_cases_ds.jsonl line 5 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-014` | `agentdojo-2024` | slack/injection_task_3+ignore_previous | unauthorized_action / ignore-previous-instructions | yes, yes | [ ] | [ ] |
| `eval-015` | `asb-2024` | all_attack_tools.jsonl line 4 (StealthDataExport) + naive | secret_disclosure / tool-forcing-directive | yes, yes | [ ] | [ ] |
| `eval-016` | `agentdojo-2024` | slack/injection_task_1+system_message | unauthorized_action / system-message-spoof | yes, yes | [ ] | [ ] |
| `eval-017` | `injecagent-2024` | attacker_cases_ds.jsonl line 30 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-018` | `agentdojo-2024` | slack/injection_task_3+direct | unauthorized_action / todo-directive | yes, yes | [ ] | [ ] |
| `eval-019` | `injecagent-2024` | attacker_cases_dh.jsonl line 23 | secret_disclosure / tool-result-instruction-override | yes, yes | [ ] | [ ] |
| `eval-020` | `agentdojo-2024` | slack/injection_task_3+system_message | unauthorized_action / system-message-spoof | yes, yes | [ ] | [ ] |

## Sign-off

- Opener (`j0hanj`): every row ticked after opening the source. Date: ____
- Reviewer (`marek-sm`): every row ticked after opening the source. Date: ____

# Raw-record manifests: the official sweep and C1 runs

These files publish the SHA-256 hash of every raw results and events file in the official sweep and C1 runs, under [decision 0025](../../decisions/0025-full-study.md) item 5's manifest form. The raw records stay outside Git, in the private raw-record storage. These files hold no provider body, canary, host path, or security or utility outcome.

## Files

| File | Run | Trials | Files hashed | SHA-256 of this file |
|---|---|---:|---:|---|
| [`sweep-raw-manifest.json`](sweep-raw-manifest.json) | `results/raw/sweep/canary-2026-sweep` | 1,080 | 2,160 | `5f60c26689ed0331b35916c77b0fb964cb4c7e07bc536381b851329bcc915cb8` |
| [`c1-raw-manifest.json`](c1-raw-manifest.json) | `results/raw/c1/canary-2026-sweep` | 12 | 24 | `95a9ec9c9611592c257964dbae90d4e1c0add6726546f683d8957e97e99ed994` |

Each file is the unedited output of `runner.raw_manifest`. The project lead ran it at about 6:05 pm Pacific on November 18, 2026, from the Gate 3 checkout at `dd9b02e`:

```
python -m runner.raw_manifest results/raw/sweep/canary-2026-sweep --out sweep-raw-manifest.json
python -m runner.raw_manifest results/raw/c1/canary-2026-sweep --out c1-raw-manifest.json
```

The two runs are written separately because both folders are named `canary-2026-sweep`, and the tool refuses two runs with one name. Anyone with access to the raw storage can compare a run with its manifest:

```
python -m runner.raw_manifest RUN --check MANIFEST
```

## What each manifest records

Both manifests record the same values:

- **Experiment:** `canary-2026-sweep`.
- **Model:** `claude-haiku-5-5`, the only requested or resolved model in the results, and `mock` is false.
- **Code commit:** `dd9b02ea5b7480171c2baab309367330effa739a`, the commit the runs recorded. It is the head of the Gate 3 branch, later than `protocol/active.json`'s `code_commit`, `2b20105`. The files that differ between the two are the Gate 3 step's protocol files and documents, and none is in the paid-run code digest's hashed paths.
- **Code digest:** `e36bd5ba3cf0ea8be80c3c3ca4a8cf43d36e154e26f4d7838d9c799df03a23a8`.
- **Paid-run record commit:** `8b313aa88d91eb49a64f34dc6142c580342c74d4`, the `recorded_commit` in the [Gate 3 record](../gate3-2026-11-15/README.md).

## What these files do not establish

- **They anchor the files only from publication onward.** They were written after the runs finished, so they can't show what a file held before November 18.
- **They cover only `results.jsonl` and `events.jsonl`.** Other files in a run folder aren't hashed here.
- **They don't replace batch hashes.** [Decision 0028](../../decisions/0028-restore-strength.md) item 8 called for batch hashes of raw records to be committed during the sweep. No commit in this repository added any.
- **The sweep folder moved once before these hashes were taken.** On November 16, after its first check, it was moved into the private storage and then restored. On November 17 the project lead re-ran `runner.sweep verify` on the restored folder, which reported `complete: True` with 1,080 of 1,080 trials, and `analysis.gate3_hashes --check-run`, which passed. The C1 folder wasn't moved.
- **They aren't a Gate 4 result.** The `SPEC.md` Section 11 Gate 4 evidence, including the sanitized manifests and generated outputs, is recorded separately.

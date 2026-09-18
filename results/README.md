# CANARY Results

This directory holds experimental evidence and the records needed to regenerate every public number from it. It defines provenance and regeneration procedure only. Field meaning lives in `SPEC.md` Section 8, serialized shapes in `schemas/`, the sanitization and release rules in `docs/DATA_RELEASE.md`, and the exact frozen instance in `protocol/active.json`.

**No release bundle exists yet.** `results/public/` is empty, no protocol has been frozen, and no result, interval, or defense-effect value has been produced. Any number appearing in the README, paper, demo, or a talk before a bundle exists is not a CANARY result.

## Layout

| Path | Contents | Public? |
|---|---|---|
| `development/` | Development-run evidence: pilots, smokes, the mock vertical slice, grid runs | No. Gitignored. Never used in paper estimates. |
| `public/` | The sanitized frozen bundle for one release: result or validation records, active protocol, manifest, generated analysis inputs | Yes, after the release checks in `docs/DATA_RELEASE.md` pass. |

Raw append-only evidence stays immutable. When it carries restricted or provider-only material it lives in access-controlled storage outside this repository, and only the sanitizer output is committed here.

## Provenance

Every file under `public/` is identified by its manifest entry, not by its filename. A bundle is traceable only if all of these agree:

- the manifest (`manifest.schema.json`): file paths, sizes, hashes, bundle type, sanitizer version, and producing commit;
- `protocol/active.json`: active tier, active-contributor count, ordered cases, channels, conditions, configurations, repeats, seeds, hashes, cutoffs, and the model or the explicit null-with-reason;
- the bound schema versions for every record family; and
- the release tag or commit.

A repair or rerun receives a new experiment or validation ID and a new manifest. It never overwrites prior evidence. Superseded bundles stay documented and are excluded from official counts.

## Regeneration

Regeneration consumes the frozen bundle. It does not consume a hand-entered value, a screenshot, a retyped table, or a live model call.

1. Clone the repository at the release tag.
2. Verify that every manifest hash matches the committed bundle.
3. Verify that the bundle validates against the schema versions bound by `protocol/active.json`.
4. Recompute the Boolean-or-null endpoints from the stored raw evidence and confirm they equal the stored derived fields.
5. Generate the analysis or validation report from the bundle and compare it against the released artifact.

The stable commands for steps 4 and 5 are defined in `docs/INTERFACES.md`. They are not implemented yet and are therefore not documented here as runnable; this file is updated in the same pull request that makes them real.

## Rules

- No file here is hand-edited. Scored fields are produced by the scorer and altered by nothing afterward, including the sanitizer.
- Unknown evidence stays `null`. It is never converted to `false`.
- Development evidence never enters a paper estimate, a README value, or a demo aggregate.
- A displayed number that cannot be traced to a manifest entry in `public/` blocks release until `SPEC.md` Section 11 resolves it.
- Adding a bundle here requires the full release checklist in `docs/DATA_RELEASE.md`, not just a passing test.
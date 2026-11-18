# ADR 0011: Versioning, Vendored Copies and Strict Rejection

**Status:** Implemented
**Scope:** `spec_version` in every file; the `v0/` directory; `tests/`

---

## 1. Context

Several independent consumers in different languages read these files. They must agree on what is valid, without mxl-schemas becoming a build dependency of all of them.

The format is still changing frequently. Every consumer lives in the same meta-repo and is updated together with it, so there is nobody yet whose files a breaking change would strand.

## 2. Decision

- Every file carries `spec_version`.
- **Pre-1.0 (now):** versions are `0.x` and the schemas live in `v0/`. A minor bump may change the format incompatibly; the schemas, fixtures and every consumer are updated in lockstep.
- **From 1.0 on:** `1.0` (in `v1/`) is the first stable release. Minor versions only add (1.0 files are valid 1.1 files); a breaking change is a new major version in a new directory (`v2/`), with `v1/` left valid.
- Schemas are referenced by their `$id` URL. Consumers vendor a copy and test it against the canonical one (drift tests); mxl-schemas is plain JSON with no dependencies.
- Fixtures (`tests/*.fixtures.json`) are part of the contract: changing a fixture's expected outcome is a breaking change.
- Unknown versions and unknown fields are rejected explicitly (`additionalProperties: false`). A consumer never silently drops what it does not understand.

## 3. Rationale

**No dependencies.** Any language can read JSON; a schema change never breaks a consumer's build by itself, and drift tests surface divergence.

**Explicit rejection over silent loss.** Dropping unknown fields would make a file look correctly loaded while losing part of the model; rejecting it makes the version mismatch visible.

**0.x while it settles.** A `1.x` number promises a stability the format does not have yet. Staying at 0.x keeps that promise for the release that can actually keep it.

## 4. Consequences

- A consumer has to be updated before it can read files of a newer version.
- Every schema change is coordinated with the consumers' vendored copies.
- Pre-1.0, a breaking minor bump comes with no compatibility shims: consumers reject files written before it, and in-repo files are migrated with the change.

## 5. History

- 2026-11-18: the format was renumbered from 1.x to 0.x and `v1/` moved to `v0/`, without any change to the format itself. Model files: 1.0→0.1, 1.1→0.2 (units), 1.2→0.3 (`data_ref`), 1.3→0.4 (array-valued derived quantities). Analysis: 1.1→0.1. Registries: `units.json` 1.1→0.2, `identifiers.json` 1.0→0.1. The other ADRs were updated to the new numbers.

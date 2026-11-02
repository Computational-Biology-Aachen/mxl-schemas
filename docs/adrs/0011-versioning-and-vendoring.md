# ADR 0011: Versioning, Vendored Copies and Strict Rejection

**Status:** Implemented
**Scope:** `spec_version` in every file; the `v1/` directory; `tests/`

---

## 1. Context

Several independent consumers in different languages read these files. They must agree on what is valid, without mxl-schemas becoming a build dependency of all of them.

## 2. Decision

- Every file carries `spec_version`. Minor versions only add (1.0 files are valid 1.1 files); a breaking change is a new major version in a new directory (`v2/`), with `v1/` left valid.
- Schemas are referenced by their `$id` URL. Consumers vendor a copy and test it against the canonical one (drift tests); mxl-schemas is plain JSON with no dependencies.
- Fixtures (`tests/*.fixtures.json`) are part of the contract: changing a fixture's expected outcome is a breaking change.
- Unknown versions and unknown fields are rejected explicitly (`additionalProperties: false`). A consumer never silently drops what it does not understand.

## 3. Rationale

**No dependencies.** Any language can read JSON; a schema change never breaks a consumer's build by itself, and drift tests surface divergence.

**Explicit rejection over silent loss.** Dropping unknown fields would make a file look correctly loaded while losing part of the model; rejecting it makes the version mismatch visible.

## 4. Consequences

- A consumer has to be updated before it can read files of a newer minor version.
- Every schema change is coordinated with the consumers' vendored copies.

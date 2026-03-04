# Implementation Plan - Compliance Enhancements

This track focuses on improving the development workflow, ensuring repository hardening, and enforcing semantic versioning.

## Current Goals

- [x] **Semantic Versioning**: Bump to v0.6.1 following repository hardening.
- [x] **Environment Fixes**: Corrected broken import in `.gemini/GEMINI.md`.
- [x] **Workflow Enforcement**: Added `just pr` helper and transitioned to PR-based updates.
- [x] **Signing Compliance**: Documented requirement for signed commits in GitHub.

## Tasks

- [x] Identify versioning gap (v0.6.0 -> v0.6.1) and apply update.
- [x] Fix broken `@./code-ordering.md` path.
- [x] Add `just pr` helper to Justfile for creating Pull Requests.
- [x] Update GEMINI.md to mandate `just check` for all commits.
- [x] Verified and documented commit signing requirements for repository integrity.

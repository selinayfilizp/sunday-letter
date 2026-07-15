# Changelog

All notable changes to The Sunday Letter are documented here.

## 0.4.0 - 2026-07-14

### Added

- End-to-end local support for both Codex and Claude Code.
- A Claude Code collector and validated marketplace manifest.
- A generated local archive with Pause, Resume, Export, Delete, and Archive actions.
- Social preview cards for the public site and sample letter.
- Continuous tests on macOS and Linux.

### Changed

- Replaced unmeasured confidence and productivity claims with dated provenance.
- Unified both supported hosts behind one collect, redact, validate, delta-gate,
  render, ledger, and archive pipeline.
- Made silence the required result when the selected source window contains no
  meaningful change.
- Serialized shared-ledger transactions so simultaneous host runs cannot reuse
  a letter number or overwrite one another.

### Security

- Sanitized generated rich text with a strict allowlist and restrictive Content
  Security Policy.
- Restricted the archive server to loopback and guarded archive actions against
  cross-origin requests and path traversal.
- Kept generated archives private by default and documented collection,
  retention, redaction, and deletion boundaries.

## 0.1.0 - 2026-04-17

- Initial public experiment.

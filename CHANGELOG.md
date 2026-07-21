# Changelog

All notable changes to The Sunday Letter are documented here.

## 0.4.1 - 2026-07-14

### Security

- The archive server now validates the Host header on every request, closing a
  DNS rebinding path that could have exposed private letters to a malicious
  website while the server was running.
- Redaction now also covers JWTs, PEM private key blocks, and Slack tokens.

### Added

- A duplicate-week guard: when a letter already shipped in the last six days,
  the runtime refuses to ship another without --force, and the skill reports
  the situation instead of forcing.
- Every ledger entry and rendered letter now carries its verified source scope
  instead of a generic label.

### Fixed

- The archive page no longer styles silent weeks in italic.
- install.sh warns when the Claude Code plugin is also installed via the
  marketplace, so slash commands are not duplicated.

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

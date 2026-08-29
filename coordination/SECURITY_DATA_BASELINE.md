# Improve Yourself — Security & Data Baseline

Status: V1 baseline / coordination

## Fixed principles

- Do not expose the full proprietary reference/learning dataset to the client unless technically required.
- Desktop clients must not connect directly to the backend database.
- Client data delivery path: HTTPS API -> backend validation/authorization -> database.
- FTP is not part of the baseline architecture.
- Collect only data actually needed for System Check / learning / validation.
- Keep personal/user-identifying data out of the hardware dataset wherever possible.
- Document data provenance by portal/source and retrieval/search path, not by individual person/account.
- Keep the product read-only with respect to user system changes unless a later explicit decision supersedes this.

## Storage / transport baseline

### Client -> server

Preferred: HTTPS API using TLS.

Responsibilities of the API layer:
- schema validation
- authentication/authorization where required
- rate limiting
- rejection of malformed or unexpected payloads
- removal/rejection of fields outside the approved data contract
- separation between public/client-facing operations and internal data administration

### Backend database

Preferred server-side candidate for the shared dataset: PostgreSQL.

Reasons:
- mature relational database
- strong schema/constraint support
- suitable for structured hardware combinations and later analytical queries
- encrypted network connections supported through TLS
- permissions can be restricted by service/role

The desktop application must not receive direct database credentials.

### Local client data

If local persistence is required, keep only the minimum needed by the client. A local SQLite database is acceptable for local state/cache. If sensitive/proprietary local data must be encrypted, SQLCipher/AES-256 is a candidate; final selection depends on the actual local data contract and key-management design.

## Encryption / secrets

- Encryption at rest is a protection layer, not a substitute for access control.
- Encryption keys/secrets must be separated from the encrypted data where practical.
- Do not hard-code production database credentials or master encryption keys into the desktop client.
- Provide a recoverable key-management/backup plan before long-lived encrypted data becomes authoritative.
- Prefer managed secret/key storage when a hosted backend is introduced, subject to the confirmed deployment platform.

## Data classes

Keep these logically separate:

1. `hardware_case`
   - hardware/environment facts used for recognition/coverage
   - no inferred recommendation stored as fact

2. `measurement`
   - actual measured/tested result with method/version/timestamp metadata

3. `source_provenance`
   - portal/source
   - retrieval/search path
   - retrieval date
   - evidence/quality notes
   - no unnecessary personal/account information

4. `derived_result`
   - later analysis/recommendation output
   - must remain distinguishable from source facts and measurements

## Privacy baseline

- Data minimization by default.
- Do not collect names, usernames, email addresses, IP addresses, account IDs, hardware serial numbers or other identifying fields unless a confirmed feature genuinely requires them.
- If a stable installation identifier becomes necessary, prefer a pseudonymous/random identifier and document purpose, retention and deletion behavior before release.
- User-facing disclosure/consent requirements must be defined from the final data contract before public release.

## Rights / protection baseline

- Source code: copyright/license protection.
- Proprietary curated dataset and internal logic: treat as confidential/proprietary material and apply access restrictions.
- Do not copy third-party protected datasets wholesale without confirming usage rights.
- Before public release, prepare/review: license/EULA or terms of use, privacy notice, third-party license inventory, and liability/warranty language appropriate to the actual product behavior.

## Current architecture choice

For the present V1 planning baseline:

`Desktop client -> HTTPS API -> backend service -> PostgreSQL`

Optional local persistence:

`Desktop client -> minimal local SQLite/SQLCipher store`

This document defines a baseline only. It does not authorize Azure/cloud deployment, new paid infrastructure, collection of user telemetry, or changes to the existing product architecture without a separate confirmed implementation decision.

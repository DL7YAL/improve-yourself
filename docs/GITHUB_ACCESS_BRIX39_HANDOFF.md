# GitHub access handoff: Brix39 and DL7YAL

Date: 2026-09-13
Status: PARTIAL — organization ownership, Windows SSH and Azure verification pending.

## Approved target

Brix39 is the personal main account. DL7YAL remains the organization and
repository owner. Keep `git@github.com:DL7YAL/improve-yourself.git`.
Do not transfer repositories or remove existing owners, keys or access.
Windows accounts and service billing are outside this task.

## Fresh evidence

- Connected GitHub user: Brix39.
- Repository owner: DL7YAL, type Organization.
- Brix39 repository permission: admin, verified by collaborator permission query.
  Repository metadata also reports admin, maintain, push and pull.
- Organization membership query returned an empty list. This is not proof of
  absence of membership and does not establish Owner status.
- The current connector exposes installations on Brix39 and DL7YAL with
  repository selection `all`. These are not evidence of Azure's installation.
  Installation administration capability and complete permission sets were
  not returned.
- GitHub CLI is unavailable in the inspected Linux session.
- Linux SSH to GitHub fails with `Permission denied (publickey)`; no usable
  agent socket was established by the check.
- Public HTTPS ls-remote and fetch succeed. This proves repository readability,
  not authenticated SSH access.
- Inspected Linux checkout is clean on
  `codex/benchmark-v1.2-runtime-evidence` at
  `fe34c0f823f394aa80c71aa3f3c02b9cf298de41`, matching its remote branch.
- Remote main was `b56aa3413480b1f082b4b2ef65346add7a1b1761`.
  This documentation branch starts there, independently of the benchmark branch.
- Multiple Windows checkouts and a Windows GitHub public key exist.
  The active Windows working source is not yet established.
- Inspected Linux repository-local author configuration is
  `DL7YAL <DL7YAL@users.noreply.github.com>`. It is not proven as Brix39's
  verified commit address. No author setting was changed.

## Changes and validation boundary

This task creates the documentation branch
`codex/brix39-github-access-handoff` and this handoff through the authenticated
GitHub connector. Successful publication demonstrates connector branch/file
write access, not command-line SSH push access.
No account role, credential, Azure setting or existing checkout content is changed.
No application behavior changes; application tests are NOT RUN.

## Required continuation

1. In DL7YAL People, verify Brix39 has Owner role. If absent, an existing Owner
   must grant it and any invitation must be accepted. Repository admin alone
   cannot establish organization ownership. No organization membership
   administration tool is exposed in this session.
2. User confirms two-factor protection and recovery readiness without sharing
   codes. These settings were not observable through the available connector.
3. Identify the active Windows checkout before configuring Git. From that
   Windows environment, run `ssh -T git@github.com` and verify the greeting
   identifies Brix39. Preserve existing private keys.
4. Verify that checkout's remote, working changes, branch and fetch. Confirm
   Brix39's actual verified/noreply commit email in GitHub settings before
   changing repository-local author configuration.
5. Inventory organization access, repository collaborators, branch rules and
   app permissions using an organization-owner session. Available tools did
   not provide a complete inventory.
6. Inspect the actual Azure Foundry GitHub connection. Limit its review access
   to required repository contents and metadata where supported. Do not infer
   its identity from this connector. Have Azure read README.md at the exact
   commit chosen for its review. Azure runtime read test: NOT RUN.
7. Record the remaining tests and final status. Keep old access until removal
   is separately approved. Do not merge this branch automatically.

## Recovery

Existing access settings and SSH remote remain unchanged.
The documentation can be superseded by a later corrective commit.
Private machine paths and credentials must remain outside this repository.

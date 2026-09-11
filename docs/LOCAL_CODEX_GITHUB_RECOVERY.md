# Local Codex and GitHub recovery

This document preserves the non-secret setup required to restore the shared
local Codex workspace after a Windows or Codex reinstallation.

## Current shared setup

- Repository: `git@github.com:DL7YAL/improve-yourself.git`
- Default branch: `main`
- Git commit identity: `DL7YAL <DL7YAL@users.noreply.github.com>`
- Local Codex is hosted by account 1 on the fixed local machine.
- Account 2 uses that same local Codex environment. It has separate ChatGPT
  context and usage, but edits the same checked-out files when it accesses the
  fixed local Codex instance.

The repository is the portable shared project record. Chat history is not a
backup mechanism.

## Secrets deliberately excluded

Never commit or share these through the repository:

- `%USERPROFILE%\.ssh\id_ed25519_github` (private key)
- access tokens, passwords, cookies, or machine-specific credentials

The public counterpart (`id_ed25519_github.pub`) may be added to GitHub under
**Settings > SSH and GPG keys**. A private key must be recreated after a clean
installation unless it has been independently backed up in an encrypted,
access-controlled password manager or recovery store.

## Recovery procedure

1. Install Git for Windows with OpenSSH and install/sign in to Codex on the
   fixed local machine as account 1.
2. Download this repository as a ZIP from GitHub, extract it somewhere
   temporary, and run its restoration script in an elevated PowerShell only if
   your environment requires elevation:

   ```powershell
   .\tools\dev\Restore-GitHubWorkspace.ps1
   ```

3. On its first execution, the script creates a new `ed25519` key and prints
   its public half. Add that public key to the GitHub **account** settings, not
   to a repository's Deploy keys page.
4. Run the script again. It clones (or refreshes) the local working copy,
   configures the repository-only Git identity, and performs a safe
   fast-forward-only pull.
5. Open the restored workspace in the fixed local Codex instance. Account 2
   then continues by connecting to that local Codex; do not create a second
   clone for it.

The script stops rather than overwriting a non-empty folder that is not already
a Git repository.

## Normal synchronization

Before starting work:

```powershell
git pull --ff-only
```

After reviewing a change:

```powershell
git add .
git commit -m "Describe the change"
git push
```

Use `git status` before committing. Do not add private keys or credentials.

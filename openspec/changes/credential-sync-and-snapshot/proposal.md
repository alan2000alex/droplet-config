## Why

Each spin-up cycle requires re-authenticating CLI tools (Claude Code, Gemini, Codex) and re-registering an SSH key with GitHub — credentials are lost when the droplet is destroyed. Copying credentials between the local machine and the VM eliminates this friction without baking secrets into cloud storage.

## What Changes

- `tear-down.sh` gains a preflight SSH reachability check, then rsyncs credential directories and the GitHub SSH keypair from the droplet to `local/creds/` before destroying
- `spin-up.sh` rsyncs credentials from `local/creds/` back to the new droplet after Ansible completes, then sets correct SSH key permissions
- `local/` is added to `.gitignore` to ensure credentials never enter version control
- Bootstrap path: first-ever spin-up is a no-op rsync (no creds yet); tear-down seeds `local/creds/` from that point forward

## Capabilities

### New Capabilities

- `credential-sync`: Bidirectional rsync of credential directories (`~/.claude/`, `~/.gemini/`, `~/.codex/`) and GitHub SSH keypair (`~/.ssh/github_ed25519`, `~/.ssh/github_ed25519.pub`) between the local machine and a droplet, executed as part of the spin-up and tear-down scripts.

### Modified Capabilities

- `spin-up-tear-down-workflow`: Tear-down gains a preflight reachability check and credential pull step; spin-up gains a credential push step and SSH key permission enforcement after Ansible completes.

## Impact

- `scripts/spin-up.sh` — adds credential push + chmod after Ansible
- `scripts/tear-down.sh` — adds SSH preflight check + credential pull before destroy
- `.gitignore` — adds `local/` exclusion
- `local/creds/` — new gitignored directory holding synced credentials between sessions
- Host dependency: `rsync` (standard on macOS and Linux)

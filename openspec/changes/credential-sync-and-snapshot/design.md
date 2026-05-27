## Context

The spin-up/tear-down workflow provisions a fresh DigitalOcean droplet via Terraform and configures it via Ansible. Currently, CLI tool credentials (`~/.claude/`, `~/.gemini/`, `~/.codex/`) and the GitHub SSH keypair are lost on every `terraform destroy`, requiring manual re-authentication and GitHub key registration on each new VM.

The droplet runs as root (`ansible_user=root`). The local machine already holds the SSH private key used to access the droplet (`~/.ssh/alan_vivo_lunix`), so no new auth mechanism is needed for the sync transport.

## Goals / Non-Goals

**Goals:**
- Save credential directories and GitHub SSH keypair from the VM to the local machine on tear-down
- Restore them to the new VM on spin-up
- Warn (and require confirmation) if the droplet is unreachable during tear-down before credentials can be pulled
- Never commit credentials to git

**Non-Goals:**
- Snapshotting the full VM disk (out of scope per user decision)
- Encrypting the local credential store (out of scope; local machine security is assumed)
- Syncing credentials for tools beyond the three listed (`~/.claude/`, `~/.gemini/`, `~/.codex/`)
- Managing DigitalOcean SSH keys for droplet access (unchanged)

## Decisions

### D1: rsync over scp for credential transfer
rsync is used rather than scp because it handles directories, is idempotent, preserves permissions with `-a`, and skips files that haven't changed. The existing SSH key and droplet IP are already available in both scripts, so the transport is zero-config.

### D2: `local/creds/` inside the repo, protected by `.gitignore`
Keeping the creds directory inside the repo root (gitignored) is convenient — it travels with the project and is found relative to `ROOT_DIR` without extra configuration. The risk of accidental git commit is mitigated by a `local/` entry in `.gitignore`. Alternative considered: `~/.droplet-creds/` outside the repo — rejected as it requires out-of-band setup and doesn't travel with the repo.

### D3: Sync specific SSH key files, not `~/.ssh/` wholesale
Only `~/.ssh/github_ed25519` and `~/.ssh/github_ed25519.pub` are synced. Syncing the whole `~/.ssh/` directory risks overwriting `~/.ssh/authorized_keys` (which controls droplet SSH access) or `~/.ssh/known_hosts` (which would cause host-key mismatch errors). Explicit file list is safer.

### D4: Credential push happens after Ansible, not before
Ansible may create home directory structure and set ownership. Pushing credentials before Ansible runs risks them being overwritten or their parent directories not existing yet. Pushing last ensures a clean, stable target state.

### D5: Preflight check uses SSH, not ICMP ping
The tear-down preflight verifies SSH reachability (same transport as the sync) rather than ICMP ping, which may be blocked by the firewall. Uses `ssh -o ConnectTimeout=5 ... exit` — if it fails, print a warning with the exact consequence (creds not saved) and prompt for confirmation before proceeding to destroy.

### D6: chmod applied via SSH after rsync push
SSH key files need `600` permissions to be accepted by the SSH client. rsync with `-a` preserves permissions from the local copy, but the local files may have incorrect permissions (e.g., if seeded manually). An explicit `chmod` via SSH after push is a reliable guarantee. Only private keys need `600`; the `.ssh/` directory itself needs `700`.

## Risks / Trade-offs

- **Droplet unreachable at tear-down** → Credentials are not pulled. Mitigation: preflight check warns clearly, user confirms before destroy proceeds. Creds are not lost forever if the droplet is still alive in DO and can be recovered manually.

- **`local/creds/` accidentally committed** → Credentials exposed in git history. Mitigation: `.gitignore` entry. No complete mitigation — relies on the gitignore being in place before `git add`.

- **Stale credentials in `local/creds/`** → If a credential is rotated inside the VM but tear-down is not run before destroy, the old credential is restored on the next spin-up and auth fails. Mitigation: always run tear-down rather than destroying via the DO console or API directly.

- **First-run bootstrap** → `local/creds/` is empty on first ever spin-up; rsync push is a no-op. User must authenticate manually once. This is acceptable and expected.

## Migration Plan

1. Add `local/` to `.gitignore`
2. Create `local/creds/` directory structure (gitignored)
3. Update `tear-down.sh` with preflight check + credential pull
4. Update `spin-up.sh` with credential push + chmod
5. Seed `local/creds/.ssh/` with the GitHub keypair manually (one-time step)
6. Run a full spin-up/tear-down cycle to verify the sync works end-to-end

No rollback needed — the scripts are self-contained and the changes are additive.

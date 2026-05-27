## 1. Repository Setup

- [x] 1.1 Add `local/` entry to `.gitignore`
- [x] 1.2 Create `local/creds/.ssh/` directory and add a `.gitkeep` placeholder so the structure is present without any real files

## 2. Update `tear-down.sh`

- [x] 2.1 Add SSH preflight check: attempt `ssh -o ConnectTimeout=5 -o BatchMode=yes root@$DROPLET_IP exit` before pulling creds
- [x] 2.2 On preflight failure, print warning that credentials will NOT be saved and prompt for `[y/N]` confirmation; exit 1 if not confirmed
- [x] 2.3 On preflight success, rsync `~/.claude/`, `~/.gemini/`, `~/.codex/` from droplet to `local/creds/`
- [x] 2.4 Rsync `~/.ssh/github_ed25519` and `~/.ssh/github_ed25519.pub` from droplet to `local/creds/.ssh/`
- [x] 2.5 Extract `DROPLET_IP` from Terraform output before the preflight check so it is available for both SSH and rsync

## 3. Update `spin-up.sh`

- [x] 3.1 After Ansible playbook completes, rsync `local/creds/.claude/`, `local/creds/.gemini/`, `local/creds/.codex/` to their respective paths on the droplet
- [x] 3.2 Rsync `local/creds/.ssh/` to `~/.ssh/` on the droplet (excludes `authorized_keys` — only named key files are in `local/creds/.ssh/`)
- [x] 3.3 After rsync, run `chmod 700 ~/.ssh && chmod 600 ~/.ssh/github_ed25519` on the droplet via SSH
- [x] 3.4 Print a summary line confirming credentials were pushed (or skipped if `local/creds/` was empty)

## 4. Verification

- [ ] 4.1 Run `./scripts/spin-up.sh` from clean state and confirm credentials are restored to the droplet
- [ ] 4.2 Verify `ssh -T git@github.com` succeeds inside the droplet without manual key setup
- [ ] 4.3 Run `./scripts/tear-down.sh` and confirm `local/creds/` is populated with credential files
- [x] 4.4 Run `git status` and confirm nothing under `local/` appears as tracked
- [ ] 4.5 Run a second full spin-up/tear-down cycle to confirm the idempotent round-trip works

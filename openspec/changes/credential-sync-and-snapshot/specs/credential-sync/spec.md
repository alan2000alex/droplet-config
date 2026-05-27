## ADDED Requirements

### Requirement: Credential directories are synced from droplet to local machine on tear-down
The system SHALL rsync `~/.claude/`, `~/.gemini/`, and `~/.codex/` from the droplet to `local/creds/` on the local machine as part of `tear-down.sh`, before `terraform destroy` runs.

#### Scenario: Successful credential pull on tear-down
- **WHEN** `./tear-down.sh` is run and the droplet is SSH-reachable
- **THEN** the contents of `~/.claude/`, `~/.gemini/`, and `~/.codex/` on the droplet are rsynced to `local/creds/.claude/`, `local/creds/.gemini/`, and `local/creds/.codex/` on the local machine before `terraform destroy` executes

#### Scenario: Credential directories do not exist on droplet
- **WHEN** `./tear-down.sh` is run and one or more of the credential directories do not exist on the droplet
- **THEN** rsync skips the missing directories without error and proceeds to destroy

---

### Requirement: GitHub SSH keypair is synced from droplet to local machine on tear-down
The system SHALL rsync `~/.ssh/github_ed25519` and `~/.ssh/github_ed25519.pub` from the droplet to `local/creds/.ssh/` on the local machine as part of `tear-down.sh`.

#### Scenario: GitHub SSH key pulled on tear-down
- **WHEN** `./tear-down.sh` is run and `~/.ssh/github_ed25519` exists on the droplet
- **THEN** both `github_ed25519` and `github_ed25519.pub` are rsynced to `local/creds/.ssh/` before destroy

#### Scenario: GitHub SSH key does not exist on droplet
- **WHEN** `./tear-down.sh` is run and `~/.ssh/github_ed25519` does not exist on the droplet
- **THEN** rsync skips the missing files without error and proceeds to destroy

---

### Requirement: Credentials are pushed from local machine to droplet on spin-up
The system SHALL rsync credential directories and GitHub SSH keypair from `local/creds/` on the local machine to the appropriate paths on the droplet after Ansible completes, as part of `spin-up.sh`.

#### Scenario: Credentials restored after Ansible
- **WHEN** `./spin-up.sh` is run and `local/creds/` contains credential data
- **THEN** `local/creds/.claude/`, `local/creds/.gemini/`, `local/creds/.codex/`, and `local/creds/.ssh/` are rsynced to their respective paths under `~` on the droplet after the Ansible playbook finishes

#### Scenario: First-run bootstrap — local/creds is empty
- **WHEN** `./spin-up.sh` is run and `local/creds/` is empty or does not exist
- **THEN** the credential push step completes without error (rsync no-ops) and spin-up finishes normally

---

### Requirement: SSH key permissions are enforced after credential push
The system SHALL set correct filesystem permissions on the synced SSH key files after pushing credentials to the droplet, so the SSH client accepts them.

#### Scenario: Permissions set after credential push
- **WHEN** credentials are pushed to the droplet by `spin-up.sh`
- **THEN** `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/github_ed25519` are executed on the droplet via SSH

---

### Requirement: `local/` is excluded from version control
The system SHALL include a `local/` entry in `.gitignore` so that no file under `local/` can be committed to the repository.

#### Scenario: local/ is gitignored
- **WHEN** files are written to `local/creds/`
- **THEN** `git status` does not list any file under `local/` as tracked or staged

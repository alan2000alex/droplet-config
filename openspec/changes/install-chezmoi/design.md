## Context

The Ansible `env` role sets up the workload user's environment after the user is created. It already installs Python scripts and writes env profile files. chezmoi is installed system-wide so any user can invoke it; `curl` is already a provisioned package.

## Goals / Non-Goals

**Goals:**
- Install the chezmoi binary to `/usr/local/bin` during provisioning
- Task is idempotent: skips download if binary already exists

**Non-Goals:**
- Running `chezmoi init` or applying a dotfiles repo
- User-local installation
- Version pinning (latest stable via official script)

## Decisions

**Use `ansible.builtin.shell` with `creates:`**
The official install script uses `$()` subshell expansion, which requires a shell. The `creates:` parameter on the shell module skips the task if `/usr/local/bin/chezmoi` already exists — the idiomatic Ansible alternative to a separate `stat`/`when` check.

**Install to `/usr/local/bin` with `-- -b /usr/local/bin`**
System-wide placement keeps the task simple: `become: true` is already set at the play level in `site.yml`, so no extra privilege escalation is needed.

**Place task in `env` role**
chezmoi is a workload environment tool. The `env` role already owns this layer of setup and runs after `user`, ensuring the target user exists.

## Risks / Trade-offs

- `curl | sh` is a network call — provisioning fails if `https://get.chezmoi.io` is unreachable → Mitigation: `curl` exits non-zero on network failure; Ansible surfaces the error clearly.
- Script always fetches latest chezmoi — version is unpinned → Acceptable for now; `creates:` means it only runs once per VM lifetime.

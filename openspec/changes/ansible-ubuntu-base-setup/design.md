## Context

The repo already contains Ansible infrastructure code for VPC/VM setup. The bash script `ubuntu-base.sh` performs a one-shot Ubuntu baseline configuration but cannot be safely re-run (non-idempotent file overwrites, no state tracking). The goal is to express the same operations as an Ansible role so they integrate naturally with the existing playbook-driven workflow, gain idempotency, and benefit from Ansible's diff/check mode for auditing.

The script covers five concerns: prerequisite validation, full system upgrade, journald disk-limit config, unattended-upgrades installation + config, and apt-daily timer scheduling. All five map cleanly to native Ansible modules with no need for `shell`/`command` tasks.

## Goals / Non-Goals

**Goals:**
- Faithful, idempotent Ansible implementation of every action in `ubuntu-base.sh`.
- Use native Ansible modules (`apt`, `ansible.builtin.copy`/`template`, `ansible.builtin.systemd`, `ansible.builtin.file`) — zero raw shell tasks.
- Structured as a role (`roles/ubuntu_base`) with per-concern task files included from `tasks/main.yml`.
- Entry-point playbook `ubuntu-base.yml` at the repo root that enforces the Ubuntu-only requirement via `assert`.
- Templates stored under `roles/ubuntu_base/templates/` for the two multi-line config files.
- Handlers for service restarts (journald, apt-daily timer, systemd daemon-reload) so restarts only fire when the config actually changes.

**Non-Goals:**
- Replacing or modifying any existing playbook or role in the repo.
- Parameterising every value (e.g. journal max size, reboot time) via variables — hardcoded defaults matching the bash script are sufficient for now.
- Supporting non-Ubuntu distributions.
- SSH key management, user creation, or firewall configuration (those belong in separate roles).

## Decisions

### Role structure over a flat playbook
**Decision:** Organise code as `roles/ubuntu_base` with per-concern task files (`system_upgrade.yml`, `journald.yml`, `unattended_upgrades.yml`, `apt_daily_timer.yml`) included from `tasks/main.yml`.
**Rationale:** Mirrors the repo's existing role-based convention, keeps each concern independently readable, and makes future extraction or reuse straightforward. Alternatives: a single flat playbook (harder to read at scale) or a collection role (overkill for a single server bootstrap).

### Handlers for service restarts
**Decision:** Declare handlers for `restart systemd-journald`, `daemon-reload`, and `restart apt-daily.timer`; notify them from the relevant task.
**Rationale:** Ansible handlers fire only when the notifying task reports `changed`, matching the script's behaviour while avoiding unnecessary service disruptions on re-runs.

### `ansible.builtin.template` for multi-line config files
**Decision:** Use Jinja2 templates (`.j2`) for `50unattended-upgrades` and the apt-daily timer drop-in rather than inline `copy: content=`.
**Rationale:** Templates are easier to read, diff, and extend. The content is static for now (no variables), but the template approach keeps the door open without any extra cost.

### Backup via `ansible.builtin.copy` with `backup: true`
**Decision:** Use the `backup` parameter on the `template` task for `50unattended-upgrades` instead of a separate shell `cp` step.
**Rationale:** Ansible's built-in backup creates a timestamped copy automatically and is idempotent — it only fires when content changes, so repeated runs don't accumulate unnecessary backup files.

### Assert Ubuntu-only at play level
**Decision:** Add `ansible.builtin.assert` as the first task checking `ansible_distribution == "Ubuntu"`.
**Rationale:** Mirrors the script's explicit guard without relying on inventory grouping. Fails fast with a clear error on non-Ubuntu targets.

## Risks / Trade-offs

- **`apt full-upgrade` on every run** → Mitigation: This is intentional and matches the script. Operators who want to skip it can tag the task `never` or limit with `--tags`. The `update_cache: true` parameter ensures the cache is fresh before upgrading.
- **Auto-reboot config (`Automatic-Reboot: "true"`)** → Mitigation: This is deployed by the script today; Ansible makes it no more or less risky. Operators are expected to understand the implication.
- **`systemd daemon-reload` required before restarting apt-daily.timer** → Mitigation: Handler order is declared explicitly (`daemon-reload` notified first, then `restart apt-daily.timer`); Ansible runs handlers in notification order within a flush.
- **No molecule/testinfra tests** → Mitigation: Out of scope for this change; a future task can add idempotency tests.

## Migration Plan

1. Merge this change into the repo.
2. Run `ansible-playbook ubuntu-base.yml -i <inventory> --check --diff` against a staging host to verify no unintended changes.
3. Run without `--check` to apply.
4. Retire `ubuntu-base.sh` (or keep it as a reference; it is not deleted by this change).

**Rollback:** All config files managed by the role are backed up by Ansible's `backup: true`. To revert, restore the backed-up file and restart the relevant service. The role makes no destructive or irreversible changes.

## Open Questions

- Should `journald` max size and the unattended-upgrade reboot time be exposed as role defaults variables for easy override? (Deferred — hardcoded for now to match script 1-for-1.)
- Should the role be tagged so operators can run individual concerns selectively (e.g. `--tags journald`)? (Recommended as a follow-up; not blocking.)

## Why

Managing Ubuntu server baseline configuration via a one-shot bash script is fragile, not idempotent, and hard to audit or re-run safely. Converting to Ansible makes the configuration declarative, repeatable, and composable with the rest of the infrastructure-as-code in this repo.

## What Changes

- Add an Ansible playbook (`ubuntu-base.yml`) that replaces `ubuntu-base.sh`.
- Add Ansible role `ubuntu_base` with tasks grouped by concern: system upgrade, journald config, unattended-upgrades, and apt-daily timer scheduling.
- Add Jinja2 templates for the two configuration files written by the script (`50unattended-upgrades` and `apt-daily.timer` drop-in).
- Remove the need to run the bash script directly; operators run `ansible-playbook ubuntu-base.yml` instead.

## Capabilities

### New Capabilities

- `system-upgrade`: Full apt system upgrade (update cache, full-upgrade, clean) using the Ansible `apt` module.
- `journald-config`: Deploy `/etc/systemd/journald.conf.d/override.conf` to cap journal disk use at 200 MB and restart the `systemd-journald` service.
- `unattended-upgrades-config`: Install `unattended-upgrades` and deploy a fully-configured `/etc/apt/apt.conf.d/50unattended-upgrades` file (all origins, auto-reboot at 02:15, unused-package cleanup, verbose syslog logging), with the original backed up.
- `apt-daily-timer-config`: Deploy `/etc/systemd/system/apt-daily.timer.d/override.conf` to schedule apt daily at 01:15 AM ± 30 min, then reload systemd and restart the timer.

### Modified Capabilities

## Impact

- New files: `ubuntu-base.yml`, `roles/ubuntu_base/tasks/main.yml`, `roles/ubuntu_base/tasks/system_upgrade.yml`, `roles/ubuntu_base/tasks/journald.yml`, `roles/ubuntu_base/tasks/unattended_upgrades.yml`, `roles/ubuntu_base/tasks/apt_daily_timer.yml`, `roles/ubuntu_base/templates/50unattended-upgrades.j2`, `roles/ubuntu_base/templates/apt-daily-timer-override.conf.j2`.
- Targets Ubuntu hosts only; playbook enforces this with `ansible_distribution == "Ubuntu"` assertion.
- Requires privilege escalation (`become: true`); assumes SSH access with sudo.
- No existing Ansible roles or playbooks are modified.

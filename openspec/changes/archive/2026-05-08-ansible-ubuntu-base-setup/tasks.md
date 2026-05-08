## 1. Role Scaffolding

- [x] 1.1 Create role directory tree: `roles/ubuntu_base/{tasks,templates,handlers}`
- [x] 1.2 Create `roles/ubuntu_base/tasks/main.yml` that includes the four per-concern task files in order

## 2. Entry-Point Playbook

- [x] 2.1 Create `ubuntu-base.yml` playbook targeting `all` hosts with `become: true`, an Ubuntu assertion task, and a role reference to `ubuntu_base`

## 3. System Upgrade Tasks

- [x] 3.1 Create `roles/ubuntu_base/tasks/system_upgrade.yml` with an `apt` task that sets `update_cache: true`, `upgrade: full`, and `autoclean: true`

## 4. Journald Config Tasks

- [x] 4.1 Create `roles/ubuntu_base/tasks/journald.yml` with a `file` task to ensure `/etc/systemd/journald.conf.d/` directory exists
- [x] 4.2 Add a `template` (or `copy`) task to deploy `journald.conf.d/override.conf` with `SystemMaxUse=200M`, notifying the `restart systemd-journald` handler
- [x] 4.3 Create `roles/ubuntu_base/templates/journald-override.conf.j2` with the `[Journal]` section content

## 5. Unattended-Upgrades Tasks

- [x] 5.1 Create `roles/ubuntu_base/tasks/unattended_upgrades.yml` with an `apt` task to install `unattended-upgrades`
- [x] 5.2 Add a `template` task to deploy `/etc/apt/apt.conf.d/50unattended-upgrades` from a template with `backup: true`
- [x] 5.3 Create `roles/ubuntu_base/templates/50unattended-upgrades.j2` with all required settings (all-origins, auto-reboot at 02:15, unused-package cleanup, verbose syslog logging)

## 6. Apt-Daily Timer Tasks

- [x] 6.1 Create `roles/ubuntu_base/tasks/apt_daily_timer.yml` with a `file` task to ensure `/etc/systemd/system/apt-daily.timer.d/` directory exists
- [x] 6.2 Add a `template` (or `copy`) task to deploy `apt-daily.timer.d/override.conf` with `OnCalendar=*-*-* 01:15` and `RandomizedDelaySec=30m`, notifying the `daemon-reload` and `restart apt-daily.timer` handlers
- [x] 6.3 Create `roles/ubuntu_base/templates/apt-daily-timer-override.conf.j2` with the `[Timer]` section content

## 7. Handlers

- [x] 7.1 Create `roles/ubuntu_base/handlers/main.yml` with handlers for: `restart systemd-journald`, `systemd daemon-reload`, and `restart apt-daily.timer` (daemon-reload must be listed before the timer restart so it fires first)

## ADDED Requirements

### Requirement: Unattended-upgrades package is installed
The role SHALL install the `unattended-upgrades` package using the Ansible `apt` module.

#### Scenario: Package already installed
- **WHEN** `unattended-upgrades` is already installed on the target host
- **THEN** the task reports `ok` and no package changes are made

#### Scenario: Package not installed
- **WHEN** `unattended-upgrades` is not installed on the target host
- **THEN** the package is installed and the task reports `changed`

### Requirement: Original config file is backed up
The role SHALL create a backup of the original `/etc/apt/apt.conf.d/50unattended-upgrades` before overwriting it, using the `backup: true` parameter on the deploy task.

#### Scenario: Original file exists and content changes
- **WHEN** `/etc/apt/apt.conf.d/50unattended-upgrades` exists and is about to be replaced with new content
- **THEN** Ansible creates a timestamped backup of the original file before writing the new content

#### Scenario: Config already matches desired state
- **WHEN** `/etc/apt/apt.conf.d/50unattended-upgrades` already contains the correct content
- **THEN** the task reports `ok`, no backup is created, and the file is not modified

### Requirement: Unattended-upgrades config is deployed with correct settings
The role SHALL deploy `/etc/apt/apt.conf.d/50unattended-upgrades` using a template with all of the following settings:
- `Unattended-Upgrade::Allowed-Origins` set to `"*:*"` (all origins).
- `Unattended-Upgrade::Automatic-Reboot "true"`.
- `Unattended-Upgrade::Automatic-Reboot-WithUsers "true"`.
- `Unattended-Upgrade::Automatic-Reboot-Time "02:15"`.
- `Unattended-Upgrade::Remove-Unused-Kernel-Packages "true"`.
- `Unattended-Upgrade::Remove-New-Unused-Dependencies "true"`.
- `Unattended-Upgrade::Remove-Unused-Dependencies "true"`.
- `Unattended-Upgrade::SyslogEnable "true"`.
- `Unattended-Upgrade::SyslogFacility "daemon"`.
- `Unattended-Upgrade::Verbose "true"`.
- `Unattended-Upgrade::MinimalSteps "true"`.
- `Unattended-Upgrade::AutoFixInterruptedDpkg "true"`.
- `Unattended-Upgrade::InstallOnShutdown "false"`.

#### Scenario: Config file is absent
- **WHEN** `/etc/apt/apt.conf.d/50unattended-upgrades` does not exist
- **THEN** the file is created from the template with all required settings and the task reports `changed`

#### Scenario: Config file already has correct content
- **WHEN** `/etc/apt/apt.conf.d/50unattended-upgrades` already matches the template output
- **THEN** the task reports `ok` and no changes are made

#### Scenario: Auto-reboot is enabled
- **WHEN** the config file is deployed
- **THEN** `Automatic-Reboot` is `"true"` and `Automatic-Reboot-Time` is `"02:15"`

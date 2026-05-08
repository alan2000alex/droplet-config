## ADDED Requirements

### Requirement: Apt-daily timer drop-in directory exists
The role SHALL ensure the directory `/etc/systemd/system/apt-daily.timer.d/` exists before deploying the timer drop-in file.

#### Scenario: Directory already exists
- **WHEN** `/etc/systemd/system/apt-daily.timer.d/` already exists on the target host
- **THEN** the task reports `ok` and makes no changes

#### Scenario: Directory does not exist
- **WHEN** `/etc/systemd/system/apt-daily.timer.d/` does not exist on the target host
- **THEN** the directory is created and the task reports `changed`

### Requirement: Apt-daily timer drop-in is deployed with correct schedule
The role SHALL deploy `/etc/systemd/system/apt-daily.timer.d/override.conf` using a template containing:
- `OnCalendar=*-*-* 01:15` (trigger daily at 01:15 AM).
- `RandomizedDelaySec=30m` (random delay up to 30 minutes).

#### Scenario: Drop-in file is absent
- **WHEN** `/etc/systemd/system/apt-daily.timer.d/override.conf` does not exist
- **THEN** the file is created with the correct `[Timer]` section content and the task reports `changed`

#### Scenario: Drop-in file already has correct content
- **WHEN** the file exists and already matches the template output
- **THEN** the task reports `ok` and no changes are made

#### Scenario: Drop-in file has incorrect schedule
- **WHEN** the file exists but `OnCalendar` or `RandomizedDelaySec` differs from the required values
- **THEN** the file is updated to the correct content and the task reports `changed`

### Requirement: Systemd daemon is reloaded and apt-daily.timer is restarted on config change
The role SHALL run `systemctl daemon-reload` and restart the `apt-daily.timer` service only when the drop-in configuration file changes.

#### Scenario: Drop-in file changed
- **WHEN** the apt-daily timer drop-in file was created or modified in the current play
- **THEN** a handler triggers `systemctl daemon-reload` followed by a restart of `apt-daily.timer`

#### Scenario: Drop-in file unchanged
- **WHEN** the apt-daily timer drop-in file was not modified in the current play
- **THEN** neither `daemon-reload` nor `apt-daily.timer` restart is executed

## ADDED Requirements

### Requirement: Journald drop-in directory exists
The role SHALL ensure the directory `/etc/systemd/journald.conf.d/` exists before deploying the drop-in configuration file.

#### Scenario: Directory already exists
- **WHEN** `/etc/systemd/journald.conf.d/` already exists on the target host
- **THEN** the task reports `ok` and makes no changes

#### Scenario: Directory does not exist
- **WHEN** `/etc/systemd/journald.conf.d/` does not exist on the target host
- **THEN** the directory is created with appropriate permissions and the task reports `changed`

### Requirement: Journald disk-limit drop-in is deployed
The role SHALL deploy `/etc/systemd/journald.conf.d/override.conf` containing `SystemMaxUse=200M` under the `[Journal]` section, using the Ansible `template` or `copy` module.

#### Scenario: Drop-in file is absent
- **WHEN** `/etc/systemd/journald.conf.d/override.conf` does not exist
- **THEN** the file is created with the correct content and the task reports `changed`

#### Scenario: Drop-in file already has correct content
- **WHEN** `/etc/systemd/journald.conf.d/override.conf` exists and already contains `SystemMaxUse=200M`
- **THEN** the task reports `ok` and the file is not modified

#### Scenario: Drop-in file has incorrect content
- **WHEN** `/etc/systemd/journald.conf.d/override.conf` exists but contains a different value
- **THEN** the file is updated to the correct content and the task reports `changed`

### Requirement: Systemd-journald is restarted on config change
The role SHALL restart the `systemd-journald` service only when the drop-in configuration file changes.

#### Scenario: Config file changed
- **WHEN** the journald drop-in file was created or modified in the current play
- **THEN** the `systemd-journald` service is restarted via a handler

#### Scenario: Config file unchanged
- **WHEN** the journald drop-in file was not modified in the current play
- **THEN** the `systemd-journald` service is NOT restarted

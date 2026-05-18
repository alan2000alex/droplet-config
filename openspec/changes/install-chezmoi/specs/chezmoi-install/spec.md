## ADDED Requirements

### Requirement: chezmoi binary installed system-wide
The Ansible `env` role SHALL install the chezmoi binary to `/usr/local/bin` using the official install script (`https://get.chezmoi.io`). The task MUST be idempotent: it SHALL skip the download if `/usr/local/bin/chezmoi` already exists.

#### Scenario: First-time provisioning
- **WHEN** the VM is provisioned and `/usr/local/bin/chezmoi` does not exist
- **THEN** the install script is executed and the chezmoi binary is placed at `/usr/local/bin/chezmoi`

#### Scenario: Re-running the playbook
- **WHEN** the playbook runs and `/usr/local/bin/chezmoi` already exists
- **THEN** the install task is skipped without error

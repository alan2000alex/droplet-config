## ADDED Requirements

### Requirement: Install Docker and supporting packages
The role SHALL install `docker.io`, `jq`, and `logrotate` via apt on the target Ubuntu host with the package cache updated before installation. The Docker service SHALL be enabled and running after installation.

#### Scenario: Packages installed on a fresh host
- **WHEN** the role runs on a host where `docker.io`, `jq`, and `logrotate` are not installed
- **THEN** all three packages are installed via apt, the apt cache is refreshed, and the `docker` service is started and enabled

#### Scenario: Packages already installed
- **WHEN** the role runs on a host where all three packages are already at their latest apt version
- **THEN** no apt changes are made and the play reports no changes for this task

#### Scenario: Non-Ubuntu host
- **WHEN** the playbook runs on a host where `ansible_distribution != "Ubuntu"`
- **THEN** the play fails immediately with an assertion error before any tasks execute

#### Scenario: Non-x86_64 host
- **WHEN** the playbook runs on a host where `ansible_architecture != "x86_64"`
- **THEN** the play fails immediately with an assertion error before any tasks execute

## ADDED Requirements

### Requirement: Ubuntu-only assertion
The playbook SHALL assert that `ansible_distribution == "Ubuntu"` before executing any tasks, failing immediately with a clear error message on non-Ubuntu targets.

#### Scenario: Ubuntu host
- **WHEN** the playbook runs against a host where `ansible_distribution` is `"Ubuntu"`
- **THEN** the assertion passes and subsequent tasks execute normally

#### Scenario: Non-Ubuntu host
- **WHEN** the playbook runs against a host where `ansible_distribution` is not `"Ubuntu"`
- **THEN** the assertion fails with a descriptive error message and no further tasks run

### Requirement: Full system upgrade
The role SHALL perform a full apt system upgrade by updating the package cache, running `apt full-upgrade`, and cleaning the local package cache, using the Ansible `apt` module.

#### Scenario: Packages are up to date
- **WHEN** all installed packages are already at their latest versions
- **THEN** the upgrade task reports `ok` (not `changed`) and no packages are modified

#### Scenario: Upgradeable packages exist
- **WHEN** one or more installed packages have newer versions available
- **THEN** the upgrade task reports `changed` and all packages are upgraded to their latest versions

#### Scenario: Cache is stale
- **WHEN** the apt cache has not been updated recently
- **THEN** the cache is refreshed before the upgrade runs (`update_cache: true`)

#### Scenario: Apt cache is cleaned after upgrade
- **WHEN** the upgrade task completes
- **THEN** the local apt package cache is cleaned (`autoclean: true` or equivalent), freeing disk space

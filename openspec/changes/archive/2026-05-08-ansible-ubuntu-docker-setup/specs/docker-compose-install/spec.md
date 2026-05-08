## ADDED Requirements

### Requirement: Install latest docker-compose binary
The role SHALL query the GitHub releases API (`api.github.com/repos/docker/compose/releases/latest`) to resolve the download URL for the `docker-compose-linux-x86_64` asset of the latest release. The binary SHALL be downloaded to `/usr/local/bin/docker-compose` with mode `0755`. If the installed version already matches the latest release tag the download SHALL be skipped.

#### Scenario: docker-compose not installed
- **WHEN** `/usr/local/bin/docker-compose` does not exist
- **THEN** the latest release tag is fetched from the GitHub API, the binary is downloaded to `/usr/local/bin/docker-compose`, and mode `0755` is set

#### Scenario: docker-compose outdated
- **WHEN** `/usr/local/bin/docker-compose` exists but its version does not match the latest release tag
- **THEN** the binary is re-downloaded and overwritten

#### Scenario: docker-compose already at latest version
- **WHEN** `/usr/local/bin/docker-compose --version` output contains the latest release tag
- **THEN** the download task is skipped and the play reports no change for this task

### Requirement: Create docker-compose shortcut and CLI plugin symlinks
The role SHALL create a symlink `/usr/local/bin/d` pointing to `docker-compose`. The role SHALL also create the directory `/usr/local/lib/docker/cli-plugins/` and a symlink `docker-compose` inside it pointing to `/usr/local/bin/docker-compose`, enabling `docker compose` sub-command support.

#### Scenario: Shortcut symlink created
- **WHEN** the role runs and `/usr/local/bin/d` does not exist
- **THEN** a symlink `/usr/local/bin/d -> docker-compose` is created

#### Scenario: CLI plugin symlink created
- **WHEN** the role runs and `/usr/local/lib/docker/cli-plugins/docker-compose` does not exist
- **THEN** the directory `/usr/local/lib/docker/cli-plugins/` is created if absent, and a symlink `docker-compose -> /usr/local/bin/docker-compose` is created inside it

#### Scenario: Symlinks already exist
- **WHEN** both symlinks already exist with the correct targets
- **THEN** the symlink tasks report no change

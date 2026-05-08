## ADDED Requirements

### Requirement: Install latest ctop binary
The role SHALL query the GitHub releases API (`api.github.com/repos/bcicen/ctop/releases/latest`) to resolve the download URL for the asset whose name ends with `linux-amd64`. The binary SHALL be downloaded to `/usr/local/bin/ctop` with mode `0755`. If the installed version already matches the latest release tag the download SHALL be skipped.

#### Scenario: ctop not installed
- **WHEN** `/usr/local/bin/ctop` does not exist
- **THEN** the latest release tag is fetched from the GitHub API, the `linux-amd64` asset URL is resolved, the binary is downloaded to `/usr/local/bin/ctop`, and mode `0755` is set

#### Scenario: ctop outdated
- **WHEN** `/usr/local/bin/ctop` exists but its version does not match the latest release tag
- **THEN** the binary is re-downloaded and overwritten

#### Scenario: ctop already at latest version
- **WHEN** `/usr/local/bin/ctop --version` output contains the latest release tag
- **THEN** the download task is skipped and the play reports no change for this task

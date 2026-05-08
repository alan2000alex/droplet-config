## ADDED Requirements

### Requirement: Deploy Docker daemon configuration
The role SHALL deploy `/etc/docker/daemon.json` with the local log driver configured to use a maximum log size of `15m` and a maximum of `5` log files. When the file changes, the `docker` service SHALL be restarted via a handler.

#### Scenario: daemon.json deployed on first run
- **WHEN** `/etc/docker/daemon.json` does not exist or differs from the expected content
- **THEN** the file is written with `log-driver: local`, `max-size: 15m`, `max-file: 5`, and the `restart docker` handler is notified

#### Scenario: daemon.json already correct
- **WHEN** `/etc/docker/daemon.json` already matches the expected content
- **THEN** the file is not overwritten and the `restart docker` handler is not notified

#### Scenario: Docker restarted after config change
- **WHEN** the `restart docker` handler is notified
- **THEN** the `docker` systemd service is restarted before the play ends

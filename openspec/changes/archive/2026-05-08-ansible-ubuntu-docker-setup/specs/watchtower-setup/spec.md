## ADDED Requirements

### Requirement: Deploy Watchtower docker-compose configuration
The role SHALL create the directory `/opt/watchtower/` and deploy `/opt/watchtower/docker-compose.yml` from a template. The compose file SHALL define a service named `watchtower` with:
- image: `nickfedor/watchtower`
- container_name: `watchtower.localhost`
- restart: `always`
- mem_limit: `128M`
- volumes: `/var/run/docker.sock:/var/run/docker.sock` and `/etc/localtime:/etc/localtime:ro`
- label: `com.centurylinklabs.watchtower.enable=true`
- command: `--label-enable --cleanup --schedule "0 15 4 * * *"`

When the compose file changes, a handler SHALL re-run `docker compose up -d` to recreate the container.

#### Scenario: Directory and compose file created on first run
- **WHEN** `/opt/watchtower/` does not exist
- **THEN** the directory is created with mode `0755`, the `docker-compose.yml` is deployed, and the `watchtower compose up` handler is notified

#### Scenario: Compose file already correct
- **WHEN** `/opt/watchtower/docker-compose.yml` already matches the template output
- **THEN** the file is not overwritten and the handler is not notified

#### Scenario: Compose file updated
- **WHEN** `/opt/watchtower/docker-compose.yml` differs from the template output
- **THEN** the file is overwritten and the `watchtower compose up` handler is notified

### Requirement: Start Watchtower container
The role SHALL start the Watchtower container using `docker compose -f /opt/watchtower/docker-compose.yml up -d`. This command is run when the compose file is first deployed or when it changes (via handler).

#### Scenario: Container started on initial deployment
- **WHEN** the `watchtower compose up` handler is notified
- **THEN** `docker compose -f /opt/watchtower/docker-compose.yml up -d` is executed and the container is running

#### Scenario: Container already running with unchanged config
- **WHEN** the Watchtower container is running and the compose file has not changed
- **THEN** `docker compose up -d` is not invoked and no change is reported for this concern

### Requirement: Deploy Watchtower manual run script
The role SHALL deploy `/opt/watchtower/run.sh` from a template with mode `0755`. The script SHALL perform a one-shot Watchtower run using `docker run --rm` against `nickfedor/watchtower` with flags `--cleanup --label-enable --run-once`.

#### Scenario: run.sh deployed on first run
- **WHEN** `/opt/watchtower/run.sh` does not exist
- **THEN** the script is deployed with mode `0755` and correct content

#### Scenario: run.sh already correct
- **WHEN** `/opt/watchtower/run.sh` already matches the template output
- **THEN** the file is not overwritten and the play reports no change

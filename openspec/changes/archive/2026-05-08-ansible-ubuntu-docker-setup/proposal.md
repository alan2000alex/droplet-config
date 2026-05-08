## Why

Managing Docker installation and tooling via a one-shot bash script is not idempotent, is hard to audit, and cannot be safely re-run on an existing server. Converting to Ansible makes the Docker setup declarative, repeatable, and composable with the rest of the infrastructure-as-code in this repo.

## What Changes

- Add an Ansible playbook (`ubuntu-docker.yml`) that replaces `ubuntu-docker.sh`.
- Add Ansible role `ubuntu_docker` with tasks grouped by concern: package installation, Docker daemon configuration, docker-compose installation, ctop installation, and Watchtower container setup.
- Add Jinja2 templates for the files written by the script (`daemon.json`, `docker-compose.yml`, `run.sh`).
- Remove the need to run the bash script directly; operators run `ansible-playbook ubuntu-docker.yml` instead.

## Capabilities

### New Capabilities

- `docker-packages`: Install `docker.io`, `jq`, and `logrotate` via apt and ensure Docker is running.
- `docker-daemon-config`: Deploy `/etc/docker/daemon.json` to configure the local log driver with size and file rotation limits, then restart Docker to apply.
- `docker-compose-install`: Query the GitHub releases API for the latest `docker-compose-linux-x86_64` binary, download it to `/usr/local/bin/docker-compose`, set permissions, and create the `/usr/local/bin/d` shortcut symlink and the Docker CLI plugin symlink.
- `ctop-install`: Query the GitHub releases API for the latest `ctop` linux-amd64 binary, download it to `/usr/local/bin/ctop`, and set permissions.
- `watchtower-setup`: Create `/opt/watchtower/`, deploy the Watchtower `docker-compose.yml`, start the container via `docker compose up -d`, and deploy the manual `/opt/watchtower/run.sh` script.

### Modified Capabilities

## Impact

- New files: `ubuntu-docker.yml`, `roles/ubuntu_docker/tasks/main.yml`, `roles/ubuntu_docker/tasks/docker_packages.yml`, `roles/ubuntu_docker/tasks/docker_daemon.yml`, `roles/ubuntu_docker/tasks/docker_compose_install.yml`, `roles/ubuntu_docker/tasks/ctop_install.yml`, `roles/ubuntu_docker/tasks/watchtower.yml`, `roles/ubuntu_docker/templates/daemon.json.j2`, `roles/ubuntu_docker/templates/watchtower-compose.yml.j2`, `roles/ubuntu_docker/templates/watchtower-run.sh.j2`, `roles/ubuntu_docker/handlers/main.yml`.
- Targets Ubuntu x86_64 hosts only; playbook enforces this with `ansible_distribution == "Ubuntu"` and `ansible_architecture == "x86_64"` assertions.
- Requires privilege escalation (`become: true`); assumes SSH access with sudo.
- Requires outbound HTTPS access to `api.github.com` and GitHub release download URLs.
- No existing Ansible roles or playbooks are modified.

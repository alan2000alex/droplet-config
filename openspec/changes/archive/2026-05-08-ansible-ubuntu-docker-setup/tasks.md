## 1. Role Scaffolding

- [x] 1.1 Create role directory tree: `roles/ubuntu_docker/{tasks,templates,handlers}`
- [x] 1.2 Create `roles/ubuntu_docker/tasks/main.yml` that includes the five per-concern task files in order

## 2. Entry-Point Playbook

- [x] 2.1 Create `ubuntu-docker.yml` playbook targeting `all` hosts with `become: true`, assertions for Ubuntu distribution and x86_64 architecture, and a role reference to `ubuntu_docker`

## 3. Docker Packages Tasks

- [x] 3.1 Create `roles/ubuntu_docker/tasks/docker_packages.yml` with an `apt` task that installs `docker.io`, `jq`, and `logrotate` with `update_cache: true`
- [x] 3.2 Add a `systemd` task to ensure the `docker` service is enabled and started

## 4. Docker Daemon Config Tasks

- [x] 4.1 Create `roles/ubuntu_docker/tasks/docker_daemon.yml` with a `template` task to deploy `/etc/docker/daemon.json` from `daemon.json.j2`, notifying the `restart docker` handler
- [x] 4.2 Create `roles/ubuntu_docker/templates/daemon.json.j2` with local log driver config (`max-size: 15m`, `max-file: 5`)

## 5. Docker Compose Install Tasks

- [x] 5.1 Create `roles/ubuntu_docker/tasks/docker_compose_install.yml` with a `uri` task to call `api.github.com/repos/docker/compose/releases/latest` and register the latest release tag and asset download URL
- [x] 5.2 Add a `command` task to check the installed docker-compose version (ignore errors if not installed) and register the result
- [x] 5.3 Add a `get_url` task to download the `docker-compose-linux-x86_64` asset to `/usr/local/bin/docker-compose` with mode `0755`, conditioned on version mismatch
- [x] 5.4 Add a `file` task to create symlink `/usr/local/bin/d -> docker-compose`
- [x] 5.5 Add a `file` task to ensure `/usr/local/lib/docker/cli-plugins/` directory exists
- [x] 5.6 Add a `file` task to create symlink `/usr/local/lib/docker/cli-plugins/docker-compose -> /usr/local/bin/docker-compose`

## 6. Ctop Install Tasks

- [x] 6.1 Create `roles/ubuntu_docker/tasks/ctop_install.yml` with a `uri` task to call `api.github.com/repos/bcicen/ctop/releases/latest` and register the latest release tag and `linux-amd64` asset download URL
- [x] 6.2 Add a `command` task to check the installed ctop version (ignore errors if not installed) and register the result
- [x] 6.3 Add a `get_url` task to download the ctop `linux-amd64` asset to `/usr/local/bin/ctop` with mode `0755`, conditioned on version mismatch

## 7. Watchtower Tasks

- [x] 7.1 Create `roles/ubuntu_docker/tasks/watchtower.yml` with a `file` task to ensure `/opt/watchtower/` directory exists with mode `0755`
- [x] 7.2 Add a `template` task to deploy `/opt/watchtower/docker-compose.yml` from `watchtower-compose.yml.j2`, notifying the `watchtower compose up` handler
- [x] 7.3 Create `roles/ubuntu_docker/templates/watchtower-compose.yml.j2` with the full Watchtower compose service definition (image, container_name, restart, mem_limit, volumes, labels, command)
- [x] 7.4 Add a `template` task to deploy `/opt/watchtower/run.sh` from `watchtower-run.sh.j2` with mode `0755`
- [x] 7.5 Create `roles/ubuntu_docker/templates/watchtower-run.sh.j2` with the one-shot `docker run --rm ... nickfedor/watchtower --cleanup --label-enable --run-once` script

## 8. Handlers

- [x] 8.1 Create `roles/ubuntu_docker/handlers/main.yml` with a `systemd` handler for `restart docker` and a `command` handler for `watchtower compose up` that runs `docker compose -f /opt/watchtower/docker-compose.yml up -d`

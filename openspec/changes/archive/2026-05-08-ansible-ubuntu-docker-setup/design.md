## Context

The repo already has an `ubuntu_base` role and `ubuntu-base.yml` playbook for baseline OS configuration. This change follows the same role-based pattern to introduce a parallel `ubuntu_docker` role and `ubuntu-docker.yml` playbook. The bash script `ubuntu-docker.sh` that it replaces downloads binaries from GitHub releases using raw `wget` + `jq` pipelines and uses non-idempotent shell commands.

## Goals / Non-Goals

**Goals:**
- Replicate all behaviour of `ubuntu-docker.sh` as idempotent Ansible tasks.
- Follow the same role structure as `ubuntu_base` (tasks split by concern, handlers, templates).
- Use built-in Ansible modules (`apt`, `get_url`, `uri`, `file`, `template`, `systemd`, `command`) — no third-party collections beyond those already in the repo.
- Restrict execution to Ubuntu x86_64 hosts via play-level assertions.

**Non-Goals:**
- Managing Docker images or containers beyond Watchtower itself.
- Supporting non-x86_64 architectures (download URLs are hardcoded to linux-x86_64 / linux-amd64, matching the original script).
- Replacing or merging with the `ubuntu_base` role.
- Handling Docker TLS or registry authentication.

## Decisions

### D1: GitHub release version resolution via `uri` module
The script resolves the latest binary URL by calling `api.github.com/repos/<owner>/<repo>/releases/latest` and parsing with `jq`. Ansible's `uri` module with `return_content: true` returns the JSON body which can be queried with `json_query` (using the `community.general` `json_query` filter, which is already available) or a simple `selectattr`/`map` Jinja2 pipeline. This avoids shelling out to `jq` while remaining readable.

**Alternative considered:** Pin explicit versions in role vars. Rejected because the script's design intent is always-latest; a pinned version would drift silently.

### D2: Idempotency for binary downloads
`get_url` is used with a `checksum` only when a checksum file is provided by upstream. For docker-compose and ctop, upstream does not publish a stable per-asset checksum URL alongside the "latest" redirect. Instead, idempotency is achieved by checking whether the installed binary's reported version matches the latest release tag before downloading. This is done by registering the `uri` response tag and comparing it to the output of `docker-compose version --short` / `ctop --version`, skipping the download task when they match.

**Alternative considered:** Always re-download and overwrite. Rejected because it causes unnecessary writes and restarts on every playbook run.

### D3: Docker daemon restart via handler
Changing `/etc/docker/daemon.json` notifies a `restart docker` handler, matching the `ubuntu_base` pattern for config-driven service restarts. This ensures Docker is only restarted when the file actually changes.

### D4: Watchtower started via `command` module with `creates` guard
`docker compose up -d` is idempotent by nature (no-ops if the container is already running), so it is run unconditionally. However, the `docker-compose.yml` template change notifies a `watchtower compose up` handler so the container is re-created only when its configuration changes.

**Alternative considered:** `community.docker.docker_compose_v2` module. Rejected to avoid adding a collection dependency; the `command` module with a `changed_when` condition is sufficient.

### D5: Templates for all generated files
`daemon.json`, `watchtower-compose.yml`, and `watchtower-run.sh` are all deployed via Jinja2 templates even though they have no variable interpolation today. This keeps the door open for future parameterisation without structural change and is consistent with the `ubuntu_base` role's use of templates.

## Risks / Trade-offs

- **GitHub API rate limit** → Mitigation: The role makes at most two unauthenticated API calls per play run; the anonymous rate limit (60 req/hour) is sufficient for human-driven playbook runs. Automated runs at high frequency should set a GitHub token via a role variable.
- **Binary integrity** → Mitigation: docker-compose publishes SHA256 checksums alongside release assets; the tasks should download and verify the checksum file. ctop does not publish checksums; the risk is accepted, matching the original script's behaviour.
- **Watchtower auto-updates docker-compose itself** → Trade-off: Watchtower updates containers by image tag, not host binaries, so this role's installed binaries are not affected.
- **`command` module for docker compose** → Trade-off: `changed_when` must be set carefully to avoid false positives. The task is marked `changed_when: false` for the `up -d` invocation since Docker Compose does not signal changes through its exit code.

## Migration Plan

1. Run `ansible-playbook ubuntu-docker.yml` on a host where `ubuntu-docker.sh` was previously run. Because all tasks are idempotent, the playbook will converge without side effects — packages will be marked present, files will be compared by content, the container will remain running.
2. No rollback is needed; the bash script is not removed by this Ansible role. If reverting is required, the script can be re-run manually.

## Open Questions

- Should a GitHub token variable (`ubuntu_docker_github_token`) be wired up now as an optional var, or deferred? (Proposed: add the var as empty-by-default and conditionally include an `Authorization` header when set.)

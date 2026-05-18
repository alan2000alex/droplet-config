## Why

chezmoi is the dotfiles manager used to manage the workload user's environment. Installing it as part of provisioning ensures it is available immediately when the VM is ready, without requiring a manual install step.

## What Changes

- Add a `chezmoi` install task to the `env` Ansible role that downloads and installs the binary system-wide using the official install script.

## Capabilities

### New Capabilities

- `chezmoi-install`: Install the chezmoi binary to `/usr/local/bin` via the official one-line install script, idempotently.

### Modified Capabilities

## Impact

- `ansible/roles/env/tasks/main.yml`: one new task added
- Requires `curl` to be available on the target (already in `packages` in `vars.yml`)

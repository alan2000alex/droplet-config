## Why

The project currently requires Ansible to be installed globally on the host machine, which ties the spin-up workflow to a specific system Python environment. Using `uvx` to invoke Ansible provides an isolated, reproducible execution environment without requiring a global install.

## What Changes

- Replace the direct `ansible` call (wait_for_connection) in `scripts/spin-up.sh` with `uvx --from ansible ansible`
- Replace the direct `ansible-playbook` call in `scripts/spin-up.sh` with `uvx --from ansible ansible-playbook`
- No changes to inventory, playbook, or Terraform configuration

## Capabilities

### New Capabilities

<!-- None introduced -->

### Modified Capabilities

- `spin-up-tear-down-workflow`: The spin-up step now invokes Ansible via `uvx` instead of a global binary — same observable behaviour, different execution mechanism.

## Impact

- `scripts/spin-up.sh`: two command substitutions updated
- Requires `uv` (and therefore `uvx`) to be installed on the host running the script
- No impact on Ansible playbook, inventory, or Terraform resources

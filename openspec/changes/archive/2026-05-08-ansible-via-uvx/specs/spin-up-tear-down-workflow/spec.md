## MODIFIED Requirements

### Requirement: `spin-up.sh` orchestrates full provisioning in one command
The system SHALL provide a `spin-up.sh` script that, when executed, performs: SSH keypair generation (if missing), `terraform init`, `terraform apply`, dynamic Ansible inventory generation from Terraform output, SSH readiness wait, and Ansible playbook execution — in that order. Ansible SHALL be invoked via `uvx --from ansible` rather than as a global binary, so that no prior Ansible installation is required on the host.

#### Scenario: Full spin-up from clean state
- **WHEN** `./spin-up.sh` is run with no prior state
- **THEN** the script generates an SSH keypair, provisions the droplet via Terraform, writes `ansible/inventory.ini` with the droplet IP, waits for SSH using `uvx --from ansible ansible`, and runs the Ansible playbook to completion using `uvx --from ansible ansible-playbook`

#### Scenario: SSH key already exists
- **WHEN** `./spin-up.sh` is run and `~/.ssh/do_vm_key` already exists
- **THEN** the script skips keygen and proceeds directly to `terraform apply`

#### Scenario: Failure during Terraform apply
- **WHEN** `terraform apply` exits with a non-zero code
- **THEN** `spin-up.sh` exits immediately without running Ansible, and prints an error message

#### Scenario: `uv` not installed on host
- **WHEN** `./spin-up.sh` is run and `uvx` is not available on PATH
- **THEN** the script fails at the Ansible invocation step with a "command not found" error

## MODIFIED Requirements

### Requirement: `spin-up.sh` orchestrates full provisioning in one command
The system SHALL provide a `spin-up.sh` script that, when executed, performs: SSH keypair generation (if missing), `terraform init`, `terraform apply`, dynamic Ansible inventory generation from Terraform output, SSH readiness wait, Ansible playbook execution, and credential push from `local/creds/` to the droplet with SSH key permission enforcement — in that order. Ansible SHALL be invoked via `uvx --from ansible` rather than as a global binary, so that no prior Ansible installation is required on the host.

#### Scenario: Full spin-up from clean state
- **WHEN** `./spin-up.sh` is run with no prior state
- **THEN** the script generates an SSH keypair, provisions the droplet via Terraform, writes `ansible/inventory.ini` with the droplet IP, waits for SSH using `uvx --from ansible ansible`, runs the Ansible playbook to completion using `uvx --from ansible ansible-playbook`, and then pushes credentials from `local/creds/` to the droplet

#### Scenario: SSH key already exists
- **WHEN** `./spin-up.sh` is run and `~/.ssh/do_vm_key` already exists
- **THEN** the script skips keygen and proceeds directly to `terraform apply`

#### Scenario: Failure during Terraform apply
- **WHEN** `terraform apply` exits with a non-zero code
- **THEN** `spin-up.sh` exits immediately without running Ansible or pushing credentials, and prints an error message

#### Scenario: `uv` not installed on host
- **WHEN** `./spin-up.sh` is run and `uvx` is not available on PATH
- **THEN** the script fails at the Ansible invocation step with a "command not found" error

---

### Requirement: `tear-down.sh` performs SSH preflight check before destroying
The system SHALL attempt an SSH connection to the droplet before pulling credentials. If the droplet is unreachable, `tear-down.sh` SHALL print a warning identifying that credentials will NOT be saved, then prompt the user for confirmation before proceeding to `terraform destroy`.

#### Scenario: Droplet SSH-reachable on tear-down
- **WHEN** `./tear-down.sh` is run and the droplet responds to SSH within 5 seconds
- **THEN** credentials are pulled to `local/creds/` and `terraform destroy` proceeds automatically

#### Scenario: Droplet unreachable on tear-down
- **WHEN** `./tear-down.sh` is run and the droplet does not respond to SSH within 5 seconds
- **THEN** the script prints a warning that credentials were not saved and prompts the user to confirm before running `terraform destroy`

#### Scenario: User aborts after unreachable warning
- **WHEN** the droplet is unreachable and the user responds with anything other than `y` at the confirmation prompt
- **THEN** `tear-down.sh` exits with code 1 without destroying any resources

---

### Requirement: `tear-down.sh` destroys all cloud resources in one command
The system SHALL provide a `tear-down.sh` script that, when executed, pulls credentials (if droplet is reachable), then runs `terraform destroy -auto-approve` and reports success or failure.

#### Scenario: Full tear-down
- **WHEN** `./tear-down.sh` is run with existing Terraform state and the droplet is reachable
- **THEN** credentials are pulled to `local/creds/`, all DigitalOcean resources (droplet, firewall) are destroyed, and the script exits with code 0

#### Scenario: No state to destroy
- **WHEN** `./tear-down.sh` is run with no existing Terraform state
- **THEN** Terraform reports nothing to destroy and the script exits with code 0

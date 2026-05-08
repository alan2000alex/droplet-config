## ADDED Requirements

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

---

### Requirement: `tear-down.sh` destroys all cloud resources in one command
The system SHALL provide a `tear-down.sh` script that, when executed, runs `terraform destroy -auto-approve` and reports success or failure.

#### Scenario: Full tear-down
- **WHEN** `./tear-down.sh` is run with existing Terraform state
- **THEN** all DigitalOcean resources (droplet, firewall, SSH key) are destroyed and the script exits with code 0

#### Scenario: No state to destroy
- **WHEN** `./tear-down.sh` is run with no existing Terraform state
- **THEN** Terraform reports nothing to destroy and the script exits with code 0

---

### Requirement: Dynamic inventory is written from Terraform output
The system SHALL extract the droplet's public IP from `terraform output -json` and write it to `ansible/inventory.ini` in INI format so Ansible can target the droplet without manual input.

#### Scenario: Inventory written after apply
- **WHEN** `terraform apply` completes and `spin-up.sh` extracts the IP
- **THEN** `ansible/inventory.ini` contains a `[droplets]` group with the droplet's IP and `ansible_user=root`

---

### Requirement: DigitalOcean API token is read from environment variable
The system SHALL read the DigitalOcean API token from the `TF_VAR_do_token` environment variable. If `TF_VAR_do_token` is not set, the scripts SHALL attempt to extract `do_token` from `terraform/terraform.tfvars` and export it as `TF_VAR_do_token` before proceeding. The token SHALL NOT be stored in any tracked file.

#### Scenario: Token present in environment
- **WHEN** `TF_VAR_do_token` is set and `./spin-up.sh` is run
- **THEN** Terraform authenticates to DigitalOcean successfully and no tfvars lookup is attempted

#### Scenario: Token in tfvars, not in environment
- **WHEN** `TF_VAR_do_token` is not set, `terraform/terraform.tfvars` exists and contains a `do_token = "..."` entry, and `./spin-up.sh` is run
- **THEN** the script extracts the token from the file, exports it as `TF_VAR_do_token`, and Terraform authenticates successfully

#### Scenario: Token missing from both sources
- **WHEN** `TF_VAR_do_token` is not set and `terraform/terraform.tfvars` does not exist or contains no `do_token` entry, and `./spin-up.sh` is run
- **THEN** `spin-up.sh` exits before calling Terraform and prints an instructional error message

#### Scenario: Tear-down with token in tfvars
- **WHEN** `TF_VAR_do_token` is not set, `terraform/terraform.tfvars` contains `do_token`, and `./tear-down.sh` is run
- **THEN** the script extracts and exports the token and Terraform destroy proceeds successfully

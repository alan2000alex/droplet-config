## ADDED Requirements

### Requirement: `spin-up.sh` orchestrates full provisioning in one command
The system SHALL provide a `spin-up.sh` script that, when executed, performs: SSH keypair generation (if missing), `terraform init`, `terraform apply`, dynamic Ansible inventory generation from Terraform output, SSH readiness wait, and Ansible playbook execution — in that order.

#### Scenario: Full spin-up from clean state
- **WHEN** `./spin-up.sh` is run with no prior state
- **THEN** the script generates an SSH keypair, provisions the droplet via Terraform, writes `ansible/inventory.ini` with the droplet IP, waits for SSH, and runs the Ansible playbook to completion

#### Scenario: SSH key already exists
- **WHEN** `./spin-up.sh` is run and `~/.ssh/do_vm_key` already exists
- **THEN** the script skips keygen and proceeds directly to `terraform apply`

#### Scenario: Failure during Terraform apply
- **WHEN** `terraform apply` exits with a non-zero code
- **THEN** `spin-up.sh` exits immediately without running Ansible, and prints an error message

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
The system SHALL read the DigitalOcean API token from the `TF_VAR_do_token` environment variable. The token SHALL NOT be stored in any tracked file.

#### Scenario: Token present in environment
- **WHEN** `TF_VAR_do_token` is set and `./spin-up.sh` is run
- **THEN** Terraform authenticates to DigitalOcean successfully

#### Scenario: Token missing
- **WHEN** `TF_VAR_do_token` is not set and `./spin-up.sh` is run
- **THEN** `spin-up.sh` exits before calling Terraform and prints an instructional error message

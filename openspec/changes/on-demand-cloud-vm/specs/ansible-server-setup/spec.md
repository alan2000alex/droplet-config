## ADDED Requirements

### Requirement: Ansible connects to the droplet using the Terraform-generated SSH key
The system SHALL configure Ansible to connect to the droplet IP from the dynamic inventory using the private SSH key generated during Terraform provisioning.

#### Scenario: Successful connection
- **WHEN** the Ansible playbook is invoked after `terraform apply`
- **THEN** Ansible establishes an SSH connection to the droplet using `~/.ssh/do_vm_key` without password prompts

---

### Requirement: System packages are installed and up-to-date
The system SHALL update the package index and install a configurable list of system packages on the droplet. The package list SHALL be defined in `ansible/vars.yml`.

#### Scenario: Package installation
- **WHEN** the Ansible playbook runs on a freshly provisioned droplet
- **THEN** all packages listed in `ansible/vars.yml` are installed

#### Scenario: Idempotent re-run
- **WHEN** the Ansible playbook is run a second time on the same droplet
- **THEN** no packages are reinstalled and the play completes without errors

---

### Requirement: A non-root sudo user is created for workload execution
The system SHALL create a dedicated non-root user (configurable name, default `workload`) with passwordless sudo access, to run workloads without using the root account.

#### Scenario: User creation
- **WHEN** the Ansible playbook runs on a fresh droplet
- **THEN** the `workload` user exists with sudo privileges and the SSH authorized key installed

#### Scenario: User already exists
- **WHEN** the Ansible playbook is re-run
- **THEN** the user task reports `ok` (no change) and the playbook completes successfully

---

### Requirement: Swap space is configured proportional to RAM
The system SHALL configure swap space on the droplet to provide an overflow buffer for RAM-intensive workloads. The swap size SHALL be configurable in `ansible/vars.yml`.

#### Scenario: Swap created on fresh droplet
- **WHEN** the Ansible playbook runs and no swap exists
- **THEN** a swap file of the configured size is created, activated, and made persistent via `/etc/fstab`

---

### Requirement: Environment variables for workloads are written to a profile script
The system SHALL write a shell profile script (`/etc/profile.d/workload-env.sh`) containing any environment variables defined in `ansible/vars.yml` under `workload_env`.

#### Scenario: Environment file written
- **WHEN** `workload_env` is non-empty in `ansible/vars.yml`
- **THEN** `/etc/profile.d/workload-env.sh` exists with the defined exports

#### Scenario: Empty workload_env
- **WHEN** `workload_env` is empty or not defined
- **THEN** no profile script is written (task skipped)

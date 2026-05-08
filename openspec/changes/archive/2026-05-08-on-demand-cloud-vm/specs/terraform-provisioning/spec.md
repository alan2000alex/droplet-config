## ADDED Requirements

### Requirement: Droplet is provisioned with configurable size and region
The system SHALL provision a DigitalOcean droplet using variables defined in `terraform.tfvars`. The droplet size SHALL default to a memory-optimized type (128 GB RAM or equivalent). Region and droplet name SHALL be configurable.

#### Scenario: Default provisioning
- **WHEN** `terraform apply` is run with default `terraform.tfvars`
- **THEN** a DigitalOcean droplet is created with the configured size, region, and name

#### Scenario: Custom size override
- **WHEN** `terraform.tfvars` specifies a different `droplet_size`
- **THEN** the provisioned droplet uses the specified size

---

### Requirement: SSH key is registered and injected into the droplet
The system SHALL register an SSH public key with DigitalOcean via Terraform and inject it into the provisioned droplet, enabling passwordless SSH access.

#### Scenario: SSH key registration on first apply
- **WHEN** `terraform apply` is run and the SSH public key does not exist in DigitalOcean
- **THEN** Terraform creates a `digitalocean_ssh_key` resource and associates it with the droplet

#### Scenario: SSH key already exists
- **WHEN** `terraform apply` is run and the SSH key fingerprint already exists in DigitalOcean
- **THEN** Terraform reuses the existing key without error

---

### Requirement: Firewall restricts inbound traffic to SSH only by default
The system SHALL attach a DigitalOcean firewall to the droplet that allows inbound SSH (TCP port 22) and blocks all other inbound traffic by default.

#### Scenario: Firewall applied on provisioning
- **WHEN** the droplet is provisioned
- **THEN** a firewall resource is attached that allows inbound TCP/22 and denies all other inbound ports

---

### Requirement: Droplet IP is exported as a Terraform output
The system SHALL output the provisioned droplet's IPv4 address after `terraform apply` so downstream tools (Ansible inventory generation) can consume it.

#### Scenario: IP output after apply
- **WHEN** `terraform apply` completes successfully
- **THEN** `terraform output droplet_ip` returns the public IPv4 address of the droplet

---

### Requirement: All resources are destroyed cleanly by `terraform destroy`
The system SHALL destroy the droplet, SSH key registration, and firewall when `terraform destroy` is run, leaving no billable resources.

#### Scenario: Full teardown
- **WHEN** `terraform destroy` is run
- **THEN** droplet, firewall, and SSH key are removed from DigitalOcean with no resources remaining

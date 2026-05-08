## Why

Running RAM-intensive workloads on a cloud VM full-time is prohibitively expensive. A provisioning workflow that brings a high-RAM droplet up on demand and tears it down when the workload completes eliminates idle cost while preserving a repeatable, reproducible environment.

## What Changes

- New Terraform configuration to provision and destroy a DigitalOcean droplet (high-RAM size, SSH key, VPC networking, firewall)
- New Ansible playbook and roles to configure the freshly provisioned droplet (package installation, environment setup, workload prerequisites)
- Helper scripts (`spin-up.sh`, `tear-down.sh`) wrapping Terraform + Ansible for a single-command workflow
- Variable files (`terraform.tfvars`, `ansible/vars.yml`) for customizing region, droplet size, and installed packages without touching core configs

## Capabilities

### New Capabilities

- `terraform-provisioning`: Terraform module that creates and destroys the DigitalOcean droplet, SSH key registration, VPC, and firewall rules
- `ansible-server-setup`: Ansible playbook that configures the droplet after boot — package installation, user setup, environment configuration for RAM-intensive workloads
- `spin-up-tear-down-workflow`: Shell helper scripts that orchestrate `terraform apply` + Ansible provisioning (spin-up) and `terraform destroy` (tear-down) in one command

### Modified Capabilities

## Impact

- No existing code affected (greenfield setup)
- Requires a DigitalOcean API token and an SSH key pair available locally
- Terraform state file will be stored locally (can be migrated to remote backend later)
- Ansible requires Python 3 on the control machine and SSH access to the droplet

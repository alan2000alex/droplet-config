## 1. Repository Scaffolding

- [x] 1.1 Create top-level directory structure: `terraform/`, `ansible/roles/`, `ansible/vars.yml`, `scripts/`
- [x] 1.2 Add `.gitignore` excluding `terraform.tfvars`, `*.tfstate`, `*.tfstate.backup`, `ansible/inventory.ini`, `~/.ssh/do_vm_key*`

## 2. Terraform Configuration

- [x] 2.1 Write `terraform/versions.tf` pinning Terraform `>= 1.5` and the `digitalocean/digitalocean` provider `~> 2.0`
- [x] 2.2 Write `terraform/variables.tf` declaring `do_token`, `droplet_size` (default `m-16vcpu-128gb`), `region` (default `nyc3`), and `droplet_name` (default `workload-vm`)
- [x] 2.3 Write `terraform/main.tf` with `digitalocean_ssh_key`, `digitalocean_droplet`, and `digitalocean_firewall` resources (SSH-only inbound rule)
- [x] 2.4 Write `terraform/outputs.tf` exporting `droplet_ip` (public IPv4)
- [x] 2.5 Create `terraform/terraform.tfvars.example` with placeholder values and usage comments; document that the real `terraform.tfvars` must not be committed

## 3. Ansible Configuration

- [x] 3.1 Write `ansible/ansible.cfg` setting `inventory = inventory.ini`, `remote_user = root`, `private_key_file = ~/.ssh/do_vm_key`, and `host_key_checking = False`
- [x] 3.2 Write `ansible/vars.yml` with `packages` list (e.g. `build-essential`, `python3-pip`, `htop`), `workload_user` (default `workload`), `swap_size` (default `8g`), and `workload_env` dict
- [x] 3.3 Create `ansible/roles/base/tasks/main.yml` — update apt cache and install packages from `vars.yml`
- [x] 3.4 Create `ansible/roles/user/tasks/main.yml` — create `workload_user`, add to sudo group, copy SSH authorized key
- [x] 3.5 Create `ansible/roles/swap/tasks/main.yml` — create swap file, `mkswap`, `swapon`, add `/etc/fstab` entry
- [x] 3.6 Create `ansible/roles/env/tasks/main.yml` — template `/etc/profile.d/workload-env.sh` from `workload_env` dict; skip when dict is empty
- [x] 3.7 Write `ansible/site.yml` playbook applying roles in order: `base` → `user` → `swap` → `env`

## 4. Workflow Scripts

- [x] 4.1 Write `scripts/spin-up.sh`: check `TF_VAR_do_token` env var (exit with error if missing), generate SSH keypair at `~/.ssh/do_vm_key` if absent, run `terraform -chdir=terraform init && apply -auto-approve`, extract IP via `terraform -chdir=terraform output -json`, write `ansible/inventory.ini`, wait for SSH with `ansible all -m wait_for_connection`, run `ansible-playbook ansible/site.yml`
- [x] 4.2 Write `scripts/tear-down.sh`: run `terraform -chdir=terraform destroy -auto-approve`
- [x] 4.3 Make both scripts executable (`chmod +x`)
- [x] 4.4 Add convenience symlinks or a top-level `Makefile` with `spin-up` and `tear-down` targets pointing to the scripts

## 5. Documentation

- [x] 5.1 Write `README.md` covering prerequisites (Terraform, Ansible, DigitalOcean account), setup steps (copy `terraform.tfvars.example`, set `TF_VAR_do_token`), spin-up and tear-down usage, and state file warning
- [x] 5.2 Document how to customize the droplet size, installed packages, and workload environment variables in `vars.yml` and `terraform.tfvars`

## 6. Validation

- [x] 6.1 Run `terraform -chdir=terraform validate` and `terraform -chdir=terraform fmt -check` to verify HCL syntax
- [x] 6.2 Run `ansible-lint ansible/site.yml` to check playbook quality (install `ansible-lint` if not present)
- [ ] 6.3 End-to-end smoke test: run `./scripts/spin-up.sh`, SSH into the droplet, verify packages and user exist, then run `./scripts/tear-down.sh` and confirm no resources remain in the DigitalOcean console

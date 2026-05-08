## Context

The user runs RAM-intensive workloads (data processing, ML training, in-memory analysis) that require a large cloud VM. Keeping such a VM running continuously is costly. The goal is an IaC-driven workflow: `./spin-up.sh` provisions and configures a fresh droplet; `./tear-down.sh` destroys it. All state is reproducible from code — no manual steps.

Target provider: DigitalOcean. Terraform manages the droplet lifecycle. Ansible configures the OS after boot. Both tools are invoked via thin shell wrappers so the user only needs to run one command.

## Goals / Non-Goals

**Goals:**
- Single-command spin-up: Terraform apply → dynamic inventory → Ansible run
- Single-command tear-down: Ansible cleanup (optional) → Terraform destroy
- Configurable droplet size and region via `terraform.tfvars`
- Idempotent Ansible roles (safe to re-run if configuration drifts)
- SSH key managed by Terraform (created in DigitalOcean, private key on disk)
- Firewall restricted to SSH (22) only by default; user can extend

**Non-Goals:**
- Remote Terraform state backend (local state is sufficient for single-user use)
- Multi-droplet or cluster provisioning
- Kubernetes or container orchestration
- Automated scheduling / cron-based spin-up (out of scope for this change)
- Windows droplets

## Decisions

### Decision 1: Terraform for provisioning, Ansible for configuration

**Chosen**: Terraform manages DigitalOcean resources (droplet, SSH key, firewall). Ansible handles OS-level configuration (packages, users, environment).

**Alternatives considered**:
- Cloud-init only: simpler but not idempotent and harder to iterate on
- Pulumi: more powerful but heavier dependency for a single-VM workflow
- Terraform provisioners: anti-pattern; mixing provisioning and configuration in one tool

**Rationale**: Clear separation of concerns. Terraform state tracks what exists; Ansible is stateless and re-runnable.

---

### Decision 2: Dynamic inventory via `terraform output` → Ansible inventory file

**Chosen**: After `terraform apply`, a shell script reads `terraform output -json` to extract the droplet's IP and writes a minimal `ansible/inventory.ini`. Ansible then uses that file.

**Alternatives considered**:
- DigitalOcean Ansible dynamic inventory plugin: requires additional credentials config and network calls at Ansible runtime
- Hardcoded inventory: defeats the purpose of dynamic provisioning

**Rationale**: Keeping it simple — no extra plugins, no extra API calls. The IP is already in Terraform state.

---

### Decision 3: SSH key generated locally, registered to DigitalOcean via Terraform

**Chosen**: `ssh-keygen` generates a dedicated keypair at `~/.ssh/do_vm_key`. Terraform's `digitalocean_ssh_key` resource registers the public key. The droplet is created with this key. Ansible uses the private key for connection.

**Alternatives considered**:
- Pre-existing SSH key: requires manual setup instructions
- Password auth: insecure and unsupported on most DO images

**Rationale**: Fully automated and reproducible. The keypair can be regenerated if lost.

---

### Decision 4: Shell wrappers (`spin-up.sh`, `tear-down.sh`) as the user interface

**Chosen**: Two shell scripts orchestrate the full workflow. `spin-up.sh`: generate SSH key (if missing) → `terraform init && terraform apply` → write inventory → `ansible-playbook`. `tear-down.sh`: `terraform destroy`.

**Alternatives considered**:
- Makefile: familiar to developers but less readable for ops-focused users
- Taskfile: adds a dependency

**Rationale**: Shell scripts have zero extra dependencies beyond Terraform and Ansible. Self-documenting with comments.

---

### Decision 5: Droplet size and region are variables, not hardcoded

**Chosen**: `terraform.tfvars` controls `droplet_size` (default: `m-16vcpu-128gb` — Memory-Optimized 128 GB), `region`, and `droplet_name`. Ansible vars in `ansible/vars.yml` control packages to install.

**Rationale**: Allows the user to quickly switch to a smaller size for testing without editing HCL.

## Risks / Trade-offs

- **Local Terraform state** → if `terraform.tfstate` is deleted, Terraform loses track of the droplet and `terraform destroy` will not clean it up. Mitigation: document that the state file must not be deleted; add a `.gitignore` entry but warn against accidental deletion.
- **SSH key on disk** → if `~/.ssh/do_vm_key` is lost after provisioning, manual droplet access is broken. Mitigation: Terraform stores the public key fingerprint; user can add a new key via DO console. Document recovery steps in README.
- **DigitalOcean API token in env / tfvars** → token must not be committed. Mitigation: `terraform.tfvars` is in `.gitignore`; instructions direct the user to use `TF_VAR_do_token` env var or a local-only tfvars file.
- **Ansible wait-for-SSH race** → droplet may not be SSH-ready immediately after `terraform apply` returns. Mitigation: `spin-up.sh` polls with `ansible -m wait_for_connection` before running the main playbook.

# On-Demand Cloud VM

Provision a high-RAM DigitalOcean droplet when you need it, destroy it when you don't.

**Terraform** manages the cloud resources. **Ansible** configures the OS. Two shell scripts wire them together so you only run one command.

---

## Prerequisites

| Tool | Install |
|------|---------|
| [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5 | `brew install terraform` |
| [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/) >= 2.14 | `pip install ansible` |
| `ansible` collections | `ansible-galaxy collection install ansible.posix` |
| DigitalOcean account | [cloud.digitalocean.com](https://cloud.digitalocean.com) |
| DigitalOcean API token | Account → API → Generate New Token (read+write) |

---

## Setup

1. **Clone / copy this repo** to your local machine.

2. **Set your API token** in your shell (never store it in a file):
   ```bash
   export TF_VAR_do_token=dop_v1_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   Add that line to `~/.bashrc` or `~/.zshrc` to persist across sessions.

3. **(Optional) Customise the droplet** — copy the example vars file:
   ```bash
   cp terraform/terraform.tfvars.example terraform/terraform.tfvars
   ```
   Then edit `terraform/terraform.tfvars` to override size, region, or name.
   See [Customisation](#customisation) below.

---

## Usage

### Spin up

```bash
./scripts/spin-up.sh
# or: make spin-up
```

This will:
1. Generate an SSH keypair at `~/.ssh/do_vm_key` (skipped if it already exists)
2. Run `terraform init` + `terraform apply` to create the droplet
3. Write `ansible/inventory.ini` with the droplet's IP
4. Wait for SSH to become available
5. Run the Ansible playbook to configure the OS

When done, the terminal prints the droplet IP and the SSH command.

### Tear down

```bash
./scripts/tear-down.sh
# or: make tear-down
```

Runs `terraform destroy` — removes the droplet, firewall, and SSH key from DigitalOcean. **No billable resources remain after this.**

### SSH into the droplet

```bash
ssh -i ~/.ssh/do_vm_key root@<droplet-ip>
# or as the workload user:
ssh -i ~/.ssh/do_vm_key workload@<droplet-ip>
```

---

## Customisation

### Droplet size / region

Edit `terraform/terraform.tfvars` (create from the example if it doesn't exist):

```hcl
droplet_size = "m-16vcpu-128gb"   # 128 GB RAM — change as needed
region       = "nyc3"             # See: doctl compute region list
droplet_name = "workload-vm"
```

Common memory-optimised sizes:

| Slug | RAM | vCPU |
|------|-----|------|
| `m-4vcpu-32gb` | 32 GB | 4 |
| `m-8vcpu-64gb` | 64 GB | 8 |
| `m-16vcpu-128gb` | 128 GB | 16 |
| `m-32vcpu-256gb` | 256 GB | 32 |

### Installed packages

Edit `ansible/vars.yml`:

```yaml
packages:
  - build-essential
  - python3-pip
  - htop
  # add any apt package here
```

### Workload environment variables

Edit the `workload_env` map in `ansible/vars.yml`:

```yaml
workload_env:
  DATA_DIR: /data
  NUM_WORKERS: "16"
  MY_API_KEY: "..."
```

These are written to `/etc/profile.d/workload-env.sh` on the droplet and available to all login shells. Leave it as `{}` to skip.

### Non-root workload user

Change the username:

```yaml
workload_user: myuser   # default: workload
```

The user gets passwordless sudo and the same SSH key as root.

---

## File structure

```
.
├── Makefile                        # spin-up / tear-down shortcuts
├── scripts/
│   ├── spin-up.sh                  # orchestrates Terraform + Ansible
│   └── tear-down.sh                # destroys all cloud resources
├── terraform/
│   ├── versions.tf                 # provider version pins
│   ├── variables.tf                # input variables
│   ├── main.tf                     # droplet, SSH key, firewall
│   ├── outputs.tf                  # exports droplet_ip
│   └── terraform.tfvars.example    # copy → terraform.tfvars
└── ansible/
    ├── ansible.cfg                 # connection defaults
    ├── vars.yml                    # packages, user, swap, env vars
    ├── site.yml                    # main playbook
    ├── inventory.ini               # generated at runtime (gitignored)
    └── roles/
        ├── base/     # apt update + package install
        ├── user/     # non-root sudo user + SSH key
        ├── swap/     # swap file creation
        └── env/      # /etc/profile.d/workload-env.sh
```

---

## Important warnings

- **Do not delete `terraform/terraform.tfstate`** while a droplet is running. Terraform uses this file to track what it created. If it's lost, `tear-down.sh` cannot destroy the droplet automatically — you will need to delete it manually in the DigitalOcean console.
- **Do not commit `terraform/terraform.tfvars`** — it is gitignored. Use `TF_VAR_do_token` in the environment instead.
- **SSH key recovery**: if `~/.ssh/do_vm_key` is lost while a droplet is running, add a new key via the DigitalOcean console (Droplet → Access → Add SSH Key), then reconnect.

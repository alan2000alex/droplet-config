#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SSH_KEY="$HOME/.ssh/do_vm_key"

# ── Preflight ────────────────────────────────────────────────────────────────

if [[ -z "${TF_VAR_do_token:-}" ]]; then
  echo "ERROR: TF_VAR_do_token is not set."
  echo "  Export your DigitalOcean API token first:"
  echo "    export TF_VAR_do_token=dop_v1_..."
  exit 1
fi

# ── SSH keypair ───────────────────────────────────────────────────────────────

if [[ ! -f "$SSH_KEY" ]]; then
  echo "==> Generating SSH keypair at $SSH_KEY"
  ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "do-workload-vm"
else
  echo "==> SSH key already exists at $SSH_KEY — skipping keygen"
fi

# ── Expose SSH public key to Terraform ───────────────────────────────────────

export TF_VAR_ssh_public_key
TF_VAR_ssh_public_key=$(cat "${SSH_KEY}.pub")

# ── Terraform ────────────────────────────────────────────────────────────────

echo "==> Initialising Terraform"
terraform -chdir="$ROOT_DIR/terraform" init -upgrade

echo "==> Provisioning droplet"
if ! terraform -chdir="$ROOT_DIR/terraform" apply -auto-approve; then
  echo "ERROR: terraform apply failed — aborting before Ansible runs"
  exit 1
fi

# ── Dynamic inventory ─────────────────────────────────────────────────────────

DROPLET_IP=$(terraform -chdir="$ROOT_DIR/terraform" output -json droplet_ip | tr -d '"')
echo "==> Droplet IP: $DROPLET_IP"

cat > "$ROOT_DIR/ansible/inventory.ini" <<EOF
[droplets]
$DROPLET_IP ansible_user=root ansible_ssh_private_key_file=$SSH_KEY
EOF
echo "==> Wrote ansible/inventory.ini"

# ── Wait for SSH ──────────────────────────────────────────────────────────────

echo "==> Waiting for SSH to become available"
ansible all \
  -i "$ROOT_DIR/ansible/inventory.ini" \
  -m wait_for_connection \
  --timeout 120

# ── Ansible ───────────────────────────────────────────────────────────────────

echo "==> Running Ansible playbook"
ansible-playbook \
  -i "$ROOT_DIR/ansible/inventory.ini" \
  "$ROOT_DIR/ansible/site.yml"

echo ""
echo "✓ Spin-up complete — droplet is ready at $DROPLET_IP"
echo "  SSH:  ssh -i $SSH_KEY root@$DROPLET_IP"
echo "  Tear down:  ./scripts/tear-down.sh"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SSH_KEY="$HOME/.ssh/alan_vivo_lunix"
VARS_FILE="$SCRIPT_DIR/../ansible/vars.yml"

# ── Preflight ────────────────────────────────────────────────────────────────

TFVARS="$ROOT_DIR/terraform/terraform.tfvars"
if [[ -z "${TF_VAR_do_token:-}" ]] && [[ -f "$TFVARS" ]]; then
  TF_VAR_do_token=$(grep -E '^\s*do_token\s*=' "$TFVARS" | sed 's/.*=\s*"\(.*\)".*/\1/')
  export TF_VAR_do_token
fi
if [[ -z "${TF_VAR_do_token:-}" ]]; then
  echo "ERROR: TF_VAR_do_token is not set."
  echo "  Export it or set do_token in terraform/terraform.tfvars"
  exit 1
fi

# ── SSH keypair ───────────────────────────────────────────────────────────────

# if [[ ! -f "$SSH_KEY" ]]; then
#   echo "==> Generating SSH keypair at $SSH_KEY"
#   ssh-keygen -t ed25519 -f "$SSH_KEY" -N "" -C "do-workload-vm"
# else
#   echo "==> SSH key already exists at $SSH_KEY — skipping keygen"
# fi

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

cat >"$ROOT_DIR/ansible/inventory.ini" <<EOF
[droplets]
$DROPLET_IP ansible_user=root ansible_ssh_private_key_file=$SSH_KEY
EOF
echo "==> Wrote ansible/inventory.ini"

# ── Ansible config ───────────────────────────────────────────────────────────

export ANSIBLE_CONFIG="$ROOT_DIR/ansible/ansible.cfg"

# ── Wait for SSH ──────────────────────────────────────────────────────────────

echo "==> Waiting for SSH to become available"
uvx --from ansible-core ansible all \
  -i "$ROOT_DIR/ansible/inventory.ini" \
  -m wait_for_connection \
  --timeout 120

# ── Ansible ───────────────────────────────────────────────────────────────────

echo "==> Running Ansible playbook"
uvx --from ansible-core ansible-galaxy collection install ansible.posix
uvx --from ansible-core ansible-playbook \
  -i "$ROOT_DIR/ansible/inventory.ini" \
  "$ROOT_DIR/ansible/site.yml"

# ── Credential sync ───────────────────────────────────────────────────────────

LOCAL_CREDS="$ROOT_DIR/local/creds"
CREDS_PUSHED=false
USERNAME=$(yq -r '.workload_user' "$VARS_FILE")

for dir in .claude .gemini .codex; do
  if [[ -d "$LOCAL_CREDS/$dir" ]]; then
    rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
      "$LOCAL_CREDS/$dir/" "$USERNAME@$DROPLET_IP:~/$dir/"
    CREDS_PUSHED=true
  fi
done

if [[ -f "$LOCAL_CREDS/.gitconfig" ]]; then
  rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
    "$LOCAL_CREDS/.gitconfig" "$USERNAME@$DROPLET_IP:~/"
  CREDS_PUSHED=true
fi

if [[ -f "$LOCAL_CREDS/.ssh/github_ed25519" ]]; then
  rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
    "$LOCAL_CREDS/.ssh/github_ed25519" \
    "$LOCAL_CREDS/.ssh/github_ed25519.pub" \
    "$USERNAME@$DROPLET_IP:~/.ssh/"
  ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" "$USERNAME@$DROPLET_IP" \
    "chmod 700 ~/.ssh && chmod 600 ~/.ssh/github_ed25519"
  CREDS_PUSHED=true
fi

if $CREDS_PUSHED; then
  echo "==> Credentials pushed to droplet"
else
  echo "==> No credentials found in local/creds/ — skipping (first run)"
fi

echo ""
echo "✓ Spin-up complete — droplet is ready at $DROPLET_IP"
echo "  SSH:  ssh -i $SSH_KEY root@$DROPLET_IP"
echo "  Tear down:  ./scripts/tear-down.sh"

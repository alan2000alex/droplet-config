#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SSH_KEY="$HOME/.ssh/alan_vivo_lunix"
LOCAL_CREDS="$ROOT_DIR/local/creds"

# ── DO token ─────────────────────────────────────────────────────────────────

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

# ── Droplet IP ────────────────────────────────────────────────────────────────

DROPLET_IP=$(terraform -chdir="$ROOT_DIR/terraform" output -json droplet_ip 2>/dev/null | tr -d '"' || true)

# ── Credential sync ───────────────────────────────────────────────────────────

if [[ -n "$DROPLET_IP" ]]; then
  echo "==> Checking SSH reachability of droplet ($DROPLET_IP)"
  if ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no \
       -i "$SSH_KEY" "root@$DROPLET_IP" exit 2>/dev/null; then
    echo "==> Pulling credentials from droplet to local/creds/"
    mkdir -p "$LOCAL_CREDS/.ssh"
    for dir in .claude .gemini .codex; do
      rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
        "root@$DROPLET_IP:~/$dir/" "$LOCAL_CREDS/$dir/" 2>/dev/null || true
    done
    for keyfile in github_ed25519 github_ed25519.pub; do
      rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
        "root@$DROPLET_IP:~/.ssh/$keyfile" "$LOCAL_CREDS/.ssh/" 2>/dev/null || true
    done
    rsync -az -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
      "root@$DROPLET_IP:~/.gitconfig" "$LOCAL_CREDS/" 2>/dev/null || true
    echo "==> Credentials saved to local/creds/"
  else
    echo "WARNING: Droplet ($DROPLET_IP) is not reachable via SSH — credentials will NOT be saved."
    read -rp "  Proceed with destroy anyway? [y/N] " confirm
    if [[ "${confirm,,}" != "y" ]]; then
      echo "Aborted."
      exit 1
    fi
  fi
fi

# ── Destroy ───────────────────────────────────────────────────────────────────

echo "==> Destroying all cloud resources"
terraform -chdir="$ROOT_DIR/terraform" destroy -auto-approve

echo ""
echo "✓ Tear-down complete — all DigitalOcean resources destroyed"

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

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

echo "==> Destroying all cloud resources"
terraform -chdir="$ROOT_DIR/terraform" destroy -auto-approve

echo ""
echo "✓ Tear-down complete — all DigitalOcean resources destroyed"

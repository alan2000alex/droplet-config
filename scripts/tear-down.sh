#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -z "${TF_VAR_do_token:-}" ]]; then
  echo "ERROR: TF_VAR_do_token is not set."
  echo "  Export your DigitalOcean API token first:"
  echo "    export TF_VAR_do_token=dop_v1_..."
  exit 1
fi

echo "==> Destroying all cloud resources"
terraform -chdir="$ROOT_DIR/terraform" destroy -auto-approve

echo ""
echo "✓ Tear-down complete — all DigitalOcean resources destroyed"

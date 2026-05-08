## Why

The preflight check in `spin-up.sh` and `tear-down.sh` fails if `TF_VAR_do_token` is not exported as an environment variable, even though Terraform natively reads `do_token` from `terraform.tfvars`. Users who store their token in `terraform.tfvars` are blocked by the bash guard before Terraform ever runs.

## What Changes

- `spin-up.sh`: if `TF_VAR_do_token` is unset, attempt to extract `do_token` from `terraform/terraform.tfvars` and export it before the error check
- `tear-down.sh`: same fallback logic applied identically

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `spin-up-tear-down-workflow`: the token-sourcing requirement gains a new scenario — when `TF_VAR_do_token` is absent from the environment, the scripts fall back to `terraform.tfvars` before failing

## Impact

- `scripts/spin-up.sh`: preflight block updated
- `scripts/tear-down.sh`: preflight block updated
- No changes to Terraform files, Ansible, or any tracked secrets

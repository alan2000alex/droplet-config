## 1. Update spin-up.sh

- [x] 1.1 Replace the single preflight `if` block with the two-block fallback pattern: attempt to extract `do_token` from `terraform/terraform.tfvars` when `TF_VAR_do_token` is unset, then error if still unset

## 2. Update tear-down.sh

- [x] 2.1 Apply the identical two-block fallback pattern to `tear-down.sh`

## 3. Verify

- [x] 3.1 Confirm `spin-up.sh` exits cleanly past the preflight when `do_token` is set only in `terraform.tfvars` (token not in env)
- [x] 3.2 Confirm both scripts still error with the instructional message when the token is absent from both env and tfvars

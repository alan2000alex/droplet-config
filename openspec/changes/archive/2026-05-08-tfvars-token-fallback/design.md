## Context

`spin-up.sh` and `tear-down.sh` both have a preflight block that exits immediately if `TF_VAR_do_token` is not set in the shell environment. Terraform itself would accept `do_token` from `terraform.tfvars`, but the bash guard runs before Terraform is invoked. Users who store their token in `terraform.tfvars` hit this guard even though their configuration is valid.

## Goals / Non-Goals

**Goals:**
- Allow `TF_VAR_do_token` to be sourced from `terraform/terraform.tfvars` as a fallback when it is absent from the environment
- Keep the hard error for cases where the token is missing from both sources

**Non-Goals:**
- Modifying Terraform variable files or provider configuration
- Supporting token sources beyond environment variable and `terraform.tfvars`
- Changing the behaviour when `TF_VAR_do_token` is already set in the environment

## Decisions

**Parse `terraform.tfvars` with `grep` + `sed`**

The file uses a simple `key = "value"` format. A one-liner extracts the token without introducing any new runtime dependencies:

```bash
grep -E '^\s*do_token\s*=' "$TFVARS" | sed 's/.*=\s*"\(.*\)".*/\1/'
```

Alternative considered: `terraform console` — rejected because it requires Terraform to already be initialised and is much heavier for a preflight step.

**Two-block structure**

The fallback and the error check are kept as separate `if` blocks. The first block silently attempts to populate `TF_VAR_do_token`; the second block (unchanged) emits the error if still unset. This keeps the error path identical to today and avoids nested conditionals.

**Same pattern in both scripts**

`tear-down.sh` has the same preflight guard and gets the same treatment. The `TFVARS` variable is derived from `ROOT_DIR` which both scripts already compute.

## Risks / Trade-offs

- **Quoted value assumption** → The `sed` pattern assumes `do_token = "..."` with double quotes, matching the format shown in `terraform.tfvars.example`. Unquoted values or single-quoted values will not be extracted and the script will fall through to the existing error. This is acceptable: the example file documents the expected format.
- **No validation of extracted value** → The script exports whatever is extracted. An empty or malformed token will reach Terraform and produce a Terraform-level auth error rather than the preflight error. This is a minor regression in UX but not a correctness issue.

## MODIFIED Requirements

### Requirement: DigitalOcean API token is read from environment variable
The system SHALL read the DigitalOcean API token from the `TF_VAR_do_token` environment variable. If `TF_VAR_do_token` is not set, the scripts SHALL attempt to extract `do_token` from `terraform/terraform.tfvars` and export it as `TF_VAR_do_token` before proceeding. The token SHALL NOT be stored in any tracked file.

#### Scenario: Token present in environment
- **WHEN** `TF_VAR_do_token` is set and `./spin-up.sh` is run
- **THEN** Terraform authenticates to DigitalOcean successfully and no tfvars lookup is attempted

#### Scenario: Token in tfvars, not in environment
- **WHEN** `TF_VAR_do_token` is not set, `terraform/terraform.tfvars` exists and contains a `do_token = "..."` entry, and `./spin-up.sh` is run
- **THEN** the script extracts the token from the file, exports it as `TF_VAR_do_token`, and Terraform authenticates successfully

#### Scenario: Token missing from both sources
- **WHEN** `TF_VAR_do_token` is not set and `terraform/terraform.tfvars` does not exist or contains no `do_token` entry, and `./spin-up.sh` is run
- **THEN** `spin-up.sh` exits before calling Terraform and prints an instructional error message

#### Scenario: Tear-down with token in tfvars
- **WHEN** `TF_VAR_do_token` is not set, `terraform/terraform.tfvars` contains `do_token`, and `./tear-down.sh` is run
- **THEN** the script extracts and exports the token and Terraform destroy proceeds successfully

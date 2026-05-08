## Context

`scripts/spin-up.sh` currently calls `ansible` and `ansible-playbook` as global binaries. This requires Ansible to be pre-installed on the host, coupling the script to whatever version happens to be on the system PATH.

`uvx` (part of the `uv` toolchain) runs a Python tool in an isolated, auto-provisioned virtual environment without requiring a prior install. Invoking Ansible via `uvx --from ansible ansible ...` makes the dependency self-contained and explicit.

## Goals / Non-Goals

**Goals:**
- Replace the two direct Ansible binary calls in `spin-up.sh` with `uvx`-prefixed equivalents
- Keep all flags, arguments, and observable behaviour identical

**Non-Goals:**
- Pinning a specific Ansible version (out of scope for this change)
- Modifying inventory, playbook, or Terraform configuration
- Changing `tear-down.sh` (it does not call Ansible)

## Decisions

### Use `uvx --from ansible ansible` rather than `uvx ansible`

`ansible` is a package that ships multiple entry points (`ansible`, `ansible-playbook`, etc.). The `--from ansible` flag tells `uvx` which package to install the tool from, and the trailing binary name selects the entry point. Without `--from`, `uvx ansible` would attempt to resolve a package literally named `ansible-playbook` for the second call, which does not exist on PyPI.

**Alternatives considered:**
- `pipx run --spec ansible ansible-playbook` — equivalent but requires `pipx`; `uv`/`uvx` is the newer, faster standard.
- Installing Ansible in a project-local venv and calling it directly — heavier setup, requires explicit activation.

## Risks / Trade-offs

- [`uv` not installed] → Script fails at the `uvx` call with a clear "command not found" error. Mitigation: document `uv` as a prerequisite in the README.
- [First run downloads Ansible] → `uvx` fetches the package on first invocation; subsequent runs use the cache. Acceptable for an infrequent spin-up script.
- [Ansible version drift] → Without a pinned version, `uvx` may pull a newer Ansible release. Acceptable for now; pinning can be added later if stability is needed.

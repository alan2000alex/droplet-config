## 1. Update spin-up.sh

- [x] 1.1 Replace `ansible all -m wait_for_connection` with `uvx --from ansible ansible all -m wait_for_connection` (line 60)
- [x] 1.2 Replace `ansible-playbook` with `uvx --from ansible ansible-playbook` (line 68)

## 2. Verify

- [x] 2.1 Run `bash -n scripts/spin-up.sh` to confirm no syntax errors

# AGENTS.md

Repository guidance for coding agents working in `check_vsphere`.

## Scope
- Applies to the entire repository.
- Keep changes minimal and focused.
- Preserve Python 3.6 compatibility (`requires-python = ">=3.6"`).

## Rule Files (Cursor/Copilot)
- Checked `.cursor/rules/`: not present.
- Checked `.cursorrules`: not present.
- Checked `.github/copilot-instructions.md`: not present.
- If any of these files are added later, treat them as additional required rules.

## Repository Map
- `checkvsphere/cli.py`: main entrypoint, command dispatch, exit normalization.
- `checkvsphere/vcmd/*.py`: plugin commands (`__cmd__` + `run()` pattern).
- `checkvsphere/tools/*.py`: shared parser, service connection, helper logic.
- `docs/`: user-facing docs for commands/options.
- `Makefile`: zipapp and distribution build targets.

## Agent Knowledge Base
- Additional onboarding docs for coding agents live in `.agents/`.
- Start with `.agents/README.md` for a navigation overview.
- Use `.agents/architecture.md` for control flow and module internals.
- Use `.agents/workflows.md` for change-specific execution checklists.
- Use `.agents/command-matrix.md` for command-to-module/doc mapping.
- Use `.agents/troubleshooting.md` for debugging and common failure modes.
- Use `.agents/monplugin.md` for `py-monplugin` behavior and patterns.

## Environment and Dependencies
- Build backend: `flit_core`.
- Runtime deps: `pyvmomi`, `monplugin`.
- Dev tooling in repo: `pre-commit` with lightweight hooks.

## Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . pre-commit build
```

Alternative from `.devcontainer/devcontainer.json`:
```bash
pip3 install --user monplugin pyVmomi pre-commit
```

## Build Commands
```bash
# Build bundled zipapp (includes installed deps in target dir)
make check_vsphere_bundle

# Build lightweight zipapp
make check_vsphere

# Build source/wheel distribution in dist/
make dist

# Equivalent direct build command
python -m build

# Remove build artifacts
make clean
```

## Lint/Formatting Commands
- No Ruff/Black/Flake8 config is present.
- Run repo checks with pre-commit:

```bash
pre-commit run --all-files
```

Configured hooks:
- `check-yaml`
- `end-of-file-fixer`
- `trailing-whitespace`

## Test Commands
Automated tests use `pytest` with two layers:
- unit tests (pure logic + mocked pyVmomi interactions)
- integration tests against `vcsim` + `govc`

Run default test suite (unit only, integration skipped by default):
```bash
pytest -q
```

Run a single unit test:
```bash
pytest tests/unit/test_perf_run_mocked.py::test_perf_run_can_be_tested_with_mocked_perf_data -q
```

Run vcsim integration tests:
```bash
pytest -q --run-integration tests/integration_vcsim
```

Run a single integration test:
```bash
pytest -q --run-integration tests/integration_vcsim/test_cli_vcsim.py::test_about_command_works_with_vcsim
```

## Testing Limitations
- `test.sh` exists in the repository but is considered unreliable.
- Do not treat `test.sh` as a required or authoritative validation source.
- `vcsim` does not perfectly match real vCenter behavior for all API surfaces.
- For unsupported simulator behavior, prefer focused unit tests with mocks.

Recommended simulator defaults:
- host `127.0.0.1`
- port `8989`
- user `user`
- password `pass`
- SSL verification disabled (`-nossl`)

Run a single smoke check:
```bash
python -m checkvsphere.cli about -nossl -s 127.0.0.1 -o 8989 -u user -p pass
```

Run one targeted scenario with threshold semantics:
```bash
python -m checkvsphere.cli snapshots --mode age --warning 1 \
  -nossl -s 127.0.0.1 -o 8989 -u user -p pass
echo $?  # verify monitoring status code
```

If you need manual checks in addition to pytest, use the smoke and threshold
commands above and verify exit codes.

## Exit Code Contract
Preserve monitoring-compatible exit codes:
- `0` OK
- `1` WARNING
- `2` CRITICAL
- `3` UNKNOWN

`checkvsphere/cli.py` normalizes invalid/unexpected exit codes to `3`.

## Code Style Guidelines

### Imports
- Prefer import grouping: standard library, third-party, local modules.
- Use explicit imports; avoid wildcard imports.
- Keep relative import style consistent with surrounding file.

### Formatting
- 4-space indentation, no tabs.
- Keep lines readable (about 100 chars, unless file already differs).
- Preserve shebang/license headers in command modules.
- Avoid broad, unrelated formatting-only rewrites.

### Types
- Type hints are partial in current code.
- Add hints when helpful, but avoid sweeping annotation refactors.
- Use Python 3.6-compatible typing syntax (no `X | Y`, no match/case).

### Naming
- Functions/variables: `snake_case`.
- Classes/exceptions: `PascalCase`.
- Command modules expose `__cmd__` and `run()`.
- Keep CLI option naming style consistent (long options are kebab-case).

### Command Module Pattern (`checkvsphere/vcmd`)
- Define `__cmd__` so the command is discoverable.
- Build arguments via `cli.Parser()`.
- Reuse shared argument specs from `CheckArgument` when possible.
- Connect to vSphere via `service_instance.connect(args)`.
- Use `monplugin.Check` and `Status` for thresholds and output.

### Error Handling
- Return clear monitoring-friendly messages.
- Prefer explicit exception types in new code; avoid new bare `except:` blocks.
- Convert unexpected failures to UNKNOWN (`3`) with actionable text.
- Keep behavior aligned with env vars: `TIMEOUT`, `CONNECT_NOFAIL`,
  `VSPHERE_DEBUG`, `VSPHERE_PASS`.

### Logging and Output
- Use `logging` for debug detail.
- Keep normal plugin output concise and suitable for monitoring systems.

### Documentation
- If CLI flags/behavior change, update docs under `docs/cmd/` and
  `docs/general-options.md`.
- Ensure examples match real command names and options.

## Commit Message Guidelines
- Aim for commit message lines below about 72 characters.
- Do not force awkward line breaks just to satisfy the limit exactly.
- Keep subject short and imperative; use body lines for rationale.

## Quick Done Checklist
1. Run relevant build/lint/test/manual CLI verification commands.
2. Run `pre-commit run --all-files` when practical.
3. Verify exit-code behavior remains within 0..3.
4. Update docs for any CLI-facing changes.

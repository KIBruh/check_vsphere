# Agent Docs

This directory is a fast-start knowledge base for coding agents working on
`check_vsphere`.

Read these files in order when starting fresh:

1. `AGENTS.md` (repo rules, commands, style)
2. `.agents/architecture.md` (how execution flows through modules)
3. `.agents/command-matrix.md` (which command lives where)
4. `.agents/workflows.md` (task checklists for common changes)
5. `.agents/troubleshooting.md` (debug tactics and known failure modes)
6. `.agents/monplugin.md` (threshold/output semantics for checks)

## Project in 60 Seconds

- This is a monitoring plugin for vSphere (Nagios/Naemon/Icinga style).
- Entrypoint is `python -m checkvsphere.cli <command> [options]`.
- Commands are plugin modules under `checkvsphere/vcmd/`.
- Most commands use `monplugin.Check` with states `OK/WARNING/CRITICAL/UNKNOWN`.
- Exit codes must stay in the 0..3 monitoring range.
- Tests are split into unit (`pytest -q`) and optional vcsim integration
  (`pytest --run-integration`).

## Known Limitations

- `test.sh` is present but unreliable; do not depend on it for validation.
- `vcsim` is not feature-complete vs. real vCenter for every API surface.
- Use unit tests with mocks for unsupported simulator behavior.

## Golden Paths

### Run one command quickly

```bash
python -m checkvsphere.cli about -nossl -s 127.0.0.1 -o 8989 -u user -p pass
```

### Run unit tests

```bash
pytest -q
```

### Run vcsim integration tests

```bash
pytest -q --run-integration tests/integration_vcsim
```

### Run a targeted manual threshold scenario

```bash
python -m checkvsphere.cli snapshots --mode age --warning 1 \
  -nossl -s 127.0.0.1 -o 8989 -u user -p pass
echo $?
```

### Run lint hooks

```bash
pre-commit run --all-files
```

## Change Philosophy

- Keep diffs minimal and targeted.
- Avoid broad formatting-only rewrites.
- Preserve Python 3.6 compatibility.
- Update docs when CLI behavior changes.
- Prefer explicit exceptions in new code (avoid introducing bare `except:`).

## Where to Look First

- Command dispatch and global error handling: `checkvsphere/cli.py`
- Common CLI options and parser wrapper: `checkvsphere/tools/cli.py`
- vSphere connection/session behavior: `checkvsphere/tools/service_instance.py`
- Shared search/filter helpers: `checkvsphere/tools/helper.py`
- Command docs: `docs/cmd/*.md`

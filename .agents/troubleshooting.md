# Troubleshooting Guide

Practical debugging notes for common failures in `check_vsphere`.

## Quick Diagnostics

### Enable debug output

```bash
VSPHERE_DEBUG=1 python -m checkvsphere.cli about -nossl -s 127.0.0.1 -o 8989 -u user -p pass
```

### Increase global timeout

```bash
TIMEOUT=120 python -m checkvsphere.cli perf ...
```

### Use password from environment

```bash
VSPHERE_PASS='secret' python -m checkvsphere.cli about -nossl -s host -u user
```

## Common Failure Modes

### "command not found"

- The command string is mapped to an alnum module name.
- Example: `host-runtime` -> module `hostruntime.py`.
- Confirm module exists in `checkvsphere/vcmd/` and exports `__cmd__`.

### Unexpected status code

- Valid plugin exit codes are only 0..3.
- `checkvsphere/cli.py` normalizes invalid values to `3`.
- If a command exits with custom values, fix that module.

### `MonIllegalInstruction`

- This comes from `py-monplugin` when API calls are mixed incorrectly.
- Common cause: calling `add_perfdata()` and `add_perfmultidata()` together.
- Use exactly one perfdata mode per `Check` instance.

### Perfdata label errors

- `py-monplugin` rejects labels containing `'` or `=`.
- Newlines in labels are normalized to spaces automatically.
- Keep labels stable, simple, and ASCII-friendly.

### Connection issues

- Check host/port/user/password and SSL flags.
- Use `-nossl` for simulator/self-signed cert environments.
- If `CONNECT_NOFAIL` is set, connection errors may be transformed into
  non-critical flow; verify environment before debugging behavior.

### Session file oddities

- `--sessionfile` caches a session ID.
- If stale sessions cause problems, remove the file and retry.
- `about` may delete the session file in specific permission-error paths.

### Empty or surprising results

- Review include/exclude regex options (`--allowed`, `--banned`).
- Review `--match-method` (`search`, `match`, `fullmatch`).
- Some commands filter templates or inaccessible objects by design.

## Simulator-Oriented Checks

Run unit tests first:

```bash
pytest -q
```

Then run vcsim integration tests when binaries are available:

```bash
pytest -q --run-integration tests/integration_vcsim
```

Baseline command:

```bash
python -m checkvsphere.cli about -nossl -s 127.0.0.1 -o 8989 -u user -p pass
```

Then run one threshold-focused command and inspect exit code:

```bash
python -m checkvsphere.cli snapshots --mode age --warning 1 -nossl -s 127.0.0.1 -o 8989 -u user -p pass
echo $?
```

## When Changing Error Handling

- Keep messages actionable for monitoring operators.
- Prefer explicit exceptions in touched code.
- Avoid changing broad behavior in unrelated commands.
- Preserve compatibility with existing automation expecting current statuses.

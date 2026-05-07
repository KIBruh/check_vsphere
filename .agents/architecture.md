# Architecture Notes

This document explains how `check_vsphere` executes commands and where behavior
is implemented.

## High-Level Flow

1. User runs `check_vsphere <cmd>` (or `python -m checkvsphere.cli <cmd>`).
2. `checkvsphere/cli.py` pops `<cmd>` from argv and maps it to a module name.
3. Command module is imported from `checkvsphere.vcmd.<sanitized_name>`.
4. Module `run()` builds parser, connects to vSphere, evaluates state.
5. Module exits using monitoring status code (0=OK, 1=WARNING, 2=CRITICAL,
   3=UNKNOWN).
6. Top-level `main()` normalizes invalid/unexpected exit values to `3`.

## Command Resolution Details

- CLI sanitization uses alnum-only mapping in `checkvsphere/cli.py`.
- Example: `host-runtime` command maps to module `hostruntime.py`.
- Discovery for help listing uses `pkgutil.walk_packages` over `vcmd` modules.
- A command module must define `__cmd__` for discoverability.

## Module Responsibilities

### `checkvsphere/cli.py`
- Global timeout (`TIMEOUT`, default 30s) via alarm signal.
- Dynamic command loading.
- Uniform exception handling and exit normalization.
- Debug traceback behavior controlled via `VSPHERE_DEBUG`.

### `checkvsphere/tools/cli.py`
- Wrapper around `argparse` with standard connection options:
  - `--host`, `--port`, `--user`, `--password`, `-nossl`
  - `--sessionfile`
  - `--match-method` (`search|match|fullmatch` for regex filters)
- Hosts reusable argument definitions (`Argument` class).

### `checkvsphere/tools/service_instance.py`
- Owns connection lifecycle (`SmartConnect`, `Disconnect`).
- Supports session reuse through `--sessionfile`.
- Optional relaxed connect semantics via `CONNECT_NOFAIL`.

### `checkvsphere/tools/helper.py`
- Shared property-collector based inventory queries (`find_entity_views`).
- Regex include/exclude filtering (`isallowed`, `isbanned`).
- Shared option specs (`CheckArgument`).

### `checkvsphere/vcmd/*.py`
- One file per CLI command.
- Pattern is:
  1. define `__cmd__`
  2. build parser
  3. connect service instance
  4. evaluate conditions/thresholds
  5. exit with plugin-compatible status and message

## Status and Threshold Pattern

Most checks use `monplugin`:

See `.agents/monplugin.md` for detailed API behavior and edge cases.

```python
check = Check()
check.set_threshold(warning=args.warning, critical=args.critical)
check.add_message(Status.WARNING, "...")
(code, message) = check.check_messages(separator="\n")
check.exit(code=code, message=message)
```

Use this pattern to stay consistent with existing output and perfdata behavior.

## Documentation Structure

- End-user docs live under `docs/`.
- Command pages are in `docs/cmd/*.md`.
- Common options and env vars are in `docs/general-options.md`.

When adding/changing a command, update docs in the same change.

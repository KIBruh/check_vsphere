# Monplugin Notes

This project heavily relies on `py-monplugin` (`monplugin` package) for status,
threshold, message aggregation, and perfdata output.

Reference source used for this note:

- `https://raw.githubusercontent.com/ConSol-Monitoring/py-monplugin/refs/heads/main/monplugin/__init__.py`

## Key Types

### `Status`

Enum values and monitoring codes:

- `Status.OK = 0`
- `Status.WARNING = 1`
- `Status.CRITICAL = 2`
- `Status.UNKNOWN = 3`

Keep command behavior aligned with these exact values.

### `Range`

Parses monitoring threshold specs, for example:

- `10` (equivalent to `0:10`)
- `10:20`
- `~:10`
- `@1:5` (invert: alert when inside range)

Important semantics:

- `check(value)` returns `True` when alert condition is met.
- Empty/unset range means no alert.

### `Threshold`

Holds warning + critical ranges and returns status for one or more values.

Priority is critical first, warning second:

1. if any value hits critical -> `CRITICAL`
2. else if any value hits warning -> `WARNING`
3. else -> `OK`

## `Check` Object Pattern

Typical usage:

```python
from monplugin import Check, Status

check = Check()
check.set_threshold(warning=args.warning, critical=args.critical)

value = 42
status = check.check_threshold(value)
check.add_message(status, f"value is {value}")
check.add_perfdata(label="metric", value=value, threshold=check.threshold)

code, message = check.check_messages(separator="\n")
check.exit(code=code, message=message)
```

## Message Aggregation Behavior

- `check.add_message(status, text)` stores messages grouped by status.
- `check.check_messages()` returns highest severity present and joined text.
- `CRITICAL` outranks `WARNING`; `OK` used when no alerts are present.
- `allok=` can override OK output text when desired.

## Perfdata Behavior

### `add_perfdata(...)`

- Adds standard performance labels.
- Label restrictions:
  - cannot contain `'`
  - cannot contain `=`
- Label newlines are replaced with spaces.

### `add_perfmultidata(entity, check, ...)`

- Alternative perfdata mode for grouped/multi-entity output.
- Do not mix with `add_perfdata()` on the same `Check` object.
- Mixing modes raises `MonIllegalInstruction`.

### Output separator nuance

- `MONPLUGIN_ICINGA` (or `I_SHOULD_HAVE_USED_NAEMON_INSTEAD`) changes perfdata
  separator behavior in `get_perfdata()`.

## `exit()` Behavior (Important)

`check.exit(...)`:

- prints status line as `"<STATUS>: <message>"`
- prints perfdata block (may be empty)
- raises `SystemExit(<status_code>)`

In this repository, top-level CLI code catches/normalizes invalid exit codes,
so command modules should still emit proper `Status` values directly.

## Practical Guidance for This Repo

- Prefer `Status` enums over raw integers in command modules.
- Keep one `Check` instance per command execution path.
- Use `check.threshold` when adding perfdata so warning/critical are exported.
- Keep messages concise and operator-focused.
- Preserve 0..3 exit code contract for monitoring compatibility.

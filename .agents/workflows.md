# Agent Workflows

Checklists for common engineering tasks in this repository.

Testing approach is hybrid:
- default unit tests with mocks: `pytest -q`
- optional vcsim integration tests: `pytest --run-integration`
- manual CLI checks for targeted smoke/exit-code validation

## 1) Add or Modify a CLI Command

1. Locate target module in `checkvsphere/vcmd/`.
2. Keep or add `__cmd__ = '<name>'` and `run()`.
3. Build args via `cli.Parser()` and shared `CheckArgument` where possible.
4. Connect using `service_instance.connect(args)`.
5. Use `monplugin.Check` + `Status` for thresholds/messages/perfdata.
6. Ensure non-happy paths return valid monitoring codes (0..3 only).
7. Update command docs in `docs/cmd/<command>.md`.
8. Run relevant command manually against simulator.

## 2) Add a New Thresholded Check

Suggested pattern:

```python
check = Check()
check.set_threshold(warning=args.warning, critical=args.critical)
value = ...
status = check.check_threshold(value)
check.add_perfdata(label="metric", value=value, threshold=check.threshold)
check.exit(code=status, message=f"metric is {value}")
```

Notes:

- Include readable message text for operators.
- Keep perfdata labels stable when possible (avoid breaking dashboards).
- Prefer explicit states for maintenance mode behavior if relevant.
- Do not mix `add_perfdata()` and `add_perfmultidata()` in one check object.

## 3) Connection or Auth Changes

Touchpoints:

- `checkvsphere/tools/cli.py` for options.
- `checkvsphere/tools/service_instance.py` for connect/session semantics.
- `docs/general-options.md` for user-visible updates.

Validation:

- Verify `--sessionfile` behavior still works.
- Verify behavior with `CONNECT_NOFAIL` (connection errors can map to OK flow).

## 4) Error-Handling Cleanup

When improving exceptions:

- Keep output monitoring-friendly and concise.
- Avoid introducing raw tracebacks unless `VSPHERE_DEBUG` is enabled.
- Prefer replacing broad `except:` with explicit exception classes in changed code.
- Preserve top-level normalization to UNKNOWN (`3`) for unexpected failures.

## 5) Docs-Only Changes

If command behavior or options changed:

1. Update `docs/cmd/<command>.md`.
2. Update `docs/general-options.md` if shared options changed.
3. Keep examples runnable with current flags.

## 6) Commit Message Hygiene

- Aim for commit message lines around 72 characters.
- Keep wording natural; do not force awkward wraps.
- Use imperative subject and short rationale in body when needed.

## 7) Verification Sequence Before Finishing

Recommended minimum sequence:

```bash
pre-commit run --all-files
pytest -q
# when vcsim + govc are available
pytest -q --run-integration tests/integration_vcsim
python -m checkvsphere.cli about -nossl -s 127.0.0.1 -o 8989 -u user -p pass
python -m checkvsphere.cli snapshots --mode age --warning 1 -nossl -s 127.0.0.1 -o 8989 -u user -p pass
echo $?  # should reflect threshold status semantics
```

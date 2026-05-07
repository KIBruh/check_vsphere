# Command Matrix

Command ownership map for quick navigation.

## Core Commands

| CLI command | Python module | User docs |
|---|---|---|
| `about` | `checkvsphere/vcmd/about.py` | `docs/cmd/about.md` |
| `datastores` | `checkvsphere/vcmd/datastores.py` | `docs/cmd/datastores.md` |
| `host-nic` | `checkvsphere/vcmd/hostnic.py` | `docs/cmd/host-nic.md` |
| `host-runtime` | `checkvsphere/vcmd/hostruntime.py` | `docs/cmd/host-runtime.md` |
| `host-service` | `checkvsphere/vcmd/hostservice.py` | `docs/cmd/host-service.md` |
| `host-storage` | `checkvsphere/vcmd/hoststorage.py` | `docs/cmd/host-storage.md` |
| `list-metrics` | `checkvsphere/vcmd/listmetrics.py` | `docs/cmd/list-metrics.md` |
| `media` | `checkvsphere/vcmd/media.py` | `docs/cmd/media.md` |
| `perf` | `checkvsphere/vcmd/perf.py` | `docs/cmd/perf.md` |
| `power-state` | `checkvsphere/vcmd/powerstate.py` | `docs/cmd/power-state.md` |
| `snapshots` | `checkvsphere/vcmd/snapshots.py` | `docs/cmd/snapshots.md` |
| `vm-guestfs` | `checkvsphere/vcmd/vmguestfs.py` | `docs/cmd/vmguestfs.md` |
| `vm-net-dev` | `checkvsphere/vcmd/vmnetdev.py` | `docs/cmd/vmnetdev.md` |
| `vm-tools` | `checkvsphere/vcmd/vmtools.py` | `docs/cmd/vmtools.md` |
| `vsan` | `checkvsphere/vcmd/vsan.py` | `docs/cmd/vsan.md` |

## Shared Inputs

These options are added by `checkvsphere/tools/cli.py` across commands:

- `-s/--host`
- `-o/--port`
- `-u/--user`
- `-p/--password` (or env `VSPHERE_PASS`)
- `-nossl/--disable-ssl-verification`
- `--sessionfile`
- `--match-method search|match|fullmatch`

## Common Shared Helpers

- `checkvsphere/tools/helper.py::CheckArgument`: reusable command arg specs.
- `checkvsphere/tools/helper.py::find_entity_views`: property collector query.
- `checkvsphere/tools/helper.py::{isallowed, isbanned}`: regex filtering.
- `checkvsphere/tools/service_instance.py::connect`: connection/session logic.

## Extension Rules for New Commands

If you add a new command, make sure all four are done:

1. Add module in `checkvsphere/vcmd/` with `__cmd__` and `run()`.
2. Ensure CLI mapping works (`<cmd>` maps to alnum module name).
3. Add docs page under `docs/cmd/`.
4. Add tests:
   - unit test in `tests/unit/` for command logic/mocks
   - integration test in `tests/integration_vcsim/` when simulator supports it
5. Keep at least one executable manual validation scenario and expected exit code.

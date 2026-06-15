# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`mbctl` is a Man8S container orchestration CLI built on nerdctl/containerd. It manages container lifecycles on a Linux host with optional Yggdrasil IPv6 mesh networking. Unknown commands are transparently proxied to `nerdctl`.

## Development Setup

The project uses a local virtualenv at `.venv/`. Install in editable mode:

```bash
pip install -e .
```

Run with the installed entry point or directly as a module:

```bash
mbctl <command>
# or
PYTHONPATH=src python -m mbctl <command>
```

Most commands require `/etc/mbctl/config.yaml` to exist with at least a `yggaddr` field (a Yggdrasil IPv6 /64 prefix, e.g. `300:6b9f:cca2:a583::/64`).

## Running Tests

```bash
pytest                                      # all tests
pytest tests/test_conf_conv.py             # single file
pytest tests/test_conf_conv.py::test_conf_convert  # single test
```

Tests in `tests/` do not require a live nerdctl/containerd environment — they only exercise config parsing, YAML round-trip, and container-object conversions.

## Architecture

### Data flow: config file → nerdctl compose

1. **`/etc/mbctl/config.yaml`** → loaded into `MBConfig` (global settings: storage path, Yggdrasil addr, network names)
2. **`/var/lib/man8s/conf/<name>/container.yaml`** → parsed into `MBContainerConf` (Pydantic model)
3. `MBContainerConf` → `MBContainer` (enriched runtime object; stores computed Yggdrasil IPv6 addr, resolved mount paths)
4. `MBContainerTree` → resolves cross-container mount references (`source: other-container:/path`) in dependency order using Kahn's algorithm
5. `MBContainer.to_compose_conf()` → `ComposeConf` → serialized as a temporary YAML file passed to `nerdctl compose up`

### Module map

| Package | Purpose |
|---|---|
| `datatypes/` | Pydantic models: `MBContainerConf`, `ComposeConf`, `MountType`. `MBContainerConfFormat` handles RoundTrip YAML updates (preserving comments). |
| `MBContainer/` | Runtime container representation. `MBContainerTree` resolves `require`-based dependencies. `MBContainerMount` handles cross-container volume sharing. |
| `MBHost/` | Host filesystem operations: loading all containers from disk (`Loader`), creating mount directories, updating on-disk configs (`UpdateConfig`). |
| `NerdClient/` | `nerdctl` wrapper. `CommandExecutor` executes subprocesses; `NerdClient` adds container-specific methods; `NerdContainerInfo` parses `nerdctl ps --format json`. |
| `cli/` | Typer commands (`run`, `list`, `tree`, `shell`, `enable`, `disable`, `autostart`). Unknown argv is passed through to `nerdctl` via `os.execvp`. |
| `network/` | Yggdrasil IPv6 address derivation: SHA-256 of container name → 64-bit suffix appended to host prefix. |

### Storage layout on disk

```
/var/lib/man8s/
  conf/<name>/container.yaml   # per-container config (and sub-mounts)
  data/<name>/...
  log/<name>/...
  cache/<name>/...
  plugin/<name>/...
  socket/<name>/...
```

### Key design decisions

- **YAML edits use `ruamel.yaml` in RoundTrip mode** (not `pyyaml`) to preserve user comments and formatting when `enable`/`disable` updates the `autostart` field.
- **Mount references** (`source: other-container:/inner/path`) are deferred until `MBContainerTree.resolve_all()` so the resolution always uses the real host path of the referenced container's mount entry.
- **`copyfrom`** mounts spin up a temporary container, copy the image path to the host with `nerdctl exec` + tar (preserving ownership), then remove the temp container before the real container starts.
- **Restart policy** maps `autostart: true` → `unless-stopped`, `false` → `no`. The systemd unit (`systemd/mbctl-startup.service`) calls `mbctl autostart` on boot.
- **DNS** can be `"host"` (none set), an IP literal, or a container name (resolved to that container's Yggdrasil address).
- **`extra_hosts`** in `MBContainerConf` is a `dict[str, str]` (hostname → IP) merged with the auto-generated Yggdrasil entries from `local_access`. User-defined entries take precedence on collision. Use `local_access` for containers reachable at `<name>.man8s.local`; use `extra_hosts` for arbitrary hostnames (e.g. public FQDN pointing to Yggdrasil IPs).
- **`extra_compose_configs`** in `MBContainerConf` are merged verbatim into the generated compose service dict, overriding built-in fields with a warning.

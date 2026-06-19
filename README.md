# Free Google Cloud token flow for DBeaver Community

[![CI](https://github.com/hu553in/dbeaver-gcloud-free/actions/workflows/ci.yml/badge.svg)](https://github.com/hu553in/dbeaver-gcloud-free/actions/workflows/ci.yml)

A free local alternative to DBeaver's paid Google Cloud token flow. It opens a **temporary DBeaver
connection** using a fresh token from `gcloud auth print-access-token`.

It is meant for setups where a Google Cloud access token can be used as the database password and
DBeaver does not handle that flow directly.

## What it does

- Reads local YAML config files
- Prompts for a config, environment, and database
- Fetches a fresh Google Cloud access token
- Starts DBeaver with a temporary connection

The tool does not modify saved DBeaver connections or store tokens in its own config.

## Requirements

- Python 3.13+
- `uv`
- DBeaver installed locally
- `gcloud` available in `PATH`
- a valid Google Cloud login session
- network access to the target database host

Additional requirements for specific workflows:

- `git` - required for `uv tool install git+...` and `uvx --from git+...`
- `make` - required for `make install-deps` and `make check`

## Configuration

Config files are discovered from:

```text
~/.config/dbeaver-gcloud-free/*.y*ml
```

### Example config

```yaml
db-driver: postgresql
dbeaver-bin: /Applications/DBeaver.app/Contents/MacOS/dbeaver

envs:
  - name: dev
    ip: 10.15.20.25
    port: 5432
  - name: test
    ip: 10.15.20.26
    port: 5432

user: awesome.user@gmail.com

databases:
  - some-db
  - another-db

show-all-dbs: true
```

### Config fields

| Name           | Required | Default                                            | Description                                                |
| -------------- | -------- | -------------------------------------------------- | ---------------------------------------------------------- |
| `db-driver`    | No       | `postgresql`                                       | DBeaver driver ID                                          |
| `dbeaver-bin`  | No       | `/Applications/DBeaver.app/Contents/MacOS/dbeaver` | Path to the DBeaver executable                             |
| `envs`         | Yes      | -                                                  | Non-empty list of environments                             |
| `user`         | Yes      | -                                                  | Database username passed to DBeaver                        |
| `databases`    | Yes      | -                                                  | Non-empty list of database names                           |
| `show-all-dbs` | No       | `false`                                            | Enables DBeaver's PostgreSQL "show all databases" property |

Each environment must contain:

- `name`
- `ip`
- `port`

## Installation

### `uv tool`

Useful commands:

```bash
uv tool install .
uv tool install git+https://github.com/hu553in/dbeaver-gcloud-free.git
dbgc
uv tool upgrade dbeaver-gcloud-free
uv tool uninstall dbeaver-gcloud-free
```

### `uvx`

Useful commands:

```bash
uvx --from . dbgc
uvx --from git+https://github.com/hu553in/dbeaver-gcloud-free.git dbgc
```

### Development checkout

Useful commands:

```bash
make install-deps
uv run python3 main.py
make check
```

Or with plain `python3` and `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install questionary pyyaml pydantic
python3 main.py
```

## Execution flow

1. Find config files in `~/.config/dbeaver-gcloud-free/*.y*ml`
2. Ask which config to use
3. Ask which environment to use
4. Ask which database to use
5. Run `gcloud auth print-access-token`
6. Start DBeaver with `-con`

## Runtime behavior

### Temporary connections only

The launcher always creates a temporary DBeaver connection:

```text
save=false
```

It does not overwrite saved DBeaver profiles.

### Token source

The token is taken from:

```bash
gcloud auth print-access-token
```

This requires an active `gcloud` authentication session.

### Validation

The config schema is validated with Pydantic.

Invalid configs fail early, for example when:

- `envs` is missing or empty
- `user` is missing or empty
- `databases` is missing or empty
- `port` is outside `1..65535`

## Example command

The script builds a command like this:

```text
dbeaver -con "driver=postgresql|host=10.15.20.25|port=5432|database=some-db|user=awesome.user@gmail.com|password=<fresh-token>|name=GCloud: dev / 10.15.20.25:5432 / some-db|save=false|connect=true"
```

If `show-all-dbs: true` is enabled, the corresponding DBeaver connection property is added as well.

## Notes

- The tool assumes the target database auth flow accepts `gcloud auth print-access-token` as the
  password.
- It does not verify network reachability before opening DBeaver.
- It does not manage token refresh after DBeaver starts.
- It is local and single-user in scope.
- The token is passed to DBeaver as part of the launch arguments, so treat the local machine and
  user session as sensitive.

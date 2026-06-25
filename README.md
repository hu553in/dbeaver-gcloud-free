# Free Google Cloud token flow for DBeaver Community

[![CI](https://github.com/hu553in/dbeaver-gcloud-free/actions/workflows/ci.yml/badge.svg)](https://github.com/hu553in/dbeaver-gcloud-free/actions/workflows/ci.yml)

Local launcher for opening a temporary DBeaver connection with a fresh token from
`gcloud auth print-access-token`.

## What it does

- Reads connection presets from local YAML files
- Prompts for config, environment, and database
- Uses the current Google Cloud CLI session as the token source
- Starts DBeaver with a temporary `-con` connection

The tool does not change saved DBeaver connections and does not store tokens.

## Requirements

- Python 3.13+
- `uv`
- DBeaver
- `gcloud` in `PATH` with an active login session
- Network access to the target database
- `git` for installing from GitHub

## Setup

Install as a `uv` tool:

```bash
uv tool install git+https://github.com/hu553in/dbeaver-gcloud-free.git
```

Or run without installing:

```bash
uvx --from git+https://github.com/hu553in/dbeaver-gcloud-free.git dbgc
```

## Configuration

Config files are discovered from:

```text
~/.config/dbeaver-gcloud-free/*.y*ml
```

Minimal config:

```yaml
db-driver: postgresql
dbeaver-bin: /Applications/DBeaver.app/Contents/MacOS/dbeaver

envs:
  - name: dev
    ip: 10.15.20.25
    port: 5432

user: awesome.user@gmail.com

databases:
  - some-db

show-all-dbs: true
```

| Name           | Required | Default                                            | Description                                                |
| -------------- | -------- | -------------------------------------------------- | ---------------------------------------------------------- |
| `db-driver`    | No       | `postgresql`                                       | DBeaver driver ID                                          |
| `dbeaver-bin`  | No       | `/Applications/DBeaver.app/Contents/MacOS/dbeaver` | Path to the DBeaver executable                             |
| `envs`         | Yes      | -                                                  | List of environments with `name`, `ip`, and `port`         |
| `user`         | Yes      | -                                                  | Database username passed to DBeaver                        |
| `databases`    | Yes      | -                                                  | Database names shown in the prompt                         |
| `show-all-dbs` | No       | `false`                                            | Enables DBeaver's PostgreSQL "show all databases" property |

## Usage

```bash
dbgc
```

From a checkout:

```bash
uv run dbgc
```

The generated DBeaver connection uses:

```text
driver=postgresql|host=10.15.20.25|port=5432|database=some-db|user=awesome.user@gmail.com|password=<fresh-token>|save=false|connect=true
```

## Runtime behavior

- Tokens come from `gcloud auth print-access-token`
- Connections are temporary (`save=false`)
- Config validation fails early for missing values and invalid ports
- The local machine and user session should be treated as sensitive because the token is passed to
  DBeaver as a launch argument

## Development

```bash
make install-deps
make check
```

Focused checks:

```bash
make lint
make check-types
```

#!/usr/bin/env python3

from __future__ import annotations

import os
import signal
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Annotated, NoReturn

import questionary
import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CONFIG_DIR = Path("~/.config/dbeaver-gcloud-free").expanduser()
CONFIG_GLOB = "*.y*ml"

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class EnvConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: NonEmptyStr
    ip: NonEmptyStr
    port: int = Field(gt=0, le=65535)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    db_driver: NonEmptyStr = Field(default="postgresql", alias="db-driver")
    dbeaver_bin: NonEmptyStr = Field(
        default="/Applications/DBeaver.app/Contents/MacOS/dbeaver", alias="dbeaver-bin"
    )

    envs: list[EnvConfig] = Field(min_length=1)
    user: NonEmptyStr
    databases: list[NonEmptyStr] = Field(min_length=1)
    show_all_dbs: bool = Field(default=False, alias="show-all-dbs")


def fail(message: str, exit_code: int = 1) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(exit_code)


def find_config_files() -> list[Path]:
    return sorted(
        (path for path in CONFIG_DIR.glob(CONFIG_GLOB) if path.is_file()),
        key=lambda path: path.name,
    )


def ensure_config_files_exist() -> list[Path]:
    files = find_config_files()
    if files:
        return files

    fail(f"""\
no config files found in {CONFIG_DIR}/{CONFIG_GLOB}.

You must create one manually, for example:

mkdir -p {CONFIG_DIR} && \\
cat >{CONFIG_DIR}/example.yml <<'EOF'
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
EOF""")


def choose_config(configs: list[Path]) -> Path:
    configs_by_name = {path.name: path for path in configs}

    selected = questionary.select("Choose config", choices=list(configs_by_name), qmark=">").ask()
    if selected is None:
        fail("operation is cancelled", 130)

    return configs_by_name[selected]


def choose_env(envs: list[EnvConfig]) -> EnvConfig:
    envs_by_name = {env.name: env for env in envs}

    selected = questionary.select("Choose environment", choices=list(envs_by_name), qmark=">").ask()
    if selected is None:
        fail("operation is cancelled", 130)

    return envs_by_name[selected]


def choose_db(databases: list[str]) -> str:
    selected = questionary.select("Choose database", choices=databases, qmark=">").ask()
    if selected is None:
        fail("operation is cancelled", 130)

    return selected


def get_gcloud_token() -> str:
    result = subprocess.run(  # nosec B603 B607
        ["gcloud", "auth", "print-access-token"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        stdin=sys.stdin,
    )

    token = result.stdout.strip()
    if not token:
        fail("unable to get access token from gcloud")

    return token


def build_conn_str(  # noqa: PLR0913
    *,
    db_driver: str,
    host: str,
    port: int,
    db: str,
    user: str,
    token: str,
    env_name: str,
    show_all_dbs: bool,
) -> str:
    parts = [
        f"driver={db_driver}",
        f"host={host}",
        f"port={port}",
        f"database={db}",
        f"user={user}",
        f"password={token}",
        f"name=GCloud: {env_name} / {host}:{port} / {db}",
        "save=false",
        "connect=true",
    ]

    if show_all_dbs:
        parts.append("prop.@dbeaver-show-non-default-db@=true")

    return "|".join(parts)


def launch_dbeaver(dbeaver_bin: str, connection_string: str) -> None:
    proc = subprocess.Popen(  # nosec B603
        [dbeaver_bin, "-con", connection_string], start_new_session=True, text=True
    )

    try:
        proc.wait()
    except KeyboardInterrupt:
        os.killpg(proc.pid, signal.SIGTERM)

        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)

        fail("operation is cancelled", 130)


def main() -> int:
    try:
        config_files = ensure_config_files_exist()
        config_file = choose_config(config_files)
        config = AppConfig.model_validate(yaml.safe_load(config_file.read_text(encoding="utf-8")))

        env_names = [env.name for env in config.envs]
        if len(env_names) != len(set(env_names)):
            fail("duplicate env names are not allowed")

        env = choose_env(config.envs)
        db = choose_db(config.databases)
        token = get_gcloud_token()

        conn_str = build_conn_str(
            db_driver=config.db_driver,
            host=env.ip,
            port=env.port,
            db=db,
            user=config.user,
            token=token,
            env_name=env.name,
            show_all_dbs=config.show_all_dbs,
        )

        launch_dbeaver(config.dbeaver_bin, conn_str)

    except Exception as exc:
        fail(str(exc))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

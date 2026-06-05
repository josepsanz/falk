"""Configuration loading for Falk.

Resolves the devices file and database URI from the environment or the
``devices.yaml`` file, so telemetry and the web API share a single source of
truth for where the database lives.
"""

import functools
import os
from pathlib import Path

import yaml

DEFAULT_DEVICES_FILE = "devices.yaml"

DEVICES_FILE_ENV = "FALK_DEVICES_FILE"
DATABASE_URI_ENV = "FALK_DATABASE_URI"


def devices_file_path() -> Path:
    """Return the path to the devices file, honouring the env override."""
    return Path(os.environ.get(DEVICES_FILE_ENV, DEFAULT_DEVICES_FILE))


@functools.lru_cache(maxsize=1)
def load_config() -> dict:
    """Load and cache the parsed devices file.

    Returns:
        The parsed YAML document with ``database`` and ``devices`` keys.
    """
    with devices_file_path().open() as fp:
        return yaml.safe_load(fp)


def database_uri() -> str:
    """Resolve the SQLAlchemy database URI.

    The ``FALK_DATABASE_URI`` environment variable wins; otherwise the URI is
    read from the devices file.
    """
    return os.environ.get(DATABASE_URI_ENV) or load_config()["database"]["uri"]

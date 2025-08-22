from pathlib import Path
from typing import Any
from dataclasses import dataclass
import json

@dataclass(frozen=True)
class eBuilderConfig:
    hostname: str
    username: str
    password: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "eBuilderConfig":
        required = ("hostname", "username", "password")
        missing = [k for k in required if k not in data]
        if missing:
            raise ValueError(f"Missing required config keys: {', '.join(missing)}")

        # Type checks
        for key in required:
            if not isinstance(data[key], str):
                raise TypeError(f"Config key '{key}' must be a string")

        return eBuilderConfig(
            hostname=data["hostname"].strip(),
            username=data["username"].strip(),
            password=data["password"],  # keep as-is; don't strip passwords
        )


def load_config(path: Path) -> eBuilderConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Config path is not a file: {path}")

    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")

    return eBuilderConfig.from_dict(data)
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
import json

@dataclass(frozen=True)
class eBuilderConfig:
    hostname: str
    username: str
    password: str
    data_cache_dir: Optional[str] = None
    daily_imports_dir: Optional[str] = None
    from_bw_dir: Optional[str] = None
    fmp_output_file: Optional[str] = None

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

        optional = ("data_cache_dir", "daily_imports_dir", "from_bw_dir", "fmp_output_file")
        for key in optional:
            if key in data and data[key] is not None and not isinstance(data[key], str):
                raise TypeError(f"Config key '{key}' must be a string or null")

        return eBuilderConfig(
            hostname=data["hostname"].strip(),
            username=data["username"].strip(),
            password=data["password"],  # keep as-is; don't strip passwords
            data_cache_dir=data.get("data_cache_dir"),
            daily_imports_dir=data.get("daily_imports_dir"),
            from_bw_dir=data.get("from_bw_dir"),
            fmp_output_file=data.get("fmp_output_file"),
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


def resolve_config_path(path_value: Optional[str], key: str) -> Path:
    if path_value is None or not path_value.strip():
        raise ValueError(
            f"Missing required config key '{key}' in config.ebuilder.json. "
            f"See config.ebuilder.example.json for the expected format."
        )

    return Path(path_value).expanduser()
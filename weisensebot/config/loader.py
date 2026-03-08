"""Configuration loading utilities."""

import json
from pathlib import Path

from weisensebot.config.schema import Config


def get_config_path() -> Path:
    """
    Get the default configuration file path.

    Implements backward compatibility:
    - First checks ~/.weisensebot/config.json (new location)
    - Falls back to ~/.nanobot/config.json (legacy location)

    Returns:
        Path to the configuration file
    """
    # 优先使用新配置目录
    new_config = Path.home() / ".weisensebot" / "config.json"

    # 如果新配置存在，直接返回
    if new_config.exists():
        return new_config

    # 检查旧配置是否存在
    old_config = Path.home() / ".nanobot" / "config.json"

    if old_config.exists():
        # 返回旧配置路径（向后兼容）
        print(f"⚠ 使用旧配置目录: {old_config}")
        print(f"   建议运行迁移脚本: python -m weisensebot.migrations.migrate_config")
        return old_config

    # 都不存在，返回新路径（后续会创建默认配置）
    return new_config


def get_data_dir() -> Path:
    """
    Get weisensebot data directory.

    Implements backward compatibility by checking both old and new locations.

    Returns:
        Path to the data directory
    """
    from weisensebot.utils.helpers import get_data_path

    return get_data_path()


def get_legacy_data_dir() -> Path | None:
    """
    Get legacy nanobot data directory if it exists.

    Returns:
        Path to legacy directory or None if it doesn't exist
    """
    old_dir = Path.home() / ".nanobot"
    return old_dir if old_dir.exists() else None


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
    path = config_path or get_config_path()

    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data = _migrate_config(data)
            return Config.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            print("Using default configuration.")

    return Config()


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(by_alias=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data

"""
Weisensebot 数据迁移模块。

提供从旧版本(nanobot)迁移数据的功能。
"""

from weisensebot.migrations.migrate_config import migrate_config

__all__ = ["migrate_config"]

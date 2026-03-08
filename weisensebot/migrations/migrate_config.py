#!/usr/bin/env python3
"""
数据迁移脚本：从 ~/.nanobot/ 迁移到 ~/.weisensebot/

用法：
    python -m weisensebot.migrations.migrate_config

功能：
    1. 检查是否存在旧的 ~/.nanobot/ 目录
    2. 如果存在，提示用户是否迁移
    3. 复制配置文件、工作区、认证数据到新目录
    4. 更新配置文件中的路径引用
    5. 保留旧目录作为备份
"""

import json
import shutil
from pathlib import Path
import sys


def migrate_config() -> bool:
    """
    执行配置迁移

    返回:
        bool: 迁移是否成功
    """
    # 定义路径
    old_dir = Path.home() / ".nanobot"
    new_dir = Path.home() / ".weisensebot"

    # 检查旧目录是否存在
    if not old_dir.exists():
        print("✓ 旧的配置目录 ~/.nanobot/ 不存在，无需迁移")
        return True

    # 检查新目录是否已存在
    if new_dir.exists():
        print("⚠ 新配置目录 ~/.weisensebot/ 已存在")
        response = input("是否继续迁移？这将覆盖部分文件 (y/N): ").strip().lower()
        if response != "y":
            print("❌ 迁移已取消")
            return False

    print(f"📦 开始从 {old_dir} 迁移到 {new_dir}...")

    # 创建新目录
    new_dir.mkdir(parents=True, exist_ok=True)

    # 需要迁移的文件/目录
    items_to_migrate = [
        "config.json",  # 配置文件
        "workspace",  # 工作区
        "history",  # CLI历史
        "cron",  # Cron任务
        "matrix-store",  # Matrix数据
    ]

    migrated_count = 0
    skipped_count = 0

    for item in items_to_migrate:
        old_path = old_dir / item
        new_path = new_dir / item

        if not old_path.exists():
            print(f"  ⏭ 跳过 {item} (不存在)")
            skipped_count += 1
            continue

        try:
            if old_path.is_file():
                shutil.copy2(old_path, new_path)
            else:
                # 如果目标已存在，先删除
                if new_path.exists():
                    shutil.rmtree(new_path)
                shutil.copytree(old_path, new_path)

            print(f"  ✓ 迁移 {item}")
            migrated_count += 1
        except Exception as e:
            print(f"  ❌ 迁移 {item} 失败: {e}")

    # 更新配置文件中的路径
    config_file = new_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新工作区路径
            if "agents" in config and "defaults" in config["agents"]:
                workspace_path = config["agents"]["defaults"].get("workspace")
                if workspace_path and ".nanobot" in workspace_path:
                    new_workspace = workspace_path.replace(".nanobot", ".weisensebot")
                    config["agents"]["defaults"]["workspace"] = new_workspace
                    print(f"  ✓ 更新工作区路径: {new_workspace}")

            # 保存更新后的配置
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"  ⚠ 更新配置文件失败: {e}")

    print(f"\n🎉 迁移完成！")
    print(f"   - 迁移了 {migrated_count} 项")
    print(f"   - 跳过了 {skipped_count} 项")
    print(f"\n💡 旧配置目录仍保留在: {old_dir}")
    print(f"   如果确认迁移成功，可以手动删除旧目录")

    return True


def check_and_prompt_migration() -> None:
    """
    检查是否需要迁移，并在需要时提示用户
    """
    old_dir = Path.home() / ".nanobot"
    new_dir = Path.home() / ".weisensebot"

    # 如果新目录已有配置，无需提示
    if new_dir.exists() and (new_dir / "config.json").exists():
        return

    # 如果旧目录存在但新目录没有，提示迁移
    if old_dir.exists() and (old_dir / "config.json").exists():
        print("\n" + "=" * 60)
        print("⚠ 检测到旧的 nanobot 配置目录")
        print("=" * 60)
        print(f"旧位置: {old_dir}")
        print(f"新位置: {new_dir}")
        print()
        response = input("是否要迁移旧配置到新目录？(Y/n): ").strip().lower()

        if response == "" or response == "y":
            migrate_config()
        else:
            print("跳过迁移，将使用默认配置")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("维思机器人 (Weisensebot) 配置迁移工具")
    print("=" * 60 + "\n")

    success = migrate_config()
    sys.exit(0 if success else 1)

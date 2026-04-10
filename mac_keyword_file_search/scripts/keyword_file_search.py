#!/usr/bin/env python3
"""
keyword_file_search.py - Mac 关键词文件检索
基于 mdfind（文件名 + 内容）+ fzf 交互式筛选，全程本地运行。
默认使用 mdfind 原生权限范围，可通过 --dir 参数限定搜索目录。
"""

from __future__ import annotations

import sys
import shutil
import subprocess
import argparse
from typing import Optional, List


# 依赖检查

def check_dep(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def ensure_deps():
    if not check_dep("fzf"):
        print("❌ 缺少依赖: fzf")
        print()
        print("  请执行以下命令安装：")
        print("    brew install fzf")
        sys.exit(1)


# 搜索

def run_mdfind(keyword: str, search_dir: Optional[str]) -> List[str]:
    """
    使用 mdfind 搜索文件名或内容包含 keyword 的文件。
    search_dir 不为空时使用 -onlyin 限定目录。
    """
    cmd = ["mdfind"]
    if search_dir:
        cmd += ["-onlyin", search_dir]
    cmd.append(keyword)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return [l for l in result.stdout.splitlines() if l.strip()]
    except subprocess.TimeoutExpired:
        print("❌ mdfind 搜索超时，请使用 --dir 缩小搜索范围", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ mdfind 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


# fzf 交互选择

def run_fzf(candidates: List[str]) -> Optional[str]:
    """启动 fzf 交互式选择，返回选中路径或 None"""
    fzf_cmd = [
        "fzf",
        "--ansi",
        "--height=70%",
        "--layout=reverse",
        "--border",
        "--prompt=🔍 选择文件: ",
        "--preview=ls -lh {} 2>/dev/null || echo '(无法预览)'",
        "--preview-window=down:3:wrap",
        "--bind=ctrl-/:toggle-preview",
    ]

    try:
        result = subprocess.run(
            fzf_cmd,
            input="\n".join(candidates),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception as e:
        print(f"❌ fzf 运行失败: {e}", file=sys.stderr)
        sys.exit(1)


# 操作菜单

def action_menu(filepath: str):
    """选择文件后的操作菜单"""
    print(f"\n📄 已选择: {filepath}\n")
    print("  [1] 复制路径到剪贴板  ← 默认（直接回车）")
    print("  [2] 用 Finder 打开所在目录")
    print("  [3] 用默认程序打开")
    print("  [4] 用 VS Code 编辑")
    print("  [5] 仅打印路径")
    print("  [q] 退出")
    print()

    choice = input("请选择操作 [1-5/q，回车=1]: ").strip().lower()
    if choice == "":
        choice = "1"

    if choice == "1":
        subprocess.run(["pbcopy"], input=filepath, text=True)
        print(f"✅ 路径已复制到剪贴板: {filepath}")

    elif choice == "2":
        subprocess.run(["open", "-R", filepath])
        print(f"✅ 已在 Finder 中显示: {filepath}")

    elif choice == "3":
        subprocess.run(["open", filepath])
        print(f"✅ 已用默认程序打开: {filepath}")

    elif choice == "4":
        if check_dep("code"):
            subprocess.run(["code", filepath])
            print(f"✅ 已用 VS Code 打开: {filepath}")
        else:
            print("❌ 未找到 VS Code 命令行工具 'code'")
            print("   请在 VS Code 中执行: Shell Command: Install 'code' command in PATH")

    elif choice == "5":
        print(filepath)

    elif choice == "q":
        pass

    else:
        print("⚠️  无效选择")


# 主入口

def main():
    parser = argparse.ArgumentParser(
        description="Mac 关键词文件检索（mdfind 文件名+内容 + fzf 交互筛选）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
说明:
  默认使用 mdfind 原生权限范围（当前用户可访问的所有文件）。
  使用 --dir 可将搜索限定在指定目录，提升速度并保护隐私。

示例:
  %(prog)s 心跳检查系统
  %(prog)s invoice --dir ~/Documents
  %(prog)s config --dir ~/myproject
  %(prog)s readme --dir .
  %(prog)s report --print
        """,
    )
    parser.add_argument("keyword", help="搜索关键词（支持中文，匹配文件名和文件内容）")
    parser.add_argument(
        "--dir", "-d",
        dest="search_dir",
        metavar="DIR",
        default=None,
        help="限定搜索目录（可选，默认搜索 mdfind 原生权限范围）",
    )
    parser.add_argument(
        "--print",
        dest="print_only",
        action="store_true",
        help="选择后直接打印路径，不显示操作菜单（适合脚本调用）",
    )

    args = parser.parse_args()

    # 检查依赖
    ensure_deps()

    keyword = args.keyword.strip()
    search_dir: Optional[str] = args.search_dir

    # 执行搜索
    lines = run_mdfind(keyword, search_dir)

    if not lines:
        scope = f"[{search_dir}]" if search_dir else "全局"
        print(f"⚠️  {scope} 未找到匹配 '{keyword}' 的文件")
        sys.exit(0)

    # fzf 交互选择
    selected = run_fzf(lines)

    if not selected:
        sys.exit(0)

    if args.print_only:
        print(selected)
    else:
        action_menu(selected)


if __name__ == "__main__":
    main()

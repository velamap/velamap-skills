#!/usr/bin/env python3
"""
ocr_extract.py — OCR 文字提取工具（主入口）

从任意来源（剪贴板截图、本地图片、URL）提取文字，输出结构化内容（Markdown / 纯文本 / JSON），供 AI 直接消费。

支持平台:
  - macOS  : ocrmac (Apple Vision Framework)
  - Linux  : pytesseract + tesseract
  - Windows: Windows.Media.Ocr (系统内置)

支持来源:
  - clipboard : 从系统剪贴板读取图片（截图后直接识别）
  - file      : 本地图片文件（PNG/JPG/BMP/TIFF/WEBP）
  - url       : 网络图片（自动下载后识别）
  - screenshot: 直接截取当前屏幕（可指定区域）

用法:
  python3 ocr_extract.py [path_or_url]
  python3 ocr_extract.py [--source SOURCE] [--input INPUT]
                         [--format FORMAT] [--lang LANG]
                         [--region x,y,w,h] [--query QUERY]

示例:
  python3 ocr_extract.py --source clipboard
  python3 ocr_extract.py --source file --input /path/to/img.png
  python3 ocr_extract.py --source url --input https://example.com/img.png
  python3 ocr_extract.py --source screenshot --region 0,0,1920,1080
  python3 ocr_extract.py /path/to/img.png
  python3 ocr_extract.py https://example.com/img.png
"""

import sys
import argparse

# 确保同目录下的模块可被导入
import os
sys.path.insert(0, os.path.dirname(__file__))

from sources import (
    get_image_from_clipboard,
    get_image_from_file,
    get_image_from_url,
    get_image_from_screenshot,
)
from engines import perform_ocr
from formatters import format_as_markdown, format_as_text, format_as_json, apply_query_filter


# 参数解析
def parse_args():
    parser = argparse.ArgumentParser(
        description='AI 专属多入口 OCR 文字提取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --source clipboard
  %(prog)s --source file --input /path/to/img.png --format markdown
  %(prog)s --source url --input https://example.com/img.png --lang en
  %(prog)s --source screenshot --region 0,0,1920,1080 --query "错误信息"

  # 快捷方式：直接传路径或 URL 作为位置参数
  %(prog)s /path/to/img.png
  %(prog)s https://example.com/img.png
        """
    )
    # 位置参数：直接传路径或 URL（可选）
    parser.add_argument(
        'path',
        nargs='?',
        default=None,
        help='图片路径或 URL（快捷方式，自动推断来源类型）'
    )
    parser.add_argument(
        '--source',
        default='clipboard',
        help='图片来源（clipboard/file/url/screenshot，默认: clipboard）'
    )
    parser.add_argument(
        '--input', '-i',
        default=None,
        help='输入路径或 URL（--source 为 file/url 时必填）'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'text', 'json'],
        default='markdown',
        help='输出格式（默认: markdown）'
    )
    parser.add_argument(
        '--lang', '-l',
        choices=['auto', 'zh', 'en'],
        default='auto',
        help='识别语言（默认: auto；zh=中文，en=英文）'
    )
    parser.add_argument(
        '--region', '-r',
        default=None,
        help='截屏区域，格式: x,y,w,h（仅 --source screenshot 有效）'
    )
    parser.add_argument(
        '--query', '-q',
        default=None,
        help='语义过滤关键词，只返回包含该关键词的行（可选）'
    )
    return parser.parse_args()


# 单图处理
def process_single_image(image, args):
    """对单张图片执行 OCR 并格式化输出"""
    lines, engine, err = perform_ocr(image, args.lang)
    if err:
        print(f"❌ OCR 失败: {err}", file=sys.stderr)
        return None

    if args.query:
        lines = apply_query_filter(lines, args.query)

    if args.format == 'markdown':
        return format_as_markdown(lines)
    elif args.format == 'text':
        return format_as_text(lines)
    elif args.format == 'json':
        return format_as_json(lines, engine, args.source)
    return ''


# 前置依赖检查
def preflight_check(source: str) -> bool:
    """
    根据来源类型，提前检查所需的系统依赖是否满足。
    发现缺失时立即打印清晰的安装提示，返回 False。
    """
    import shutil
    from deps import IS_LINUX, get_linux_install_cmd

    missing = []

    # Linux 剪贴板需要 xclip/xsel
    if source == 'clipboard' and IS_LINUX:
        if shutil.which('xclip') is None and shutil.which('xsel') is None:
            missing.append(f"xclip 或 xsel（Linux 剪贴板工具）\n    安装命令: {get_linux_install_cmd('xclip')}")

    if missing:
        print("❌ 缺少以下系统依赖，请先安装后重试：", file=sys.stderr)
        for item in missing:
            print(f"   • {item}", file=sys.stderr)
        return False
    return True


# 路径/URL 智能推断
def _infer_source(value: str) -> tuple:
    """
    将路径或 URL 字符串推断为 (source, input_path)。
    """
    if value.startswith('http://') or value.startswith('https://'):
        return 'url', value
    return 'file', value


# 主流程
def main():
    args = parse_args()

    # 位置参数优先：直接传路径/URL 时自动推断来源
    if args.path is not None:
        args.source, args.input = _infer_source(args.path)

    if args.source in ('file', 'url') and not args.input:
        print(f"❌ --source {args.source} 需要指定 --input 参数", file=sys.stderr)
        sys.exit(1)

    # 前置依赖检查
    if not preflight_check(args.source):
        sys.exit(1)

    print(f"🔍 OCR 提取中 [来源: {args.source}] [语言: {args.lang}] [格式: {args.format}]",
          file=sys.stderr)

    # 获取图片并执行 OCR
    if args.source == 'clipboard':
        print("   Reading clipboard...", end=' ', flush=True, file=sys.stderr)
        img, err = get_image_from_clipboard()
        if err:
            print(f"\n❌ {err}", file=sys.stderr)
            sys.exit(1)
        print(f"✓ ({img.width}x{img.height})", file=sys.stderr)
        result = process_single_image(img, args)

    elif args.source == 'file':
        print(f"   Loading file: {args.input}...", end=' ', flush=True, file=sys.stderr)
        img, err = get_image_from_file(args.input)
        if err:
            print(f"\n❌ {err}", file=sys.stderr)
            sys.exit(1)
        print(f"✓ ({img.width}x{img.height})", file=sys.stderr)
        result = process_single_image(img, args)

    elif args.source == 'url':
        img, err = get_image_from_url(args.input)
        if err:
            print(f"❌ {err}", file=sys.stderr)
            sys.exit(1)
        print(f"   Image size: {img.width}x{img.height}", file=sys.stderr)
        result = process_single_image(img, args)

    elif args.source == 'screenshot':
        print("   Taking screenshot...", end=' ', flush=True, file=sys.stderr)
        img, err = get_image_from_screenshot(args.region)
        if err:
            print(f"\n❌ {err}", file=sys.stderr)
            sys.exit(1)
        print(f"✓ ({img.width}x{img.height})", file=sys.stderr)
        result = process_single_image(img, args)

    else:
        print(f"❌ 未知来源: {args.source}", file=sys.stderr)
        sys.exit(1)

    # 输出结果
    if result is None:
        sys.exit(1)

    if not result.strip():
        print("⚠️  未识别到任何文字内容", file=sys.stderr)
        sys.exit(0)

    print(result)


if __name__ == '__main__':
    main()

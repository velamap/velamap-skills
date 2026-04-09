"""
sources.py — 图像获取层

负责从各种来源（剪贴板、本地文件、URL、截屏）获取图片对象。
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlretrieve
from urllib.parse import urlparse
from deps import (
    IS_MACOS, IS_LINUX, IS_WINDOWS, PLATFORM,
    ensure_pillow, get_linux_install_cmd,
)

# 支持的图片格式
SUPPORTED_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.gif'}


def get_image_from_clipboard():
    """从剪贴板获取图片（macOS/Windows 用 Pillow，Linux 用 xclip）"""
    if not ensure_pillow():
        return None, "Pillow 安装失败"

    from PIL import Image

    if IS_MACOS or IS_WINDOWS:
        try:
            from PIL import ImageGrab
            # macOS 上 ImageGrab.grabclipboard() 内部调用 osascript，
            # 会产生键盘布局相关的系统级 stderr 噪音，通过临时重定向抑制。
            if IS_MACOS:
                devnull_fd = os.open(os.devnull, os.O_WRONLY)
                saved_stderr_fd = os.dup(2)
                os.dup2(devnull_fd, 2)
                os.close(devnull_fd)
                try:
                    img = ImageGrab.grabclipboard()
                finally:
                    os.dup2(saved_stderr_fd, 2)
                    os.close(saved_stderr_fd)
            else:
                img = ImageGrab.grabclipboard()
            if img is None:
                return None, (
                    "剪贴板中没有图片\n"
                    "   可以通过以下方式提供图片：\n"
                    "   • 先截图并复制到剪贴板，再重新运行\n"
                    "   • 指定本地图片：python3 ocr_extract.py /path/to/image.png\n"
                    "   • 指定在线图片：python3 ocr_extract.py https://example.com/image.png"
                )
            return img, None
        except Exception as e:
            return None, str(e)

    elif IS_LINUX:
        import io
        for cmd in [
            ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'],
            ['xsel', '--clipboard', '--output'],
        ]:
            try:
                r = subprocess.run(cmd, capture_output=True)
                if r.returncode == 0 and r.stdout:
                    img = Image.open(io.BytesIO(r.stdout))
                    return img, None
            except FileNotFoundError:
                continue
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img:
                return img, None
        except Exception:
            pass
        return None, f"Linux 剪贴板读取失败，请安装 xclip: {get_linux_install_cmd('xclip')}"

    return None, f"不支持的平台: {PLATFORM}"


def get_image_from_file(path: str):
    """从本地图片文件加载"""
    p = Path(path)
    if not p.exists():
        return None, f"文件不存在: {path}"
    if p.suffix.lower() not in SUPPORTED_IMAGE_EXTS:
        return None, (
            f"不支持的图片格式: {p.suffix}\n"
            f"支持的格式: {', '.join(sorted(SUPPORTED_IMAGE_EXTS))}"
        )
    if not ensure_pillow():
        return None, "Pillow 安装失败"
    from PIL import Image
    try:
        img = Image.open(path)
        img.load()  # 强制解码，提前发现损坏文件
        return img, None
    except Exception as e:
        return None, f"图片读取失败: {e}"


def get_image_from_url(url: str):
    """从 URL 下载图片，返回 (image, error)"""
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return None, f"不支持的 URL 协议: {parsed.scheme}（仅支持 http/https）"

    suffix = Path(parsed.path).suffix or '.png'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        print(f"   Downloading from URL...", end=' ', flush=True)
        urlretrieve(url, tmp_path)
        print("✓")
        img, err = get_image_from_file(tmp_path)
        os.unlink(tmp_path)
        return img, err

    except Exception as e:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return None, f"URL 下载失败: {e}"


def get_image_from_screenshot(region: str = None):
    """截取当前屏幕（可指定区域 'x,y,w,h'）"""
    if not ensure_pillow():
        return None, "Pillow 安装失败"
    from PIL import ImageGrab
    try:
        bbox = None
        if region:
            parts = [int(v.strip()) for v in region.split(',')]
            if len(parts) != 4:
                return None, "--region 格式错误，应为 x,y,w,h（如 0,0,1920,1080）"
            x, y, w, h = parts
            bbox = (x, y, x + w, y + h)
        img = ImageGrab.grab(bbox=bbox)
        return img, None
    except Exception as e:
        return None, f"截屏失败: {e}"

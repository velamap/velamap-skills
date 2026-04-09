"""
deps.py — 依赖管理模块

负责自动检测和安装所需的 Python 包及系统依赖。
"""

import sys
import subprocess
import platform

PLATFORM = platform.system()   # 'Darwin' | 'Linux' | 'Windows'
IS_MACOS   = PLATFORM == 'Darwin'
IS_LINUX   = PLATFORM == 'Linux'
IS_WINDOWS = PLATFORM == 'Windows'


def _pip_install(package: str, quiet: bool = True) -> bool:
    """尝试自动安装 pip 包，返回是否成功"""
    print(f"📦 正在安装 {package} ...")
    args = [sys.executable, '-m', 'pip', 'install', package]
    if quiet:
        args.append('-q')
    try:
        subprocess.check_call(args)
        print(f"✅ {package} 安装成功")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {package} 安装失败，请手动运行: pip install {package}")
        return False


def ensure_pillow() -> bool:
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return _pip_install('Pillow')


def ensure_requests() -> bool:
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return _pip_install('requests')


def ensure_ocrmac() -> bool:
    """macOS 专用"""
    try:
        from ocrmac.ocrmac import text_from_image  # noqa: F401
        return True
    except ImportError:
        return _pip_install('ocrmac')


def ensure_pytesseract() -> bool:
    """Linux OCR 引擎"""
    try:
        import pytesseract  # noqa: F401
        return True
    except ImportError:
        return _pip_install('pytesseract')


def check_tesseract_binary() -> bool:
    try:
        r = subprocess.run(['tesseract', '--version'], capture_output=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def get_linux_pkg_manager() -> str:
    """
    检测当前 Linux 发行版使用的包管理器。
    返回值: 'apt' | 'dnf' | 'yum' | 'pacman' | 'zypper' | 'unknown'
    """
    import shutil
    for mgr in ('apt', 'dnf', 'yum', 'pacman', 'zypper'):
        if shutil.which(mgr):
            return mgr
    return 'unknown'


# 各包管理器对应的安装命令模板
_INSTALL_CMDS = {
    # package_key: {pkg_manager: install_command}
    'tesseract': {
        'apt':    'sudo apt install tesseract-ocr tesseract-ocr-chi-sim',
        'dnf':    'sudo dnf install tesseract tesseract-langpack-chi-sim',
        'yum':    'sudo yum install tesseract',
        'pacman': 'sudo pacman -S tesseract tesseract-data-chi_sim',
        'zypper': 'sudo zypper install tesseract-ocr tesseract-ocr-traineddata-chinese_simplified',
    },
    'xclip': {
        'apt':    'sudo apt install xclip',
        'dnf':    'sudo dnf install xclip',
        'yum':    'sudo yum install xclip',
        'pacman': 'sudo pacman -S xclip',
        'zypper': 'sudo zypper install xclip',
    },
}


def get_linux_install_cmd(package: str) -> str:
    """
    根据当前 Linux 发行版返回对应的安装命令。
    package: 'tesseract' | 'xclip'
    """
    mgr = get_linux_pkg_manager()
    cmds = _INSTALL_CMDS.get(package, {})
    if mgr in cmds:
        return cmds[mgr]
    # 未知包管理器，返回通用提示
    return f"请使用系统包管理器安装 {package}（如 apt/dnf/pacman 等）"



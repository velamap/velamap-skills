# ocr-extract

本地 OCR 文字提取工具。在本机运行，无需上传图片，不消耗图片 token。

## 文件结构

```
ocr_extract/
├── SKILL.md              # AI Skill 说明（供 AI 读取，了解何时及如何调用）
├── README.md             # 本文件（开发者参考）
└── scripts/
    ├── ocr_extract.py    # 主入口：参数解析、前置检查、主流程调度
    ├── deps.py           # 依赖管理：自动安装 pip 包、检测系统工具
    ├── sources.py        # 图像获取层：剪贴板 / 本地文件 / URL / 截屏
    ├── engines.py        # OCR 引擎层：按平台调用对应引擎
    └── formatters.py     # 输出格式化：Markdown / 纯文本 / JSON + 语义过滤
```

## 快速使用

```bash
# 在 ocr_extract/ 目录下执行

# 从剪贴板读取截图（最常用）
python3 scripts/ocr_extract.py --source clipboard

# 快捷方式：直接传路径或 URL
python3 scripts/ocr_extract.py /path/to/image.png
python3 scripts/ocr_extract.py https://example.com/screenshot.png

# 截取当前屏幕
python3 scripts/ocr_extract.py --source screenshot
```

## 各平台 OCR 引擎

| 平台 | 引擎 | 安装 |
|------|------|------|
| macOS | `ocrmac`（Apple Vision） | `pip install ocrmac` |
| Windows | `Windows.Media.Ocr`（系统内置） | 无需安装 |
| Linux (Ubuntu/Debian) | `tesseract` + `pytesseract` | `sudo apt install tesseract-ocr tesseract-ocr-chi-sim` |
| Linux (Fedora/RHEL) | `tesseract` + `pytesseract` | `sudo dnf install tesseract tesseract-langpack-chi-sim` |
| Linux (Arch) | `tesseract` + `pytesseract` | `sudo pacman -S tesseract tesseract-data-chi_sim` |
| Linux (openSUSE) | `tesseract` + `pytesseract` | `sudo zypper install tesseract-ocr tesseract-ocr-traineddata-chinese_simplified` |

## 模块说明

### `ocr_extract.py` — 主入口
- 解析命令行参数（支持位置参数快捷方式）
- 前置依赖检查（缺失时立即提示安装命令）
- 根据 `--source` 调度对应的图像获取函数
- 调用 OCR 引擎，格式化输出结果

### `deps.py` — 依赖管理
- `ensure_pillow()` / `ensure_ocrmac()` / `ensure_pytesseract()`：自动 pip 安装
- `check_tesseract_binary()`：检测 tesseract 系统命令是否可用
- `get_linux_pkg_manager()`：检测当前 Linux 发行版的包管理器（apt/dnf/pacman/zypper）
- `get_linux_install_cmd(package)`：根据发行版返回对应的安装命令

### `sources.py` — 图像获取层
- `get_image_from_clipboard()`：读取剪贴板图片（macOS/Windows 用 Pillow，Linux 用 xclip）
- `get_image_from_file(path)`：加载本地图片文件
- `get_image_from_url(url)`：下载网络图片（临时文件，用完即删）
- `get_image_from_screenshot(region)`：截取当前屏幕（可指定区域）

### `engines.py` — OCR 引擎层
- `perform_ocr(image, lang)`：主入口，按平台选择引擎，失败直接报错
- 返回格式：`[{'text': str, 'confidence': float, 'bbox': ...}, ...]`

### `formatters.py` — 输出格式化
- `format_as_markdown(lines)`：尝试还原表格结构
- `format_as_text(lines)`：纯文本，每行一条
- `format_as_json(lines, engine, source)`：含置信度和坐标
- `apply_query_filter(lines, query)`：关键词过滤

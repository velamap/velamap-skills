---
name: ocr-extract
description: 本地 OCR 文字提取工具。在本机运行，无需上传图片，不消耗图片 token。支持四种来源：剪贴板（用户已截图）、本地图片文件、URL 图片、AI 主动截屏；输出 Markdown/纯文本/JSON 供 AI 直接消费。
---

# ocr-extract Skill 说明

## 功能概述

给 AI 换上一双高清眼睛：从任意来源提取图片中的文字内容，输出结构化文本供 AI 直接理解和处理。

**核心价值**：
- 🖼️ 多入口：
  - `clipboard`：读取用户已截图的剪贴板内容（需用户先截图）
  - `file`：本地图片文件
  - `url`：网络图片（自动下载后识别）
  - `screenshot`：AI 主动截取当前屏幕（无需用户操作，可指定区域）
- ⚡ 本地运行：OCR 完全在本机执行，无需上传图片，速度快且**大幅节省 token**（图片不经过 LLM，只传文字结果）
- 🔍 高精度：macOS 使用 Apple Vision Framework，Windows 使用系统内置 OCR，Linux 使用 tesseract
- 📝 结构化输出：Markdown（默认，AI 最易消费）/ 纯文本 / JSON（含坐标和置信度）
- 🔎 语义过滤：`--query` 参数只返回 AI 感兴趣的内容

---

## 平台支持与 OCR 引擎

| 平台 | 引擎 | 说明 |
|------|------|------|
| macOS | `ocrmac` (Apple Vision) | 精度最高，利用 Apple Neural Engine，需安装 `ocrmac` |
| Windows | `Windows.Media.Ocr` (系统内置) | 无需额外安装即可使用 |
| Linux (Ubuntu/Debian) | `tesseract` | `sudo apt install tesseract-ocr tesseract-ocr-chi-sim` |
| Linux (Fedora/RHEL) | `tesseract` | `sudo dnf install tesseract tesseract-langpack-chi-sim` |
| Linux (Arch) | `tesseract` | `sudo pacman -S tesseract tesseract-data-chi_sim` |
| Linux (openSUSE) | `tesseract` | `sudo zypper install tesseract-ocr tesseract-ocr-traineddata-chinese_simplified` |

## 何时调用

### 调用时机
**当 AI 需要"读取"图片中的文字内容时，优先调用本工具**（而非直接将图片发给 LLM）：

- 用户截图后说"帮我看看这张图里写了什么" → 使用 `clipboard`（读取用户已截好的图）
- 需要提取监控截图中的数值（CPU 水位、错误码等） → 使用 `clipboard`
- 需要识别网络图片中的文字 → 使用 `url`
- 需要读取本地图片文件中的文字 → 使用 `file`
- 自动化流程中 AI 需要主动截屏并提取关键信息 → 使用 `screenshot`（无需用户操作）

> **为什么优先用本工具而非直接发图给 LLM？**
> OCR 在本地运行，只将识别出的文字传给 AI，**不消耗图片 token**，速度更快、成本更低。
> 如果图片以文字内容为主（截图、文档、报错信息等），优先调用本工具；
> 如果图片需要视觉理解（图表趋势、UI 布局、照片内容等），则直接发图给 AI。

## 调用方式

```bash
# 标准方式
python3 scripts/ocr_extract.py \
  --source <来源> \
  [--input <路径或URL>] \
  [--format <输出格式>] \
  [--lang <语言>] \
  [--region x,y,w,h] \
  [--query <关键词>]

# 快捷方式：直接传路径或 URL，自动推断来源类型
python3 scripts/ocr_extract.py /path/to/image.png
python3 scripts/ocr_extract.py https://example.com/img.png
```

> **说明**：以上命令需在本 SKILL 目录（即 `SKILL.md` 所在目录）下执行。
> 若在其他目录调用，请将 `scripts/ocr_extract.py` 替换为该文件的绝对路径。

### 参数说明

| 参数 | 可选值 | 默认值 | 说明 |
|------|-------|-------|------|
| `--source` | `clipboard` / `file` / `url` / `screenshot` | `clipboard` | 图片来源 |
| `--input` | 路径或 URL | — | `file`/`url` 时必填 |
| `--format` | `markdown` / `text` / `json` | `markdown` | 输出格式 |
| `--lang` | `auto` / `zh` / `en` | `auto` | 识别语言（auto=中英混合，zh=中文，en=英文） |
| `--region` | `x,y,w,h` | 全屏 | 仅 `screenshot` 有效，指定截图区域 |
| `--query` | 关键词字符串 | — | 语义过滤，只返回包含关键词的行 |

---

## 调用示例

```bash
# 从剪贴板截图提取文字（最常用）
python3 scripts/ocr_extract.py --source clipboard

# 读取本地图片，输出 Markdown
python3 scripts/ocr_extract.py \
  --source file --input /path/to/chart.png

# 从 URL 下载图片并识别英文
python3 scripts/ocr_extract.py \
  --source url --input https://example.com/screenshot.png --lang en

# 截取屏幕左上角区域，只提取包含"错误"的行
python3 scripts/ocr_extract.py \
  --source screenshot --region 0,0,960,540 --query "错误"

# 输出 JSON 格式（含置信度和坐标，适合精确定位）
python3 scripts/ocr_extract.py \
  --source clipboard --format json
```

---

## 调用返回

**OCR 进度信息输出到 stderr（不影响 AI 捕获结果）**：
```
🔍 OCR 提取中 [来源: clipboard] [语言: auto] [格式: markdown]
   Reading clipboard... ✓ (1920x1080)
```

**识别结果输出到 stdout**（AI 直接捕获）：

- `--format markdown`（默认）：
  ```markdown
  识别到的文字第一行
  识别到的文字第二行

  | 列1 | 列2 | 列3 |
  | --- | --- | --- |
  | 数据1 | 数据2 | 数据3 |
  ```

- `--format text`：
  ```
  识别到的文字第一行
  识别到的文字第二行
  ```

- `--format json`：
  ```json
  {
    "engine": "ocrmac",
    "source": "clipboard",
    "total_lines": 5,
    "lines": [
      {"text": "识别到的文字", "confidence": 0.98, "bbox": [...]}
    ]
  }
  ```

**失败情况**：
- `❌ 剪贴板中没有图片`：需要先截图并复制到剪贴板，或改用 `--source file` / `--source url`
- `❌ 不支持的图片格式: .xxx`：检查文件格式
- `⚠️ 未识别到任何文字内容`：图片可能模糊或无文字

---

## 依赖说明

### 自动安装的依赖

| 依赖 | 平台 | 说明 |
|------|------|------|
| `Pillow` | 所有平台 | 图片处理基础库 |
| `ocrmac` | macOS | Apple Vision OCR 封装 |
| `pytesseract` | Linux | Tesseract Python 封装 |

### 需手动安装的依赖

| 依赖 | 平台 | 安装命令 |
|------|------|---------|
| `xclip` | Linux (Ubuntu/Debian) | `sudo apt install xclip` |
| `xclip` | Linux (Fedora/RHEL) | `sudo dnf install xclip` |
| `xclip` | Linux (Arch) | `sudo pacman -S xclip` |
| `xclip` | Linux (openSUSE) | `sudo zypper install xclip` |
| `tesseract-ocr` | Linux (Ubuntu/Debian) | `sudo apt install tesseract-ocr tesseract-ocr-chi-sim` |
| `tesseract-ocr` | Linux (Fedora/RHEL) | `sudo dnf install tesseract tesseract-langpack-chi-sim` |
| `tesseract-ocr` | Linux (Arch) | `sudo pacman -S tesseract tesseract-data-chi_sim` |
| `tesseract-ocr` | Linux (openSUSE) | `sudo zypper install tesseract-ocr tesseract-ocr-traineddata-chinese_simplified` |

> **提示**：运行时工具会自动检测当前发行版并输出对应的安装命令，无需手动查表。

---

## 使用场景示例

### 场景1：读取监控截图中的数值
```
用户：截了一张 CPU 监控图，帮我读出当前水位

AI：调用 ocr_extract.py --source clipboard --query "CPU"
输出：当前 CPU 水位：604.55C，峰值：892.3C

AI：根据识别内容分析当前负载情况...
```

### 场景2：读取网页截图中的错误信息
```
用户：这个报错截图是什么问题

AI：调用 ocr_extract.py --source clipboard --query "error exception"
输出：NullPointerException at UserService.java:42

AI：这是一个空指针异常，原因是...
```

### 场景3：自动截屏提取关键信息（无需用户手动截图）
```
AI：需要读取当前屏幕上的告警信息

AI：调用 ocr_extract.py --source screenshot --query "告警 WARN ERROR"
输出：[当前屏幕上的告警文字]

AI：检测到以下告警：...
```

---

## 脚本执行流程

1. 解析命令行参数，校验必填项
2. 前置依赖检查（Linux 剪贴板工具等）
3. 根据 `--source` 获取图片（剪贴板/文件/URL/截屏）
4. 图片文件来源：验证文件存在性和格式合法性
5. 按平台调用对应 OCR 引擎（macOS=ocrmac，Windows=系统内置，Linux=tesseract）
6. 执行 OCR 识别，获取带置信度的文字行列表
7. 应用 `--query` 语义过滤（如有）
8. 按 `--format` 格式化输出（Markdown 尝试还原表格结构）
9. 识别结果输出到 **stdout**，进度信息输出到 **stderr**

---

## 注意事项

- **结果输出到 stdout**：AI 可直接通过命令替换 `$(...)` 捕获识别结果，进度信息不会干扰
- **Linux 剪贴板**：需要在图形界面环境（X11/Wayland）下运行，纯 SSH 终端无法访问剪贴板
- **macOS 精度最高**：Apple Vision Framework 对中文的识别准确率显著优于 tesseract
- **表格还原**：Markdown 格式会尝试自动识别表格结构，但复杂表格可能需要人工校正

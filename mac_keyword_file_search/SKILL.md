---
name: keyword_file_search
description: "Mac 通过关键字检索文件。本地运行不联网，不记录数据，保护隐私。支持按文件名、文件内容或两者组合进行检索，交互式筛选精准定位目标文件并返回完整路径。"
---

# keyword_file_search — Mac 关键词文件检索

## 概述

基于 macOS 原生 `mdfind`（Spotlight 引擎）+ `fzf` 的文件检索工具：

- **文件名 + 文件内容**双重匹配
- **支持中文**关键词
- 默认使用 `mdfind` 原生权限范围（当前用户可访问的所有文件）
- 可通过 `--dir` 参数**限定搜索目录**，提升速度并保护隐私
- 全程本地运行，不联网，不上传数据，不申请额外系统权限
- 单文件，无框架依赖，可直接运行

## 依赖

| 工具 | 说明 | 安装方式 |
|------|------|----------|
| `mdfind` | macOS Spotlight 搜索引擎，系统内置 | 系统自带，无需配置 |
| `fzf` | 交互式模糊筛选 | `brew install fzf` |

## 用法

```bash
python keyword_file_search.py <keyword> [--dir DIR]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keyword` | 搜索关键词（必填，支持中文） | — |
| `--dir DIR` / `-d DIR` | 限定搜索目录（可选） | 不限定，使用 mdfind 原生范围 |

## 示例

```bash
# 全局搜索（mdfind 原生权限范围）
python keyword_file_search.py 心跳检查系统

# 限定在 ~/Documents 目录搜索（更快、更精准）
python keyword_file_search.py invoice --dir ~/Documents

# 限定在当前目录搜索
python keyword_file_search.py config --dir .

# 限定在自定义工作目录搜索
python keyword_file_search.py readme --dir ~/wypfiles
```

## 工作流程

1. 调用 `mdfind [-onlyin DIR] <keyword>` 检索文件名和内容
2. 将结果传入 `fzf` 进行交互式模糊筛选（支持 `Ctrl+/` 切换预览）
3. 用户选中后，**直接输出文件完整路径**

## 关于 --dir 参数

`mdfind` 默认搜索当前用户可访问的所有文件（包括 iCloud Drive、Documents、Downloads 等）。

如需缩小范围：
- 使用 `--dir ~/Documents` 只搜索文档目录
- 使用 `--dir ~/myproject` 只搜索项目目录
- 使用 `--dir .` 只搜索当前目录

这样既能提升搜索速度，也能避免搜索到不相关的系统文件。

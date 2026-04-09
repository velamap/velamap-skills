"""
formatters.py — 输出格式化层

将 OCR 识别结果格式化为 Markdown / 纯文本 / JSON，
并提供语义关键词过滤功能。
"""

import json


# 格式化函数
def _is_table_row(texts: list) -> bool:
    """简单启发式：一行内有多个短词，可能是表格行"""
    return len(texts) >= 3 and all(len(t) < 30 for t in texts)


def format_as_markdown(lines: list, page_label: str = None) -> str:
    """将 OCR 结果格式化为 Markdown，尝试还原表格结构"""
    if not lines:
        return ""

    texts = [item['text'] for item in lines]
    result_parts = []

    if page_label:
        result_parts.append(f"## {page_label}\n")

    i = 0
    table_buffer = []
    normal_buffer = []

    def flush_normal():
        if normal_buffer:
            result_parts.append('\n'.join(normal_buffer))
            normal_buffer.clear()

    def flush_table():
        if table_buffer:
            header = table_buffer[0]
            result_parts.append('| ' + ' | '.join(header) + ' |')
            result_parts.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
            for row in table_buffer[1:]:
                while len(row) < len(header):
                    row.append('')
                result_parts.append('| ' + ' | '.join(row[:len(header)]) + ' |')
            table_buffer.clear()

    for text in texts:
        parts = text.split()
        if _is_table_row(parts):
            flush_normal()
            table_buffer.append(parts)
        else:
            flush_table()
            normal_buffer.append(text)

    flush_table()
    flush_normal()

    return '\n'.join(result_parts)


def format_as_text(lines: list, page_label: str = None) -> str:
    """纯文本输出"""
    texts = [item['text'] for item in lines]
    result = '\n'.join(texts)
    if page_label:
        result = f"=== {page_label} ===\n{result}"
    return result


def format_as_json(lines: list, engine: str, source: str, page_label: str = None) -> str:
    """JSON 输出，包含置信度和坐标"""
    output = {
        'engine': engine,
        'source': source,
        'page': page_label,
        'total_lines': len(lines),
        'lines': lines,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


# 语义过滤
def apply_query_filter(lines: list, query: str) -> list:
    """
    简单语义过滤：保留包含 query 关键词（或相关行）的内容。
    未来可接入 LLM 做更智能的过滤。
    """
    if not query:
        return lines
    query_lower = query.lower()
    keywords = query_lower.split()
    filtered = [
        item for item in lines
        if any(kw in item['text'].lower() for kw in keywords)
    ]
    return filtered if filtered else lines  # 无匹配时返回全部，避免空结果

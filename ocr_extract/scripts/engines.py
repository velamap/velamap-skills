"""
engines.py — OCR 引擎层

跨平台 OCR 引擎封装：
  macOS  : ocrmac (Apple Vision Framework)
  Windows: Windows.Media.Ocr（系统内置）
  Linux  : pytesseract + tesseract

安装失败直接报错。
"""

import os
import tempfile

from deps import (
    IS_MACOS, IS_LINUX, IS_WINDOWS,
    ensure_ocrmac, ensure_pytesseract,
    check_tesseract_binary, get_linux_install_cmd,
)


def _ocr_with_ocrmac(image, lang: str):
    """macOS: Apple Vision Framework"""
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp_path = tmp.name
    tmp.close()
    image.save(tmp_path, 'PNG')

    try:
        from ocrmac.ocrmac import text_from_image
        lang_map = {
            'zh': ['zh-Hans', 'zh-Hant'],
            'en': ['en-US'],
            'auto': ['zh-Hans', 'zh-Hant', 'en-US'],
        }
        lang_pref = lang_map.get(lang, lang_map['auto'])
        results = text_from_image(tmp_path, language_preference=lang_pref)
        # results: [(text, confidence, bbox), ...]
        lines = [{'text': t, 'confidence': round(c, 3), 'bbox': b} for t, c, b in results]
        return lines, None
    except Exception as e:
        return None, f"ocrmac 识别失败: {e}"
    finally:
        os.unlink(tmp_path)


def _ocr_with_windows_media(image, lang: str):
    """Windows: Windows.Media.Ocr（系统内置，无需安装）"""
    import asyncio

    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    tmp_path = tmp.name
    tmp.close()
    image.save(tmp_path, 'PNG')

    try:
        import winrt.windows.media.ocr as win_ocr
        import winrt.windows.storage as win_storage
        import winrt.windows.graphics.imaging as win_imaging

        async def _do_ocr():
            lang_tag = 'zh-Hans' if lang in ('zh', 'auto') else 'en-US'
            ocr_lang = win_ocr.OcrEngine.try_create_from_language(
                winrt.windows.globalization.Language(lang_tag)
            )
            if ocr_lang is None:
                ocr_lang = win_ocr.OcrEngine.try_create_from_user_profile_languages()
            if ocr_lang is None:
                raise RuntimeError("无法创建 Windows OCR 引擎")

            file = await win_storage.StorageFile.get_file_from_path_async(tmp_path)
            stream = await file.open_async(win_storage.FileAccessMode.READ)
            decoder = await win_imaging.BitmapDecoder.create_async(stream)
            bitmap = await decoder.get_software_bitmap_async()
            result = await ocr_lang.recognize_async(bitmap)
            return result

        result = asyncio.run(_do_ocr())
        lines = [{'text': line.text, 'confidence': 1.0, 'bbox': None}
                 for line in result.lines]
        return lines, None
    except ImportError:
        return None, "winrt 未安装，请运行: pip install winrt"
    except Exception as e:
        return None, f"Windows.Media.Ocr 失败: {e}"
    finally:
        os.unlink(tmp_path)


def _ocr_with_tesseract(image, lang: str):
    """Linux / 通用: pytesseract + tesseract"""
    if not check_tesseract_binary():
        if IS_LINUX:
            hint = get_linux_install_cmd('tesseract')
        elif IS_WINDOWS:
            hint = "https://github.com/UB-Mannheim/tesseract/wiki"
        else:
            hint = "brew install tesseract tesseract-lang"
        return None, f"tesseract 未安装，请先安装: {hint}"

    if not ensure_pytesseract():
        return None, "pytesseract 安装失败，请手动运行: pip install pytesseract"

    try:
        import pytesseract
        lang_map = {'zh': 'chi_sim+chi_tra+eng', 'en': 'eng', 'auto': 'chi_sim+eng'}
        tess_lang = lang_map.get(lang, 'chi_sim+eng')
        data = pytesseract.image_to_data(image, lang=tess_lang,
                                         output_type=pytesseract.Output.DICT)
        lines = []
        n = len(data['text'])
        for i in range(n):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])
            if text and conf > 0:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                lines.append({'text': text, 'confidence': round(conf / 100, 3),
                               'bbox': [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]})
        return lines, None
    except Exception as e:
        return None, f"pytesseract 识别失败: {e}"


def perform_ocr(image, lang: str = 'auto'):
    """
    跨平台 OCR 主入口，按平台选择引擎，失败直接报错。
    返回: (lines, engine_name, error)
      lines: [{'text': str, 'confidence': float, 'bbox': ...}, ...]
    """
    if IS_MACOS:
        if not ensure_ocrmac():
            return None, None, "ocrmac 安装失败，请手动运行: pip install ocrmac"
        lines, err = _ocr_with_ocrmac(image, lang)
        if lines is not None:
            return lines, 'ocrmac', None
        return None, None, err

    elif IS_WINDOWS:
        lines, err = _ocr_with_windows_media(image, lang)
        if lines is not None:
            return lines, 'windows_media_ocr', None
        return None, None, err

    else:  # Linux
        lines, err = _ocr_with_tesseract(image, lang)
        if lines is not None:
            return lines, 'tesseract', None
        return None, None, err

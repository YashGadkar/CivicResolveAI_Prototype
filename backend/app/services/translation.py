from __future__ import annotations

import httpx

from ..config import get_settings

settings = get_settings()


class TranslationError(RuntimeError):
    pass


LANGUAGE_OPTIONS = [
    {"code": "en", "name": "English"},
    {"code": "hi", "name": "Hindi"},
    {"code": "mr", "name": "Marathi"},
    {"code": "bn", "name": "Bengali"},
    {"code": "gu", "name": "Gujarati"},
    {"code": "pa", "name": "Punjabi"},
    {"code": "ta", "name": "Tamil"},
    {"code": "te", "name": "Telugu"},
    {"code": "kn", "name": "Kannada"},
    {"code": "ml", "name": "Malayalam"},
    {"code": "or", "name": "Odia"},
    {"code": "ur", "name": "Urdu"},
    {"code": "as", "name": "Assamese"},
    {"code": "ne", "name": "Nepali"},
    {"code": "sa", "name": "Sanskrit"},
    {"code": "ar", "name": "Arabic"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "it", "name": "Italian"},
    {"code": "ru", "name": "Russian"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh-CN", "name": "Chinese (Simplified)"},
    {"code": "th", "name": "Thai"},
    {"code": "id", "name": "Indonesian"},
    {"code": "tr", "name": "Turkish"},
    {"code": "fa", "name": "Persian"},
]

_CODE_TO_NAME = {item["code"].casefold(): item["name"] for item in LANGUAGE_OPTIONS}
_NAME_TO_CODE = {item["name"].casefold(): item["code"] for item in LANGUAGE_OPTIONS}


def available_languages() -> list[dict[str, str]]:
    return LANGUAGE_OPTIONS.copy()


def _language_code(value: str | None, fallback: str = "auto") -> str:
    if not value:
        return fallback
    normalized = value.strip().casefold()
    if normalized in _NAME_TO_CODE:
        return _NAME_TO_CODE[normalized]
    for code in _CODE_TO_NAME:
        if normalized == code:
            return next(item["code"] for item in LANGUAGE_OPTIONS if item["code"].casefold() == code)
    return fallback


def language_name(code: str) -> str:
    return _CODE_TO_NAME.get(code.casefold(), code)


def translate_text(text: str, target_language: str, source_language: str | None = None) -> dict[str, str]:
    original = text.strip()
    if not original:
        raise TranslationError("The citizen statement is empty and cannot be translated.")

    target_code = _language_code(target_language, fallback="")
    if not target_code:
        raise TranslationError("That translation language is not supported by the staff workspace.")

    source_code = _language_code(source_language, fallback="auto")
    if source_code != "auto" and source_code.casefold() == target_code.casefold():
        return {
            "original_text": original,
            "translated_text": original,
            "source_language": source_code,
            "target_language": target_code,
            "target_language_name": language_name(target_code),
            "provider": "Original statement",
        }

    try:
        with httpx.Client(timeout=settings.translation_timeout_seconds) as client:
            response = client.get(
                settings.translation_base_url,
                params={
                    "client": "gtx",
                    "sl": source_code,
                    "tl": target_code,
                    "dt": "t",
                    "q": original,
                },
                headers={"User-Agent": "CivicResolveAI/0.7 staff-translation"},
            )
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise TranslationError("Translation service is temporarily unavailable. The original citizen statement is unchanged.") from exc

    try:
        translated = "".join(
            segment[0]
            for segment in payload[0]
            if isinstance(segment, list) and segment and isinstance(segment[0], str)
        ).strip()
        detected = payload[2] if len(payload) > 2 and isinstance(payload[2], str) else source_code
    except (IndexError, TypeError) as exc:
        raise TranslationError("Translation service returned an unreadable response. Please retry.") from exc

    if not translated:
        raise TranslationError("Translation service returned no translated text. Please retry.")

    return {
        "original_text": original,
        "translated_text": translated,
        "source_language": detected or source_code,
        "target_language": target_code,
        "target_language_name": language_name(target_code),
        "provider": "Machine translation gateway",
    }

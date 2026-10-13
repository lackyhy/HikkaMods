# meta developer: @lackyhyyy666
# requires: pycountry

import gettext

import pycountry
from .. import loader, utils

# Словарь русских названий стран и их альтернативных названий/синонимов к кодам ISO Alpha-2
COUNTRY_ALIASES = {
    # Россия / РФ
    "россия": "RU", "рф": "RU", "ru": "RU", "rus": "RU", "russia": "RU", "ру": "RU", "рус": "RU",
    # Украина
    "украина": "UA", "ua": "UA", "ukr": "UA", "ukraine": "UA", "укр": "UA",
    # Беларусь
    "беларусь": "BY", "белоруссия": "BY", "by": "BY", "blr": "BY", "belarus": "BY", "рб": "BY", "бел": "BY",
    # Казахстан
    "казахстан": "KZ", "kz": "KZ", "kaz": "KZ", "kazakhstan": "KZ", "каз": "KZ",
    # США / Америка
    "сша": "US", "америка": "US", "us": "US", "usa": "US", "united states": "US",
    # Германия
    "германия": "DE", "de": "DE", "deu": "DE", "germany": "DE", "нем": "DE",
    # Франция
    "франция": "FR", "fr": "FR", "fra": "FR", "france": "FR",
    # Великобритания / Англия
    "великобритания": "GB", "англия": "GB", "gb": "GB", "uk": "GB", "england": "GB", "англ": "GB", "британия": "GB",
    # Испания
    "испания": "ES", "es": "ES", "esp": "ES", "spain": "ES", "исп": "ES",
    # Италия
    "италия": "IT", "it": "IT", "ita": "IT", "italy": "IT", "ит": "IT",
    # Китай
    "китай": "CN", "cn": "CN", "chn": "CN", "china": "CN", "кнр": "CN",
    # Япония
    "япония": "JP", "jp": "JP", "jpn": "JP", "japan": "JP", "яп": "JP",
    # Турция
    "турция": "TR", "tr": "TR", "tur": "TR", "turkey": "TR", "тур": "TR",
    # Бразилия
    "бразилия": "BR", "br": "BR", "bra": "BR", "brazil": "BR",
    # Канада
    "канада": "CA", "ca": "CA", "can": "CA", "canada": "CA",
    # Польша
    "польша": "PL", "pl": "PL", "pol": "PL", "poland": "PL", "пол": "PL",
    # Египет
    "египет": "EG", "eg": "EG", "egy": "EG", "egypt": "EG",
    # Грузия
    "грузия": "GE", "ge": "GE", "geo": "GE", "georgia": "GE",
    # Армения
    "армения": "AM", "am": "AM", "arm": "AM", "armenia": "AM", "арм": "AM",
    # Азербайджан
    "азербайджан": "AZ", "az": "AZ", "aze": "AZ", "azerbaijan": "AZ", "аз": "AZ",
    # Узбекистан
    "узбекистан": "UZ", "uz": "UZ", "uzb": "UZ", "uzbekistan": "UZ", "узб": "UZ",
    # Кыргызстан / Киргизия
    "кыргызстан": "KG", "киргизия": "KG", "kg": "KG", "kgz": "KG", "kyrgyzstan": "KG",
    # Молдавия / Молдова
    "молдова": "MD", "молдавия": "MD", "md": "MD", "mda": "MD", "moldova": "MD",
    # ОАЭ
    "оаэ": "AE", "эмираты": "AE", "ae": "AE", "uae": "AE",
    # Финляндия
    "финляндия": "FI", "fi": "FI", "fin": "FI", "finland": "FI", "фин": "FI",
    # Швеция
    "швеция": "SE", "se": "SE", "swe": "SE", "sweden": "SE", "швед": "SE",
    # Норвегия
    "норвегия": "NO", "no": "NO", "nor": "NO", "norway": "NO",
    # Нидерланды / Голландия
    "нидерланды": "NL", "голландия": "NL", "nl": "NL", "nld": "NL", "netherlands": "NL",
    # Португалия
    "португалия": "PT", "pt": "PT", "prt": "PT", "portugal": "PT",
    # Греция
    "греция": "GR", "gr": "GR", "grc": "GR", "greece": "GR",
    # Аргентина
    "аргентина": "AR", "ar": "AR", "arg": "AR", "argentina": "AR",
    # Корея (Южная)
    "корея": "KR", "южная корея": "KR", "kr": "KR", "kor": "KR", "korea": "KR",
    # Израиль
    "израиль": "IL", "il": "IL", "isr": "IL", "israel": "IL",
    # Сербия
    "сербия": "RS", "rs": "RS", "srb": "RS", "serbia": "RS",
    # Чехия
    "чехия": "CZ", "cz": "CZ", "cze": "CZ", "czechia": "CZ",
    # Таджикистан
    "таджикистан": "TJ", "tj": "TJ", "tjk": "TJ", "tajikistan": "TJ",
    # Палестина
    "палестина": "PS", "ps": "PS", "pse": "PS", "palestine": "PS",
}

def country_code_to_flag(code: str) -> str:
    """Преобразует ISO 3166-1 alpha-2 код страны в символ флага эмодзи."""
    code = code.upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)


def _load_ru_translation():
    try:
        return gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["ru"])
    except Exception:
        return None


_RU = _load_ru_translation()


def ru_name(country) -> str:
    """Русское название страны (через переводы pycountry), иначе английское"""
    name = getattr(country, "common_name", None) or country.name
    if _RU:
        return _RU.gettext(name)
    return name


def _build_ru_index() -> dict:
    """Индекс русских названий всех стран → alpha_2 (раньше по-русски находились только ~40 стран)"""
    index = {}
    if not _RU:
        return index
    for country in pycountry.countries:
        for attr in ("name", "common_name", "official_name"):
            value = getattr(country, attr, None)
            if value:
                index.setdefault(_RU.gettext(value).lower().replace("ё", "е"), country.alpha_2)
    return index


RU_INDEX = _build_ru_index()


def find_country_code(query: str):
    query = query.strip().lower()
    if not query:
        return None

    if query in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[query]

    normalized = query.replace("ё", "е")
    if normalized in RU_INDEX:
        return RU_INDEX[normalized]

    if query.isalpha() and len(query) in (2, 3):
        key = "alpha_2" if len(query) == 2 else "alpha_3"
        country = pycountry.countries.get(**{key: query.upper()})
        if country:
            return country.alpha_2

    # Частичное совпадение по русскому названию ("корея" → "Южная Корея")
    if len(normalized) >= 4:
        for name, code in RU_INDEX.items():
            if normalized in name:
                return code

    try:
        matches = pycountry.countries.search_fuzzy(query)
        if matches:
            return getattr(matches[0], "alpha_2", None)
    except Exception:
        pass
    return None


@loader.tds
class FlagsMod(loader.Module):
    """Модуль для получения флагов стран в формате эмодзи."""

    strings = {
        "name": "Flags",
        "no_arg": "⚠️ <b>Укажите страну или код (например, <code>.flag ru</code>, <code>.flag германия</code> или <code>.flag ru, ua, kz</code>)</b>",
        "not_found": "❌ <b>Страна не найдена:</b> <code>{}</code>",
        "flag_out": "{} <b>{}</b> ({}) — <code>{}</code>",
    }

    @loader.command(
        ru_doc="[страна/код, ...] - Показывает флаг страны (можно несколько через запятую) для удобного копирования",
        en_doc="[country/code, ...] - Shows the flag of the specified country (comma-separated list supported)",
    )
    async def flagcmd(self, message):
        """[country/code, ...] - Shows the flag of the specified country"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings("no_arg"))
            return

        queries = [q.strip() for q in args.split(",") if q.strip()] if "," in args else [args]
        lines = []
        for query in queries[:30]:
            code = find_country_code(query)
            flag_emoji = country_code_to_flag(code) if code else ""
            if not flag_emoji:
                lines.append(self.strings("not_found").format(utils.escape_html(query)))
                continue

            country = pycountry.countries.get(alpha_2=code)
            name = ru_name(country) if country else code
            lines.append(self.strings("flag_out").format(flag_emoji, utils.escape_html(name), code, flag_emoji))

        await utils.answer(message, "\n".join(lines))

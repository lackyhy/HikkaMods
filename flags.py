# meta developer: @lackyhyyy666

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


@loader.tds
class FlagsMod(loader.Module):
    """Модуль для получения флагов стран в формате эмодзи."""

    strings = {
        "name": "Flags",
        "no_arg": "<emoji document_id=5210952531676504517>⚠️</emoji> <b>Укажите страну или код (например, <code>.flag ru</code> или <code>.flag россия</code>)</b>",
        "not_found": "<emoji document_id=5210952531676504517>❌</emoji> <b>Страна не найдена:</b> <code>{}</code>",
        "flag_out": "<b>Страна:</b> {} ({})\n<b>Флаг:</b> <code>{}</code>",
    }

    strings_ru = {
        "no_arg": "<emoji document_id=5210952531676504517>⚠️</emoji> <b>Укажите страну или код (например, <code>.flag ru</code> или <code>.flag россия</code>)</b>",
        "not_found": "<emoji document_id=5210952531676504517>❌</emoji> <b>Страна не найдена:</b> <code>{}</code>",
        "flag_out": "<b>Страна:</b> {} ({})\n<b>Флаг:</b> <code>{}</code>",
    }

    @loader.command(
        ru_doc="[страна/код] - Показывает флаг указанной страны (эмодзи в моноширинном тексте для удобного копирования)",
        en_doc="[country/code] - Shows the flag of the specified country (emoji formatted for easy copying)",
    )
    async def flagcmd(self, message):
        """[country/code] - Shows the flag of the specified country"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings("no_arg"))
            return

        query = args.lower()
        code = None
        country_name = None

        # 1. Проверяем точные совпадения в словаре русских названий/алиасов
        if query in COUNTRY_ALIASES:
            code = COUNTRY_ALIASES[query]

        # 2. Если введен 2-буквенный или 3-буквенный ISO код прямо
        if not code and query.isalpha():
            if len(query) == 2:
                country = pycountry.countries.get(alpha_2=query.upper())
                if country:
                    code = country.alpha_2
                    country_name = getattr(country, "name", code)
            elif len(query) == 3:
                country = pycountry.countries.get(alpha_3=query.upper())
                if country:
                    code = country.alpha_2
                    country_name = getattr(country, "name", code)

        # 3. Пробуем нечеткий поиск через pycountry (для названий на английском)
        if not code:
            try:
                matches = pycountry.countries.search_fuzzy(query)
                if matches:
                    country = matches[0]
                    code = getattr(country, "alpha_2", None)
                    country_name = getattr(country, "name", code)
            except Exception:
                pass

        if not code:
            await utils.answer(message, self.strings("not_found").format(args))
            return

        flag_emoji = country_code_to_flag(code)
        if not flag_emoji:
            await utils.answer(message, self.strings("not_found").format(args))
            return

        if not country_name:
            country = pycountry.countries.get(alpha_2=code)
            country_name = getattr(country, "name", code) if country else code

        await utils.answer(
            message,
            self.strings("flag_out").format(country_name, code, flag_emoji)
        )


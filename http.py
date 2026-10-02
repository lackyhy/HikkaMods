# meta developer: @lackyhyyy666

from .. import loader, utils


@loader.tds
class HTTPStatusMod(loader.Module):
    """Справочник HTTP-кодов статусов"""

    strings = {
        "name": "HttpStatusCodes",
        "not_found": "❌ <b>Код <code>{}</code> не найден в справочнике.</b>",
        "usage": "❌ <b>Укажите HTTP-код, например:</b> <code>.httpsc 404</code>",
    }

    _codes = {
        # 1xx — Информационные
        100: ("ℹ", "Continue", "Запрос принят, продолжай"),
        101: ("ℹ", "Switching Protocols", "Изменение протокола; подчиняйся Upgrade хедеру"),
        102: ("ℹ", "Processing", "Запрос принят, но обработка ещё не завершена"),
        103: ("ℹ", "Early Hints", "Ранние подсказки для предзагрузки ресурсов"),

        # 2xx — Успешные
        200: ("✅", "OK", "Запрос успешный, контент отображён"),
        201: ("✅", "Created", "Ресурс создан, URL прилагается"),
        202: ("✅", "Accepted", "Запрос принят и обрабатывается оффлайн"),
        203: ("✅", "Non-Authoritative Information", "Промежуточный прокси/кэш модифицировал заголовки ответа"),
        204: ("✅", "No Content", "Запрос успешный, нет контента"),
        205: ("✅", "Reset Content", "Очистить форму для продолжения"),
        206: ("✅", "Partial Content", "Частичный контент прилагается"),
        207: ("✅", "Multi-Status", "Множественный статус (WebDAV)"),
        208: ("✅", "Already Reported", "Элемент уже был перечислен (WebDAV)"),
        226: ("✅", "IM Used", "Сервер выполнил GET-запрос и ответ — результат манипуляций"),

        # 3xx — Перенаправления
        300: ("↩", "Multiple Choices", "У объекта есть несколько источников"),
        301: ("↩", "Moved Permanently", "Адрес изменён навсегда"),
        302: ("↩", "Found", "Адрес изменён временно"),
        303: ("↩", "See Other", "Адрес и/или объект изменён"),
        304: ("↩", "Not Modified", "Контент не изменился с предыдущего запроса"),
        305: ("↩", "Use Proxy", "Повторите запрос через указанный в Location прокси (устаревший)"),
        306: ("↩", "Switch Proxy", "Зарезервирован; ранее — переключение прокси (не используется)"),
        307: ("↩", "Temporary Redirect", "Временное перенаправление"),
        308: ("↩", "Permanent Redirect", "Постоянное перенаправление с сохранением метода"),

        # 4xx — Ошибки клиента
        400: ("🚫", "Bad Request", "Ошибка формирования запроса со стороны клиента"),
        401: ("🚫", "Unauthorized", "Не авторизован"),
        402: ("🚫", "Payment Required", "Не оплачено"),
        403: ("🚫", "Forbidden", "Доступ запрещён — бан / нехватка прав"),
        404: ("🚫", "Not Found", "Не найдено"),
        405: ("🚫", "Method Not Allowed", "Метод запрещён"),
        406: ("🚫", "Not Acceptable", "Метод недоступен"),
        407: ("🚫", "Proxy Authentication Required", "Не хватает авторизации прокси"),
        408: ("🚫", "Request Timeout", "Время ожидания истекло"),
        409: ("🚫", "Conflict", "Конфликт запросов"),
        410: ("🚫", "Gone", "Адрес не существует и был перемещён"),
        411: ("🚫", "Length Required", "Требуется указание длины контента запроса"),
        412: ("🚫", "Precondition Failed", "Предусловие в хедерах неверно"),
        413: ("🚫", "Payload Too Large", "Запрос слишком большой"),
        414: ("🚫", "URI Too Long", "Ссылка слишком большая"),
        415: ("🚫", "Unsupported Media Type", "Неподдерживаемый формат контента"),
        416: ("🚫", "Range Not Satisfiable", "Не входит в разрешённый диапазон"),
        417: ("🚫", "Expectation Failed", "Ожидания не выполняются"),
        418: ("🚫", "I'm a Teapot", "Я — чайник (пасхалка RFC 2324)"),
        421: ("🚫", "Misdirected Request", "Запрос направлен не на тот сервер"),
        422: ("🚫", "Unprocessable Entity", "Синтаксис верный, но семантическая ошибка (WebDAV)"),
        423: ("🚫", "Locked", "Ресурс заблокирован (WebDAV)"),
        424: ("🚫", "Failed Dependency", "Зависимость от другого запроса не выполнена (WebDAV)"),
        425: ("🚫", "Too Early", "Сервер не готов обрабатывать запрос — риск повтора"),
        426: ("🚫", "Upgrade Required", "Необходимо обновить протокол"),
        428: ("🚫", "Precondition Required", "Требуется предусловие в запросе"),
        429: ("🚫", "Too Many Requests", "Слишком много запросов — рейт-лимит"),
        431: ("🚫", "Request Header Fields Too Large", "Заголовки запроса слишком большие"),
        444: ("🚫", "Connection Closed Without Response", "Сервер закрыл соединение без ответа (Nginx)"),
        451: ("🚫", "Unavailable For Legal Reasons", "Недоступно по юридическим причинам"),
        497: ("🚫", "HTTP Request Sent to HTTPS Port", "HTTP-запрос отправлен на HTTPS-порт (Nginx)"),
        499: ("🚫", "Client Closed Request", "Клиент оборвал соединение до ответа сервера (Nginx)"),

        # 5xx — Ошибки сервера
        500: ("💢", "Internal Server Error", "Ошибка сервера"),
        501: ("💢", "Not Implemented", "Операция не поддерживается"),
        502: ("💢", "Bad Gateway", "Прокси / шлюз недоступен"),
        503: ("💢", "Service Unavailable", "Перегрузка сервера"),
        504: ("💢", "Gateway Timeout", "Таймаут прокси / шлюза"),
        505: ("💢", "HTTP Version Not Supported", "Версия HTTP не соответствует требованиям"),
        506: ("💢", "Variant Also Negotiates", "Ошибка конфигурации контента на сервере"),
        507: ("💢", "Insufficient Storage", "Недостаточно места на сервере (WebDAV)"),
        508: ("💢", "Loop Detected", "Обнаружена бесконечная петля (WebDAV)"),
        510: ("💢", "Not Extended", "Требуется расширение запроса"),
        511: ("💢", "Network Authentication Required", "Требуется сетевая аутентификация"),
        520: ("💢", "Web Server Returned an Unknown Error", "Сервер вернул непредвиденный или пустой ответ (Cloudflare)"),
        521: ("💢", "Web Server Is Down", "Исходный веб-сервер отключён или сбросил соединение (Cloudflare)"),
        522: ("💢", "Connection Timed Out", "Таймаут TCP-соединения между Cloudflare и сервером"),
        524: ("💢", "A Timeout Occurred", "Соединение установлено, но сервер слишком долго генерирует ответ (Cloudflare)"),
        525: ("💢", "SSL Handshake Failed", "Сбой рукопожатия SSL между Cloudflare и сервером"),
    }

    _categories = {
        "1xx": "ℹ Информационные",
        "2xx": "✅ Успешные",
        "3xx": "↩ Перенаправления",
        "4xx": "🚫 Ошибки клиента",
        "5xx": "💢 Ошибки сервера",
    }

    def _format_code(self, code: int) -> str:
        emoji, name, desc = self._codes[code]
        return f"{emoji} <code>{code}</code> <b>{name}</b>\n     └ {desc}"

    async def httpsccmd(self, message):
        """<код> — Показать описание HTTP-кода"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings("usage"))
            return

        if not args.isdigit():
            await utils.answer(message, self.strings("usage"))
            return

        code = int(args)
        if code not in self._codes:
            await utils.answer(message, self.strings("not_found").format(code))
            return

        await utils.answer(message, self._format_code(code))

    async def httpscscmd(self, message):
        """Показать полный список HTTP-кодов"""
        sections = []

        for prefix, title in self._categories.items():
            digit = int(prefix[0])
            codes = sorted(c for c in self._codes if c // 100 == digit)
            if not codes:
                continue

            lines = [f"<b>━━━ {title} ━━━</b>"]
            for code in codes:
                emoji, name, desc = self._codes[code]
                lines.append(f"{emoji} <code>{code}</code> <b>{name}</b> — {desc}")
            sections.append("\n".join(lines))

        header = ""
        await utils.answer(message, header + "\n\n".join(sections))

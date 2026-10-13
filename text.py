# meta developer: @lackyhyyy666
# requires: beautifulsoup4

import re
import asyncio
from collections import OrderedDict
import unicodedata
import urllib.parse
import aiohttp
from bs4 import BeautifulSoup
from .. import loader, utils


def normalize_text(text: str) -> str:
    """Очищает текст от всех видов странных Unicode-шрифтов, невидимых символов и комбинируемых знаков."""
    if not text:
        return ""
    
    # 1. Применяем стандартную нормализацию Unicode NFKC
    text = unicodedata.normalize("NFKC", text)

    # 2. Удаляем невидимые символы (Zero-width space, joiners, soft hyphens, BOM)
    text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]', '', text)

    # 3. Удаляем комбинируемые диакритические знаки
    text = "".join(c for c in text if not unicodedata.combining(c))

    # 4. Замена нескольких пустых строк на двойной перевод строки
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def lat_to_cyr(text: str) -> str:
    """Декодирует транслитерированный латинский текст русскоязычных песен в кириллицу."""
    if not text:
        return ""
    res = text.lower()

    # Множественная замена буквосочетаний (по убыванию длины)
    multi_map = [
        ("shch", "щ"), ("sch", "щ"), ("ch", "ч"), ("sh", "ш"), ("zh", "ж"),
        ("kh", "х"), ("ts", "ц"), ("ya", "я"), ("yu", "ю"), ("yo", "ё"),
        ("ye", "е"), ("ja", "я"), ("ju", "ю"), ("jo", "ё"), ("je", "е"),
        ("ck", "к"), ("ph", "ф"), ("qu", "кв")
    ]
    for lat, cyr in multi_map:
        res = res.replace(lat, cyr)

    single_map = {
        "a": "а", "b": "б", "c": "к", "v": "в", "g": "г", "d": "д", "e": "е", "z": "з",
        "i": "и", "j": "й", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
        "p": "п", "r": "р", "s": "с", "t": "т", "u": "у", "f": "ф", "h": "х",
        "y": "ы", "w": "в", "x": "кс", "q": "к"
    }
    chars = [single_map.get(c, c) for c in res]
    return "".join(chars).strip()


def prepare_search_queries(raw_query: str) -> list:
    """Генерирует поисковые варианты названия трека, очищая мусор, ремиксы, цифровые ID и транслит."""
    queries = []

    text = normalize_text(raw_query)

    # 1. Удаляем расширения аудиофайлов
    text = re.sub(r'\.(mp3|flac|wav|m4a|ogg|opus|aac)$', '', text, flags=re.IGNORECASE).strip()

    # 2. Удаляем цифровые ID треков VK / Telegram (например _456616245 или -456616245)
    text = re.sub(r'(_|-)\d{5,}', '', text).strip()

    # 3. Очищаем мусор вроде // speed up, (slowed + reverb), [prod. by ...], (remix)
    clean = re.sub(r'(//|\|).*$', '', text).strip()
    clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', clean).strip()
    clean = re.sub(r'\b(speed\s*up|slowed(\s*\+\s*reverb)?|reverb|remix|prod\.?|prod\s+by|official\s+audio|lyric\s+video|nightcore)\b', '', clean, flags=re.IGNORECASE).strip()

    # Заменяем тире и подчеркивания на единые символы
    clean_dash = re.sub(r'[—–]', '-', clean)
    clean_spaces = re.sub(r'[_—–-]', ' ', clean)
    clean_spaces = re.sub(r'\s+', ' ', clean_spaces).strip()

    if clean:
        queries.append(clean)
    if clean_spaces and clean_spaces != clean:
        queries.append(clean_spaces)

    # 4. Автоматическая расшифровка транслита (например "avtostopom-po-faze-sna" -> "автостопом по фазе сна")
    if clean_spaces and re.search(r'[a-zA-Z]', clean_spaces):
        cyr = lat_to_cyr(clean_spaces)
        if cyr and cyr != clean_spaces.lower():
            queries.append(cyr)

    # 5. Разбор пар Исполнитель - Трек (по дефису)
    if "-" in clean_dash:
        parts = [p.strip() for p in clean_dash.split("-") if p.strip()]
        if len(parts) >= 2:
            left = parts[0]
            right = parts[1]

            first_artist = re.split(r'[,&/\\]|\b(feat\.?|ft\.?)\b', right, flags=re.IGNORECASE)[0].strip()
            if first_artist:
                queries.append(f"{first_artist} - {left}")
                queries.append(f"{first_artist} {left}")
                queries.append(f"{left} {first_artist}")

            left_artist = re.split(r'[,&/\\]|\b(feat\.?|ft\.?)\b', left, flags=re.IGNORECASE)[0].strip()
            if left_artist:
                queries.append(f"{left_artist} {right}")

                # Транслит каждой из частей
                cyr_left = lat_to_cyr(left_artist)
                cyr_right = lat_to_cyr(right)
                if cyr_left or cyr_right:
                    queries.append(f"{cyr_left} {cyr_right}".strip())

    # 6. Усеченный вариант (до 5 слов) и его кириллизация
    words = clean_spaces.split()
    if len(words) > 5:
        short_q = " ".join(words[:5])
        queries.append(short_q)
        cyr_short = lat_to_cyr(short_q)
        if cyr_short:
            queries.append(cyr_short)

    seen = set()
    result = []
    for q in queries:
        qn = q.lower().strip()
        if qn and qn not in seen:
            seen.add(qn)
            result.append(q)

    return result


def match_score(query: str, candidate: str) -> float:
    """Доля слов запроса, найденных в «исполнитель + название» кандидата"""
    q_words = set(re.findall(r"\w+", query.lower()))
    c_words = set(re.findall(r"\w+", candidate.lower()))
    if not q_words:
        return 0.0
    return len(q_words & c_words) / len(q_words)


@loader.tds
class TrackLyricsMod(loader.Module):
    """Модуль для поиска и нормализации текстов песен с различных платформ"""

    strings = {
        "name": "TrackLyrics",
        "no_args": "⚠️ <b>Не удалось определить трек!</b>\nНапишите <code>.ttx</code> в комментариях под музыкой в канале, ответьте на аудиозапись или укажите название трека!\nПример: <code>.ttx Исполнитель - Трек</code>",
        "searching": "🔍 <b>Ищу текст песни...</b>",
        "not_found": "❌ <b>Текст для трека «{}» не найден.</b>",
        "lyrics_template": "🎙 <b>Текст песни:</b> <code>{}</code>\n\n{}",
        "error": "❌ <b>Ошибка при поиске:</b>\n<code>{}</code>",
    }

    strings_ru = {
        "no_args": "⚠️ <b>Не удалось определить трек!</b>\nНапишите <code>.ttx</code> в комментариях под музыкой в канале, ответьте на аудиозапись или укажите название трека!\nПример: <code>.ttx Исполнитель - Трек</code>",
        "searching": "🔍 <b>Ищу текст песни...</b>",
        "not_found": "❌ <b>Текст для трека «{}» не найден.</b>",
        "lyrics_template": "🎙 <b>Текст песни:</b> <code>{}</code>\n\n{}",
        "error": "❌ <b>Ошибка при поиске:</b>\n<code>{}</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allowed_users",
                [],
                "ID пользователей, которым разрешено вызывать .ttx (владельцу можно всегда). * — всем",
                validator=loader.validators.Series(loader.validators.String()),
            ),
        )
        self._processed_ids = OrderedDict()

    def _is_allowed(self, message) -> bool:
        if getattr(message, "out", False):
            return True
        sender_id = getattr(message, "sender_id", None)
        if not sender_id:
            return False
        if sender_id == getattr(self, "tg_id", None):
            return True
        allowed = {str(x).strip().lstrip("@").lower() for x in (self.config["allowed_users"] or [])}
        if "*" in allowed or str(sender_id) in allowed:
            return True
        username = getattr(getattr(message, "sender", None), "username", None)
        return bool(username) and username.lower() in allowed

    def _extract_track_from_single_msg(self, target_msg) -> str:
        """Извлекает название РОВНО ОДНОГО трека из конкретного сообщения."""
        if not target_msg:
            return ""

        # 1. Проверяем ID3-теги исполнителя и названия через message.file
        try:
            f = getattr(target_msg, "file", None)
            if f:
                performer = getattr(f, "performer", "") or ""
                title = getattr(f, "title", "") or ""
                if performer or title:
                    q = f"{performer} - {title}".strip(" -")
                    if q:
                        return q

                name = getattr(f, "name", "") or ""
                if name:
                    clean_name = re.sub(r'\.(mp3|flac|wav|m4a|ogg|opus|aac)$', '', name, flags=re.IGNORECASE).strip()
                    if clean_name:
                        return clean_name
        except Exception:
            pass

        # 2. Прямая проверка атрибутов документа в media
        if getattr(target_msg, "media", None):
            document = getattr(target_msg.media, "document", None)
            if document and hasattr(document, "attributes"):
                for attr in document.attributes:
                    performer = getattr(attr, "performer", "") or ""
                    title = getattr(attr, "title", "") or ""
                    if performer or title:
                        q = f"{performer} - {title}".strip(" -")
                        if q:
                            return q

                    file_name = getattr(attr, "file_name", "") or ""
                    if file_name:
                        clean_fn = re.sub(r'\.(mp3|flac|wav|m4a|ogg|opus|aac)$', '', file_name, flags=re.IGNORECASE).strip()
                        if clean_fn:
                            return clean_fn

        # 3. Если это не аудиозапись с тегами, проверяем текст поста
        text_content = getattr(target_msg, "raw_text", None) or getattr(target_msg, "text", "") or ""
        if text_content:
            lines = [l.strip() for l in text_content.split("\n") if l.strip()]
            for l in lines:
                if not l.startswith("http://") and not l.startswith("https://") and not l.startswith("."):
                    return l

        return ""

    def _extract_all_queries_from_msg(self, target_msg) -> list:
        """Извлекает название трека из сообщения (ровно 1 трек на 1 аудиосообщение)."""
        q = self._extract_track_from_single_msg(target_msg)
        return [q] if q else []

    def _msg_key(self, message):
        # ID сообщения уникален только внутри чата — ключ должен включать chat_id
        return (getattr(message, "chat_id", None), getattr(message, "id", None))

    @loader.watcher(only_messages=True)
    async def watcher(self, message):
        """Отслеживает .ttx от разрешённых пользователей (в т.ч. в комментариях канала)"""
        if getattr(message, "out", False):
            # Свои команды обрабатывает сам ttxcmd
            return

        text = (getattr(message, "raw_text", None) or "").strip()
        prefix = self.get_prefix()
        if not text.lower().startswith(f"{prefix}ttx"):
            return
        rest = text[len(prefix) + 3:]
        if rest and not rest[0].isspace():
            return  # например ".ttxfoo" — не наша команда

        # Раньше на .ttx реагировал любой человек в любом чате, и юзербот
        # отвечал от вашего аккаунта — теперь только разрешённые
        if not self._is_allowed(message):
            return

        await self._process_ttx(message)

    @loader.command(
        ru_doc="[название / реплай / в комментариях] - Находит текст песни и нормализует кривые шрифты",
        en_doc="[title / reply / in comments] - Finds track lyrics and normalizes weird fonts",
    )
    async def ttxcmd(self, message):
        """[title / reply / in comments] - Search track lyrics"""
        await self._process_ttx(message)

    async def _process_ttx(self, message):
        key = self._msg_key(message)
        if key in self._processed_ids:
            return
        self._processed_ids[key] = True
        while len(self._processed_ids) > 500:
            self._processed_ids.popitem(last=False)

        args = utils.get_args_raw(message).strip()

        track_queries = []
        seen_queries = set()

        def add_track_q(q):
            if q:
                qn = q.lower().strip()
                if qn and qn not in seen_queries:
                    seen_queries.add(qn)
                    track_queries.append(q)

        if args:
            add_track_q(args)
        else:
            candidates = []
            
            # Получаем реплай или главный пост обсуждения
            reply = await message.get_reply_message()
            top_id = getattr(message, "reply_to_top_id", None) or getattr(getattr(message, "reply_to", None), "reply_to_top_id", None) or getattr(message, "reply_to_msg_id", None)
            
            top_msg = None
            if top_id:
                try:
                    top_msg = await message.client.get_messages(message.chat_id, ids=top_id)
                except Exception:
                    pass

            target = reply or top_msg

            if target:
                candidates.append(target)

                # Если это альбом (несколько медиафайлов в одном посте), собираем строго сообщения этого же альбома
                gid = getattr(target, "grouped_id", None)
                if gid:
                    try:
                        # Альбом — до 10 соседних сообщений вокруг поста, а не 20 последних в чате
                        album_ids = list(range(max(1, target.id - 10), target.id + 11))
                        for m in await message.client.get_messages(target.chat_id, ids=album_ids):
                            if m and getattr(m, "grouped_id", None) == gid and m.id != target.id:
                                candidates.append(m)
                    except Exception:
                        pass
            else:
                # Если реплай/топ-пост не найдены, сканируем строго ПЕРВОЕ ближайшее аудио-сообщение
                try:
                    async for m in message.client.iter_messages(message.chat_id, limit=10):
                        if m and m.id != message.id:
                            extracted = self._extract_all_queries_from_msg(m)
                            if extracted:
                                candidates.append(m)
                                break
                except Exception:
                    pass

            for target_msg in candidates:
                extracted_list = self._extract_all_queries_from_msg(target_msg)
                for item in extracted_list:
                    add_track_q(item)

        if not track_queries:
            await utils.answer(message, self.strings("no_args"))
            return

        # Отправляем сообщение со статусом поиска
        try:
            await utils.answer(message, self.strings("searching"))
        except Exception:
            pass

        found_any = False
        sent_first = False

        for raw_q in track_queries:
            clean_query = normalize_text(raw_q)
            clean_query = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27ff\u2b00-\u2bff]', '', clean_query).strip()
            clean_query = re.sub(r'^[🎧🎵🎶🔥✨\s]+|[🎧🎵🎶🔥✨\s]+$', '', clean_query).strip()

            lyrics = await self._fetch_lyrics(clean_query)
            if lyrics:
                found_any = True
                normalized_lyrics = normalize_text(lyrics)
                if len(normalized_lyrics) > 3700:
                    normalized_lyrics = normalized_lyrics[:3700] + "\n\n[Текст сокращен из-за лимита Telegram...]"

                formatted_res = self.strings("lyrics_template").format(
                    utils.escape_html(clean_query), utils.escape_html(normalized_lyrics)
                )

                if not sent_first:
                    await utils.answer(message, formatted_res)
                    sent_first = True
                else:
                    await message.client.send_message(
                        message.chat_id,
                        formatted_res,
                        reply_to=getattr(message, "reply_to_msg_id", None) or message.id
                    )

        if not found_any:
            await utils.answer(message, self.strings("not_found").format(utils.escape_html(track_queries[0])))

    async def _scrape_genius(self, session, song_url: str) -> str:
        """Скрапит текст песни с сайта Genius."""
        try:
            async with session.get(song_url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    for tag in soup(["script", "style", "header", "footer", "iframe"]):
                        tag.decompose()
                    containers = soup.find_all("div", {"data-lyrics-container": "true"})
                    if not containers:
                        containers = soup.find_all("div", class_=re.compile(r"Lyrics__Container"))
                    if containers:
                        text_parts = []
                        for c in containers:
                            for br in c.find_all("br"):
                                br.replace_with("\n")
                            text_parts.append(c.get_text())
                        res = "\n".join(text_parts).strip()
                        if res:
                            return res
        except Exception:
            pass
        return ""

    async def _scrape_azlyrics(self, session, url: str) -> str:
        """Скрапит текст песни с сайта AZLyrics."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    for tag in soup(["script", "style", "header", "footer"]):
                        tag.decompose()
                    comment = soup.find(string=re.compile(r"Usage of azlyrics", re.IGNORECASE))
                    if comment and comment.parent:
                        target_div = comment.parent
                        for br in target_div.find_all("br"):
                            br.replace_with("\n")
                        return target_div.get_text().strip()
        except Exception:
            pass
        return ""

    async def _scrape_text_pesni(self, session, url: str) -> str:
        """Скрапит текст песни с русскоязычного портала Text-pesni."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    for tag in soup(["script", "style", "header", "footer"]):
                        tag.decompose()
                    container = soup.find("div", class_=re.compile(r"(block_text|song-text|lyrics)"))
                    if container:
                        for br in container.find_all("br"):
                            br.replace_with("\n")
                        return container.get_text().strip()
        except Exception:
            pass
        return ""

    async def _fetch_single_query(self, session, q: str) -> str:
        """Параллельно выполняет запросы к быстрым API сервисам текстов."""

        async def try_lrclib():
            try:
                url = f"https://lrclib.net/api/search?q={urllib.parse.quote(q)}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        if data and isinstance(data, list):
                            # Берём лучшее совпадение по исполнителю и названию,
                            # а не первый попавшийся трек с похожим словом
                            ranked = sorted(
                                (item for item in data if item.get("plainLyrics") or item.get("syncedLyrics")),
                                key=lambda item: match_score(
                                    q, f"{item.get('artistName', '')} {item.get('trackName', '')}"
                                ),
                                reverse=True,
                            )
                            if ranked:
                                item = ranked[0]
                                lyrics = item.get("plainLyrics") or item.get("syncedLyrics")
                                return re.sub(r'\[\d+:\d+\.\d+\]', '', lyrics).strip()
            except Exception:
                pass
            return ""

        async def try_genius():
            try:
                search_url = f"https://genius.com/api/search/song?q={urllib.parse.quote(q)}"
                async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        response = data.get("response", {})
                        # Результаты лежат в response.sections[].hits (раньше код искал
                        # response.hits, которого нет, и Genius не срабатывал никогда)
                        hits = list(response.get("hits", []))
                        for section in response.get("sections", []):
                            hits.extend(section.get("hits", []))
                        songs = [h["result"] for h in hits if h.get("type") == "song" and h.get("result", {}).get("url")]
                        if songs:
                            best = max(songs, key=lambda r: match_score(q, r.get("full_title", "")))
                            return await self._scrape_genius(session, best["url"])
            except Exception:
                pass
            return ""

        # Запускаем все провайдеры параллельно
        results = await asyncio.gather(try_lrclib(), try_genius(), return_exceptions=True)
        for res in results:
            if isinstance(res, str) and res.strip():
                return res.strip()

        # Фолбэк-поиск в DuckDuckGo если быстрые API не вернули результата
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q + ' текст песни lyrics')}"
            async with session.get(ddg_url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, "html.parser")
                    results_links = soup.find_all("a", class_="result__url")
                    for r in results_links:
                        href = r.get("href", "").strip()
                        if "genius.com" in href:
                            lyrics = await self._scrape_genius(session, href)
                            if lyrics:
                                return lyrics
                        elif "azlyrics.com" in href:
                            lyrics = await self._scrape_azlyrics(session, href)
                            if lyrics:
                                return lyrics
                        elif "text-pesni.com" in href:
                            lyrics = await self._scrape_text_pesni(session, href)
                            if lyrics:
                                return lyrics
        except Exception:
            pass

        return ""

    async def _fetch_lyrics(self, query: str) -> str:
        """Молниеносный параллельный поиск текста песни через все источники."""
        queries = prepare_search_queries(query)[:2]

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            for q in queries:
                try:
                    res = await asyncio.wait_for(self._fetch_single_query(session, q), timeout=6)
                    if res:
                        return res
                except Exception:
                    pass

        return ""


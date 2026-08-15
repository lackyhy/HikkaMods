# meta developer: @lackyhyyy666

import asyncio
import html
import re
import socket
from datetime import datetime, timezone
from urllib.parse import quote, urlparse

import aiohttp
from .. import loader, utils

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


def get_flag_emoji(country_code: str) -> str:
    """Конвертирует ISO 3166-1 alpha-2 код страны в emoji флаг"""
    if not country_code or len(country_code) != 2:
        return "🌐"
    return "".join(chr(127397 + ord(c.upper())) for c in country_code)


def get_tz_time(tz_name: str):
    """Получает текущее локальное время и смещение UTC по имени часового пояса"""
    if ZoneInfo and tz_name:
        try:
            now = datetime.now(ZoneInfo(tz_name))
            offset = now.strftime("%z")
            formatted_offset = f"UTC{offset[:3]}:{offset[3:]}" if offset else ""
            return now.strftime("%H:%M:%S (%d.%m.%Y)"), formatted_offset
        except Exception:
            pass
    return None, None


@loader.tds
class SinfMod(loader.Module):
    """Модуль для получения подробной информации о любом адресе: IP/Домен, Географический адрес/Координаты, Крипто-кошелек, MAC-адрес."""

    strings = {"name": "Sinf"}

    @loader.command()
    async def sinfcmd(self, message):
        """<адрес / IP / домен / кошелек / координаты> — Вся доступная информация об адресе"""
        args = utils.get_args_raw(message)

        # Если аргумент не указан, проверяем реплай
        if not args:
            reply = await message.get_reply_message()
            if reply and reply.raw_text:
                args = reply.raw_text.strip()

        if not args:
            await utils.answer(
                message,
                "<b>⚠️ Укажите адрес для получения информации!</b>\n\n"
                "<i>Поддерживаемые типы адресов:</i>\n"
                "• <b>IP / Домен / Ссылка:</b> <code>.sinf 8.8.8.8</code> или <code>.sinf google.com</code>\n"
                "• <b>Физический адрес:</b> <code>.sinf Москва, Тверская 1</code>\n"
                "• <b>Координаты:</b> <code>.sinf 55.7558, 37.6173</code>\n"
                "• <b>Крипто-кошелек:</b> <code>.sinf 0x71C...</code> (BTC, ETH, TON, TRX, LTC)\n"
                "• <b>MAC-адрес:</b> <code>.sinf 00:1A:2B:3C:4D:5E</code>",
            )
            return

        query = args.strip()
        await utils.answer(message, "<b>🔍 Сбор информации об адресе...</b>")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        timeout = aiohttp.ClientTimeout(total=8)

        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            # 1. Проверка на MAC-адрес
            mac_match = re.match(
                r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$|^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$",
                query,
            )
            if mac_match:
                res = await self._lookup_mac(session, query)
                if res:
                    await utils.answer(message, res)
                    return

            # 2. Проверка на Координаты (lat, lon)
            coord_match = re.match(
                r"^([-+]?\d{1,3}\.\d+)[,\s]+([-+]?\d{1,3}\.\d+)$", query
            )
            if coord_match:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    res = await self._lookup_coords(session, lat, lon)
                    if res:
                        await utils.answer(message, res)
                        return

            # 3. Проверка на Крипто-кошелек
            crypto_res = await self._lookup_crypto(session, query)
            if crypto_res:
                await utils.answer(message, crypto_res)
                return

            # 4. Проверка на IP или Домен/URL
            clean_host = query
            if "://" in query:
                parsed_url = urlparse(query)
                clean_host = parsed_url.hostname or query
            elif "/" in query:
                clean_host = query.split("/")[0]

            # Удаляем порт если есть (например, 127.0.0.1:8080 или site.com:443)
            if ":" in clean_host and not clean_host.count(":") > 1:  # не IPv6
                clean_host = clean_host.split(":")[0]

            is_ip = self._is_ip(clean_host)
            is_domain = False

            if not is_ip:
                # Проверяем, можно ли зарезолвить как домен
                try:
                    loop = asyncio.get_event_loop()
                    addr_info = await loop.getaddrinfo(clean_host, None)
                    if addr_info:
                        is_domain = True
                except Exception:
                    pass

            if is_ip or is_domain:
                res = await self._lookup_ip_or_domain(session, clean_host, query, is_domain)
                if res:
                    await utils.answer(message, res)
                    return

            # 5. Иначе обрабатываем как Физический / Географический адрес
            geo_res = await self._lookup_geo_address(session, query)
            if geo_res:
                await utils.answer(message, geo_res)
                return

            await utils.answer(
                message,
                f"<b>❌ Не удалось найти информацию по запросу:</b> <code>{html.escape(query)}</code>",
            )

    def _is_ip(self, text: str) -> bool:
        """Проверка, является ли строка IPv4 или IPv6"""
        try:
            socket.inet_pton(socket.AF_INET, text)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, text)
                return True
            except socket.error:
                return False

    async def _lookup_ip_or_domain(
        self, session: aiohttp.ClientSession, host: str, original_query: str, is_domain: bool
    ) -> str:
        """Получение информации об IP или Домене"""
        ip_address = host
        resolved_ip = None

        if is_domain:
            try:
                loop = asyncio.get_event_loop()
                resolved_ip = await loop.run_in_executor(
                    None, lambda: socket.gethostbyname(host)
                )
                ip_address = resolved_ip
            except Exception:
                pass

        # Запрос к IP Geolocation API (ip-api.com)
        url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query"
        data = None
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
        except Exception:
            pass

        if not data or data.get("status") != "success":
            # Фолбэк на ipapi.co
            try:
                async with session.get(f"https://ipapi.co/{ip_address}/json/") as resp:
                    if resp.status == 200:
                        raw = await resp.json()
                        data = {
                            "status": "success",
                            "query": ip_address,
                            "country": raw.get("country_name"),
                            "countryCode": raw.get("country_code"),
                            "regionName": raw.get("region"),
                            "city": raw.get("city"),
                            "zip": raw.get("postal"),
                            "lat": raw.get("latitude"),
                            "lon": raw.get("longitude"),
                            "timezone": raw.get("timezone"),
                            "isp": raw.get("org"),
                            "org": raw.get("org"),
                            "as": raw.get("asn"),
                            "reverse": raw.get("hostname"),
                            "mobile": False,
                            "proxy": False,
                            "hosting": False,
                        }
            except Exception:
                pass

        if not data or data.get("status") != "success":
            return ""

        country = html.escape(data.get("country") or "Н/Д")
        country_code = data.get("countryCode") or ""
        flag = get_flag_emoji(country_code)
        region = html.escape(data.get("regionName") or "")
        city = html.escape(data.get("city") or "")
        zip_code = html.escape(str(data.get("zip") or "Н/Д"))
        lat = data.get("lat")
        lon = data.get("lon")
        tz = data.get("timezone") or ""
        isp = html.escape(data.get("isp") or "Н/Д")
        org = html.escape(data.get("org") or "Н/Д")
        as_num = html.escape(data.get("as") or "Н/Д")
        reverse_dns = html.escape(data.get("reverse") or "Н/Д")

        is_mobile = "📱 Да" if data.get("mobile") else "❌ Нет"
        is_proxy = "🛡 Да" if data.get("proxy") else "❌ Нет"
        is_hosting = "🖥 Да" if data.get("hosting") else "❌ Нет"

        # Определение типа IP (v4/v6)
        ip_ver = "IPv6" if ":" in data.get("query", "") else "IPv4"

        local_time, utc_offset = get_tz_time(tz)
        tz_str = f"<code>{tz}</code>" if tz else "Н/Д"
        if local_time:
            tz_str += f"\n• <b>Местное время:</b> <code>{local_time}</code> ({utc_offset})"

        maps_links = ""
        if lat is not None and lon is not None:
            gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            ymaps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
            maps_links = f"\n• <b>Карты:</b> <a href=\"{gmaps}\">Google Maps</a> | <a href=\"{ymaps}\">Yandex Maps</a>"

        header_title = f"<b>🌐 Информация о домене:</b> <code>{html.escape(host)}</code>" if is_domain else f"<b>🌐 Информация об IP-адресе:</b> <code>{html.escape(host)}</code>"

        res_lines = [
            header_title,
            "",
            f"<b>📌 IP Адрес:</b> <code>{data.get('query')}</code> ({ip_ver})"
        ]

        if is_domain and resolved_ip:
            res_lines.append(f"<b>🔗 Зарезолвленный IP:</b> <code>{resolved_ip}</code>")

        res_lines.extend([
            "",
            "<b>📍 Геолокация:</b>",
            f"• <b>Страна:</b> {flag} {country} ({country_code})",
            f"• <b>Регион / Город:</b> {region}, {city}".strip(", "),
            f"• <b>Почтовый индекс:</b> <code>{zip_code}</code>",
            f"• <b>Координаты:</b> <code>{lat}, {lon}</code>" + maps_links,
            "",
            "<b>🕐 Время и Часовой пояс:</b>",
            f"• <b>Часовой пояс:</b> {tz_str}",
            "",
            "<b>🖥 Сеть и Провайдер:</b>",
            f"• <b>Reverse DNS (PTR):</b> <code>{reverse_dns}</code>",
            f"• <b>Провайдер (ISP):</b> {isp}",
            f"• <b>Организация:</b> {org}",
            f"• <b>AS Номер:</b> <code>{as_num}</code>",
            "",
            "<b>🛡 Характеристики:</b>",
            f"• <b>Хостинг / Data-центр:</b> {is_hosting}",
            f"• <b>Прокси / VPN:</b> {is_proxy}",
            f"• <b>Мобильная сеть:</b> {is_mobile}",
        ])

        # Если это был домен, пробуем запросить HTTP статус и Server header
        if is_domain:
            http_info = await self._fetch_http_info(session, host)
            if http_info:
                res_lines.extend(["", "<b>💻 Веб-сервер (HTTP):</b>", http_info])

        return "\n".join(res_lines)

    async def _fetch_http_info(self, session: aiohttp.ClientSession, domain: str) -> str:
        """Получает заголовок сервера и HTTP статус для домена"""
        url = f"https://{domain}" if not domain.startswith("http") else domain
        try:
            async with session.get(url, allow_redirects=True, ssl=False) as resp:
                status_code = resp.status
                server = resp.headers.get("Server", "Не указан")

                # Читаем кусочек HTML для поиска <title>
                title = "Не найден"
                try:
                    body = await resp.content.read(4096)
                    text = body.decode("utf-8", errors="ignore")
                    title_match = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        title = title_match.group(1).strip()
                        title = re.sub(r"\s+", " ", title)
                        if len(title) > 60:
                            title = title[:57] + "..."
                except Exception:
                    pass

                return (
                    f"• <b>HTTP Статус:</b> <code>{status_code}</code>\n"
                    f"• <b>Сервер:</b> <code>{html.escape(server)}</code>\n"
                    f"• <b>Заголовок страницы:</b> <code>{html.escape(title)}</code>"
                )
        except Exception:
            return ""

    async def _lookup_geo_address(self, session: aiohttp.ClientSession, address_query: str) -> str:
        """Геокодирование физического адреса через OpenStreetMap Nominatim"""
        url = f"https://nominatim.openstreetmap.org/search?q={quote(address_query)}&format=json&addressdetails=1&limit=1&accept-language=ru"
        nominatim_headers = {"User-Agent": "HikkaSinfModule/1.0 (TelegramUserbot)"}
        try:
            async with session.get(url, headers=nominatim_headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and isinstance(data, list) and len(data) > 0:
                        place = data[0]
                        display_name = html.escape(place.get("display_name", ""))
                        lat = place.get("lat")
                        lon = place.get("lon")
                        category = html.escape(place.get("class", ""))
                        type_name = html.escape(place.get("type", ""))
                        addr = place.get("address", {})

                        country = html.escape(addr.get("country", "Н/Д"))
                        country_code = addr.get("country_code", "").upper()
                        flag = get_flag_emoji(country_code)

                        state = html.escape(addr.get("state") or addr.get("region") or "")
                        city = html.escape(
                            addr.get("city")
                            or addr.get("town")
                            or addr.get("village")
                            or addr.get("county")
                            or ""
                        )
                        road = html.escape(addr.get("road") or "")
                        house = html.escape(addr.get("house_number") or "")
                        postcode = html.escape(addr.get("postcode") or "Н/Д")

                        gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        ymaps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"

                        street_str = f"{road} {house}".strip()
                        if not street_str:
                            street_str = "Не указана"

                        return (
                            f"<b>🗺 Информация о географическом адресе:</b>\n<code>{html.escape(address_query)}</code>\n\n"
                            f"<b>📍 Найденный объект:</b>\n"
                            f"• <b>Полный адрес:</b> <code>{display_name}</code>\n"
                            f"• <b>Страна:</b> {flag} {country} ({country_code})\n"
                            f"• <b>Регион / Город:</b> {state}, {city}".strip(", ") + "\n"
                            f"• <b>Улица / Дом:</b> {street_str}\n"
                            f"• <b>Почтовый индекс:</b> <code>{postcode}</code>\n"
                            f"• <b>Тип:</b> <code>{category} ({type_name})</code>\n\n"
                            f"<b>📍 Координаты и Карты:</b>\n"
                            f"• <b>Широта, Долгота:</b> <code>{lat}, {lon}</code>\n"
                            f"• <b>Карты:</b> <a href=\"{gmaps}\">Google Maps</a> | <a href=\"{ymaps}\">Yandex Maps</a>"
                        )
        except Exception:
            pass

        return ""

    async def _lookup_coords(self, session: aiohttp.ClientSession, lat: float, lon: float) -> str:
        """Обратное геокодирование по географическим координатам (широта, долгота)"""
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1&accept-language=ru"
        nominatim_headers = {"User-Agent": "HikkaSinfModule/1.0 (TelegramUserbot)"}
        try:
            async with session.get(url, headers=nominatim_headers) as resp:
                if resp.status == 200:
                    place = await resp.json()
                    if place and "display_name" in place:
                        display_name = html.escape(place.get("display_name", ""))
                        addr = place.get("address", {})

                        country = html.escape(addr.get("country", "Н/Д"))
                        country_code = addr.get("country_code", "").upper()
                        flag = get_flag_emoji(country_code)

                        city = html.escape(
                            addr.get("city")
                            or addr.get("town")
                            or addr.get("village")
                            or addr.get("state")
                            or ""
                        )
                        postcode = html.escape(addr.get("postcode") or "Н/Д")

                        gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                        ymaps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"

                        return (
                            f"<b>📍 Информация о координатах:</b> <code>{lat}, {lon}</code>\n\n"
                            f"<b>🗺 Найденное место:</b>\n"
                            f"• <b>Адрес:</b> <code>{display_name}</code>\n"
                            f"• <b>Страна:</b> {flag} {country} ({country_code})\n"
                            f"• <b>Населенный пункт:</b> {city}\n"
                            f"• <b>Почтовый индекс:</b> <code>{postcode}</code>\n\n"
                            f"<b>🗺 Карты:</b> <a href=\"{gmaps}\">Google Maps</a> | <a href=\"{ymaps}\">Yandex Maps</a>"
                        )
        except Exception:
            pass

        gmaps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        ymaps = f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
        return (
            f"<b>📍 Координаты:</b> <code>{lat}, {lon}</code>\n\n"
            f"<b>🗺 Карты:</b> <a href=\"{gmaps}\">Google Maps</a> | <a href=\"{ymaps}\">Yandex Maps</a>"
        )

    async def _lookup_crypto(self, session: aiohttp.ClientSession, addr: str) -> str:
        """Определение и считывание информации о крипто-кошельке"""
        # TON (EQ... или UQ...)
        if re.match(r"^(EQ|UQ)[A-Za-z0-9_-]{46}$", addr):
            try:
                async with session.get(f"https://tonapi.io/v2/accounts/{addr}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        raw_balance = int(data.get("balance", 0))
                        balance_ton = raw_balance / 1e9
                        status = data.get("status", "active")
                        is_wallet = "Да" if data.get("is_wallet") else "Нет"
                        name = data.get("name") or "Личный кошелек"

                        return (
                            f"<b>💎 Информация о TON кошельке:</b>\n<code>{addr}</code>\n\n"
                            f"• <b>Сеть:</b> The Open Network (TON)\n"
                            f"• <b>Имя / Метка:</b> <code>{html.escape(name)}</code>\n"
                            f"• <b>Баланс:</b> <code>{balance_ton:,.4f} TON</code>\n"
                            f"• <b>Статус:</b> <code>{status}</code>\n"
                            f"• <b>Кошелек:</b> {is_wallet}\n\n"
                            f"🔗 <a href=\"https://tonscan.org/address/{addr}\">Открыть в Tonscan</a>"
                        )
            except Exception:
                pass

        # Ethereum / EVM (0x...)
        if re.match(r"^0x[a-fA-F0-9]{40}$", addr):
            try:
                async with session.get(
                    f"https://api.blockchair.com/ethereum/dashboards/address/{addr}"
                ) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        data = res_json.get("data", {}).get(addr, {}).get("address", {})
                        if data:
                            bal_wei = int(data.get("balance", 0))
                            bal_eth = bal_wei / 1e18
                            tx_count = data.get("transaction_count", 0)

                            rec_eth = int(data.get("received_approximate", 0)) / 1e18
                            sent_eth = int(data.get("spent_approximate", 0)) / 1e18

                            return (
                                f"<b>💎 Информация о Ethereum (EVM) кошельке:</b>\n<code>{addr}</code>\n\n"
                                f"• <b>Сеть:</b> Ethereum (EVM)\n"
                                f"• <b>Баланс:</b> <code>{bal_eth:,.4f} ETH</code>\n"
                                f"• <b>Всего получено:</b> <code>{rec_eth:,.4f} ETH</code>\n"
                                f"• <b>Всего отправлено:</b> <code>{sent_eth:,.4f} ETH</code>\n"
                                f"• <b>Количество транзакций:</b> <code>{tx_count}</code>\n\n"
                                f"🔗 <a href=\"https://etherscan.io/address/{addr}\">Открыть в Etherscan</a>"
                            )
            except Exception:
                pass

        # Bitcoin (1..., 3..., bc1...)
        if re.match(r"^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$", addr):
            try:
                async with session.get(
                    f"https://api.blockchair.com/bitcoin/dashboards/address/{addr}"
                ) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        data = res_json.get("data", {}).get(addr, {}).get("address", {})
                        if data:
                            bal_sat = int(data.get("balance", 0))
                            bal_btc = bal_sat / 1e8
                            tx_count = data.get("transaction_count", 0)
                            rec_btc = int(data.get("received", 0)) / 1e8
                            sent_btc = int(data.get("spent", 0)) / 1e8

                            return (
                                f"<b>₿ Информация о Bitcoin кошельке:</b>\n<code>{addr}</code>\n\n"
                                f"• <b>Сеть:</b> Bitcoin (BTC)\n"
                                f"• <b>Баланс:</b> <code>{bal_btc:,.8f} BTC</code>\n"
                                f"• <b>Всего получено:</b> <code>{rec_btc:,.8f} BTC</code>\n"
                                f"• <b>Всего отправлено:</b> <code>{sent_btc:,.8f} BTC</code>\n"
                                f"• <b>Количество транзакций:</b> <code>{tx_count}</code>\n\n"
                                f"🔗 <a href=\"https://www.blockchain.com/btc/address/{addr}\">Открыть в Blockchain.com</a>"
                            )
            except Exception:
                pass

        # Litecoin (L..., M..., ltc1...)
        if re.match(r"^(L|M|ltc1)[a-zA-HJ-NP-Z0-9]{25,62}$", addr):
            try:
                async with session.get(
                    f"https://api.blockchair.com/litecoin/dashboards/address/{addr}"
                ) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        data = res_json.get("data", {}).get(addr, {}).get("address", {})
                        if data:
                            bal_sat = int(data.get("balance", 0))
                            bal_ltc = bal_sat / 1e8
                            tx_count = data.get("transaction_count", 0)

                            return (
                                f"<b>Ł Информация о Litecoin кошельке:</b>\n<code>{addr}</code>\n\n"
                                f"• <b>Сеть:</b> Litecoin (LTC)\n"
                                f"• <b>Баланс:</b> <code>{bal_ltc:,.8f} LTC</code>\n"
                                f"• <b>Транзакций:</b> <code>{tx_count}</code>\n\n"
                                f"🔗 <a href=\"https://blockchair.com/litecoin/address/{addr}\">Открыть в Blockchair</a>"
                            )
            except Exception:
                pass

        # TRON (T...)
        if re.match(r"^T[a-zA-Z0-9]{33}$", addr):
            try:
                async with session.get(
                    f"https://api.blockchair.com/tron/dashboards/address/{addr}"
                ) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        data = res_json.get("data", {}).get(addr, {}).get("address", {})
                        if data:
                            bal_sun = int(data.get("balance", 0))
                            bal_trx = bal_sun / 1e6
                            tx_count = data.get("transaction_count", 0)

                            return (
                                f"<b>🔴 Информация о TRON кошельке:</b>\n<code>{addr}</code>\n\n"
                                f"• <b>Сеть:</b> TRON (TRX)\n"
                                f"• <b>Баланс:</b> <code>{bal_trx:,.4f} TRX</code>\n"
                                f"• <b>Транзакций:</b> <code>{tx_count}</code>\n\n"
                                f"🔗 <a href=\"https://tronscan.org/#/address/{addr}\">Открыть в Tronscan</a>"
                            )
            except Exception:
                pass

        return ""

    async def _lookup_mac(self, session: aiohttp.ClientSession, mac: str) -> str:
        """Поиск производителя устройства по MAC-адресу"""
        clean_mac = mac.replace(":", "").replace("-", "").replace(".", "").upper()
        try:
            async with session.get(f"https://api.maclookup.app/v2/macs/{clean_mac}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success") and data.get("found"):
                        company = html.escape(data.get("company", "Неизвестно"))
                        country_code = data.get("country", "")
                        flag = get_flag_emoji(country_code)
                        mac_prefix = html.escape(data.get("macPrefix", ""))

                        return (
                            f"<b>🔌 Информация о MAC-адресе:</b> <code>{html.escape(mac)}</code>\n\n"
                            f"• <b>Производитель:</b> <code>{company}</code>\n"
                            f"• <b>Страна вендора:</b> {flag} {country_code}\n"
                            f"• <b>OUI Префикс:</b> <code>{mac_prefix}</code>"
                        )
        except Exception:
            pass

        return (
            f"<b>🔌 Информация о MAC-адресе:</b> <code>{html.escape(mac)}</code>\n\n"
            f"• <b>Статус:</b> Формат верен, но вендор не найден в публичной базе OUI."
        )

# meta developer: @lackyhyyy666
# scope: hikka_only
# scope: hikka_min 1.6.2

import asyncio
import html
import logging
import re
from telethon import types
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class SmartBroadcastMod(loader.Module):
    """Модуль объявлений с пингом реальных участников группы (.sba) и без пинга (.sb). Поддерживает добавление ID пользователей в .cfg"""

    strings = {
        "name": "SmartBroadcast",
        "no_text": (
            "<b>⚠️ Укажите текст объявления или ответьте на сообщение!</b>\n\n"
            "<b>Использование:</b>\n"
            "• <code>.sb &lt;текст&gt;</code> — Объявление без пинга\n"
            "• <code>.sba &lt;текст&gt;</code> — Объявление с пингом юзернеймов участников (@user1, @user2...)\n\n"
            "<i>Вы можете добавить ID пользователей в <code>.cfg</code> в поле <code>allowed_users</code>, чтобы дать им доступ к модулю.</i>"
        ),
        "not_a_group": "<b>⚠️ Команда .sba с пингом работает только в группах и супергруппах!</b>",
        "access_denied": "<b>❌ У вас нет доступа к использованию модуля объявлений.</b>",
        "config_allowed_users": "ID пользователей через запятую или пробел, которым разрешено использовать .sb и .sba",
        "config_batch_size": "Количество участников в одном пинг-сообщении",
        "config_delay": "Задержка в секундах между отправкой пинг-сообщений",
        "config_announcement_prefix": "Заголовок объявления (HTML)",
        "config_delete_command": "Удалять исходное сообщение с командой (.sb / .sba)",
    }

    strings_ru = {
        "no_text": (
            "<b>⚠️ Укажите текст объявления или ответьте на сообщение!</b>\n\n"
            "<b>Использование:</b>\n"
            "• <code>.sb &lt;текст&gt;</code> — Объявление без пинга\n"
            "• <code>.sba &lt;текст&gt;</code> — Объявление с пингом юзернеймов участников (@user1, @user2...)\n\n"
            "<i>Вы можете добавить ID пользователей в <code>.cfg</code> в поле <code>allowed_users</code>, чтобы дать им доступ к модулю.</i>"
        ),
        "not_a_group": "<b>⚠️ Команда .sba с пингом работает только в группах и супергруппах!</b>",
        "access_denied": "<b>❌ У вас нет доступа к использованию модуля объявлений.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allowed_users",
                "",
                lambda: self.strings("config_allowed_users"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "batch_size",
                5,
                lambda: self.strings("config_batch_size"),
                validator=loader.validators.Integer(minimum=1, maximum=50),
            ),
            loader.ConfigValue(
                "delay",
                1.0,
                lambda: self.strings("config_delay"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "announcement_prefix",
                "📢 <b>Объявление:</b>",
                lambda: self.strings("config_announcement_prefix"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "delete_command",
                True,
                lambda: self.strings("config_delete_command"),
                validator=loader.validators.Boolean(),
            ),
        )

    def _is_allowed(self, message) -> bool:
        """Проверяет, разрешено ли пользователю выполнять команды модуля"""
        if getattr(message, "out", False):
            return True

        sender_id = getattr(message, "sender_id", None)
        if not sender_id:
            return False

        owner_id = getattr(self, "tg_id", None) or getattr(
            getattr(self, "_client", None), "tg_id", None
        )
        if owner_id and sender_id == owner_id:
            return True

        raw_allowed = self.config["allowed_users"]
        if not raw_allowed:
            return False

        allowed_set = set()
        if isinstance(raw_allowed, (int, str)):
            raw_allowed = [raw_allowed]

        for item in raw_allowed:
            if isinstance(item, int):
                allowed_set.add(item)
            elif isinstance(item, str):
                for sub in re.split(r"[,\s]+", item.strip()):
                    if sub.lstrip("-").isdigit():
                        allowed_set.add(int(sub))

        return sender_id in allowed_set

    async def _get_chat_users(self, message):
        """Получает список реальных участников чата"""
        users = []
        seen_ids = set()

        chat = getattr(message, "chat", None)
        if not chat:
            try:
                chat = await self._client.get_entity(message.chat_id)
            except Exception:
                chat = message.chat_id

        # 1. Запрашиваем участников через get_participants
        try:
            participants = await self._client.get_participants(chat, limit=300)
            for u in participants:
                if u.id in seen_ids:
                    continue
                if getattr(u, "bot", False) or getattr(u, "deleted", False) or getattr(u, "is_self", False):
                    continue
                seen_ids.add(u.id)
                users.append(u)
        except Exception as e:
            logger.warning(f"[SmartBroadcast] get_participants failed: {e}")

        # 2. Если get_participants не сработал, итерируемся по iter_participants
        if not users:
            try:
                async for u in self._client.iter_participants(chat, limit=300):
                    if u.id in seen_ids:
                        continue
                    if getattr(u, "bot", False) or getattr(u, "deleted", False) or getattr(u, "is_self", False):
                        continue
                    seen_ids.add(u.id)
                    users.append(u)
            except Exception as e:
                logger.warning(f"[SmartBroadcast] iter_participants failed: {e}")

        # 3. Фолбэк: если список скрыт, собираем активных авторов из сообщений чата
        if not users:
            try:
                async for msg in self._client.iter_messages(chat, limit=200):
                    sender = getattr(msg, "sender", None)
                    if not sender and getattr(msg, "from_id", None):
                        try:
                            sender = await self._client.get_entity(msg.from_id)
                        except Exception:
                            pass

                    if sender and isinstance(sender, types.User):
                        if sender.id not in seen_ids and not (
                            getattr(sender, "bot", False)
                            or getattr(sender, "deleted", False)
                            or getattr(sender, "is_self", False)
                        ):
                            seen_ids.add(sender.id)
                            users.append(sender)
            except Exception as e:
                logger.warning(f"[SmartBroadcast] iter_messages fallback failed: {e}")

        return users

    @loader.command(
        ru_doc="<текст / реплай> — Отправить объявление в чат без пинга",
        en_doc="<text / reply> — Send announcement without ping",
    )
    async def sbcmd(self, message: types.Message):
        """<text / reply> — Send announcement without ping"""
        if not self._is_allowed(message):
            await utils.answer(message, self.strings("access_denied"))
            return
        await self._process_broadcast(message, with_ping=False)

    @loader.command(
        ru_doc="<текст / реплай> — Отправить объявление с пингом юзернеймов группы (@user1, @user2...)",
        en_doc="<text / reply> — Send announcement with group usernames ping (@user1, @user2...)",
    )
    async def sbacmd(self, message: types.Message):
        """<text / reply> — Send announcement with group usernames ping (@user1, @user2...)"""
        if not self._is_allowed(message):
            await utils.answer(message, self.strings("access_denied"))
            return
        await self._process_broadcast(message, with_ping=True)

    @loader.watcher()
    async def watcher(self, message: types.Message):
        """Перехватывает команды .sb и .sba от пользователей из allowed_users"""
        if not isinstance(message, types.Message) or getattr(message, "out", False):
            return

        text = message.raw_text or message.text or ""
        if not text:
            return

        prefixes = (".", "!")
        if hasattr(self, "get_prefix"):
            try:
                p = self.get_prefix()
                if isinstance(p, (list, tuple, set)):
                    prefixes = tuple(p)
                elif isinstance(p, str) and p:
                    prefixes = (p,)
            except Exception:
                pass

        matched_prefix = None
        for p in prefixes:
            if text.startswith(p):
                matched_prefix = p
                break

        if not matched_prefix:
            return

        cmd_body = text[len(matched_prefix):].strip()
        cmd_name = cmd_body.split()[0].lower() if cmd_body else ""

        if cmd_name not in ("sb", "sba"):
            return

        if not self._is_allowed(message):
            return

        with_ping = (cmd_name == "sba")
        await self._process_broadcast(message, with_ping=with_ping)

    async def _process_broadcast(self, message: types.Message, with_ping: bool):
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message() if message.is_reply else None

        text = ""
        media = None

        if args:
            text = args
            if reply and reply.media:
                media = reply.media
        elif reply:
            text = reply.raw_text or reply.text or ""
            if reply.media:
                media = reply.media

        if not text and not media:
            await utils.answer(message, self.strings("no_text"))
            return

        # Получаем пользователя, который вызвал команду
        sender = await message.get_sender() if hasattr(message, "get_sender") else getattr(message, "sender", None)
        if not sender and getattr(message, "sender_id", None):
            try:
                sender = await self._client.get_entity(message.sender_id)
            except Exception:
                sender = None

        sender_tag = ""
        if sender:
            if getattr(sender, "username", None):
                sender_tag = f"@{sender.username}"
            else:
                first = getattr(sender, "first_name", "") or ""
                last = getattr(sender, "last_name", "") or ""
                full_name = f"{first} {last}".strip() or "Пользователь"
                sender_tag = f'<a href="tg://user?id={sender.id}">{html.escape(full_name)}</a>'

        prefix = str(self.config["announcement_prefix"]).strip()

        has_custom_tag = False
        tags_to_replace = [
            "{@name_ктоюзнул}",
            "{@name_кто_юзнул}",
            "{@name}",
            "{name}",
            "{@username}",
            "{username}",
            "{sender}",
            "{user}",
            "{mention}",
        ]

        for tag in tags_to_replace:
            if tag in prefix:
                prefix = prefix.replace(tag, sender_tag)
                has_custom_tag = True
            if tag in text:
                text = text.replace(tag, sender_tag)
                has_custom_tag = True

        header = f"{prefix}\n\n" if prefix else ""

        if has_custom_tag or not sender_tag:
            formatted_announcement = f"{header}{text}".strip() if text else prefix
        else:
            formatted_announcement = f"{header}{text}\n\n{sender_tag}".strip() if text else f"{prefix}\n\n{sender_tag}"

        if with_ping:
            if not (message.is_group or message.is_channel):
                await utils.answer(message, self.strings("not_a_group"))
                return

            users = await self._get_chat_users(message)

            if not users:
                await self._send_single_announcement(message, formatted_announcement, media)
                return

            try:
                batch_size = int(self.config["batch_size"])
                if batch_size < 1:
                    batch_size = 5
            except (ValueError, TypeError):
                batch_size = 5

            try:
                delay = float(self.config["delay"])
                if delay < 0.1:
                    delay = 0.5
            except (ValueError, TypeError):
                delay = 1.0

            chunks = [users[i:i + batch_size] for i in range(0, len(users), batch_size)]

            if self.config["delete_command"]:
                try:
                    await message.delete()
                except Exception:
                    pass

            for index, chunk in enumerate(chunks):
                mentions = []
                for u in chunk:
                    if getattr(u, "username", None):
                        mentions.append(f"@{u.username}")
                    else:
                        name = u.first_name or u.last_name or "Пользователь"
                        mentions.append(f'<a href="tg://user?id={u.id}">{html.escape(name)}</a>')

                pings_str = ", ".join(mentions)
                full_text = f"{pings_str}\n\n{formatted_announcement}"

                try:
                    if index == 0 and media:
                        await self._client.send_file(
                            message.chat_id,
                            media,
                            caption=full_text,
                            parse_mode="html"
                        )
                    else:
                        await self._client.send_message(
                            message.chat_id,
                            full_text,
                            parse_mode="html"
                        )
                except Exception as e:
                    logger.error(f"[SmartBroadcast] Ошибка отправки пинга (пачка {index}): {e}")

                if index < len(chunks) - 1:
                    await asyncio.sleep(delay)
        else:
            if self.config["delete_command"]:
                try:
                    await message.delete()
                except Exception:
                    pass

            await self._send_single_announcement(message, formatted_announcement, media)

    async def _send_single_announcement(self, message: types.Message, text: str, media=None):
        try:
            if media:
                await self._client.send_file(
                    message.chat_id,
                    media,
                    caption=text,
                    parse_mode="html"
                )
            else:
                await self._client.send_message(
                    message.chat_id,
                    text,
                    parse_mode="html"
                )
        except Exception as e:
            logger.error(f"[SmartBroadcast] Ошибка отправки объявления: {e}")
            await utils.answer(message, text)

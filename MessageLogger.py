# meta developer: @lackyhyyy666

import datetime
import logging
from collections import deque
from telethon import events
from telethon.tl.types import Channel, Chat, User
from telethon.utils import get_peer_id
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class DeletedLoggerMod(loader.Module):
    """Перехватывает и пересылает удаленные сообщения (включая стикеры, медиа, голосовые) в заданный чат"""

    strings = {
        "name": "DeletedLogger",
        "chat_set": "✅ <b>Чат для логирования установлен:</b> <code>{}</code>",
        "invalid_chat": "❌ <b>Не удалось определить чат.</b> Передай ID/юзернейм чата или ответь на сообщение в нём.",
        "status": (
            "⚙️ <b>Статус DeletedLogger:</b>\n"
            "• <b>Лог-чат:</b> <code>{}</code>\n"
            "• <b>ЛС (PM):</b> {}\n"
            "• <b>Группы:</b> {}\n"
            "• <b>Свои сообщения:</b> {}\n"
            "• <b>Игнорируемых чатов:</b> <code>{}</code>\n"
            "• <b>Сообщений в кэше:</b> <code>{}</code>"
        ),
        "toggle_pm": "👁 Логирование удалений в ЛС: {}",
        "toggle_group": "👥 Логирование удалений в группах: {}",
        "toggle_self": "👤 Логирование собственных сообщений: {}",
        "ignored_add": "🚫 <b>Чат/Пользователь добавлен в игнорируемые:</b> <code>{}</code>",
        "ignored_remove": "✅ <b>Чат/Пользователь удален из игнорируемых:</b> <code>{}</code>",
        "ignored_list": "🚫 <b>Список игнорируемых чатов/пользователей:</b>\n{}",
        "ignored_empty": "ℹ️ <b>Список игнорируемых чатов пуст.</b>",
    }

    strings_ru = {
        "chat_set": "✅ <b>Чат для логирования установлен:</b> <code>{}</code>",
        "invalid_chat": "❌ <b>Не удалось определить чат.</b> Передай ID/юзернейм чата или ответь на сообщение в нём.",
        "status": (
            "⚙️ <b>Статус DeletedLogger:</b>\n"
            "• <b>Лог-чат:</b> <code>{}</code>\n"
            "• <b>ЛС (PM):</b> {}\n"
            "• <b>Группы:</b> {}\n"
            "• <b>Свои сообщения:</b> {}\n"
            "• <b>Игнорируемых чатов:</b> <code>{}</code>\n"
            "• <b>Сообщений в кэше:</b> <code>{}</code>"
        ),
        "toggle_pm": "👁 Логирование удалений в ЛС: {}",
        "toggle_group": "👥 Логирование удалений в группах: {}",
        "toggle_self": "👤 Логирование собственных сообщений: {}",
        "ignored_add": "🚫 <b>Чат/Пользователь добавлен в игнорируемые:</b> <code>{}</code>",
        "ignored_remove": "✅ <b>Чат/Пользователь удален из игнорируемых:</b> <code>{}</code>",
        "ignored_list": "🚫 <b>Список игнорируемых чатов/пользователей:</b>\n{}",
        "ignored_empty": "ℹ️ <b>Список игнорируемых чатов пуст.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "log_chat",
                "me",
                lambda: "ID чата/канала или 'me' (Избранное), куда отправлять удаленные сообщения",
                validator=loader.validators.Union(
                    loader.validators.Integer(), loader.validators.String()
                ),
            ),
            loader.ConfigValue(
                "log_pms",
                True,
                lambda: "Логировать ли удаления в личных сообщениях",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "log_groups",
                True,
                lambda: "Логировать ли удаления в группах",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "log_self",
                True,
                lambda: "Логировать ли свои собственные сообщения (удаление и редактирование)",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ignored_chats",
                [],
                lambda: "Список ID или usernames игнорируемых чатов/пользователей (ЛС и группы)",
                validator=loader.validators.Series(
                    validator=loader.validators.Union(
                        loader.validators.Integer(), loader.validators.String()
                    )
                )
                if hasattr(loader.validators, "Series")
                else loader.validators.Union(
                    loader.validators.List(), loader.validators.String()
                ),
            ),
            loader.ConfigValue(
                "max_cache",
                2500,
                lambda: "Количество сообщений, хранимых в кэше памяти",
                validator=loader.validators.Integer(minimum=100, maximum=10000),
            ),
        )
        self._cache = {}
        self._order = deque()

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

        try:
            if hasattr(client, "list_event_handlers"):
                handlers = client.list_event_handlers()
                for handler, builder in list(handlers):
                    if getattr(handler, "__name__", "") in ["_on_delete_event", "_on_edit_event"]:
                        client.remove_event_handler(handler, builder)
        except Exception:
            pass

        client.add_event_handler(self._on_delete_event, events.MessageDeleted())
        client.add_event_handler(self._on_edit_event, events.MessageEdited())

    async def on_unload(self):
        try:
            if hasattr(self, "client") and self.client and hasattr(self.client, "list_event_handlers"):
                handlers = self.client.list_event_handlers()
                for handler, builder in list(handlers):
                    if getattr(handler, "__name__", "") in ["_on_delete_event", "_on_edit_event"]:
                        self.client.remove_event_handler(handler, builder)
        except Exception:
            pass

    def _get_ignored_chats(self):
        raw = self.config["ignored_chats"]
        if isinstance(raw, (list, tuple, set)):
            items = list(raw)
        elif isinstance(raw, (int, str)):
            if isinstance(raw, int):
                items = [raw]
            else:
                items = [x.strip() for x in str(raw).split(",") if x.strip()]
        else:
            items = []

        res = []
        for item in items:
            if isinstance(item, int):
                res.append(item)
            elif isinstance(item, str):
                item_str = item.strip()
                if item_str.lstrip("-").isdigit():
                    res.append(int(item_str))
                else:
                    res.append(item_str.lower().lstrip("@"))
        return res

    def _is_chat_ignored(self, chat_id, username=None):
        ignored = self._get_ignored_chats()
        if not ignored:
            return False

        if chat_id in ignored:
            return True

        if username:
            clean_user = username.lower().lstrip("@")
            if clean_user in ignored:
                return True

        return False

    async def watcher(self, message):
        """Сохраняет входящие сообщения в кольцевой кэш"""
        if not hasattr(message, "id") or not hasattr(message, "chat_id") or not message.chat_id:
            return

        # Игнорируем логирование самого лог-чата во избежание рекурсии
        target = self._get_target_chat()
        if target != "me" and message.chat_id == target:
            return

        # Игнорируем чаты и пользователя из списка игнорируемых
        chat_username = None
        if hasattr(message, "chat") and getattr(message.chat, "username", None):
            chat_username = message.chat.username
        if self._is_chat_ignored(message.chat_id, chat_username):
            return

        key = (message.chat_id, message.id)
        if key not in self._cache:
            self._cache[key] = message
            self._order.append(key)

            # Очищаем кэш при переполнении
            max_size = self.config["max_cache"]
            while len(self._order) > max_size:
                old_key = self._order.popleft()
                self._cache.pop(old_key, None)

    async def _get_chat_link(self, msg):
        if msg.is_private:
            user_id = getattr(msg, "chat_id", None)
            if not user_id:
                try:
                    chat = await msg.get_chat()
                    if chat:
                        user_id = getattr(chat, "id", None)
                except Exception:
                    pass

            if not user_id:
                try:
                    sender = await msg.get_sender()
                    if sender:
                        user_id = getattr(sender, "id", None)
                except Exception:
                    pass

            if user_id:
                clean_id = str(abs(user_id))
                return f'<a href="tg://user?id={clean_id}">ЛС</a>'

            return "ЛС"

        try:
            chat = await msg.get_chat()
            title = utils.escape_html(getattr(chat, "title", str(msg.chat_id)))
            username = getattr(chat, "username", None)
            if username:
                return f'<a href="tg://resolve?domain={username}">{title}</a>'

            clean_id = str(msg.chat_id).replace("-100", "").replace("-", "")
            return f'<a href="https://t.me/c/{clean_id}/{msg.id}">{title}</a>'
        except Exception:
            return utils.escape_html(str(msg.chat_id))

    async def _on_edit_event(self, event):
        """Обрабатывает редактирование сообщений Telegram API"""
        msg = getattr(event, "message", event)
        if not hasattr(msg, "id") or not hasattr(msg, "chat_id") or not msg.chat_id:
            return

        target = self._get_target_chat()
        if target != "me" and msg.chat_id == target:
            return

        chat_username = None
        if hasattr(msg, "chat") and getattr(msg.chat, "username", None):
            chat_username = msg.chat.username
        if self._is_chat_ignored(msg.chat_id, chat_username):
            return

        if msg.is_private and not self.config["log_pms"]:
            return
        if not msg.is_private and not self.config["log_groups"]:
            return

        # Фильтрация собственных сообщений
        if not self.config["log_self"]:
            if getattr(msg, "out", False):
                return
            try:
                me = await self.client.get_me()
                if getattr(msg, "sender_id", None) == me.id:
                    return
            except Exception:
                pass

        key = (msg.chat_id, msg.id)
        old_msg = self._cache.get(key)
        self._cache[key] = msg  # Обновляем состояние в кэше

        if not old_msg:
            return

        old_text = getattr(old_msg, "raw_text", None) or getattr(old_msg, "text", "") or ""
        new_text = getattr(msg, "raw_text", None) or getattr(msg, "text", "") or ""

        if not old_text and getattr(old_msg, "media", None):
            old_text = "[Медиафайл]"
        if not new_text and getattr(msg, "media", None):
            new_text = "[Медиафайл]"

        if old_text == new_text:
            return

        try:
            sender = await msg.get_sender()
            sender_name = utils.escape_html(getattr(sender, "first_name", "Неизвестный"))
            sender_id = getattr(sender, "id", "Unknown")
        except Exception:
            sender_name = "Неизвестный"
            sender_id = "Unknown"

        chat_link = await self._get_chat_link(msg)
        sender_str = f'<a href="tg://user?id={sender_id}">{sender_name}</a> [<code>{sender_id}</code>]' if sender_id != "Unknown" else sender_name

        header = (
            f"✏️ <b>Отредактировано сообщение</b>\n"
            f"👤 <b>От:</b> {sender_str} - ({chat_link})"
        )

        formatted_log = (
            f"{header}\n\n"
            f"<b>Изначально:</b>\n{utils.escape_html(old_text)}\n\n"
            f"<b>Итог:</b>\n{utils.escape_html(new_text)}"
        )

        try:
            if getattr(msg, "media", None) and not getattr(old_msg, "media", None):
                await self.client.send_file(
                    target,
                    msg.media,
                    caption=formatted_log[:1024],
                    link_preview=False,
                )
            else:
                await self.client.send_message(target, formatted_log, link_preview=False)
        except Exception as e:
            logger.error(f"Ошибка при логировании редактирования сообщения: {e}")

    async def _on_delete_event(self, event):
        """Обрабатывает удаление сообщений Telegram API"""
        target = self._get_target_chat()
        event_chat_id = event.chat_id

        for msg_id in event.deleted_ids:
            msg = None

            # Если chat_id передан в событии
            if event_chat_id:
                key = (event_chat_id, msg_id)
                msg = self._cache.pop(key, None)
            else:
                # Если chat_id пустой (часто бывает при удалении в ЛС)
                for (c_id, m_id), cached_msg in list(self._cache.items()):
                    if m_id == msg_id:
                        msg = cached_msg
                        self._cache.pop((c_id, m_id), None)
                        break

            if not msg:
                continue

            # Фильтрация игнорируемых чатов (ЛС и группы)
            chat_username = None
            if hasattr(msg, "chat") and getattr(msg.chat, "username", None):
                chat_username = msg.chat.username
            if self._is_chat_ignored(msg.chat_id, chat_username):
                continue

            # Фильтрация ЛС / Группы
            if msg.is_private and not self.config["log_pms"]:
                continue
            if not msg.is_private and not self.config["log_groups"]:
                continue

            # Фильтрация собственных сообщений
            if not self.config["log_self"]:
                if getattr(msg, "out", False):
                    continue
                try:
                    me = await self.client.get_me()
                    if getattr(msg, "sender_id", None) == me.id:
                        continue
                except Exception:
                    pass

            # Получаем отправителя и чат
            try:
                sender = await msg.get_sender()
                sender_name = utils.escape_html(getattr(sender, "first_name", "Неизвестный"))
                sender_id = getattr(sender, "id", "Unknown")
            except Exception:
                sender_name = "Неизвестный"
                sender_id = "Unknown"

            chat_link = await self._get_chat_link(msg)
            sender_str = f'<a href="tg://user?id={sender_id}">{sender_name}</a> [<code>{sender_id}</code>]' if sender_id != "Unknown" else sender_name

            header = (
                f"🗑 <b>Удалено сообщение</b>\n"
                f"👤 <b>От:</b> {sender_str} - ({chat_link})"
            )

            sent_time_str = "Неизвестно"
            if hasattr(msg, "date") and msg.date:
                try:
                    sent_time_str = msg.date.astimezone().strftime("%d.%m.%Y %H:%M:%S")
                except Exception:
                    sent_time_str = msg.date.strftime("%d.%m.%Y %H:%M:%S")

            deleted_time_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

            time_footer = (
                f"\n\n<b>Отправлено:</b> {sent_time_str}\n"
                f"<b>Удалено:</b> {deleted_time_str}"
            )

            try:
                # Если сообщение содержало стикер, файл, войс, фото или видео
                if msg.media:
                    caption = (
                        f"{header}\n💬 <b>Подпись:</b> {utils.escape_html(msg.raw_text)}{time_footer}"
                        if msg.raw_text
                        else f"{header}{time_footer}"
                    )
                    await self.client.send_file(
                        target,
                        msg.media,
                        caption=caption[:1024],
                        link_preview=False,
                    )
                elif msg.raw_text:
                    text = f"{header}\n💬 <b>Текст:</b>\n{utils.escape_html(msg.raw_text)}{time_footer}"
                    await self.client.send_message(target, text, link_preview=False)
            except Exception as e:
                logger.error(f"Ошибка при пересылке удаленного сообщения: {e}")

    def _get_target_chat(self):
        target = self.config["log_chat"]
        if isinstance(target, str) and (target.lstrip("-").isdigit()):
            return int(target)
        return target

    async def _toggle_ignore(self, message, action="toggle"):
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        target_id = None
        display_name = ""

        if args:
            if args.lstrip("-").isdigit():
                target_id = int(args)
                display_name = str(target_id)
            else:
                try:
                    entity = await self.client.get_entity(args)
                    target_id = get_peer_id(entity)
                    title = getattr(entity, "title", None) or getattr(entity, "first_name", None)
                    display_name = f"{title} ({target_id})" if title else str(target_id)
                except Exception:
                    clean_arg = args.lower().lstrip("@")
                    target_id = clean_arg
                    display_name = f"@{clean_arg}"
        elif reply:
            target_id = reply.chat_id
            try:
                chat = await reply.get_chat()
                title = getattr(chat, "title", None) or getattr(chat, "first_name", None)
                display_name = f"{title} ({target_id})" if title else str(target_id)
            except Exception:
                display_name = str(target_id)
        elif message.chat_id:
            target_id = message.chat_id
            try:
                chat = await message.get_chat()
                title = getattr(chat, "title", None) or getattr(chat, "first_name", None)
                display_name = f"{title} ({target_id})" if title else str(target_id)
            except Exception:
                display_name = str(target_id)
        else:
            await utils.answer(message, self.strings("invalid_chat"))
            return

        ignored = self._get_ignored_chats()

        if action == "add":
            if target_id not in ignored:
                ignored.append(target_id)
            is_added = True
        elif action == "remove":
            if target_id in ignored:
                ignored.remove(target_id)
            is_added = False
        else:  # toggle
            if target_id in ignored:
                ignored.remove(target_id)
                is_added = False
            else:
                ignored.append(target_id)
                is_added = True

        self.config["ignored_chats"] = ignored

        if is_added:
            await utils.answer(message, self.strings("ignored_add").format(display_name))
        else:
            await utils.answer(message, self.strings("ignored_remove").format(display_name))

    @loader.command(ru_doc="[ID / @username / reply] — Установить целевой чат для отправки логов")
    async def setlogchat(self, message):
        """[ID / reply] — Set target chat for deleted message logs"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        target_id = None
        if args:
            if args.lstrip("-").isdigit():
                target_id = int(args)
            elif args.lower() in ["me", "self"]:
                target_id = "me"
            else:
                target_id = args
        elif reply:
            target_id = reply.chat_id
        else:
            target_id = message.chat_id

        self.config["log_chat"] = target_id
        await utils.answer(message, self.strings("chat_set").format(target_id))

    @loader.command(ru_doc="[ID / @username / reply] — Добавить или удалить чат/ЛС из списка игнорируемых")
    async def ignorechat(self, message):
        """[ID / @username / reply] — Add or remove a chat/PM from ignored list"""
        await self._toggle_ignore(message, action="toggle")

    @loader.command(ru_doc="[ID / @username / reply] — Добавить или удалить чат/ЛС из списка игнорируемых")
    async def ignore_chat(self, message):
        """[ID / @username / reply] — Add or remove a chat/PM from ignored list"""
        await self._toggle_ignore(message, action="toggle")

    @loader.command(ru_doc="[ID / @username / reply] — Удалить чат/ЛС из списка игнорируемых")
    async def delignorechat(self, message):
        """[ID / @username / reply] — Remove a chat/PM from ignored list"""
        await self._toggle_ignore(message, action="remove")

    @loader.command(ru_doc="Показать список игнорируемых чатов")
    async def ignorelist(self, message):
        """Show list of ignored chats"""
        ignored = self._get_ignored_chats()
        if not ignored:
            await utils.answer(message, self.strings("ignored_empty"))
            return

        res = [f"• <code>{item}</code>" for item in ignored]
        await utils.answer(
            message,
            self.strings("ignored_list").format("\n".join(res)),
        )

    @loader.command(ru_doc="Переключить перехват удалений в личных сообщениях")
    async def togglepmlog(self, message):
        """Toggle logging deletions in PMs"""
        new_state = not self.config["log_pms"]
        self.config["log_pms"] = new_state
        state_str = "<b>ВКЛ</b> ✅" if new_state else "<b>ВЫКЛ</b> ❌"
        await utils.answer(message, self.strings("toggle_pm").format(state_str))

    @loader.command(ru_doc="Переключить перехват удалений в группах")
    async def togglegrouplog(self, message):
        """Toggle logging deletions in groups"""
        new_state = not self.config["log_groups"]
        self.config["log_groups"] = new_state
        state_str = "<b>ВКЛ</b> ✅" if new_state else "<b>ВЫКЛ</b> ❌"
        await utils.answer(message, self.strings("toggle_group").format(state_str))

    @loader.command(ru_doc="Переключить логирование собственных сообщений")
    async def togglelogself(self, message):
        """Toggle logging self messages"""
        new_state = not self.config["log_self"]
        self.config["log_self"] = new_state
        state_str = "<b>ВКЛ</b> ✅" if new_state else "<b>ВЫКЛ</b> ❌"
        await utils.answer(message, self.strings("toggle_self").format(state_str))

    @loader.command(ru_doc="Показать статус и текущие настройки логгера")
    async def logstatus(self, message):
        """Show current configuration status"""
        await utils.answer(
            message,
            self.strings("status").format(
                self.config["log_chat"],
                "✅" if self.config["log_pms"] else "❌",
                "✅" if self.config["log_groups"] else "❌",
                "✅" if self.config["log_self"] else "❌",
                len(self._get_ignored_chats()),
                len(self._order),
            ),
        )
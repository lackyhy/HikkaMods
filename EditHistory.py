# meta developer: @lackyhyyy666
# scope: hikka_only
# scope: hikka_min 1.6.2

import html
import logging
import re
from telethon import events, types
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class EditHistoryMod(loader.Module):
    """Модуль для отслеживания истории редактирования сообщений (.edits). Выводит исходные сообщения и все редакции."""

    strings = {
        "name": "EditHistory",
        "no_reply": "<b>⚠️ Ответьте на отредактированное сообщение командой <code>.edits</code>!</b>",
        "no_history": (
            "<b>⚠️ История изменений этого сообщения не найдена.</b>\n"
            "<i>(Сообщение не редактировалось при боте или было отправлено до загрузки модуля)</i>"
        ),
        "no_edits": (
            "<b>ℹ️ Для этого сообщения зафиксирована только 1 версия.</b>\n"
            "<i>(Сообщение либо не редактировалось, либо изменение произошло до загрузки модуля)</i>"
        ),
        "access_denied": "<b>❌ У вас нет доступа к использованию этой команды.</b>",
        "cleared": "<b>🗑 История измененных сообщений очищена.</b>",
        "stats": "<b>📊 Зафиксировано сообщений в истории:</b> <code>{}</code>",
        "config_allowed_users": "ID пользователей через запятую или пробел, которым разрешено использовать .edits",
        "config_max_cache": "Максимальное количество сообщений в памяти для истории изменений",
        "config_ignore_bots": "Игнорировать редактирования сообщений от ботов",
    }

    strings_ru = {
        "no_reply": "<b>⚠️ Ответьте на отредактированное сообщение командой <code>.edits</code>!</b>",
        "no_history": (
            "<b>⚠️ История изменений этого сообщения не найдена.</b>\n"
            "<i>(Сообщение не редактировалось при боте или было отправлено до загрузки модуля)</i>"
        ),
        "no_edits": (
            "<b>ℹ️ Для этого сообщения зафиксирована только 1 версия.</b>\n"
            "<i>(Сообщение либо не редактировалось, либо изменение произошло до загрузки модуля)</i>"
        ),
        "access_denied": "<b>❌ У вас нет доступа к использованию этой команды.</b>",
        "cleared": "<b>🗑 История измененных сообщений очищена.</b>",
        "stats": "<b>📊 Зафиксировано сообщений в истории:</b> <code>{}</code>",
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
                "max_cache",
                3000,
                lambda: self.strings("config_max_cache"),
                validator=loader.validators.Integer(minimum=100, maximum=20000),
            ),
            loader.ConfigValue(
                "ignore_bots",
                True,
                lambda: self.strings("config_ignore_bots"),
                validator=loader.validators.Boolean(),
            ),
        )
        self._history = {}
        self._registered_events = False

    async def client_ready(self, client, db):
        self._client = client
        if not self._registered_events:
            client.add_event_handler(self._on_message_event, events.NewMessage)
            client.add_event_handler(self._on_message_event, events.MessageEdited)
            self._registered_events = True

    def _is_allowed(self, message) -> bool:
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

    async def _on_message_event(self, event):
        """Хэндлер для новых и отредактированных сообщений (Telethon events)"""
        try:
            message = getattr(event, "message", event)
            if not isinstance(message, types.Message):
                return

            chat_id = getattr(message, "chat_id", None)
            msg_id = getattr(message, "id", None)
            if not chat_id or not msg_id:
                return

            sender = getattr(message, "sender", None)
            if self.config["ignore_bots"] and sender and getattr(sender, "bot", False):
                return

            text = message.raw_text or message.text or ""
            if not text and getattr(message, "media", None):
                text = "[Медиафайл]"

            if not text:
                return

            dt = getattr(message, "edit_date", None) or getattr(message, "date", None)
            date_str = dt.strftime("%H:%M:%S") if dt else ""

            msg_key = (chat_id, msg_id)

            if msg_key not in self._history:
                self._history[msg_key] = [{
                    "text": text,
                    "date": date_str,
                }]
            else:
                last_entry = self._history[msg_key][-1]
                if last_entry["text"] != text:
                    self._history[msg_key].append({
                        "text": text,
                        "date": date_str,
                    })

            try:
                max_cache = int(self.config["max_cache"])
            except (ValueError, TypeError):
                max_cache = 3000

            if len(self._history) > max_cache:
                first_key = next(iter(self._history))
                del self._history[first_key]

        except Exception as e:
            logger.error(f"[EditHistory] Error in _on_message_event: {e}")

    @loader.watcher()
    async def watcher(self, message: types.Message):
        """Отслеживает команды .edits / .eh от сторонних разрешенных пользователей"""
        if not isinstance(message, types.Message) or getattr(message, "out", False):
            return

        text = message.raw_text or message.text or ""
        if not text:
            return

        raw_t = text.strip()
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
            if raw_t.startswith(p):
                matched_prefix = p
                break

        if not matched_prefix:
            return

        cmd_body = raw_t[len(matched_prefix):].strip()
        cmd_name = cmd_body.split()[0].lower() if cmd_body else ""
        if cmd_name in ("edits", "eh", "history", "edited"):
            if self._is_allowed(message):
                await self._show_edits(message)

    @loader.command(
        ru_doc="<реплай> — Показать историю редактирования сообщения (1, 2, 3... итог)",
        en_doc="<reply> — Show message edit history (1, 2, 3... result)",
    )
    async def editscmd(self, message: types.Message):
        """<reply> — Show message edit history"""
        if not self._is_allowed(message):
            await utils.answer(message, self.strings("access_denied"))
            return
        await self._show_edits(message)

    @loader.command(
        ru_doc="<реплай> — Показать историю редактирования сообщения (алиас)",
        en_doc="<reply> — Show message edit history (alias)",
    )
    async def ehcmd(self, message: types.Message):
        """<reply> — Show message edit history"""
        if not self._is_allowed(message):
            await utils.answer(message, self.strings("access_denied"))
            return
        await self._show_edits(message)

    @loader.command(
        ru_doc="— Очистить сохраненную историю редактирования сообщений",
        en_doc="— Clear stored edit history cache",
    )
    async def cleareditscmd(self, message: types.Message):
        """— Clear stored edit history cache"""
        self._history.clear()
        await utils.answer(message, self.strings("cleared"))

    @loader.command(
        ru_doc="— Показать количество отслеживаемых сообщений в памяти",
        en_doc="— Show number of tracked messages in memory",
    )
    async def editstatscmd(self, message: types.Message):
        """— Show number of tracked messages in memory"""
        await utils.answer(message, self.strings("stats").format(len(self._history)))

    async def _show_edits(self, message: types.Message):
        """Показывает историю версий исходного сообщения"""
        reply = await message.get_reply_message() if message.is_reply else None
        if not reply:
            await utils.answer(message, self.strings("no_reply"))
            return

        msg_key = (reply.chat_id, reply.id)

        if msg_key not in self._history:
            await utils.answer(message, self.strings("no_history"))
            return

        history_list = self._history[msg_key]

        if len(history_list) <= 1:
            await utils.answer(message, self.strings("no_edits"))
            return

        previous_versions = history_list[:-1]
        final_version = history_list[-1]

        lines = [""]

        for idx, entry in enumerate(previous_versions, 1):
            time_str = f"<i>[{entry['date']}]</i> " if entry.get("date") else ""
            safe_text = html.escape(entry["text"])
            lines.append(f"<b>{idx})</b> {time_str}<code>{safe_text}</code>")

        final_text = html.escape(final_version["text"])
        lines.append(f"\n<b>Итог:</b> <code>{final_text}</code>")

        res = "\n".join(lines)
        await utils.answer(message, res)

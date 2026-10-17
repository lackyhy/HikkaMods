# meta developer: @lackyhyyy666
# scope: hikka_only
# scope: hikka_min 1.6.0

import logging
import math
import re
import time

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class NotesMod(loader.Module):
    """Заметки: создание, просмотр, редактирование, удаление, поиск и напоминания"""

    strings = {
        "name": "Notes",
        "no_args": "❌ <b>Не указано имя заметки.</b>",
        "no_text": "❌ <b>Нет текста.</b> Напиши его после имени или ответь на сообщение.",
        "not_found": "❌ <b>Заметка</b> <code>{}</code> <b>не найдена.</b>",
        "exists": "❌ <b>Заметка</b> <code>{}</code> <b>уже существует.</b> Используй <code>.nedit</code>.",
        "added": "✅ <b>Заметка</b> <code>{}</code> <b>создана.</b>",
        "edited": "✏️ <b>Заметка</b> <code>{}</code> <b>изменена.</b>",
        "appended": "➕ <b>Текст добавлен в заметку</b> <code>{}</code>.",
        "renamed": "🔁 <b>Заметка</b> <code>{}</code> <b>→</b> <code>{}</code>",
        "deleted": "🗑 <b>Заметка</b> <code>{}</code> <b>удалена.</b>",
        "rename_args": "❌ <b>Формат:</b> <code>.nren старое новое</code>",
        "empty": "📭 <b>Заметок пока нет.</b> Создай первую: <code>.nadd имя текст</code>",
        "list_head": "📒 <b>Твои заметки ({}):</b>\n\n",
        "list_item": "• <code>{}</code>{} — {}\n",
        "show": "📝 <b>{}</b>\n\n{}\n\n<i>Создана: {}\nИзменена: {}</i>",
        "show_remind": "\n<i>⏰ Напоминание: {}</i>",
        "no_query": "❌ <b>Укажи, что искать.</b>",
        "find_head": "🔎 <b>Найдено ({}):</b>\n\n",
        "find_none": "🔎 <b>Ничего не найдено.</b>",
        "clear_confirm": "⚠️ <b>Это удалит все заметки ({}).</b>\nПодтверди: <code>.nclear да</code>",
        "cleared": "🧹 <b>Все заметки удалены.</b>",
        "remind_set": "⏰ <b>Напомню о</b> <code>{}</code> <b>в {}</b> (через {}).",
        "remind_off": "🔕 <b>Напоминание для</b> <code>{}</code> <b>отменено.</b>",
        "remind_none": "ℹ️ <b>У заметки</b> <code>{}</code> <b>нет напоминания.</b>",
        "remind_bad_time": (
            "❌ <b>Не понял время.</b> Примеры: <code>30m</code>, <code>2h</code>, "
            "<code>1h30m</code>, <code>1d</code> (число без единиц — минуты)"
        ),
        "reminds_head": "⏰ <b>Активные напоминания ({}):</b>\n\n",
        "reminds_item": "• <code>{}</code> — {} (через {})\n",
        "reminds_empty": "⏰ <b>Активных напоминаний нет.</b>",
        "remind_msg": "⏰ <b>Напоминание:</b> <code>{}</code>\n\n{}",
        "remind_snoozed": "\n\n<i>🔁 Напомню снова в {}</i>",
        "remind_stopped": "\n\n<i>🛑 Напоминание остановлено</i>",
        "remind_gone": "❌ <b>Заметка уже удалена.</b>",
        "ui_head": "📒 <b>Заметки ({})</b>\n",
        "ui_query": "🔎 <i>Поиск:</i> <code>{}</code>\n",
        "ui_empty": "\n📭 <i>Ничего нет. Нажми «Создать».</i>",
        "ui_hint": "\n<i>Выбери заметку:</i>",
        "ui_add_ph": "Введи: имя текст",
        "ui_search_ph": "Что искать?",
        "ui_edit_ph": "Новый текст заметки",
        "ui_append_ph": "Текст, который нужно дописать",
        "ui_rename_ph": "Новое имя (одно слово)",
        "ui_remind_ph": "Через сколько? Например: 30m, 2h, 1d",
        "ui_del_ask": "🗑 <b>Удалить заметку</b> <code>{}</code><b>?</b>",
        "ui_clear_ask": "⚠️ <b>Удалить все заметки ({})?</b> Это нельзя отменить.",
        "ui_add_fmt": "❌ Формат: имя текст",
        "ui_gone": "❌ Заметка не найдена",
        "ui_empty_text": "❌ Пустой текст",
        "ui_one_word": "❌ Нужно одно слово",
        "ui_bad_time": "❌ Не понял время. Примеры: 30m, 2h, 1h30m, 1d",
        "ui_remind_set": "⏰ Напомню в {}",
        "ui_remind_off": "🔕 Напоминание отменено",
        "help": (
            "📒 <b>Заметки</b>\n\n"
            "<code>.notes</code> — меню с кнопками\n"
            "<code>.nadd имя текст</code> — создать (или ответом на сообщение)\n"
            "<code>.nshow имя</code> — показать\n"
            "<code>.nlist</code> — список\n"
            "<code>.nedit имя текст</code> — заменить текст\n"
            "<code>.nappend имя текст</code> — дописать в конец\n"
            "<code>.nren старое новое</code> — переименовать\n"
            "<code>.ndel имя</code> — удалить\n"
            "<code>.nfind запрос</code> — поиск\n"
            "<code>.nclear да</code> — удалить все\n\n"
            "⏰ <b>Напоминания</b> (приходят в Избранное)\n"
            "<code>.nremind имя [время]</code> — напомнить (по умолчанию — из настроек)\n"
            "<code>.nunremind имя</code> — отменить напоминание\n"
            "<code>.nreminds</code> — активные напоминания\n"
            "<i>Время: 30m, 2h, 1h30m, 1d. Настройки: .cfg Notes</i>"
        ),
    }

    # минуты в одной единице времени
    _UNITS = {
        "": 1,
        "m": 1,
        "min": 1,
        "м": 1,
        "мин": 1,
        "h": 60,
        "ч": 60,
        "d": 1440,
        "д": 1440,
    }
    _MAX_MINUTES = 366 * 1440

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "remind_delay",
                60,
                lambda: "Через сколько минут напоминать по умолчанию (.nremind без времени и кнопка «Напомнить»)",
                validator=loader.validators.Integer(minimum=1, maximum=self._MAX_MINUTES),
            ),
            loader.ConfigValue(
                "snooze_buttons",
                [60, 30],
                lambda: "Кнопки повтора в напоминании, в минутах (например 60 → «+1ч», 30 → «+30мин»)",
                validator=loader.validators.Series(
                    validator=loader.validators.Integer(
                        minimum=1, maximum=self._MAX_MINUTES
                    )
                ),
            ),
            loader.ConfigValue(
                "auto_remind",
                False,
                lambda: "Автоматически ставить напоминание (через remind_delay) на каждую новую заметку",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timezone",
                "",
                lambda: "Твой часовой пояс относительно UTC для отображения времени: +3, -5, +5:30. Пусто — время сервера",
                validator=loader.validators.String(),
            ),
        )

    # ---------- helpers ----------

    def _notes(self) -> dict:
        return self.get("notes", {})

    def _save(self, notes: dict):
        self.set("notes", notes)

    @staticmethod
    def _key(name: str) -> str:
        return name.lower()

    def _tz_offset(self):
        """Смещение из конфига в секундах; None — использовать время сервера."""
        raw = str(self.config["timezone"] or "").upper().replace(" ", "")
        raw = raw.replace("UTC", "").replace("GMT", "")
        match = re.fullmatch(r"([+-]?)(\d{1,2})(?::(\d{2}))?", raw)
        if not match:
            return None

        hours, mins = int(match.group(2)), int(match.group(3) or 0)
        if hours > 14 or mins >= 60:
            return None
        return (-1 if match.group(1) == "-" else 1) * (hours * 3600 + mins * 60)

    def _fmt_time(self, ts: float) -> str:
        offset = self._tz_offset()
        moment = time.localtime(ts) if offset is None else time.gmtime(ts + offset)
        return time.strftime("%d.%m.%Y %H:%M", moment)

    @staticmethod
    def _fmt_delta(minutes: int) -> str:
        days, rest = divmod(max(0, int(minutes)), 1440)
        hours, mins = divmod(rest, 60)
        parts = []
        if days:
            parts.append(f"{days}д")
        if hours:
            parts.append(f"{hours}ч")
        if mins or not parts:
            parts.append(f"{mins}мин")
        return " ".join(parts)

    @staticmethod
    def _minutes_left(ts: float) -> int:
        return max(0, math.ceil((ts - time.time()) / 60))

    @classmethod
    def _parse_minutes(cls, raw: str):
        """'1h30m' / '2ч' / '45' → минуты; None, если формат не распознан."""
        raw = (raw or "").lower().replace(" ", "")
        if not raw:
            return None

        pos, total = 0, 0
        for match in re.finditer(r"(\d+)([a-zа-яё]*)", raw):
            if match.start() != pos:
                return None
            unit = cls._UNITS.get(match.group(2))
            if unit is None:
                return None
            total += int(match.group(1)) * unit
            pos = match.end()

        if pos != len(raw) or not 0 < total <= cls._MAX_MINUTES:
            return None
        return total

    @staticmethod
    def _preview(text: str, limit: int = 40) -> str:
        line = " ".join(text.split())
        if len(line) > limit:
            line = line[: limit - 1] + "…"
        return utils.escape_html(line)

    @staticmethod
    def _body(text: str, limit: int = 3200) -> str:
        # Обрезаем до экранирования, чтобы не разрезать HTML-сущность вроде &amp;
        if len(text) > limit:
            text = text[:limit] + "…"
        return utils.escape_html(text)

    def _list_line(self, note: dict) -> str:
        return self.strings["list_item"].format(
            utils.escape_html(note["name"]),
            " ⏰" if note.get("remind_at") else "",
            self._preview(note["text"]),
        )

    def _show_text(self, note: dict, body: str) -> str:
        text = self.strings["show"].format(
            utils.escape_html(note["name"]),
            body,
            self._fmt_time(note["created"]),
            self._fmt_time(note["updated"]),
        )
        if note.get("remind_at"):
            text += self.strings["show_remind"].format(
                self._fmt_time(note["remind_at"])
            )
        return text

    def _new_note(self, name: str, text: str) -> dict:
        now = time.time()
        note = {"name": name, "text": text, "created": now, "updated": now}
        if self.config["auto_remind"]:
            note["remind_at"] = now + self.config["remind_delay"] * 60
        return note

    def _set_remind(self, key: str, minutes: int):
        notes = self._notes()
        if key not in notes:
            return None
        at = time.time() + minutes * 60
        notes[key]["remind_at"] = at
        self._save(notes)
        return at

    def _clear_remind(self, key: str) -> bool:
        notes = self._notes()
        if key not in notes or not notes[key].pop("remind_at", None):
            return False
        self._save(notes)
        return True

    async def _parse(self, message, need_text: bool = True):
        """Возвращает (имя, текст). Текст берётся из аргументов или из реплая."""
        raw = utils.get_args_raw(message)
        parts = raw.split(maxsplit=1) if raw else []
        name = parts[0] if parts else None
        text = parts[1] if len(parts) > 1 else None

        if need_text and text is None:
            reply = await message.get_reply_message()
            if reply and (reply.raw_text or "").strip():
                text = reply.raw_text

        return name, text

    # ---------- commands ----------

    async def nhelpcmd(self, message):
        """— Список команд модуля"""
        await utils.answer(message, self.strings["help"])

    async def naddcmd(self, message):
        """<имя> <текст> — Создать заметку (текст можно взять из реплая)"""
        name, text = await self._parse(message)
        if not name:
            return await utils.answer(message, self.strings["no_args"])
        if not text:
            return await utils.answer(message, self.strings["no_text"])

        notes = self._notes()
        key = self._key(name)
        if key in notes:
            return await utils.answer(
                message, self.strings["exists"].format(utils.escape_html(name))
            )

        notes[key] = self._new_note(name, text)
        self._save(notes)
        await utils.answer(
            message, self.strings["added"].format(utils.escape_html(name))
        )

    async def nshowcmd(self, message):
        """<имя> — Показать заметку"""
        name, _ = await self._parse(message, need_text=False)
        if not name:
            return await utils.answer(message, self.strings["no_args"])

        note = self._notes().get(self._key(name))
        if not note:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )

        await utils.answer(
            message, self._show_text(note, utils.escape_html(note["text"]))
        )

    async def nlistcmd(self, message):
        """— Список всех заметок"""
        notes = self._notes()
        if not notes:
            return await utils.answer(message, self.strings["empty"])

        out = self.strings["list_head"].format(len(notes))
        for note in sorted(notes.values(), key=lambda n: n["name"].lower()):
            out += self._list_line(note)
        await utils.answer(message, out)

    async def neditcmd(self, message):
        """<имя> <новый текст> — Заменить текст заметки (или ответом на сообщение)"""
        name, text = await self._parse(message)
        if not name:
            return await utils.answer(message, self.strings["no_args"])

        notes = self._notes()
        key = self._key(name)
        if key not in notes:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )
        if not text:
            return await utils.answer(message, self.strings["no_text"])

        notes[key]["text"] = text
        notes[key]["updated"] = time.time()
        self._save(notes)
        await utils.answer(
            message,
            self.strings["edited"].format(utils.escape_html(notes[key]["name"])),
        )

    async def nappendcmd(self, message):
        """<имя> <текст> — Дописать текст в конец заметки"""
        name, text = await self._parse(message)
        if not name:
            return await utils.answer(message, self.strings["no_args"])

        notes = self._notes()
        key = self._key(name)
        if key not in notes:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )
        if not text:
            return await utils.answer(message, self.strings["no_text"])

        notes[key]["text"] += "\n" + text
        notes[key]["updated"] = time.time()
        self._save(notes)
        await utils.answer(
            message,
            self.strings["appended"].format(utils.escape_html(notes[key]["name"])),
        )

    async def nrencmd(self, message):
        """<старое> <новое> — Переименовать заметку"""
        raw = utils.get_args_raw(message).split()
        if len(raw) != 2:
            return await utils.answer(message, self.strings["rename_args"])

        old, new = raw
        notes = self._notes()
        old_key, new_key = self._key(old), self._key(new)

        if old_key not in notes:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(old))
            )
        if new_key in notes and new_key != old_key:
            return await utils.answer(
                message, self.strings["exists"].format(utils.escape_html(new))
            )

        note = notes.pop(old_key)
        note["name"] = new
        note["updated"] = time.time()
        notes[new_key] = note
        self._save(notes)
        await utils.answer(
            message,
            self.strings["renamed"].format(
                utils.escape_html(old), utils.escape_html(new)
            ),
        )

    async def ndelcmd(self, message):
        """<имя> — Удалить заметку"""
        name, _ = await self._parse(message, need_text=False)
        if not name:
            return await utils.answer(message, self.strings["no_args"])

        notes = self._notes()
        key = self._key(name)
        if key not in notes:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )

        removed = notes.pop(key)
        self._save(notes)
        await utils.answer(
            message,
            self.strings["deleted"].format(utils.escape_html(removed["name"])),
        )

    async def nfindcmd(self, message):
        """<запрос> — Поиск по именам и тексту заметок"""
        query = utils.get_args_raw(message).strip().lower()
        if not query:
            return await utils.answer(message, self.strings["no_query"])

        found = [
            n
            for n in self._notes().values()
            if query in n["name"].lower() or query in n["text"].lower()
        ]
        if not found:
            return await utils.answer(message, self.strings["find_none"])

        out = self.strings["find_head"].format(len(found))
        for note in sorted(found, key=lambda n: n["name"].lower()):
            out += self._list_line(note)
        await utils.answer(message, out)

    async def nclearcmd(self, message):
        """да — Удалить ВСЕ заметки (нужно подтверждение)"""
        notes = self._notes()
        if not notes:
            return await utils.answer(message, self.strings["empty"])

        if utils.get_args_raw(message).strip().lower() not in ("да", "yes", "confirm"):
            return await utils.answer(
                message, self.strings["clear_confirm"].format(len(notes))
            )

        self._save({})
        await utils.answer(message, self.strings["cleared"])

    # ---------- reminders ----------

    async def nremindcmd(self, message):
        """<имя> [время] — Напомнить о заметке в Избранном (30m, 2h, 1h30m, 1d)"""
        parts = utils.get_args_raw(message).split(maxsplit=1)
        if not parts:
            return await utils.answer(message, self.strings["no_args"])

        name = parts[0]
        key = self._key(name)
        if key not in self._notes():
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )

        if len(parts) > 1:
            minutes = self._parse_minutes(parts[1])
            if minutes is None:
                return await utils.answer(message, self.strings["remind_bad_time"])
        else:
            minutes = self.config["remind_delay"]

        at = self._set_remind(key, minutes)
        await utils.answer(
            message,
            self.strings["remind_set"].format(
                utils.escape_html(self._notes()[key]["name"]),
                self._fmt_time(at),
                self._fmt_delta(minutes),
            ),
        )

    async def nunremindcmd(self, message):
        """<имя> — Отменить напоминание для заметки"""
        name, _ = await self._parse(message, need_text=False)
        if not name:
            return await utils.answer(message, self.strings["no_args"])

        key = self._key(name)
        note = self._notes().get(key)
        if not note:
            return await utils.answer(
                message, self.strings["not_found"].format(utils.escape_html(name))
            )

        name = utils.escape_html(note["name"])
        if not self._clear_remind(key):
            return await utils.answer(message, self.strings["remind_none"].format(name))
        await utils.answer(message, self.strings["remind_off"].format(name))

    async def nremindscmd(self, message):
        """— Список активных напоминаний"""
        active = sorted(
            (n for n in self._notes().values() if n.get("remind_at")),
            key=lambda n: n["remind_at"],
        )
        if not active:
            return await utils.answer(message, self.strings["reminds_empty"])

        out = self.strings["reminds_head"].format(len(active))
        for note in active:
            out += self.strings["reminds_item"].format(
                utils.escape_html(note["name"]),
                self._fmt_time(note["remind_at"]),
                self._fmt_delta(self._minutes_left(note["remind_at"])),
            )
        await utils.answer(message, out)

    @loader.loop(interval=20, autostart=True)
    async def reminder_loop(self):
        notes = self._notes()
        now = time.time()
        due = [k for k, n in notes.items() if n.get("remind_at") and n["remind_at"] <= now]
        if not due:
            return

        # Снимаем напоминания до отправки, чтобы не прислать их дважды
        for key in due:
            notes[key].pop("remind_at", None)
        self._save(notes)

        for key in due:
            try:
                await self.inline.form(
                    text=self._remind_text(notes[key]),
                    message=self._tg_id,
                    reply_markup=self._remind_markup(key),
                )
            except Exception:
                logger.exception("Notes: не удалось отправить напоминание %s", key)

    def _remind_text(self, note: dict) -> str:
        return self.strings["remind_msg"].format(
            utils.escape_html(note["name"]), self._body(note["text"], 3000)
        )

    def _remind_markup(self, key: str) -> list:
        markup = []
        snooze = [
            {
                "text": "+" + self._fmt_delta(minutes),
                "callback": self._remind_snooze,
                "args": (key, minutes),
            }
            for minutes in list(self.config["snooze_buttons"])[:4]
        ]
        if snooze:
            markup.append(snooze)
        markup.append(
            [{"text": "🛑 Остановить", "callback": self._remind_stop, "args": (key,)}]
        )
        return markup

    async def _remind_snooze(self, call, key, minutes):
        at = self._set_remind(key, minutes)
        if at is None:
            return await self._remind_gone(call)

        await call.answer(self.strings["ui_remind_set"].format(self._fmt_time(at)))
        await call.edit(
            text=self._remind_text(self._notes()[key])
            + self.strings["remind_snoozed"].format(self._fmt_time(at)),
            reply_markup=[
                [{"text": "🛑 Остановить", "callback": self._remind_stop, "args": (key,)}]
            ],
        )

    async def _remind_stop(self, call, key):
        note = self._notes().get(key)
        if not note:
            return await self._remind_gone(call)

        self._clear_remind(key)
        await call.answer(self.strings["ui_remind_off"])
        await call.edit(
            text=self._remind_text(note) + self.strings["remind_stopped"],
            reply_markup=[[{"text": "🗑 Закрыть", "action": "close"}]],
        )

    async def _remind_gone(self, call):
        await call.answer(self.strings["ui_gone"], show_alert=True)
        await call.edit(
            text=self.strings["remind_gone"],
            reply_markup=[[{"text": "🗑 Закрыть", "action": "close"}]],
        )

    # ---------- inline UI (.notes) ----------

    PAGE_SIZE = 8

    async def notescmd(self, message):
        """— Открыть меню заметок с кнопками"""
        text, markup = self._menu()
        await self.inline.form(text=text, message=message, reply_markup=markup)

    def _filtered(self, query=None):
        notes = sorted(self._notes().values(), key=lambda n: n["name"].lower())
        if query:
            q = query.lower()
            notes = [
                n for n in notes if q in n["name"].lower() or q in n["text"].lower()
            ]
        return notes

    def _menu(self, page: int = 0, query=None):
        notes = self._filtered(query)
        total = len(notes)
        pages = max(1, -(-total // self.PAGE_SIZE))
        page = max(0, min(page, pages - 1))
        chunk = notes[page * self.PAGE_SIZE : (page + 1) * self.PAGE_SIZE]

        text = self.strings["ui_head"].format(total)
        if query:
            text += self.strings["ui_query"].format(utils.escape_html(query))
        text += self.strings["ui_hint"] if chunk else self.strings["ui_empty"]

        markup, row = [], []
        for n in chunk:
            row.append(
                {
                    "text": ("⏰ " if n.get("remind_at") else "📝 ") + n["name"][:20],
                    "callback": self._open,
                    "args": (self._key(n["name"]), page, query),
                }
            )
            if len(row) == 2:
                markup.append(row)
                row = []
        if row:
            markup.append(row)

        if pages > 1:
            nav = []
            if page > 0:
                nav.append(
                    {"text": "⬅️", "callback": self._page, "args": (page - 1, query)}
                )
            nav.append({"text": f"{page + 1}/{pages}", "callback": self._noop})
            if page < pages - 1:
                nav.append(
                    {"text": "➡️", "callback": self._page, "args": (page + 1, query)}
                )
            markup.append(nav)

        markup.append(
            [
                {
                    "text": "➕ Создать",
                    "input": self.strings["ui_add_ph"],
                    "handler": self._add_input,
                    "args": (query,),
                },
                {
                    "text": "🔎 Поиск",
                    "input": self.strings["ui_search_ph"],
                    "handler": self._search_input,
                },
            ]
        )
        if query:
            markup.append(
                [{"text": "✖️ Сбросить поиск", "callback": self._page, "args": (0, None)}]
            )
        markup.append(
            [
                {"text": "🧹 Очистить всё", "callback": self._clear_ask},
                {"text": "❌ Закрыть", "action": "close"},
            ]
        )
        return text, markup

    def _view(self, key: str, page: int, query):
        note = self._notes()[key]
        text = self._show_text(note, self._body(note["text"]))
        args = (key, page, query)

        if note.get("remind_at"):
            remind_row = [
                {"text": "🔕 Отменить напоминание", "callback": self._unremind_cb, "args": args}
            ]
        else:
            remind_row = [
                {
                    "text": "⏰ Через " + self._fmt_delta(self.config["remind_delay"]),
                    "callback": self._remind_cb,
                    "args": args,
                },
                {
                    "text": "🕒 Своё время",
                    "input": self.strings["ui_remind_ph"],
                    "handler": self._remind_input,
                    "args": args,
                },
            ]

        markup = [
            [
                {
                    "text": "✏️ Изменить",
                    "input": self.strings["ui_edit_ph"],
                    "handler": self._edit_input,
                    "args": args,
                },
                {
                    "text": "➕ Дописать",
                    "input": self.strings["ui_append_ph"],
                    "handler": self._append_input,
                    "args": args,
                },
            ],
            [
                {
                    "text": "🔁 Переименовать",
                    "input": self.strings["ui_rename_ph"],
                    "handler": self._rename_input,
                    "args": args,
                },
                {"text": "🗑 Удалить", "callback": self._del_ask, "args": args},
            ],
            remind_row,
            [{"text": "⬅️ Назад", "callback": self._page, "args": (page, query)}],
        ]
        return text, markup

    # notice — строка статуса над сообщением. Нужна для inline-ввода:
    # у него нет callback-запроса, поэтому call.answer() там не работает.

    async def _show_menu(self, call, page=0, query=None, notice=None):
        text, markup = self._menu(page, query)
        if notice:
            text = f"{notice}\n\n{text}"
        await call.edit(text=text, reply_markup=markup)

    async def _show_view(self, call, key, page, query, notice=None):
        if key not in self._notes():
            return await self._show_menu(call, page, query, self.strings["ui_gone"])
        text, markup = self._view(key, page, query)
        if notice:
            text = f"{notice}\n\n{text}"
        await call.edit(text=text, reply_markup=markup)

    # ----- callbacks -----

    async def _noop(self, call):
        await call.answer()

    async def _page(self, call, page, query):
        await self._show_menu(call, page, query)

    async def _open(self, call, key, page, query):
        await self._show_view(call, key, page, query)

    async def _remind_cb(self, call, key, page, query):
        at = self._set_remind(key, self.config["remind_delay"])
        if at is not None:
            await call.answer(self.strings["ui_remind_set"].format(self._fmt_time(at)))
        await self._show_view(call, key, page, query)

    async def _unremind_cb(self, call, key, page, query):
        if self._clear_remind(key):
            await call.answer(self.strings["ui_remind_off"])
        await self._show_view(call, key, page, query)

    # ----- inline inputs -----

    async def _add_input(self, call, value, query):
        parts = (value or "").split(maxsplit=1)
        if len(parts) < 2:
            return await self._show_menu(call, 0, query, self.strings["ui_add_fmt"])

        name, text = parts
        notes = self._notes()
        key = self._key(name)
        if key in notes:
            return await self._show_menu(
                call, 0, query, f"❌ «{utils.escape_html(name)}» уже существует"
            )

        notes[key] = self._new_note(name, text)
        self._save(notes)
        await self._show_view(call, key, 0, query, "✅ Создана")

    async def _search_input(self, call, value):
        query = (value or "").strip() or None
        await self._show_menu(call, 0, query)

    async def _edit_input(self, call, value, key, page, query):
        notes = self._notes()
        if key not in notes:
            return await self._show_view(call, key, page, query)
        if not (value or "").strip():
            return await self._show_view(
                call, key, page, query, self.strings["ui_empty_text"]
            )

        notes[key]["text"] = value
        notes[key]["updated"] = time.time()
        self._save(notes)
        await self._show_view(call, key, page, query, "✏️ Изменена")

    async def _append_input(self, call, value, key, page, query):
        notes = self._notes()
        if key not in notes:
            return await self._show_view(call, key, page, query)
        if not (value or "").strip():
            return await self._show_view(
                call, key, page, query, self.strings["ui_empty_text"]
            )

        notes[key]["text"] += "\n" + value
        notes[key]["updated"] = time.time()
        self._save(notes)
        await self._show_view(call, key, page, query, "➕ Добавлено")

    async def _rename_input(self, call, value, key, page, query):
        notes = self._notes()
        if key not in notes:
            return await self._show_view(call, key, page, query)

        parts = (value or "").split()
        if len(parts) != 1:
            return await self._show_view(
                call, key, page, query, self.strings["ui_one_word"]
            )

        new = parts[0]
        new_key = self._key(new)
        if new_key in notes and new_key != key:
            return await self._show_view(
                call, key, page, query, f"❌ «{utils.escape_html(new)}» уже существует"
            )

        note = notes.pop(key)
        note["name"] = new
        note["updated"] = time.time()
        notes[new_key] = note
        self._save(notes)
        await self._show_view(call, new_key, page, query, "🔁 Переименована")

    async def _remind_input(self, call, value, key, page, query):
        minutes = self._parse_minutes(value)
        if minutes is None:
            return await self._show_view(
                call, key, page, query, self.strings["ui_bad_time"]
            )

        at = self._set_remind(key, minutes)
        notice = self.strings["ui_remind_set"].format(self._fmt_time(at)) if at else None
        await self._show_view(call, key, page, query, notice)

    # ----- delete / clear -----

    async def _del_ask(self, call, key, page, query):
        note = self._notes().get(key)
        if not note:
            return await self._show_view(call, key, page, query)

        await call.edit(
            text=self.strings["ui_del_ask"].format(utils.escape_html(note["name"])),
            reply_markup=[
                [
                    {
                        "text": "✅ Да, удалить",
                        "callback": self._del_do,
                        "args": (key, page, query),
                    },
                    {
                        "text": "↩️ Отмена",
                        "callback": self._open,
                        "args": (key, page, query),
                    },
                ]
            ],
        )

    async def _del_do(self, call, key, page, query):
        notes = self._notes()
        notes.pop(key, None)
        self._save(notes)
        await call.answer("🗑 Удалена")
        await self._show_menu(call, page, query)

    async def _clear_ask(self, call):
        notes = self._notes()
        if not notes:
            return await call.answer("📭 Заметок нет")

        await call.edit(
            text=self.strings["ui_clear_ask"].format(len(notes)),
            reply_markup=[
                [
                    {"text": "✅ Да, очистить", "callback": self._clear_do},
                    {"text": "↩️ Отмена", "callback": self._page, "args": (0, None)},
                ]
            ],
        )

    async def _clear_do(self, call):
        self._save({})
        await call.answer("🧹 Всё удалено")
        await self._show_menu(call)

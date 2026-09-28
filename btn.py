# meta developer: @lackyhyyy666
# scope: inline

import html
import re
from urllib.parse import quote

from telethon.extensions import markdown as telethon_markdown
from telethon.tl.types import Message, MessageService
from .. import loader, utils
from ..inline.types import InlineCall


@loader.tds
class InlineButtonsMod(loader.Module):
    """Модуль для создания и добавления инлайн-кнопок под любым сообщением с полным сохранением Markdown-форматирования и кастомных эмодзи."""

    strings = {
        "name": "InlineButtons",
        "no_buttons": "<b>⚠️ Не найдено ни одной кнопки!</b>\n<i>Используйте формат: <code>[1. Название - https://ссылка.com]</code> или <code>[1. ] [2. ]</code></i>",
        "no_text": "<b>⚠️ Укажите текст сообщения или ответьте реплаем на готовое сообщение!</b>",
        "help": (
            "<b>🔘 Модуль создания и редактирования Инлайн-кнопок</b>\n\n"
            "<b>🛠 Команды:</b>\n"
            "• <code>.btn [текст] [1. Кнопка - Ссылка]</code> — Прямое редактирование команды в инлайн-сообщение\n"
            "• <code>.editbtn [текст] [1. Кнопка - Ссылка]</code> — Отредактировать текст и кнопки\n"
            "• <code>.addbtn [1. Кнопка - Ссылка]</code> — Добавить кнопки (сохраняя форматирование реплая)\n\n"
            "<b>💡 Форматы кнопок:</b>\n"
            "1. <b>Ссылка:</b> <code>[1. Написать - t.me/lackyhyyy666]</code> или <code>[Яндекс - yandex.ru]</code>\n"
            "2. <b>Всплывающее окно (Toast/Alert):</b> <code>[1. Нажми - callback:Привет всем!]</code>\n"
            "3. <b>Закрыть / Удалить сообщение:</b> <code>[❌ Закрыть - close]</code>\n"
            "4. <b>Интерактивный переключатель:</b> <code>[🟢 Статус ON - toggle]</code>\n"
            "5. <b>Поделиться:</b> <code>[Поделиться - share:Ваш текст]</code>\n"
            "6. <b>Простая нумерованная кнопка:</b> <code>[1. Текст]</code>\n\n"
            "<b>Ряды кнопок:</b> создаются с новой строки или разделяются через <code>||</code>"
        ),
        "edit_help": (
            "<b>✏️ Редактирование кнопок (.editbtn)</b>\n\n"
            "Введите текст с кнопками или ответьте на сообщение:\n"
            "<code>.editbtn Новый текст [1. Новая кнопка - t.me/lackyhyyy666]</code>"
        ),
        "add_help": (
            "<b>➕ Добавление кнопок (.addbtn)</b>\n\n"
            "Ответьте на сообщение и укажите кнопки:\n"
            "<code>.addbtn [1. Написать - t.me/lackyhyyy666]</code>"
        ),
    }

    def _get_formatted_text(self, msg) -> str:
        """Извлекает Markdown-текст сообщения с сохранением жирного/курсива/кода и кастомных эмодзи."""
        if not msg or isinstance(msg, MessageService):
            return ""

        # 1. Приоритет: встроенный метод Hikka utils.md(msg)
        try:
            if hasattr(utils, "md"):
                res = utils.md(msg)
                if res:
                    return res
        except Exception:
            pass

        # 2. Фолбэк: телетоновский markdown unparse
        text_raw = getattr(msg, "message", "") or getattr(msg, "text", "") or ""
        entities = getattr(msg, "entities", None)

        if text_raw and entities:
            try:
                return telethon_markdown.unparse(text_raw, entities)
            except Exception:
                pass

        if hasattr(msg, "text") and msg.text:
            return msg.text
        if hasattr(msg, "raw_text") and msg.raw_text:
            return msg.raw_text
        return text_raw

    @loader.command(
        ru_doc="[текст / реплай] [1. Кнопка - Ссылка] — Превратить текущее сообщение в инлайн-сообщение с кнопками",
        en_doc="[text / reply] [1. Button - Link] — Turn current message into inline message with buttons",
    )
    async def btncmd(self, message: Message):
        """[текст / реплай] [1. Кнопка - Ссылка] — Создать сообщение с инлайн-кнопками"""
        args_raw = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args_raw and not reply:
            await utils.answer(message, self.strings("help"))
            return

        base_text = self._get_formatted_text(reply)
        parsed_text, button_rows = self._parse_buttons(args_raw)

        final_text = parsed_text if parsed_text else base_text
        if not final_text:
            final_text = "🔘 <b>Инлайн-кнопки:</b>"

        if not button_rows:
            await utils.answer(message, self.strings("no_buttons"))
            return

        try:
            await self.inline.form(
                text=final_text,
                message=message,
                reply_markup=button_rows,
                disable_security=True,
            )
        except Exception as exc:
            await utils.answer(
                message,
                f"<b>⚠️ Ошибка инлайн-бота:</b> <code>{html.escape(str(exc))}</code>\n\n"
                "<i>Убедитесь, что у вас включен инлайн-бот в настройках Hikka.</i>",
            )

    @loader.command(
        ru_doc="[текст / реплай] [1. Кнопка - Ссылка] — Редактировать текущую команду в сообщение с кнопками",
        en_doc="[text / reply] [1. Button - Link] — Edit current message into button message",
    )
    async def editbtncmd(self, message: Message):
        """[текст / реплай] [1. Кнопка - Ссылка] — Отредактировать сообщение с кнопками"""
        args_raw = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args_raw and not reply:
            await utils.answer(message, self.strings("edit_help"))
            return

        base_text = self._get_formatted_text(reply)
        parsed_text, button_rows = self._parse_buttons(args_raw)

        final_text = parsed_text if parsed_text else base_text
        if not final_text:
            final_text = "🔘 <b>Отредактированное сообщение:</b>"

        if not button_rows:
            await utils.answer(message, self.strings("no_buttons"))
            return

        try:
            await self.inline.form(
                text=final_text,
                message=message,
                reply_markup=button_rows,
                disable_security=True,
            )
        except Exception as exc:
            await utils.answer(
                message,
                f"<b>⚠️ Ошибка редактирования:</b> <code>{html.escape(str(exc))}</code>",
            )

    @loader.command(
        ru_doc="[реплай] [1. Кнопка - Ссылка] — Добавить кнопки (отредактировав текущее сообщение)",
        en_doc="[reply] [1. Button - Link] — Add buttons by editing current message",
    )
    async def addbtncmd(self, message: Message):
        """[реплай] [1. Кнопка - Ссылка] — Добавить кнопки к сообщению"""
        args_raw = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args_raw:
            await utils.answer(message, self.strings("add_help"))
            return

        base_text = self._get_formatted_text(reply)
        parsed_text, extra_button_rows = self._parse_buttons(args_raw)

        final_text = parsed_text if parsed_text else base_text
        if not final_text:
            final_text = "🔘 <b>Сообщение с кнопками:</b>"

        if not extra_button_rows:
            await utils.answer(message, self.strings("no_buttons"))
            return

        try:
            await self.inline.form(
                text=final_text,
                message=message,
                reply_markup=extra_button_rows,
                disable_security=True,
            )
        except Exception as exc:
            await utils.answer(
                message,
                f"<b>⚠️ Ошибка добавления кнопок:</b> <code>{html.escape(str(exc))}</code>",
            )

    async def _toast_callback(self, call: InlineCall, toast_text: str):
        """Обработчик всплывающих уведомлений для callback-кнопок."""
        await call.answer(toast_text, show_alert=True)

    async def _close_callback(self, call: InlineCall):
        """Удаляет инлайн-сообщение по нажатию кнопки Закрыть."""
        await call.delete()

    async def _toggle_callback(self, call: InlineCall, current_state: str):
        """Динамическое переключение состояния кнопки в режиме реального времени."""
        if "🟢" in current_state or "ON" in current_state.upper():
            new_state = current_state.replace("🟢", "🔴").replace("ON", "OFF")
            toast = "Режим выключен 🔴"
        elif "🔴" in current_state or "OFF" in current_state.upper():
            new_state = current_state.replace("🔴", "🟢").replace("OFF", "ON")
            toast = "Режим включен 🟢"
        else:
            new_state = f"✅ {current_state}"
            toast = f"Состояние изменено: {new_state}"

        await call.answer(toast, show_alert=False)

        if hasattr(call, "reply_markup") and call.reply_markup:
            new_markup = []
            for row in call.reply_markup:
                new_row = []
                for btn in row:
                    if isinstance(btn, dict) and btn.get("text") == current_state:
                        new_btn = dict(btn)
                        new_btn["text"] = new_state
                        new_btn["args"] = (new_state,)
                        new_row.append(new_btn)
                    else:
                        new_row.append(btn)
                new_markup.append(new_row)
            await call.edit(reply_markup=new_markup)

    def _parse_buttons(self, raw_input: str):
        """Парсит текст и структуру инлайн-кнопок из строки ввода."""
        if not raw_input:
            return "", []

        lines = [l.strip() for l in re.split(r"\n|\|\|", raw_input) if l.strip()]

        text_parts = []
        button_rows = []

        for line in lines:
            buttons_in_line = re.findall(r"\[([^\]]+)\]", line)
            if buttons_in_line:
                line_text = re.sub(r"\[[^\]]+\]", "", line).strip()
                if line_text:
                    text_parts.append(line_text)

                row = []
                for b in buttons_in_line:
                    btn_obj = self._parse_single_button(b)
                    if btn_obj:
                        row.append(btn_obj)

                if row:
                    button_rows.append(row)
            else:
                text_parts.append(line)

        msg_text = "\n".join(text_parts).strip()
        return msg_text, button_rows

    def _parse_single_button(self, raw_str: str):
        """Разбирает содержимое внутри [ ... ] в объект кнопки."""
        content = raw_str.strip()
        if not content:
            return None

        num_match = re.match(r"^(\d+)[\.\:\)]?\s*(.*)$", content)
        if num_match:
            btn_num = num_match.group(1)
            remainder = num_match.group(2).strip()
        else:
            btn_num = None
            remainder = content

        if not remainder:
            title = f"{btn_num}." if btn_num else "Кнопка"
            toast_text = f"Взаимодействие с кнопкой №{btn_num}" if btn_num else "Нажата кнопка"
            return {
                "text": title,
                "callback": self._toast_callback,
                "args": (toast_text,),
            }

        rem_lower = remainder.lower()
        if rem_lower in ("close", "delete", "закрыть", "удалить"):
            title = f"{btn_num}. Закрыть" if btn_num else remainder
            return {
                "text": title,
                "callback": self._close_callback,
            }
        elif rem_lower == "toggle" or rem_lower.startswith("toggle:"):
            title = remainder[7:].strip() if rem_lower.startswith("toggle:") else (f"{btn_num}. Переключатель" if btn_num else remainder)
            return {
                "text": title,
                "callback": self._toggle_callback,
                "args": (title,),
            }
        elif rem_lower.startswith("callback:"):
            cb_msg = remainder[9:].strip()
            title = f"{btn_num}. Callback" if btn_num else "Callback"
            return {
                "text": title,
                "callback": self._toast_callback,
                "args": (cb_msg,),
            }
        elif rem_lower.startswith("share:"):
            share_text = remainder[6:].strip()
            title = f"{btn_num}. Поделиться" if btn_num else "Поделиться"
            return {
                "text": title,
                "url": f"https://t.me/share/url?url={quote(share_text)}",
            }

        url_match = re.search(r"(https?://\S+|tg://\S+|t\.me/\S+|@[a-zA-Z0-9_]{4,})", remainder, re.IGNORECASE)
        if url_match:
            raw_url = url_match.group(1)
            text_before = remainder[:url_match.start()].strip()
            text_before = re.sub(r"[\s\-\|\:\-\>]+$", "", text_before).strip()

            if text_before:
                title_part = text_before
            else:
                title_part = "Ссылка"

            if btn_num:
                if re.match(rf"^{btn_num}[\.\:\)]", title_part):
                    final_title = title_part
                else:
                    final_title = f"{btn_num}. {title_part}"
            else:
                final_title = title_part

            full_url = self._fix_url(raw_url)
            return {"text": final_title, "url": full_url}

        parts = re.split(r"\s*(?:-|\||->)\s*", remainder, maxsplit=1)
        title_part = parts[0].strip()
        target_part = parts[1].strip() if len(parts) > 1 else ""

        if btn_num:
            if title_part:
                if re.match(rf"^{btn_num}[\.\:\)]", title_part):
                    title = title_part
                else:
                    title = f"{btn_num}. {title_part}"
            else:
                title = f"{btn_num}."
        else:
            title = title_part if title_part else "Кнопка"

        if target_part:
            tgt_lower = target_part.lower()
            if tgt_lower in ("close", "delete", "закрыть", "удалить"):
                return {
                    "text": title,
                    "callback": self._close_callback,
                }
            elif tgt_lower.startswith("callback:"):
                return {
                    "text": title,
                    "callback": self._toast_callback,
                    "args": (target_part[9:].strip(),),
                }
            elif tgt_lower.startswith("share:"):
                return {
                    "text": title,
                    "url": f"https://t.me/share/url?url={quote(target_part[6:].strip())}",
                }
            else:
                full_url = self._fix_url(target_part)
                return {"text": title, "url": full_url}

        if self._is_url(title_part):
            full_url = self._fix_url(title_part)
            return {"text": title, "url": full_url}

        toast_text = f"Нажата кнопка №{btn_num}: {title_part}" if btn_num else f"Нажата кнопка: {title_part}"
        return {
            "text": title,
            "callback": self._toast_callback,
            "args": (toast_text,),
        }

    def _fix_url(self, url: str) -> str:
        """Приводит ссылку к валидному формату с префиксом https:// или tg://."""
        url = url.strip()
        if url.startswith("@"):
            return f"https://t.me/{url[1:]}"
        if not url.startswith(("http://", "https://", "tg://")):
            return f"https://{url}"
        return url

    def _is_url(self, text: str) -> bool:
        if text.startswith(("@", "http://", "https://", "tg://", "t.me/")):
            return True
        if re.match(r"^[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(/.*)?$", text):
            return True
        return False

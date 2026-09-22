# meta developer: @lackyhyyy666
# scope: inline

import html
import re
from urllib.parse import quote

from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import InlineCall


@loader.tds
class InlineButtonsMod(loader.Module):
    """Модуль для добавления интерактивных инлайн-кнопок (ссылок, алертов, кнопок пересылки) под любым сообщением."""

    strings = {
        "name": "InlineButtons",
        "no_buttons": "<b>⚠️ Не найдено ни одной кнопки!</b>\n<i>Используйте формат: <code>[1. Название - https://ссылка.com]</code> или <code>[1. ] [2. ]</code></i>",
        "no_text": "<b>⚠️ Укажите текст сообщения или ответьте реплаем на готовое сообщение!</b>",
        "help": (
            "<b>🔘 Модуль создания Инлайн-кнопок под сообщением</b>\n\n"
            "<b>🛠 Способы использования:</b>\n\n"
            "<b>1. Нумерованные кнопки и ссылки:</b>\n"
            "<code>.btn Ваш текст [1. Яндекс - yandex.ru] [2. Гугл - google.com]</code>\n\n"
            "<b>2. Быстрые кнопки с номерами [1. ] [2. ]:</b>\n"
            "<code>.btn Ваш текст [1. ] [2. ]</code>\n\n"
            "<b>3. Несколько рядов кнопок (через || или с новой строки):</b>\n"
            "<code>.btn Ваш текст\n"
            "[1. Кнопка 1 - https://ссылка1.com] [2. Кнопка 2 - https://ссылка2.com]\n"
            "[3. Кнопка 3 - https://ссылка3.com]</code>\n\n"
            "<b>4. Добавление кнопок реплаем на сообщение:</b>\n"
            "<i>Ответьте на любое сообщение и введите:</i>\n"
            "<code>.btn [1. ] [2. ]</code>\n\n"
            "<b>5. Всплывающее уведомление (Callback Toast):</b>\n"
            "<code>.btn [1. Нажми - callback:Привет, это всплывающее окно!]</code>"
        ),
    }

    @loader.command(
        ru_doc="[текст / реплай] [1. Кнопка - Ссылка] — Создать сообщение с инлайн-кнопками снизу",
        en_doc="[text / reply] [1. Button - Link] — Create message with inline buttons below",
    )
    async def btncmd(self, message: Message):
        """[текст / реплай] [1. Кнопка - Ссылка] — Добавить инлайн-кнопки под сообщение"""
        args_raw = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args_raw and not reply:
            await utils.answer(message, self.strings("help"))
            return

        base_text = ""
        if reply:
            if reply.raw_text:
                base_text = reply.raw_text.strip()
            elif reply.caption:
                base_text = reply.caption.strip()

        parsed_text, button_rows = self._parse_buttons(args_raw)

        # Если был текст в команде, он имеет приоритет или дополняет базовый
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
                f"<b>⚠️ Ошибка вызова инлайн-бота:</b> <code>{html.escape(str(exc))}</code>\n\n"
                "<i>Убедитесь, что у вас включен инлайн-бот в настройках Hikka.</i>",
            )


    async def _toast_callback(self, call: InlineCall, toast_text: str):
        """Обработчик всплывающих уведомлений для callback-кнопок"""
        await call.answer(toast_text, show_alert=True)

    def _parse_buttons(self, raw_input: str):
        """Парсит текст и структуру инлайн-кнопок из строки ввода."""
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

        # Проверяем на наличие номера кнопки (например, 1., 1), 1:, 1)
        num_match = re.match(r"^(\d+)[\.\:\)]?\s*(.*)$", content)
        if num_match:
            btn_num = num_match.group(1)
            remainder = num_match.group(2).strip()
        else:
            btn_num = None
            remainder = content

        # Если кнопка пустая вроде [1. ] или [1]
        if not remainder:
            title = f"{btn_num}." if btn_num else "Кнопка"
            toast_text = f"Взаимодействие с кнопкой №{btn_num}" if btn_num else "Нажата кнопка"
            return {
                "text": title,
                "callback": self._toast_callback,
                "args": (toast_text,),
            }

        # 1. Проверяем на явный callback: или share:
        if remainder.lower().startswith("callback:"):
            cb_msg = remainder[9:].strip()
            title = f"{btn_num}. Callback" if btn_num else "Callback"
            return {
                "text": title,
                "callback": self._toast_callback,
                "args": (cb_msg,),
            }
        elif remainder.lower().startswith("share:"):
            share_text = remainder[6:].strip()
            title = f"{btn_num}. Поделиться" if btn_num else "Поделиться"
            return {
                "text": title,
                "url": f"https://t.me/share/url?url={quote(share_text)}",
            }

        # 2. Ищем прямое упоминание URL (http://, https://, tg://, t.me/) в remainder
        url_match = re.search(r"(https?://\S+|tg://\S+|t\.me/\S+)", remainder, re.IGNORECASE)
        if url_match:
            raw_url = url_match.group(1)
            text_before = remainder[:url_match.start()].strip()
            # Очищаем префиксные разделители (тире, двоеточия, слэши) перед ссылкой
            text_before = re.sub(r"[\s\-\|\:\-\>]+$", "", text_before).strip()

            if text_before:
                title_part = text_before
            else:
                domain_match = re.search(r"://([^/]+)", raw_url)
                title_part = domain_match.group(1) if domain_match else "Ссылка"

            if btn_num:
                if re.match(rf"^{btn_num}[\.\:\)]", title_part):
                    final_title = title_part
                else:
                    final_title = f"{btn_num}. {title_part}"
            else:
                final_title = title_part

            return {"text": final_title, "url": raw_url}

        # 3. Разделение по традиционным разделителям ( - , | , -> , : )
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
            if target_part.lower().startswith("callback:"):
                return {
                    "text": title,
                    "callback": self._toast_callback,
                    "args": (target_part[9:].strip(),),
                }
            elif target_part.lower().startswith("share:"):
                return {
                    "text": title,
                    "url": f"https://t.me/share/url?url={quote(target_part[6:].strip())}",
                }
            else:
                url = target_part
                if not url.startswith(("http://", "https://", "tg://")):
                    url = f"https://{url}"
                return {"text": title, "url": url}

        # 4. Если target_part отсутствует, проверяем не является ли title_part сам по себе доменным именем
        if self._is_url(title_part):
            url = title_part if title_part.startswith(("http://", "https://", "tg://")) else f"https://{title_part}"
            return {"text": title, "url": url}

        # 5. Текст без ссылки -> создаем callback toast
        toast_text = f"Нажата кнопка №{btn_num}: {title_part}" if btn_num else f"Нажата кнопка: {title_part}"
        return {
            "text": title,
            "callback": self._toast_callback,
            "args": (toast_text,),
        }

    def _is_url(self, text: str) -> bool:
        if text.startswith(("http://", "https://", "tg://", "t.me/")):
            return True
        if re.match(r"^[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(/.*)?$", text):
            return True
        return False



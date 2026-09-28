# meta developer: @lackyhyyy666
# scope: hikka_only
# scope: hikka_min 1.6.2

import html
import logging
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class KissMod(loader.Module):
    """Модуль милых RP-взаимодействий от @lackyhyyy666"""

    strings = {
        "name": "Kiss",
        "no_target": "<b>⚠️ Укажите пользователя (@username/ID) или ответьте на его сообщение!</b>",
    }

    async def _get_target_and_extra(self, message: Message):
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()

        target_entity = None
        extra_text = args

        if reply:
            target_entity = await reply.get_sender()
        elif args:
            first_arg = args.split()[0]
            if first_arg.startswith("@") or first_arg.lstrip("-").isdigit():
                try:
                    client = getattr(self, "_client", None) or getattr(self, "client", None)
                    target_entity = await client.get_entity(first_arg)
                    extra_text = args[len(first_arg):].strip()
                except Exception:
                    pass

        if not target_entity and message.is_private:
            try:
                chat = await message.get_chat()
                if getattr(chat, "id", None) != self._me.id:
                    target_entity = chat
            except Exception:
                pass

        return target_entity, extra_text

    async def _send_action(self, message: Message, emoji: str, action_verb: str, post_target: str = ""):
        target_entity, extra_text = await self._get_target_and_extra(message)
        if not target_entity:
            await utils.answer(message, self.strings("no_target"))
            return

        self_name = utils.escape_html(get_display_name(self._me))
        self_link = f'<a href="tg://user?id={self._me.id}">{self_name}</a>'

        target_name = utils.escape_html(get_display_name(target_entity))
        target_id = getattr(target_entity, "id", 0)
        target_link = f'<a href="tg://user?id={target_id}">{target_name}</a>'

        post_str = f" {post_target}" if post_target else ""
        out = f"{emoji} <b>{self_link} {action_verb} {target_link}{post_str}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    @loader.command(
        ru_doc="[@username / reply / extra] — Погладить по голове",
        en_doc="[@username / reply / extra] — Pat on the head",
    )
    async def pattcmd(self, message: Message):
        """[@username / reply / extra] — Pat on the head"""
        await self._send_action(message, "🫳", "погладил(а)", "по голове")

    @loader.command(
        ru_doc="[@username / reply / extra] — Обнять",
        en_doc="[@username / reply / extra] — Hug",
    )
    async def hugcmd(self, message: Message):
        """[@username / reply / extra] — Hug"""
        await self._send_action(message, "🫂", "обнял(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Поцеловать в щёчку",
        en_doc="[@username / reply / extra] — Kiss on the cheek",
    )
    async def kisscmd(self, message: Message):
        """[@username / reply / extra] — Kiss on the cheek"""
        await self._send_action(message, "💋", "поцеловал(а) в щёчку")

    @loader.command(
        ru_doc="[@username / reply / extra] — Облизать",
        en_doc="[@username / reply / extra] — Lick",
    )
    async def lickcmd(self, message: Message):
        """[@username / reply / extra] — Lick"""
        await self._send_action(message, "👅", "облизал(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Дать пощёчину",
        en_doc="[@username / reply / extra] — Slap",
    )
    async def slapcmd(self, message: Message):
        """[@username / reply / extra] — Slap"""
        await self._send_action(message, "👋", "дал(а) пощёчину")

    @loader.command(
        ru_doc="[@username / reply / extra] — Укусить",
        en_doc="[@username / reply / extra] — Bite",
    )
    async def bitecmd(self, message: Message):
        """[@username / reply / extra] — Bite"""
        await self._send_action(message, "🦮", "укусил(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Прижаться",
        en_doc="[@username / reply / extra] — Cuddle",
    )
    async def cuddlecmd(self, message: Message):
        """[@username / reply / extra] — Cuddle"""
        await self._send_action(message, "🤗", "прижался(ась) к")

    @loader.command(
        ru_doc="[@username / reply / extra] — Тыкнуть в носик",
        en_doc="[@username / reply / extra] — Boop nose",
    )
    async def boopcmd(self, message: Message):
        """[@username / reply / extra] — Boop nose"""
        await self._send_action(message, "👉", "тыкнул(а) в носик")

    @loader.command(
        ru_doc="[@username / reply / extra] — Взять за ручку",
        en_doc="[@username / reply / extra] — Hold hand",
    )
    async def handholdcmd(self, message: Message):
        """[@username / reply / extra] — Hold hand"""
        await self._send_action(message, "🤝", "взял(а) за ручку")

    @loader.command(
        ru_doc="[@username / reply / extra] — Покормить вкусняшкой",
        en_doc="[@username / reply / extra] — Feed",
    )
    async def feedcmd(self, message: Message):
        """[@username / reply / extra] — Feed"""
        await self._send_action(message, "🍰", "покормил(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Потыкать пальцем",
        en_doc="[@username / reply / extra] — Poke",
    )
    async def pokecmd(self, message: Message):
        """[@username / reply / extra] — Poke"""
        await self._send_action(message, "👉", "потыкал(а) пальцем в")

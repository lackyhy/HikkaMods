# meta developer: @lackyhyyy666

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
        "no_two_targets": "<b>⚠️ Укажите двух пользователей или ответьте на сообщение!</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "gender",
                "по умолчанию",
                lambda: "Пол пользователя для RP-команд",
                validator=loader.validators.Choice(["по умолчанию", "мужской", "женский"]),
            ),
        )

    def _format_verb(self, verb: str) -> str:
        gender = str(self.config["gender"]).lower().strip()
        if gender in ["мужской", "male", "m"]:
            return verb.replace("(ась)", "").replace("(а)", "").replace("(a)", "")
        elif gender in ["женский", "female", "f"]:
            res = verb.replace("ся(ась)", "ась").replace("(ась)", "ась")
            res = res.replace("(а)", "а").replace("(a)", "а")
            return res
        return verb

    async def _get_target_and_extra(self, message: Message):
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()

        target_entity = None
        extra_text = args

        if reply:
            target_entity = await reply.get_sender()
        elif args:
            first_arg = args.split()[0]
            if (
                first_arg.startswith("@")
                or first_arg.lstrip("-").isdigit()
                or first_arg.startswith("t.me/")
                or first_arg.startswith("https://t.me/")
            ):
                try:
                    target_entity = await message.client.get_entity(first_arg)
                    extra_text = args[len(first_arg):].strip()
                except Exception:
                    target_entity = None

        if not target_entity and message.is_private:
            try:
                target_entity = await message.get_chat()
            except Exception:
                pass

        return target_entity, extra_text

    async def _get_two_targets_and_extra(self, message: Message):
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()
        reply_sender = await reply.get_sender() if reply else None

        words = args.split()
        target1 = None
        target2 = None
        used = 0

        if len(words) >= 1:
            w1 = words[0]
            if (
                w1.startswith("@")
                or w1.lstrip("-").isdigit()
                or w1.startswith("t.me/")
                or w1.startswith("https://t.me/")
            ):
                try:
                    target1 = await message.client.get_entity(w1)
                    used += 1
                except Exception:
                    target1 = None

        if len(words) >= used + 1:
            w2 = words[used]
            if (
                w2.startswith("@")
                or w2.lstrip("-").isdigit()
                or w2.startswith("t.me/")
                or w2.startswith("https://t.me/")
            ):
                try:
                    target2 = await message.client.get_entity(w2)
                    used += 1
                except Exception:
                    target2 = None

        if not target1 and reply_sender:
            target1 = reply_sender
        elif not target1 and message.is_private:
            try:
                target1 = await message.get_chat()
            except Exception:
                pass

        if not target2 and reply_sender and getattr(target1, "id", None) != getattr(reply_sender, "id", None):
            target2 = reply_sender

        extra_text = " ".join(words[used:]).strip()
        return target1, target2, extra_text

    async def _send_action(self, message: Message, emoji: str, action_verb: str, post_target: str = ""):
        me = await message.client.get_me()
        target_entity, extra_text = await self._get_target_and_extra(message)

        if not target_entity:
            await utils.answer(message, self.strings("no_target"))
            return

        self_name = utils.escape_html(get_display_name(me))
        self_link = f'<a href="tg://user?id={me.id}">{self_name}</a>'

        target_name = utils.escape_html(get_display_name(target_entity))
        target_id = getattr(target_entity, "id", 0)
        target_link = f'<a href="tg://user?id={target_id}">{target_name}</a>'

        formatted_verb = self._format_verb(action_verb)
        post_str = f" {post_target}" if post_target else ""
        out = f"{emoji} <b>{self_link} {formatted_verb} {target_link}{post_str}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    async def _send_two_target_action(
        self,
        message: Message,
        emoji: str,
        verb_between: str,
        prep_target2: str,
        post_str: str = "",
    ):
        me = await message.client.get_me()
        t1, t2, extra_text = await self._get_two_targets_and_extra(message)

        if not t1 or not t2:
            await utils.answer(message, self.strings("no_two_targets"))
            return

        self_name = utils.escape_html(get_display_name(me))
        self_link = f'<a href="tg://user?id={me.id}">{self_name}</a>'

        t1_name = utils.escape_html(get_display_name(t1))
        t1_link = f'<a href="tg://user?id={getattr(t1, "id", 0)}">{t1_name}</a>'

        t2_name = utils.escape_html(get_display_name(t2))
        t2_link = f'<a href="tg://user?id={getattr(t2, "id", 0)}">{t2_name}</a>'

        formatted_verb = self._format_verb(verb_between)
        post = f" {post_str}" if post_str else ""
        out = f"{emoji} <b>{self_link} {formatted_verb} {t1_link} {prep_target2} {t2_link}{post}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    async def _send_all_action(self, message: Message, emoji: str, action_verb: str, target_all_phrase: str):
        me = await message.client.get_me()
        extra_text = utils.get_args_raw(message).strip()

        self_name = utils.escape_html(get_display_name(me))
        self_link = f'<a href="tg://user?id={me.id}">{self_name}</a>'

        formatted_verb = self._format_verb(action_verb)
        out = f"{emoji} <b>{self_link} {formatted_verb} {target_all_phrase}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    @loader.command(
        ru_doc="[@user1] [@user2 / reply] [extra] — Посмеяться вместе с @target1 над @target2",
        en_doc="[@user1] [@user2 / reply] [extra] — Laugh together with @target1 at @target2",
    )
    async def laughcmd(self, message: Message):
        """[@user1] [@user2 / reply] [extra] — Laugh together with @target1 at @target2"""
        await self._send_two_target_action(message, "🤣", "посмеялся(ась) вместе с", "над")

    @loader.command(
        ru_doc="[@user1] [@user2 / reply] [extra] — Зашипперить @target1 с @target2",
        en_doc="[@user1] [@user2 / reply] [extra] — Ship @target1 with @target2",
    )
    async def shipcmd(self, message: Message):
        """[@user1] [@user2 / reply] [extra] — Ship @target1 with @target2"""
        await self._send_two_target_action(message, "👩‍❤️‍👨", "зашипперил(а)", "с")

    @loader.command(
        ru_doc="[@user1] [@user2 / reply] [extra] — Посплетничать с @target1 о @target2",
        en_doc="[@user1] [@user2 / reply] [extra] — Gossip with @target1 about @target2",
    )
    async def gossipcmd(self, message: Message):
        """[@user1] [@user2 / reply] [extra] — Gossip with @target1 about @target2"""
        await self._send_two_target_action(message, "🗣", "посплетничал(а) вместе с", "о")


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
        ru_doc="[@username / reply / extra] — Приобнять",
        en_doc="[@username / reply / extra] — Gently hug",
    )
    async def higcmd(self, message: Message):
        """[@username / reply / extra] — Gently hug"""
        await self._send_action(message, "🫂", "приобнял(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Поцеловать в щёчку",
        en_doc="[@username / reply / extra] — Kiss on the cheek",
    )
    async def kisscmd(self, message: Message):
        """[@username / reply / extra] — Kiss on the cheek"""
        await self._send_action(message, "💋", "поцеловал(а) в щёчку")

    @loader.command(
        ru_doc="[@username / reply / extra] — Поцеловать в засос",
        en_doc="[@username / reply / extra] — Passionately kiss",
    )
    async def kissscmd(self, message: Message):
        """[@username / reply / extra] — Passionately kiss"""
        await self._send_action(message, "💋", "поцеловал(а) в засос")

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

    @loader.command(
        ru_doc="[@username / reply / extra] — Отсосать",
        en_doc="[@username / reply / extra] — Perform blowjob",
    )
    async def otscmd(self, message: Message):
        """[@username / reply / extra] — Perform blowjob"""
        await self._send_action(message, "😮‍💨", "отсосал(а) у")

    @loader.command(
        ru_doc="[@username / reply / extra] — Отлизать",
        en_doc="[@username / reply / extra] — Perform cunnilingus",
    )
    async def otlcmd(self, message: Message):
        """[@username / reply / extra] — Perform cunnilingus"""
        await self._send_action(message, "👅", "отлизал(а) у")

    @loader.command(
        ru_doc="[@username / reply / extra] — Ударить",
        en_doc="[@username / reply / extra] — Hit",
    )
    async def hitcmd(self, message: Message):
        """[@username / reply / extra] — Hit"""
        await self._send_action(message, "👊", "ударил(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Изнасиловать",
        en_doc="[@username / reply / extra] — Rape",
    )
    async def rapecmd(self, message: Message):
        """[@username / reply / extra] — Rape"""
        await self._send_action(message, "🔞", "изнасиловал(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Нежный кусь",
        en_doc="[@username / reply / extra] — Gentle bite",
    )
    async def gbitecmd(self, message: Message):
        """[@username / reply / extra] — Gentle bite"""
        await self._send_action(message, "🦮", "сделал(а) нежный кусь")

    @loader.command(
        ru_doc="[@username / reply / extra] — Пнуть",
        en_doc="[@username / reply / extra] — Kick",
    )
    async def kickcmd(self, message: Message):
        """[@username / reply / extra] — Kick"""
        await self._send_action(message, "🦶", "пнул(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Пощекотать",
        en_doc="[@username / reply / extra] — Tickle",
    )
    async def ticklecmd(self, message: Message):
        """[@username / reply / extra] — Tickle"""
        await self._send_action(message, "🤏", "пощекотал(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Сесть на лицо",
        en_doc="[@username / reply / extra] — Sit on face",
    )
    async def sitfacecmd(self, message: Message):
        """[@username / reply / extra] — Sit on face"""
        await self._send_action(message, "🍑", "сел(а) на лицо")

    @loader.command(
        ru_doc="[@username / reply / extra] — Шлёпнуть по попке",
        en_doc="[@username / reply / extra] — Spank butt",
    )
    async def spankcmd(self, message: Message):
        """[@username / reply / extra] — Spank butt"""
        await self._send_action(message, "🍑", "шлёпнул(а) по попке")

    @loader.command(
        ru_doc="[@username / reply / extra] — Полапать за интимные места",
        en_doc="[@username / reply / extra] — Grope",
    )
    async def gropecmd(self, message: Message):
        """[@username / reply / extra] — Grope"""
        await self._send_action(message, "👐", "полапал(а) за интимные места")

    @loader.command(
        ru_doc="[@username / reply / extra] — Подмигнуть",
        en_doc="[@username / reply / extra] — Wink",
    )
    async def winkcmd(self, message: Message):
        """[@username / reply / extra] — Wink"""
        await self._send_action(message, "😉", "подмигнул(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Дать подзатыльник",
        en_doc="[@username / reply / extra] — Slap head",
    )
    async def headslapcmd(self, message: Message):
        """[@username / reply / extra] — Slap head"""
        await self._send_action(message, "🫲", "дал(а) подзатыльник")

    @loader.command(
        ru_doc="[@username / reply / extra] — Трахнуть",
        en_doc="[@username / reply / extra] — Fuck",
    )
    async def fuckcmd(self, message: Message):
        """[@username / reply / extra] — Fuck"""
        await self._send_action(message, "👉👌", "трахнул(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Помацать",
        en_doc="[@username / reply / extra] — Feel/Fondle",
    )
    async def feelcmd(self, message: Message):
        """[@username / reply / extra] — Feel/Fondle"""
        await self._send_action(message, "🤲", "помацал(а)")

    @loader.command(
        ru_doc="[extra] — Отсосать всем",
        en_doc="[extra] — Perform blowjob on everyone",
    )
    async def otsacmd(self, message: Message):
        """[extra] — Perform blowjob on everyone"""
        await self._send_all_action(message, "😮‍💨", "отсосал(а)", "у всех")

    @loader.command(
        ru_doc="[extra] — Отлизать всем",
        en_doc="[extra] — Perform cunnilingus on everyone",
    )
    async def otlacmd(self, message: Message):
        """[extra] — Perform cunnilingus on everyone"""
        await self._send_all_action(message, "👅", "отлизал(а)", "у всех")

    @loader.command(
        ru_doc="[extra] — Трахнуть всех",
        en_doc="[extra] — Fuck everyone",
    )
    async def fuckacmd(self, message: Message):
        """[extra] — Fuck everyone"""
        await self._send_all_action(message, "👉👌", "трахнул(а)", "всех")

    @loader.command(
        ru_doc="[extra] — Обнять всех",
        en_doc="[extra] — Hug everyone",
    )
    async def hugacmd(self, message: Message):
        """[extra] — Hug everyone"""
        await self._send_all_action(message, "🫂", "обнял(а)", "всех")



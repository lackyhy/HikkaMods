# meta developer: @lackyhyyy666
# scope: inline

import asyncio
import html
import logging
import re
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
        "config_gender": "Пол владельца для RP-команд",
        "config_allowed_users": "ID или юзернеймы пользователей (через запятую/пробел), которым разрешено использовать RP-команды модуля",
        "config_allowed_chats": "ID или юзернеймы чатов/групп (через запятую/пробел), в которых всем участникам разрешено использовать RP-команды (* для всех групп)",
        "config_ask_gender": "Спрашивать пол пользователя при первом вызове RP-команды, если он ещё не указан",
        "config_user_genders": "Гендеры для разрешённых пользователей в формате ID:пол или @username:пол (например: 123456789: ж, @friend: женский)",
    }

    strings_ru = {
        "no_target": "<b>⚠️ Укажите пользователя (@username/ID) или ответьте на его сообщение!</b>",
        "no_two_targets": "<b>⚠️ Укажите двух пользователей или ответьте на сообщение!</b>",
        "config_gender": "Пол владельца для RP-команд",
        "config_allowed_users": "ID или юзернеймы пользователей (через запятую/пробел), которым разрешено использовать RP-команды модуля",
        "config_allowed_chats": "ID или юзернеймы чатов/групп (через запятую/пробел), в которых всем участникам разрешено использовать RP-команды (* для всех групп)",
        "config_ask_gender": "Спрашивать пол пользователя при первом вызове RP-команды, если он ещё не указан",
        "config_user_genders": "Гендеры для разрешённых пользователей в формате ID:пол или @username:пол (например: 123456789: ж, @friend: женский)",
    }

    def __init__(self):
        self._pending_commands = {}
        self._memory_db = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "gender",
                "по умолчанию",
                lambda: self.strings("config_gender"),
                validator=loader.validators.Choice(["по умолчанию", "мужской", "женский"]),
            ),
            loader.ConfigValue(
                "allowed_users",
                "",
                lambda: self.strings("config_allowed_users"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "allowed_chats",
                "",
                lambda: self.strings("config_allowed_chats"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "ask_gender",
                True,
                lambda: self.strings("config_ask_gender"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "user_genders",
                "",
                lambda: self.strings("config_user_genders"),
                validator=loader.validators.String(),
            ),
        )

    async def client_ready(self, client, db):
        self._client = client
        self.db = db
        try:
            me = await client.get_me()
            self.tg_id = me.id
        except Exception:
            pass

    def _db_get(self, key, default=None):
        if hasattr(self, "get") and callable(self.get):
            try:
                res = self.get(key, default)
                if res is not None:
                    return res
            except Exception:
                pass
        db = getattr(self, "db", getattr(self, "_db", None))
        if db and hasattr(db, "get"):
            try:
                res = db.get(self.strings["name"], key, default)
                if res is not None:
                    return res
            except Exception:
                pass
        return getattr(self, "_memory_db", {}).get(key, default)

    def _db_set(self, key, value):
        if not hasattr(self, "_memory_db"):
            self._memory_db = {}
        self._memory_db[key] = value

        if hasattr(self, "set") and callable(self.set):
            try:
                self.set(key, value)
                return
            except Exception:
                pass
        db = getattr(self, "db", getattr(self, "_db", None))
        if db and hasattr(db, "set"):
            try:
                db.set(self.strings["name"], key, value)
            except Exception:
                pass

    def _get_saved_genders(self) -> dict:
        data = self._db_get("user_genders_db", {})
        if not isinstance(data, dict):
            return {}
        return data

    def _get_saved_gender(self, user_id: int, username: str = None) -> str:
        genders = self._get_saved_genders()
        if user_id:
            if user_id in genders:
                return genders[user_id]
            if str(user_id) in genders:
                return genders[str(user_id)]
        if username:
            u = username.lower().lstrip("@")
            if u in genders:
                return genders[u]
            if f"@{u}" in genders:
                return genders[f"@{u}"]
        return None

    def _set_saved_gender(self, user_id: int, gender: str, username: str = None):
        genders = self._get_saved_genders()
        if user_id:
            genders[str(user_id)] = gender
        if username:
            genders[username.lower().lstrip("@")] = gender
        self._db_set("user_genders_db", genders)

    def _get_rp_map(self):
        if not hasattr(self, "_rp_map") or not self._rp_map:
            self._rp_map = {}
            for attr in dir(self):
                if attr.endswith("cmd") and callable(getattr(self, attr)):
                    cmd_name = attr[:-3]
                    if cmd_name not in ["kisschat", "kissgender"]:
                        self._rp_map[cmd_name] = getattr(self, attr)
        return self._rp_map

    def _is_chat_allowed(self, message: Message) -> bool:
        raw_chats = self.config["allowed_chats"]
        if not raw_chats:
            return False

        if not (message.is_group or message.is_channel):
            return False

        if isinstance(raw_chats, str) and raw_chats.strip() in ["*", "all", "все"]:
            return True

        chat_id = getattr(message, "chat_id", None)
        chat = getattr(message, "chat", None)
        chat_username = getattr(chat, "username", None) if chat else None
        if chat_username:
            chat_username = chat_username.lower().lstrip("@")

        allowed_chat_ids = set()
        allowed_chat_usernames = set()

        items = raw_chats if isinstance(raw_chats, (list, tuple)) else re.split(r"[,\s]+", str(raw_chats).strip())
        for item in items:
            s = str(item).strip()
            if not s:
                continue
            s_clean = re.sub(r"^(?:https?://)?(?:t\.me/)?", "", s).strip()
            if s_clean in ["*", "all", "все"]:
                return True
            if s_clean.lstrip("-").isdigit():
                val = int(s_clean)
                allowed_chat_ids.add(val)
                raw_digits = abs(val)
                s_digits = str(raw_digits)
                if s_digits.startswith("100"):
                    try:
                        stripped = int(s_digits[3:])
                        allowed_chat_ids.add(stripped)
                        allowed_chat_ids.add(-stripped)
                    except Exception:
                        pass
                else:
                    try:
                        allowed_chat_ids.add(int(f"-100{s_digits}"))
                    except Exception:
                        pass
            else:
                allowed_chat_usernames.add(s_clean.lstrip("@").lower())

        if chat_id:
            if chat_id in allowed_chat_ids:
                return True
            raw_cid = abs(chat_id)
            if raw_cid in allowed_chat_ids or -raw_cid in allowed_chat_ids:
                return True
            s_cid = str(raw_cid)
            if s_cid.startswith("100"):
                try:
                    c_short = int(s_cid[3:])
                    if c_short in allowed_chat_ids or -c_short in allowed_chat_ids:
                        return True
                except Exception:
                    pass

        if chat_username and chat_username in allowed_chat_usernames:
            return True

        return False

    def _is_allowed(self, message: Message) -> bool:
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

        if self._is_chat_allowed(message):
            return True

        raw_allowed = self.config["allowed_users"]
        if not raw_allowed:
            return False

        allowed_set = set()
        allowed_usernames = set()
        if isinstance(raw_allowed, (int, str)):
            raw_allowed = [raw_allowed]

        for item in raw_allowed:
            if isinstance(item, int):
                allowed_set.add(item)
            elif isinstance(item, str):
                for sub in re.split(r"[,\s]+", str(item).strip()):
                    clean_sub = sub.strip()
                    if not clean_sub:
                        continue
                    clean_sub = re.sub(r"^(?:https?://)?(?:t\.me/)?", "", clean_sub).strip()
                    if clean_sub.lstrip("-").isdigit():
                        allowed_set.add(int(clean_sub))
                    else:
                        allowed_usernames.add(clean_sub.lstrip("@").lower())

        if sender_id in allowed_set:
            return True

        sender = getattr(message, "sender", None)
        username = getattr(sender, "username", None) if sender else None
        if username and username.lower().lstrip("@") in allowed_usernames:
            return True

        return False

    def _has_known_gender(self, sender) -> bool:
        if not sender:
            return True

        sender_id = getattr(sender, "id", None)
        username = getattr(sender, "username", None)
        if username:
            username = username.lower().lstrip("@")

        saved = self._get_saved_gender(sender_id, username)
        if saved in ["мужской", "женский"]:
            return True

        raw_user_genders = self.config["user_genders"]
        if raw_user_genders:
            items = []
            if isinstance(raw_user_genders, str):
                items = re.split(r"[,\n;]+", raw_user_genders.strip())
            elif isinstance(raw_user_genders, (list, tuple)):
                items = raw_user_genders

            for item in items:
                if ":" in str(item):
                    user_part, gender_part = str(item).split(":", 1)
                    user_part = user_part.strip().lower().lstrip("@")
                    g_val = gender_part.strip().lower()

                    match = False
                    if sender_id and user_part.lstrip("-").isdigit() and int(user_part) == sender_id:
                        match = True
                    elif username and user_part == username:
                        match = True

                    if match and g_val in ["ж", "женский", "female", "f", "м", "мужской", "male", "m"]:
                        return True

        owner_id = getattr(self, "tg_id", None) or getattr(
            getattr(self, "_client", None), "tg_id", None
        )
        if owner_id and sender_id == owner_id:
            cfg_g = str(self.config["gender"]).lower().strip()
            if cfg_g in ["мужской", "женский"]:
                return True

        return False

    def _get_gender_for_sender(self, sender) -> str:
        if not sender:
            return str(self.config["gender"]).lower().strip()

        sender_id = getattr(sender, "id", None)
        username = getattr(sender, "username", None)
        if username:
            username = username.lower().lstrip("@")

        owner_id = getattr(self, "tg_id", None) or getattr(
            getattr(self, "_client", None), "tg_id", None
        )

        saved = self._get_saved_gender(sender_id, username)
        if saved:
            return saved

        raw_user_genders = self.config["user_genders"]
        if raw_user_genders:
            items = []
            if isinstance(raw_user_genders, str):
                items = re.split(r"[,\n;]+", raw_user_genders.strip())
            elif isinstance(raw_user_genders, (list, tuple)):
                items = raw_user_genders

            for item in items:
                if ":" in str(item):
                    user_part, gender_part = str(item).split(":", 1)
                    user_part = user_part.strip().lower().lstrip("@")
                    g_val = gender_part.strip().lower()

                    match = False
                    if sender_id and user_part.lstrip("-").isdigit() and int(user_part) == sender_id:
                        match = True
                    elif username and user_part == username:
                        match = True

                    if match:
                        if g_val in ["ж", "женский", "female", "f"]:
                            return "женский"
                        elif g_val in ["м", "мужской", "male", "m"]:
                            return "мужской"
                        elif g_val in ["дефолт", "по умолчанию", "default"]:
                            return "по умолчанию"

        if owner_id and sender_id == owner_id:
            return str(self.config["gender"]).lower().strip()

        return str(self.config["gender"]).lower().strip()

    async def _ask_gender(self, message: Message, sender):
        sender_id = getattr(message, "sender_id", None) or (getattr(sender, "id", None) if sender else None)
        sender_name = utils.escape_html(get_display_name(sender)) if sender else "Пользователь"
        sender_link = f'<a href="tg://user?id={sender_id}">{sender_name}</a>' if sender_id else sender_name

        prompt_text = (
            f"👋 <b>{sender_link}</b>, вы используете RP-команду впервые!\n\n"
            "Укажите ваш пол для правильных окончаний глаголов (<i>поцеловал / поцеловала</i>):"
        )

        inline_sent = False
        if hasattr(self, "inline") and self.inline:
            try:
                await self.inline.form(
                    text=prompt_text,
                    message=message,
                    reply_markup=[
                        [
                            {
                                "text": "👨 Мужской",
                                "callback": self._gender_callback,
                                "args": (sender_id, "мужской"),
                            },
                            {
                                "text": "👩 Женский",
                                "callback": self._gender_callback,
                                "args": (sender_id, "женский"),
                            },
                        ]
                    ],
                    always_allow=True,
                )
                inline_sent = True
            except Exception as e:
                logger.warning(f"[KissMod] inline.form failed: {e}")

        if not inline_sent:
            fallback_text = (
                f"{prompt_text}\n\n"
                "👉 <b>Ответьте на это сообщение:</b> <code>м</code> (мужской) или <code>ж</code> (женский)"
            )
            prompt_msg = await utils.answer(message, fallback_text)
            if sender_id and sender_id in self._pending_commands:
                self._pending_commands[sender_id]["prompt_msg"] = prompt_msg

    async def _gender_callback(self, call, target_user_id: int, gender: str):
        from_user = getattr(call, "from_user", None)
        user_id = getattr(from_user, "id", None)
        if not user_id or user_id != int(target_user_id):
            await call.answer("❌ Это выбор не для вас!", show_alert=True)
            return

        username = getattr(from_user, "username", None)
        self._set_saved_gender(int(target_user_id), gender, username)
        await call.answer(f"✅ Выбран {gender} пол!", show_alert=False)

        pending = self._pending_commands.pop(int(target_user_id), None)

        try:
            await call.delete()
        except Exception:
            try:
                await call.edit(f"✅ Пол сохранён: <b>{gender}</b>")
            except Exception:
                pass

        if pending:
            orig_msg = pending["message"]
            func = pending["func"]
            try:
                await func(orig_msg)
            except Exception as e:
                logger.error(f"[KissMod] Pending command execution error: {e}")

    @loader.command(
        ru_doc="— Включить/выключить доступ к RP-командам для текущей группы",
        en_doc="— Enable/disable access to RP commands for current group",
    )
    async def kisschatcmd(self, message: Message):
        """Включить/выключить доступ к RP-командам для текущей группы"""
        if not (message.is_group or message.is_channel):
            await utils.answer(message, "<b>⚠️ Эта команда работает только в группах!</b>")
            return

        chat_id_str = str(message.chat_id)
        raw_chats = self.config["allowed_chats"]
        current_chats = []
        if raw_chats:
            if isinstance(raw_chats, str):
                current_chats = [c.strip() for c in re.split(r"[,\s]+", raw_chats.strip()) if c.strip()]
            elif isinstance(raw_chats, (list, tuple)):
                current_chats = [str(c).strip() for c in raw_chats if str(c).strip()]

        if chat_id_str in current_chats:
            current_chats.remove(chat_id_str)
            self.config["allowed_chats"] = ", ".join(current_chats)
            await utils.answer(message, "<b>❌ RP-команды выключены для этой группы!</b>")
        else:
            current_chats.append(chat_id_str)
            self.config["allowed_chats"] = ", ".join(current_chats)
            await utils.answer(
                message,
                "<b>✅ RP-команды включены для этой группы!</b>\n"
                "<i>Все участники теперь могут использовать RP-команды. При первом вызове бот спросит их пол.</i>"
            )

    @loader.command(
        ru_doc="[м/ж] — Установить или изменить свой гендер для RP-команд",
        en_doc="[m/f] — Set or change your gender for RP commands",
    )
    async def kissgendercmd(self, message: Message):
        """[м/ж] — Установить или изменить свой гендер для RP-команд"""
        args = utils.get_args_raw(message).strip().lower()
        sender = await message.get_sender() if hasattr(message, "get_sender") else getattr(message, "sender", None)
        sender_id = getattr(message, "sender_id", None) or (getattr(sender, "id", None) if sender else None)

        if not sender_id:
            return

        if not args:
            cur = self._get_gender_for_sender(sender)
            await utils.answer(
                message,
                f"👤 <b>Ваш текущий пол:</b> <code>{cur}</code>\n\n"
                "Чтобы изменить: <code>.kissgender м</code> или <code>.kissgender ж</code>"
            )
            return

        gender = None
        if args in ["м", "муж", "мужской", "парень", "male", "m", "1"]:
            gender = "мужской"
        elif args in ["ж", "жен", "женский", "девушка", "female", "f", "2"]:
            gender = "женский"
        elif args in ["дефолт", "по умолчанию", "default", "0"]:
            gender = "по умолчанию"

        if not gender:
            await utils.answer(
                message,
                "⚠️ Укажите пол: <code>.kissgender м</code> (мужской) или <code>.kissgender ж</code> (женский)"
            )
            return

        username = getattr(sender, "username", None) if sender else None
        self._set_saved_gender(sender_id, gender, username)
        await utils.answer(message, f"✅ Ваш пол успешно установлен: <b>{gender}</b>!")

    @loader.watcher()
    async def watcher(self, message: Message):
        if not isinstance(message, Message):
            return
        if getattr(message, "out", False):
            return

        sender_id = getattr(message, "sender_id", None)
        text = message.raw_text or message.text or ""
        text_clean = text.strip()

        # 1. Проверяем, отвечает ли пользователь на текстовый запрос пола
        if sender_id and sender_id in self._pending_commands:
            now = asyncio.get_event_loop().time()
            if now - self._pending_commands[sender_id].get("time", 0) > 300:
                self._pending_commands.pop(sender_id, None)
            else:
                detected = None
                t_low = text_clean.lower()
                if t_low in ["м", "муж", "мужской", "парень", "male", "m", "1"]:
                    detected = "мужской"
                elif t_low in ["ж", "жен", "женский", "девушка", "female", "f", "2"]:
                    detected = "женский"

                if detected:
                    sender = await message.get_sender() if hasattr(message, "get_sender") else getattr(message, "sender", None)
                    username = getattr(sender, "username", None)
                    self._set_saved_gender(sender_id, detected, username)

                    pending = self._pending_commands.pop(sender_id, None)
                    if pending:
                        prompt_msg = pending.get("prompt_msg")
                        if prompt_msg:
                            try:
                                await prompt_msg.delete()
                            except Exception:
                                pass
                        try:
                            await message.delete()
                        except Exception:
                            pass
                        orig_msg = pending["message"]
                        func = pending["func"]
                        try:
                            await func(orig_msg)
                        except Exception as e:
                            logger.error(f"[KissMod] Pending command execution error: {e}")
                    return

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

        body = text[len(matched_prefix):].strip()
        if not body:
            return

        cmd_name = body.split()[0].lower()

        if not self._is_allowed(message):
            return

        # Специальная команда смены гендера для участников
        if cmd_name in ["kissgender", "rpgender"]:
            try:
                await self.kissgendercmd(message)
            except Exception as e:
                logger.error(f"[KissMod] kissgender error: {e}")
            return

        rp_map = self._get_rp_map()
        func = rp_map.get(cmd_name)
        if not func:
            return

        sender = await message.get_sender() if hasattr(message, "get_sender") else getattr(message, "sender", None)

        # 2. Если включен опрос пола и пол ещё не известен — спрашиваем пол
        if self.config["ask_gender"] and not self._has_known_gender(sender):
            self._pending_commands[sender_id] = {
                "message": message,
                "func": func,
                "time": asyncio.get_event_loop().time(),
                "cmd_name": cmd_name,
            }
            await self._ask_gender(message, sender)
            return

        # 3. Выполняем RP-команду
        try:
            await func(message)
        except Exception as e:
            logger.error(f"[KissMod] watcher execution error for {cmd_name}: {e}")

    def _format_verb(self, verb: str, sender=None) -> str:
        gender = self._get_gender_for_sender(sender)
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
                if message.out:
                    target_entity = await message.get_chat()
                else:
                    target_entity = await message.client.get_me()
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
                if message.out:
                    target1 = await message.get_chat()
                else:
                    target1 = await message.client.get_me()
            except Exception:
                pass

        if not target2 and reply_sender and getattr(target1, "id", None) != getattr(reply_sender, "id", None):
            target2 = reply_sender

        extra_text = " ".join(words[used:]).strip()
        return target1, target2, extra_text

    async def _send_action(self, message: Message, emoji: str, action_verb: str, post_target: str = ""):
        sender = await message.get_sender()
        if not sender:
            sender = await message.client.get_me()

        target_entity, extra_text = await self._get_target_and_extra(message)

        if not target_entity:
            await utils.answer(message, self.strings("no_target"))
            return

        sender_name = utils.escape_html(get_display_name(sender))
        sender_id = getattr(sender, "id", 0)
        sender_link = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

        target_name = utils.escape_html(get_display_name(target_entity))
        target_id = getattr(target_entity, "id", 0)
        target_link = f'<a href="tg://user?id={target_id}">{target_name}</a>'

        formatted_verb = self._format_verb(action_verb, sender=sender)
        post_str = f" {post_target}" if post_target else ""
        out = f"{emoji} <b>{sender_link} {formatted_verb} {target_link}{post_str}!</b>"

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
        sender = await message.get_sender()
        if not sender:
            sender = await message.client.get_me()

        t1, t2, extra_text = await self._get_two_targets_and_extra(message)

        if not t1 or not t2:
            await utils.answer(message, self.strings("no_two_targets"))
            return

        sender_name = utils.escape_html(get_display_name(sender))
        sender_id = getattr(sender, "id", 0)
        sender_link = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

        t1_name = utils.escape_html(get_display_name(t1))
        t1_link = f'<a href="tg://user?id={getattr(t1, "id", 0)}">{t1_name}</a>'

        t2_name = utils.escape_html(get_display_name(t2))
        t2_link = f'<a href="tg://user?id={getattr(t2, "id", 0)}">{t2_name}</a>'

        formatted_verb = self._format_verb(verb_between, sender=sender)
        post = f" {post_str}" if post_str else ""
        out = f"{emoji} <b>{sender_link} {formatted_verb} {t1_link} {prep_target2} {t2_link}{post}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    async def _send_all_action(self, message: Message, emoji: str, action_verb: str, target_all_phrase: str):
        sender = await message.get_sender()
        if not sender:
            sender = await message.client.get_me()
        extra_text = utils.get_args_raw(message).strip()

        sender_name = utils.escape_html(get_display_name(sender))
        sender_id = getattr(sender, "id", 0)
        sender_link = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

        formatted_verb = self._format_verb(action_verb, sender=sender)
        out = f"{emoji} <b>{sender_link} {formatted_verb} {target_all_phrase}!</b>"

        if extra_text:
            out += f"\n<i>«{html.escape(extra_text)}»</i>"

        await utils.answer(message, out)

    async def _send_solo_action(self, message: Message, emoji: str, action_verb: str):
        sender = await message.get_sender()
        if not sender:
            sender = await message.client.get_me()

        extra_text = utils.get_args_raw(message).strip()

        sender_name = utils.escape_html(get_display_name(sender))
        sender_id = getattr(sender, "id", 0)
        sender_link = f'<a href="tg://user?id={sender_id}">{sender_name}</a>'

        formatted_verb = self._format_verb(action_verb, sender=sender)
        out = f"{emoji} <b>{sender_link} {formatted_verb}!</b>"

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
        ru_doc="[@username / reply / extra] — Поцеловать в лобик",
        en_doc="[@username / reply / extra] — Kiss on the forehead",
    )
    async def kiscmd(self, message: Message):
        """[@username / reply / extra] — Kiss on the forehead"""
        await self._send_action(message, "💋", "поцеловал(а) в лобик")

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
    async def footkickcmd(self, message: Message):
        """[@username / reply / extra] — Kick"""
        await self._send_action(message, "🦶", "пнул(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Пнуть",
        en_doc="[@username / reply / extra] — Kick",
    )
    async def fkickcmd(self, message: Message):
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

    @loader.command(
        ru_doc="[@username / reply / extra] — Укутать в пледик",
        en_doc="[@username / reply / extra] — Wrap in a blanket",
    )
    async def blanketcmd(self, message: Message):
        """[@username / reply / extra] — Wrap in a blanket"""
        await self._send_action(message, "🧣", "укутал(а)", "в пледик")

    @loader.command(
        ru_doc="[@username / reply / extra] — Налить чаю",
        en_doc="[@username / reply / extra] — Pour tea",
    )
    async def teacmd(self, message: Message):
        """[@username / reply / extra] — Pour tea"""
        await self._send_action(message, "☕", "налил(а) чаю")

    @loader.command(
        ru_doc="[@username / reply / extra] — Потискать за щёчки",
        en_doc="[@username / reply / extra] — Squish cheeks",
    )
    async def squishcmd(self, message: Message):
        """[@username / reply / extra] — Squish cheeks"""
        await self._send_action(message, "🤏", "потискал(а)", "за щёчки")

    @loader.command(
        ru_doc="[@username / reply / extra] — Игриво ущипнуть",
        en_doc="[@username / reply / extra] — Playfully pinch",
    )
    async def pinchcmd(self, message: Message):
        """[@username / reply / extra] — Playfully pinch"""
        await self._send_action(message, "🤏", "игриво ущипнул(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Испепелить взглядом",
        en_doc="[@username / reply / extra] — Incinerate with a glance",
    )
    async def burncmd(self, message: Message):
        """[@username / reply / extra] — Incinerate with a glance"""
        await self._send_action(message, "💀", "испепелил(а)", "взглядом")

    @loader.command(
        ru_doc="[@username / reply / extra] — Испепелить взглядом",
        en_doc="[@username / reply / extra] — Incinerate with a glance",
    )
    async def incineratecmd(self, message: Message):
        """[@username / reply / extra] — Incinerate with a glance"""
        await self._send_action(message, "💀", "испепелил(а)", "взглядом")

    @loader.command(
        ru_doc="[@username / reply / extra] — Погладить по голове",
        en_doc="[@username / reply / extra] — Pat on the head",
    )
    async def patcmd(self, message: Message):
        """[@username / reply / extra] — Pat on the head"""
        await self._send_action(message, "🫳", "погладил(а)", "по голове")

    @loader.command(
        ru_doc="[@username / reply / extra] — Взять за ручку",
        en_doc="[@username / reply / extra] — Hold hand",
    )
    async def holdcmd(self, message: Message):
        """[@username / reply / extra] — Hold hand"""
        await self._send_action(message, "🤝", "взял(а) за ручку")

    @loader.command(
        ru_doc="[@username / reply / extra] — Дать печеньку",
        en_doc="[@username / reply / extra] — Give a cookie",
    )
    async def cookiecmd(self, message: Message):
        """[@username / reply / extra] — Give a cookie"""
        await self._send_action(message, "🍪", "дал(а) печеньку")

    @loader.command(
        ru_doc="[@username / reply / extra] — Налить кофе",
        en_doc="[@username / reply / extra] — Pour coffee",
    )
    async def coffeecmd(self, message: Message):
        """[@username / reply / extra] — Pour coffee"""
        await self._send_action(message, "☕️", "налил(а) кофе")

    @loader.command(
        ru_doc="[@username / reply / extra] — Поцеловать в шею",
        en_doc="[@username / reply / extra] — Kiss neck",
    )
    async def kissneckcmd(self, message: Message):
        """[@username / reply / extra] — Kiss neck"""
        await self._send_action(message, "💋", "поцеловал(а) в шею")

    @loader.command(
        ru_doc="[@username / reply / extra] — Признаться в любви",
        en_doc="[@username / reply / extra] — Confess love",
    )
    async def lovecmd(self, message: Message):
        """[@username / reply / extra] — Confess love"""
        await self._send_action(message, "❤️", "признался(ась) в любви")

    @loader.command(
        ru_doc="[@username / reply / extra] — Уложить спать",
        en_doc="[@username / reply / extra] — Put to sleep",
    )
    async def sleepcmd(self, message: Message):
        """[@username / reply / extra] — Put to sleep"""
        await self._send_action(message, "💤", "уложил(а) спать")

    @loader.command(
        ru_doc="[@username / reply / extra] — Сделать массаж",
        en_doc="[@username / reply / extra] — Give a massage",
    )
    async def massagecmd(self, message: Message):
        """[@username / reply / extra] — Give a massage"""
        await self._send_action(message, "💆", "сделал(а) массаж")

    @loader.command(
        ru_doc="[extra] — Забутониться",
        en_doc="[extra] — Curl up like a bud",
    )
    async def batoncmd(self, message: Message):
        """[extra] — Curl up like a bud"""
        await self._send_solo_action(message, "🧣", "забатонился(ась)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Почухать",
        en_doc="[@username / reply / extra] — Scratch",
    )
    async def chuhcmd(self, message: Message):
        """[@username / reply / extra] — Scratch"""
        await self._send_action(message, "💅", "почухал(а)")

    @loader.command(
        ru_doc="[@username / reply / extra] — Зачухать",
        en_doc="[@username / reply / extra] — Scratch intensely",
    )
    async def zachuhcmd(self, message: Message):
        """[@username / reply / extra] — Scratch intensely"""
        await self._send_action(message, "💅", "зачухал(а)")

    @loader.command(
        ru_doc="[extra] — Мурчать",
        en_doc="[extra] — Purr",
    )
    async def murrcmd(self, message: Message):
        """[extra] — Purr"""
        await self._send_solo_action(message, "🐈", "помурчал(а)")

    @loader.command(
        ru_doc="[extra] — Помяукать",
        en_doc="[extra] — Meow",
    )
    async def meowcmd(self, message: Message):
        """[extra] — Meow"""
        await self._send_solo_action(message, "🐈‍⬛", "помяукал(а)")

    @loader.command(
        ru_doc="— Анимированное признание в любви с сердечками",
        en_doc="— Animated love confession with hearts",
    )
    async def iloveyoucmd(self, message: Message):
        """— Animated love confession with hearts"""
        frames = [
            "❤️",
            "❤️❤️❤️",
            "❤️❤️❤️❤️❤️",
            "❤️❤️❤️❤️❤️❤️",
            "❤️❤️❤️❤️❤️❤️\n❤️⠀⠀⠀⠀❤️\n❤️⠀⠀⠀⠀❤️\n❤️⠀⠀⠀⠀❤️\n❤️❤️❤️❤️❤️❤️",
            "🤍🤍🤍🤍🤍🤍\n🤍 ай⠀⠀⠀🤍\n🤍⠀⠀⠀⠀🤍\n🤍⠀⠀⠀⠀🤍\n🤍🤍🤍🤍🤍🤍",
            "🤍🤍🤍🤍🤍🤍\n🤍 ай ладно...🤍\n🤍⠀⠀⠀⠀🤍\n🤍⠀⠀⠀⠀🤍\n🤍🤍🤍🤍🤍🤍",
            "🤍🤍🤍🤍🤍🤍\n🤍 ай ладно...🤍\n🤍 ты мне ⠀🤍🤍\n🤍⠀⠀⠀⠀🤍\n🤍🤍🤍🤍🤍🤍",
            "🤍🤍🤍🤍🤍🤍\n🤍 ай ладно...🤍\n🤍 ты мне ⠀🤍🤍\n🤍 нравишься 🤍\n🤍🤍🤍🤍🤍🤍",
        ]

        for frame in frames:
            try:
                await utils.answer(message, frame)
            except Exception:
                pass
            await asyncio.sleep(0.3)

    @loader.command(
        ru_doc="Показать шпаргалку RP-команд",
        en_doc="Show cheat sheet of RP commands",
    )
    async def kisshelpcmd(self, message: Message):
        """Show cheat sheet of RP commands"""
        await self._show_help(message)

    async def _show_help(self, message: Message):
        help_text = (
            "<b>✨ Шпаргалка RP-действий</b>\n"
            "<i>(Укажите юзернейм/ID, ответьте на сообщение или используйте в ЛС)</i>\n\n"
            "<b>💖 Забота и нежность:</b>\n"
            "🧣 <code>.baton</code> — забутониться\n"
            "🐈 <code>.murr</code> — помурчать\n"
            "🐈‍⬛ <code>.meow</code> — помяукать\n"
            "💅 <code>.chuh</code> — почухать\n"
            "💅 <code>.zachuh</code> — зачухать\n"
            "💋 <code>.kis</code> — поцеловать в лобик\n"
            "💋 <code>.kiss</code> — поцеловать в щёчку\n"
            "💋 <code>.kissneck</code> — поцеловать в шею\n"
            "💋 <code>.kisss</code> — поцеловать в засос\n"
            "🫂 <code>.hug</code> — крепко обнять\n"
            "🫂 <code>.hig</code> — приобнять\n"
            "🫳 <code>.pat</code> | <code>.patt</code> — погладить по голове\n"
            "🥰 <code>.cuddle</code> — прижаться к себе\n"
            "🤝 <code>.hold</code> | <code>.handhold</code> — взять за руку\n"
            "🧣 <code>.blanket</code> — укутать в пледик\n"
            "🍓 <code>.feed</code> — покормить вкусняшкой\n"
            "🍪 <code>.cookie</code> — дать печеньку\n"
            "☕ <code>.tea</code> — налить чаю\n"
            "☕️ <code>.coffee</code> — налить кофе\n"
            "❤️ <code>.love</code> — признаться в любви\n"
            "🤍 <code>.iloveyou</code> — анимированное признание в любви\n"
            "💤 <code>.sleep</code> — уложить спать\n"
            "💆 <code>.massage</code> — сделать массаж\n\n"
            "<b>😏 Игривые и флирт:</b>\n"
            "👅 <code>.lick</code> — лизнуть\n"
            "😼 <code>.bite</code> — укусить\n"
            "🦮 <code>.gbite</code> — нежный кусь\n"
            "🤏 <code>.squish</code> — потискать за щёчки\n"
            "🤏 <code>.pinch</code> — игриво ущипнуть\n"
            "👉 <code>.poke</code> — тыкнуть пальцем\n"
            "👉 <code>.boop</code> — тыкнуть в носик\n"
            "😉 <code>.wink</code> — подмигнуть\n"
            "🍑 <code>.spank</code> — шлёпнуть по попке\n\n"
            "<b>🔥 Горячие и 18+:</b>\n"
            "🍑 <code>.sitface</code> — сесть на лицо\n"
            "👐 <code>.grope</code> — полапать за интимные места\n"
            "🤲 <code>.feel</code> — помацать\n"
            "👅 <code>.otl</code> — отлизать\n"
            "😮‍💨 <code>.ots</code> — отсосать\n"
            "👉👌 <code>.fuck</code> — трахнуть\n"
            "🔞 <code>.rape</code> — изнасиловать\n\n"
            "<b>⚡️ Агрессия и урон:</b>\n"
            "👋 <code>.slap</code> — дать пощёчину\n"
            "👊 <code>.hit</code> — смачно ударить\n"
            "🦶 <code>.fkick</code> | <code>.footkick</code> — пнуть\n"
            "🫲 <code>.headslap</code> — дать подзатыльник\n"
            "🤏 <code>.tickle</code> — пощекотать\n"
            "💀 <code>.burn</code> | <code>.incinerate</code> — испепелить взглядом\n\n"
            "<b>👥 Парные команды:</b>\n"
            "🤣 <code>.laugh</code> — посмеяться с @user1 над @user2\n"
            "👩‍❤️‍👨 <code>.ship</code> — зашипперить @user1 с @user2\n"
            "🗣 <code>.gossip</code> — посплетничать с @user1 о @user2\n\n"
            "<b>🌐 Массовые (на всех):</b>\n"
            "🫂 <code>.huga</code> | 😮‍💨 <code>.otsa</code> | 👅 <code>.otla</code> | 👉👌 <code>.fucka</code>"
        )
        await utils.answer(message, help_text)
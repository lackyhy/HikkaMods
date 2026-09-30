# meta developer: @lackyhyyy666

import logging
from telethon import events
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class ModControlMod(loader.Module):
    """Модуль управления доступом и блокировкой стороннего вызова пользовательских модулей"""

    strings = {
        "name": "ModControl",
        "enabled": "🔒 <b>Блокировка сторонних команд ВКЛЮЧЕНА!</b>\n<i>Пользовательские модули (кроме исключений) недоступны другим юзерам.</i>",
        "disabled": "🔓 <b>Блокировка сторонних команд ВЫКЛЮЧЕНА!</b>\n<i>Все модули работают в обычном режиме.</i>",
        "ignored_add": "✅ <b>Модуль добавлен в белый список (разрешён для всех):</b> <code>{}</code>",
        "ignored_remove": "❌ <b>Модуль удален из белого списка:</b> <code>{}</code>",
        "ignored_list": "📋 <b>Список игнорируемых (всегда разрешенных) модулей:</b>\n{}",
        "ignored_empty": "ℹ️ <b>Список исключений пуст. Все пользовательские модули блокируются для сторонних юзеров.</b>",
        "status": (
            "⚙️ <b>Статус ModControl:</b>\n"
            "• <b>Блокировка сторонних команд:</b> {}\n"
            "• <b>Игнорируемые модули (белый список):</b> <code>{}</code> шт.\n"
            "• <b>Всего загружено модулей:</b> <code>{}</code> шт."
        ),
        "no_args": "<b>⚠️ Укажите название модуля! (Например: <code>.modignore Kiss</code>)</b>",
    }

    strings_ru = {
        "enabled": "🔒 <b>Блокировка сторонних команд ВКЛЮЧЕНА!</b>\n<i>Пользовательские модули (кроме исключений) недоступны другим юзерам.</i>",
        "disabled": "🔓 <b>Блокировка сторонних команд ВЫКЛЮЧЕНА!</b>\n<i>Все модули работают в обычном режиме.</i>",
        "ignored_add": "✅ <b>Модуль добавлен в белый список (разрешён для всех):</b> <code>{}</code>",
        "ignored_remove": "❌ <b>Модуль удален из белого списка:</b> <code>{}</code>",
        "ignored_list": "📋 <b>Список игнорируемых (всегда разрешенных) модулей:</b>\n{}",
        "ignored_empty": "ℹ️ <b>Список исключений пуст. Все пользовательские модули блокируются для сторонних юзеров.</b>",
        "status": (
            "⚙️ <b>Статус ModControl:</b>\n"
            "• <b>Блокировка сторонних команд:</b> {}\n"
            "• <b>Игнорируемые модули (белый список):</b> <code>{}</code> шт.\n"
            "• <b>Всего загружено модулей:</b> <code>{}</code> шт."
        ),
        "no_args": "<b>⚠️ Укажите название модуля! (Например: <code>.modignore Kiss</code>)</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включена ли блокировка выполнения сторонних вызовов команд пользовательских модулей",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ignored_modules",
                [],
                lambda: "Список имен или классов модулей-исключений (работают всегда)",
                validator=loader.validators.Series(
                    validator=loader.validators.String()
                )
                if hasattr(loader.validators, "Series")
                else loader.validators.List(),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

        # Перехватываем входящие сообщения на самом высоком приоритете в Telethon
        try:
            if hasattr(client, "list_event_handlers"):
                handlers = client.list_event_handlers()
                for handler, builder in list(handlers):
                    if getattr(handler, "__name__", "") == "_on_incoming_check":
                        client.remove_event_handler(handler, builder)
        except Exception:
            pass

        client.add_event_handler(self._on_incoming_check, events.NewMessage(incoming=True))

        # Перемещаем наш хэндлер в самое начало очереди client._events
        try:
            if hasattr(client, "_events") and isinstance(client._events, list):
                for i, (handler, builder) in enumerate(list(client._events)):
                    if getattr(handler, "__name__", "") == "_on_incoming_check":
                        item = client._events.pop(i)
                        client._events.insert(0, item)
                        break
        except Exception:
            pass

    async def _on_incoming_check(self, event):
        """Перехватчик входящих сообщений для блокировки выполнения команд других пользователей"""
        if not self.config["enabled"]:
            return

        message = getattr(event, "message", event)
        if not message or not getattr(message, "raw_text", None):
            return

        # Если сообщение от владельца бота (исходящее или от me.id), разрешаем
        if getattr(message, "out", False):
            return

        try:
            me = await self.client.get_me()
            if getattr(message, "sender_id", None) == me.id:
                return
        except Exception:
            pass

        text = message.raw_text.strip()
        if not text:
            return

        # Получаем список префиксов Hikka
        prefixes = [".", ",", "/", "!"]
        try:
            if hasattr(self, "allmodules") and hasattr(self.allmodules, "prefix"):
                p = self.allmodules.prefix
                if isinstance(p, str):
                    prefixes = [p]
                elif isinstance(p, (list, tuple, set)):
                    prefixes = list(p)
        except Exception:
            pass

        matched_prefix = None
        for pref in prefixes:
            if text.startswith(pref):
                matched_prefix = pref
                break

        if not matched_prefix:
            return

        # Извлекаем имя команды
        cmd_name = text[len(matched_prefix):].split()[0].lower()

        # Получаем информацию о модуле, которому принадлежит команда
        mod_name, is_core = self._find_module_by_cmd(cmd_name)

        # Системные модули Hikka всегда разрешены
        if is_core or mod_name in ["loadermod", "helpmod", "adminmod", "modcontrolmod", "modcontrol"]:
            return

        # Проверяем белый список (список исключений)
        ignored_list = [str(x).lower().strip() for x in self._get_ignored_modules()]

        if mod_name and (mod_name.lower() in ignored_list or cmd_name.lower() in ignored_list):
            return

        # Если модуль не в белом списке и блокировка активна - останавливаем обработку команды!
        raise events.StopPropagation

    def _get_ignored_modules(self):
        raw = self.config["ignored_modules"]
        if isinstance(raw, (list, tuple, set)):
            return list(raw)
        elif isinstance(raw, str):
            return [x.strip() for x in raw.split(",") if x.strip()]
        return []

    def _find_module_by_cmd(self, cmd_name: str):
        """Определяет имя модуля по имени команды"""
        cmd_name = cmd_name.lower().strip()

        try:
            modules = []
            if hasattr(self, "allmodules") and hasattr(self.allmodules, "modules"):
                modules = self.allmodules.modules
            elif hasattr(self, "lookup"):
                modules = list(self.lookup.values())

            for mod in modules:
                mod_class_name = mod.__class__.__name__
                mod_string_name = getattr(mod, "strings", {}).get("name", mod_class_name)

                # Проверяем методы модуля
                for attr_name in dir(mod):
                    if attr_name.endswith("cmd") and attr_name[:-3].lower() == cmd_name:
                        is_core = mod_class_name in ["LoaderMod", "HelpMod", "AdminMod", "ModControlMod"]
                        return mod_string_name, is_core

                # Проверяем словари команд если есть
                if hasattr(mod, "commands") and isinstance(mod.commands, dict):
                    if cmd_name in [c.lower() for c in mod.commands.keys()]:
                        is_core = mod_class_name in ["LoaderMod", "HelpMod", "AdminMod", "ModControlMod"]
                        return mod_string_name, is_core

        except Exception:
            pass

        return None, False

    @loader.command(
        ru_doc="Переключить блокировку выполнения сторонних команд пользовательских модулей",
        en_doc="Toggle blocking third-party execution of custom module commands",
    )
    async def togglemods(self, message):
        """Toggle blocking third-party execution of custom module commands"""
        new_state = not self.config["enabled"]
        self.config["enabled"] = new_state
        if new_state:
            await utils.answer(message, self.strings("enabled"))
        else:
            await utils.answer(message, self.strings("disabled"))

    @loader.command(
        ru_doc="Переключить блокировку выполнения сторонних команд",
        en_doc="Toggle blocking third-party execution of custom module commands",
    )
    async def modtoggle(self, message):
        """Toggle blocking third-party execution of custom module commands"""
        await self.togglemods(message)

    @loader.command(
        ru_doc="[Название] — Добавить или удалить модуль из списка исключений (белого списка)",
        en_doc="[Name] — Add or remove module from whitelist/ignore list",
    )
    async def modignore(self, message):
        """[Name] — Add or remove module from whitelist/ignore list"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return

        ignored = [str(x).strip() for x in self._get_ignored_modules()]
        target = args

        # Регистронезависимая проверка
        found = None
        for item in ignored:
            if item.lower() == target.lower():
                found = item
                break

        if found:
            ignored.remove(found)
            is_added = False
        else:
            ignored.append(target)
            is_added = True

        self.config["ignored_modules"] = ignored

        if is_added:
            await utils.answer(message, self.strings("ignored_add").format(target))
        else:
            await utils.answer(message, self.strings("ignored_remove").format(target))

    @loader.command(
        ru_doc="Показать список игнорируемых (разрешенных) модулей",
        en_doc="Show list of whitelisted modules",
    )
    async def modignorelist(self, message):
        """Show list of whitelisted modules"""
        ignored = self._get_ignored_modules()
        if not ignored:
            await utils.answer(message, self.strings("ignored_empty"))
            return

        res = [f"• <code>{item}</code>" for item in ignored]
        await utils.answer(
            message,
            self.strings("ignored_list").format("\n".join(res)),
        )

    @loader.command(
        ru_doc="Показать статус блокировки и список загруженных модулей",
        en_doc="Show module blocking status",
    )
    async def modstatus(self, message):
        """Show module blocking status"""
        total_mods = 0
        try:
            if hasattr(self, "allmodules") and hasattr(self.allmodules, "modules"):
                total_mods = len(self.allmodules.modules)
        except Exception:
            pass

        state_str = "<b>ВКЛЮЧЕНА</b> 🔒" if self.config["enabled"] else "<b>ВЫКЛЮЧЕНА</b> 🔓"
        ignored_count = len(self._get_ignored_modules())

        await utils.answer(
            message,
            self.strings("status").format(state_str, ignored_count, total_mods),
        )

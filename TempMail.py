# meta developer: @lackyhyyy666
# scope: hikka

import time
import aiohttp
from .. import loader, utils


@loader.tds
class TempMailMod(loader.Module):
    """Временная почта с уведомлениями через mail.tm"""

    strings = {"name": "TempMail"}

    def __init__(self):
        self.config = loader.ModuleConfig()
        # Храним данные созданных аккаунтов в памяти: {chat_id: account_data}
        self.email_accounts = {}

    async def _api_request(self, method: str, endpoint: str, json_data: dict = None, headers: dict = None):
        """Вспомогательный метод для асинхронных HTTP-запросов"""
        url = f"https://api.mail.tm{endpoint}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(method, url, json=json_data, headers=headers, timeout=10) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json(), None
                    return None, f"Ошибка API ({resp.status})"
            except Exception as e:
                return None, f"Ошибка сети: {str(e)}"

    async def _create_email_account(self):
        """Создание аккаунта на mail.tm"""
        # 1. Получаем домены
        data, err = await self._api_request("GET", "/domains")
        if err or not data or not data.get("hydra:member"):
            return None, err or "Домены недоступны"
        domain = data["hydra:member"][0]["domain"]

        # 2. Генерируем почту и пароль
        email = f"user{int(time.time())}@{domain}"
        password = "TempPass123!"

        # 3. Регистрируем аккаунт
        _, err = await self._api_request("POST", "/accounts", json_data={"address": email, "password": password})
        if err:
            return None, f"Не удалось создать аккаунт: {err}"

        # 4. Получаем токен авторизации
        token_data, err = await self._api_request("POST", "/token", json_data={"address": email, "password": password})
        if err or not token_data or not token_data.get("token"):
            return None, f"Не удалось получить токен: {err}"

        return {
            "email": email,
            "password": password,
            "token": token_data["token"],
            "domain": domain,
            "created_at": time.time(),
        }, None

    async def _check_emails(self, token: str):
        """Проверка входящих писем"""
        headers = {"Authorization": f"Bearer {token}"}
        data, err = await self._api_request("GET", "/messages", headers=headers)
        if err or not data or "hydra:member" not in data:
            return None, err or "Не удалось получить список писем"

        messages = data["hydra:member"]
        if not messages:
            return [], None

        full_messages = []
        for msg in messages:
            msg_data, _ = await self._api_request("GET", f"/messages/{msg['id']}", headers=headers)
            if msg_data:
                full_messages.append(msg_data)

        return full_messages, None

    @loader.command()
    async def mail(self, message):
        """Создать новый временный email"""
        message = await utils.answer(message, "🔄 <b>Создаем временный email...</b>")

        account_data, error = await self._create_email_account()
        if error:
            await utils.answer(message, f"❌ <b>{error}</b>")
            return

        chat_id = message.chat_id
        self.email_accounts[chat_id] = account_data

        text = (
            f"✅ <b>Временный email создан!</b>\n\n"
            f"📧 <b>Email:</b> <code>{account_data['email']}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{account_data['password']}</code>\n\n"
            f"<i>Используйте <code>.mailcheck</code> для проверки входящих писем.</i>"
        )
        await utils.answer(message, text)

    @loader.command()
    async def mailrefresh(self, message):
        """Создать новую почту (перезаписать текущую)"""
        message = await utils.answer(message, "🔄 <b>Генерируем новый адрес почты...</b>")

        account_data, error = await self._create_email_account()
        if error:
            await utils.answer(message, f"❌ <b>{error}</b>")
            return

        chat_id = message.chat_id
        self.email_accounts[chat_id] = account_data

        text = (
            f"🔄 <b>Почта успешно обновлена!</b>\n\n"
            f"📧 <b>Новый Email:</b> <code>{account_data['email']}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{account_data['password']}</code>\n\n"
            f"<i>Старый ящик для этого чата перезаписан.</i>"
        )
        await utils.answer(message, text)

    @loader.command()
    async def mailcheck(self, message):
        """Проверить входящие письма"""
        chat_id = message.chat_id
        if chat_id not in self.email_accounts:
            await utils.answer(message, "❌ <b>Сначала создайте email командой <code>.mail</code></b>")
            return

        message = await utils.answer(message, "🔄 <b>Проверяем входящие письма...</b>")
        account_data = self.email_accounts[chat_id]

        messages_list, error = await self._check_emails(account_data["token"])
        if error:
            await utils.answer(message, f"❌ <b>{error}</b>")
            return

        if not messages_list:
            await utils.answer(message, "📭 <b>Входящих писем пока нет.</b>")
            return

        response_text = f"📧 <b>Получено писем: {len(messages_list)}</b>\n\n"
        for msg in messages_list:
            from_addr = utils.escape_html(msg.get("from", {}).get("address", "Неизвестно"))
            subject = utils.escape_html(msg.get("subject") or "Без темы")
            body = msg.get("text", "")
            preview = utils.escape_html(body[:150] + "..." if len(body) > 150 else body)

            response_text += (
                f"<b>От:</b> <code>{from_addr}</code>\n"
                f"<b>Тема:</b> {subject}\n"
                f"<b>Текст:</b>\n<i>{preview}</i>\n"
                f"───────────────\n"
            )

        await utils.answer(message, response_text)

    @loader.command()
    async def mailinfo(self, message):
        """Показать текущий email и пароль"""
        chat_id = message.chat_id
        if chat_id not in self.email_accounts:
            await utils.answer(message, "❌ <b>Сначала создайте email командой <code>.mail</code></b>")
            return

        account_data = self.email_accounts[chat_id]
        text = (
            f"📧 <b>Текущий email:</b> <code>{account_data['email']}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{account_data['password']}</code>"
        )
        await utils.answer(message, text)
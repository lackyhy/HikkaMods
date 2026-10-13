# meta developer: @lackyhyyy666
# scope: hikka

import json
import logging
import random
import re
import secrets
import string
import time

import aiohttp
from .. import loader, utils

logger = logging.getLogger(__name__)

API_URL = "https://api.mail.tm"


def _html_to_text(raw) -> str:
    """mail.tm отдаёт html как список строк — склеиваем и убираем теги"""
    if isinstance(raw, (list, tuple)):
        raw = "\n".join(str(x) for x in raw)
    raw = str(raw or "")
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", raw)
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\n\s*\n+", "\n\n", raw).strip()


@loader.tds
class TempMailMod(loader.Module):
    """Временная почта с уведомлениями через mail.tm"""

    strings = {
        "name": "TempMail",
        "cfg_notify": "Присылать уведомления о новых письмах в чат, где создан ящик",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "notify",
                True,
                lambda: self.strings("cfg_notify"),
                validator=loader.validators.Boolean(),
            ),
        )

    # ---------- хранение ----------

    def _accounts(self) -> dict:
        """{str(chat_id): account_data} — хранится в БД, переживает перезапуск"""
        data = self.get("accounts", {})
        return data if isinstance(data, dict) else {}

    def _save_account(self, chat_id, account_data):
        accounts = self._accounts()
        accounts[str(chat_id)] = account_data
        self.set("accounts", accounts)

    def _get_account(self, chat_id):
        return self._accounts().get(str(chat_id))

    # ---------- API ----------

    async def _api_request(self, session, method: str, endpoint: str, json_data: dict = None, token: str = None):
        headers = {"Authorization": f"Bearer {token}"} if token else None
        try:
            async with session.request(method, f"{API_URL}{endpoint}", json=json_data, headers=headers) as resp:
                if resp.status in (200, 201):
                    try:
                        return await resp.json(content_type=None), None
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        return None, "Некорректный формат ответа API"
                if resp.status == 401:
                    return None, "Токен ящика устарел — создайте новый через .mailrefresh"
                if resp.status == 429:
                    return None, "Слишком много запросов к mail.tm, попробуйте позже"
                return None, f"Ошибка API ({resp.status})"
        except Exception as e:
            return None, f"Ошибка сети: {e}"

    def _session(self):
        return aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15))

    async def _create_email_account(self):
        async with self._session() as session:
            data, err = await self._api_request(session, "GET", "/domains")
            domains = [d for d in (data or {}).get("hydra:member", []) if d.get("isActive", True)]
            if err or not domains:
                return None, err or "Домены недоступны"
            domain = random.choice(domains)["domain"]

            # Случайные логин и пароль: раньше пароль был общим для всех ящиков,
            # а адрес — предсказуемым, и чужой мог войти в ваш ящик.
            alphabet = string.ascii_lowercase + string.digits
            login = "".join(secrets.choice(alphabet) for _ in range(12))
            email = f"{login}@{domain}"
            password = secrets.token_urlsafe(16)

            _, err = await self._api_request(session, "POST", "/accounts", json_data={"address": email, "password": password})
            if err:
                return None, f"Не удалось создать аккаунт: {err}"

            token_data, err = await self._api_request(session, "POST", "/token", json_data={"address": email, "password": password})
            if err or not token_data or not token_data.get("token"):
                return None, f"Не удалось получить токен: {err}"

        return {
            "email": email,
            "password": password,
            "token": token_data["token"],
            "domain": domain,
            "created_at": time.time(),
            "seen": [],
        }, None

    async def _list_messages(self, session, token: str):
        data, err = await self._api_request(session, "GET", "/messages", token=token)
        if err or not data or "hydra:member" not in data:
            return None, err or "Не удалось получить список писем"
        return [m for m in data["hydra:member"] if isinstance(m, dict) and "id" in m], None

    async def _fetch_full(self, session, token: str, msg_ids):
        result = []
        for msg_id in msg_ids:
            msg_data, _ = await self._api_request(session, "GET", f"/messages/{msg_id}", token=token)
            if msg_data:
                result.append(msg_data)
        return result

    def _format_message(self, msg: dict, preview_len: int = 300) -> str:
        from_info = msg.get("from")
        if isinstance(from_info, dict):
            from_addr = from_info.get("address") or from_info.get("name") or "Неизвестно"
        else:
            from_addr = str(from_info) if from_info else "Неизвестно"

        subject = utils.escape_html(msg.get("subject") or "Без темы")
        body = msg.get("text") or _html_to_text(msg.get("html")) or msg.get("intro") or ""
        body = str(body).strip()
        if len(body) > preview_len:
            body = body[:preview_len] + "..."

        return (
            f"<b>От:</b> <code>{utils.escape_html(from_addr)}</code>\n"
            f"<b>Тема:</b> {subject}\n"
            f"<b>Текст:</b>\n<i>{utils.escape_html(body)}</i>\n"
            f"───────────────\n"
        )

    # ---------- команды ----------

    async def _new_mailbox(self, message, status_text: str, title: str, footer: str):
        message = await utils.answer(message, status_text)

        account_data, error = await self._create_email_account()
        if error:
            await utils.answer(message, f"❌ <b>{utils.escape_html(error)}</b>")
            return

        self._save_account(message.chat_id, account_data)

        await utils.answer(
            message,
            f"{title}\n\n"
            f"📧 <b>Email:</b> <code>{account_data['email']}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{account_data['password']}</code>\n\n"
            f"<i>{footer}</i>",
        )

    @loader.command()
    async def mail(self, message):
        """Создать новый временный email"""
        if self._get_account(message.chat_id):
            acc = self._get_account(message.chat_id)
            await utils.answer(
                message,
                f"📧 <b>В этом чате уже есть ящик:</b> <code>{acc['email']}</code>\n"
                f"<i>Используйте <code>.mailrefresh</code>, чтобы создать новый.</i>",
            )
            return

        await self._new_mailbox(
            message,
            "🔄 <b>Создаем временный email...</b>",
            "✅ <b>Временный email создан!</b>",
            "Используйте .mailcheck для проверки входящих писем."
            + (" Новые письма будут приходить сюда автоматически." if self.config["notify"] else ""),
        )

    @loader.command()
    async def mailrefresh(self, message):
        """Создать новую почту (перезаписать текущую)"""
        await self._new_mailbox(
            message,
            "🔄 <b>Генерируем новый адрес почты...</b>",
            "🔄 <b>Почта успешно обновлена!</b>",
            "Старый ящик для этого чата перезаписан.",
        )

    @loader.command()
    async def mailcheck(self, message):
        """Проверить входящие письма"""
        chat_id = message.chat_id
        account_data = self._get_account(chat_id)
        if not account_data:
            await utils.answer(message, "❌ <b>Сначала создайте email командой <code>.mail</code></b>")
            return

        message = await utils.answer(message, "🔄 <b>Проверяем входящие письма...</b>")

        async with self._session() as session:
            listing, error = await self._list_messages(session, account_data["token"])
            if error:
                await utils.answer(message, f"❌ <b>{utils.escape_html(error)}</b>")
                return
            if not listing:
                await utils.answer(message, "📭 <b>Входящих писем пока нет.</b>")
                return
            messages_list = await self._fetch_full(session, account_data["token"], [m["id"] for m in listing[:10]])

        account_data["seen"] = list({*account_data.get("seen", []), *(m["id"] for m in listing)})
        self._save_account(chat_id, account_data)

        response_text = f"📧 <b>Писем в ящике: {len(listing)}</b>\n\n"
        for msg in messages_list:
            item_text = self._format_message(msg)
            if len(response_text) + len(item_text) > 3900:
                response_text += "\n⚠️ <i>Остальные письма не поместились из-за лимита Telegram...</i>"
                break
            response_text += item_text

        await utils.answer(message, response_text)

    @loader.command()
    async def mailinfo(self, message):
        """Показать текущий email и пароль"""
        account_data = self._get_account(message.chat_id)
        if not account_data:
            await utils.answer(message, "❌ <b>Сначала создайте email командой <code>.mail</code></b>")
            return

        created = time.strftime("%d.%m.%Y %H:%M", time.localtime(account_data.get("created_at", 0)))
        await utils.answer(
            message,
            f"📧 <b>Текущий email:</b> <code>{account_data['email']}</code>\n"
            f"🔑 <b>Пароль:</b> <code>{account_data['password']}</code>\n"
            f"🕐 <b>Создан:</b> <code>{created}</code>\n"
            f"🌐 <i>Войти в ящик через браузер можно на mail.tm</i>",
        )

    # ---------- уведомления ----------

    @loader.loop(interval=60, autostart=True)
    async def _notify_loop(self):
        if not self.config["notify"]:
            return

        accounts = self._accounts()
        if not accounts:
            return

        changed = False
        async with self._session() as session:
            for chat_id, account_data in accounts.items():
                listing, error = await self._list_messages(session, account_data.get("token"))
                if error or not listing:
                    continue

                seen = set(account_data.get("seen", []))
                new_ids = [m["id"] for m in listing if m["id"] not in seen]
                if not new_ids:
                    continue

                account_data["seen"] = list(seen | set(new_ids))
                changed = True

                for msg in await self._fetch_full(session, account_data["token"], new_ids[:5]):
                    try:
                        await self._client.send_message(
                            int(chat_id),
                            f"📨 <b>Новое письмо на</b> <code>{account_data['email']}</code>\n\n"
                            + self._format_message(msg, preview_len=1000),
                        )
                    except Exception as e:
                        logger.warning(f"[TempMail] Не удалось отправить уведомление: {e}")

        if changed:
            self.set("accounts", accounts)

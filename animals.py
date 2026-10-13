# meta developer: @lackyhyyy666

import time

import aiohttp
from .. import loader, utils


def _first(*keys):
    """Достаёт ссылку на картинку из ответа API по первому найденному ключу"""
    def extract(data):
        if isinstance(data, list):
            data = data[0] if data else {}
        for key in keys:
            if isinstance(data, dict) and data.get(key):
                return data[key]
        return None
    return extract


def _tinyfox(data):
    loc = data.get("loc") if isinstance(data, dict) else None
    return f"https://api.tinyfox.dev{loc}" if loc else None


# Для каждого животного — несколько API: если один упал, пробуем следующий
SOURCES = {
    "cat": [
        ("https://api.thecatapi.com/v1/images/search", _first("url")),
        ("https://cataas.com/cat?json=true", _first("url")),
    ],
    "dog": [
        ("https://dog.ceo/api/breeds/image/random", _first("message")),
        ("https://random.dog/woof.json", _first("url")),
    ],
    "fox": [
        ("https://randomfox.ca/floof/", _first("image")),
        ("https://api.tinyfox.dev/img.json?animal=fox", _tinyfox),
    ],
    "panda": [
        # some-random-api часто закрыт проверкой Cloudflare — держим запасной источник
        ("https://some-random-api.com/animal/panda", _first("image", "link")),
        ("https://api.tinyfox.dev/img.json?animal=wah", _tinyfox),
    ],
    "bird": [
        ("https://some-random-api.com/animal/bird", _first("image", "link")),
        ("https://some-random-api.com/img/bird", _first("link", "image")),
    ],
    "raccoon": [("https://api.tinyfox.dev/img.json?animal=racc", _tinyfox)],
    "capy": [("https://api.tinyfox.dev/img.json?animal=capy", _tinyfox)],
    "otter": [("https://api.tinyfox.dev/img.json?animal=otter", _tinyfox)],
}

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp")


@loader.tds
class AnimalsMod(loader.Module):
    """Фото милых животных. Включите allow_all_users, чтобы команды работали у всех в чате"""
    strings = {
        "name": "Animals",
        "cat_caption": "🐱 Котик",
        "dog_caption": "🐶 Пёсик",
        "fox_caption": "🦊 Лисичка",
        "panda_caption": "🐼 Панда",
        "bird_caption": "🐦 Птичка",
        "raccoon_caption": "🦝 Енотик",
        "capy_caption": "🦫 Капибара",
        "otter_caption": "🦦 Выдра",
        "error": "❌ Не удалось загрузить картинку.",
        "cfg_allow_all": "Разрешить всем пользователям в чате использовать команды животных",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allow_all_users",
                False,
                lambda: self.strings("cfg_allow_all"),
                validator=loader.validators.Boolean(),
            ),
        )
        self._last_call = {}

    # Команды без @loader.unrestricted: раньше они и так были доступны всем,
    # поэтому allow_all_users ни на что не влиял, а при включении бот отвечал дважды.
    # Теперь чужие вызовы обрабатывает только watcher и только при включённой настройке.

    @loader.ratelimit
    async def catcmd(self, message):
        """Отправить фото котика"""
        await self._send_animal(message, "cat")

    @loader.ratelimit
    async def dogcmd(self, message):
        """Отправить фото пёсика"""
        await self._send_animal(message, "dog")

    @loader.ratelimit
    async def foxcmd(self, message):
        """Отправить фото лисы"""
        await self._send_animal(message, "fox")

    @loader.ratelimit
    async def pandacmd(self, message):
        """Отправить фото панды"""
        await self._send_animal(message, "panda")

    @loader.ratelimit
    async def birdcmd(self, message):
        """Отправить фото птички"""
        await self._send_animal(message, "bird")

    @loader.ratelimit
    async def raccooncmd(self, message):
        """Отправить фото енота"""
        await self._send_animal(message, "raccoon")

    @loader.ratelimit
    async def capycmd(self, message):
        """Отправить фото капибары"""
        await self._send_animal(message, "capy")

    @loader.ratelimit
    async def ottercmd(self, message):
        """Отправить фото выдры"""
        await self._send_animal(message, "otter")

    async def _fetch_image_url(self, animal_type):
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for api_url, extract in SOURCES[animal_type]:
                try:
                    async with session.get(api_url) as resp:
                        if resp.status != 200:
                            continue
                        img_url = extract(await resp.json(content_type=None))
                        if not img_url:
                            continue
                        if img_url.startswith("/"):
                            img_url = "https://cataas.com" + img_url
                        # random.dog иногда отдаёт видео — пропускаем
                        if not img_url.lower().split("?")[0].endswith(IMAGE_EXTS) and "cataas" not in img_url:
                            continue
                        return img_url
                except Exception:
                    continue
        return None

    async def _send_animal(self, message, animal_type):
        img_url = await self._fetch_image_url(animal_type)
        reply_to = getattr(message, "reply_to_msg_id", None)

        if not img_url:
            await utils.answer(message, self.strings("error"))
            return

        try:
            await self._client.send_file(
                message.chat_id,
                img_url,
                caption=self.strings(f"{animal_type}_caption"),
                reply_to=reply_to if getattr(message, "out", False) else message.id,
            )
        except Exception:
            await utils.answer(message, self.strings("error"))
            return

        # Удаляем свою команду только после успешной отправки — раньше при
        # ошибке бот пытался отредактировать уже удалённое сообщение и падал
        if getattr(message, "out", False):
            try:
                await message.delete()
            except Exception:
                pass

    @loader.watcher(only_messages=True)
    async def watcher(self, message):
        if not self.config["allow_all_users"] or getattr(message, "out", False):
            return

        text = getattr(message, "raw_text", "") or ""
        prefix = self.get_prefix()
        if not text.startswith(prefix):
            return

        body = text[len(prefix):].strip()
        if not body:
            return

        animal = body.split()[0].lower()
        if animal in SOURCES:
            # Антиспам для чужих вызовов: не чаще раза в 3 секунды на чат
            now = time.monotonic()
            if now - self._last_call.get(message.chat_id, 0) < 3:
                return
            self._last_call[message.chat_id] = now
            try:
                await self._send_animal(message, animal)
            except Exception:
                pass

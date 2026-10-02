# meta developer: @lackyhyyy666

from .. import loader, utils
import aiohttp

@loader.tds
class AnimalsMod(loader.Module):
    """Модуль с животными, доступный всем пользователям в чате"""
    strings = {
        "name": "Animals",
        "cat_caption": "🐱 Котик",
        "dog_caption": "🐶 Пёсик",
        "fox_caption": "🦊 Лисичка",
        "panda_caption": "🐼 Панда",
        "koala_caption": "🐨 Коала",
        "bird_caption": "🐦 Птичка",
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

    @loader.unrestricted
    @loader.ratelimit
    async def catcmd(self, message):
        """Отправить фото котика"""
        await self._send_animal(message, "https://api.thecatapi.com/v1/images/search", "cat")

    @loader.unrestricted
    @loader.ratelimit
    async def dogcmd(self, message):
        """Отправить фото пёсика"""
        await self._send_animal(message, "https://dog.ceo/api/breeds/image/random", "dog")

    @loader.unrestricted
    @loader.ratelimit
    async def foxcmd(self, message):
        """Отправить фото лисы"""
        await self._send_animal(message, "https://randomfox.ca/floof/", "fox")

    @loader.unrestricted
    @loader.ratelimit
    async def pandacmd(self, message):
        """Отправить фото панды"""
        await self._send_animal(message, "https://some-random-api.com/img/panda", "panda")

    @loader.unrestricted
    @loader.ratelimit
    async def birdcmd(self, message):
        """Отправить фото птички"""
        await self._send_animal(message, "https://some-random-api.com/img/bird", "bird")

    async def _send_animal(self, message, api_url, animal_type):
        if getattr(message, "out", False):
            try:
                await message.delete()
            except Exception:
                pass

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if animal_type == "cat":
                            img_url = data[0]["url"]
                        elif animal_type == "dog":
                            img_url = data["message"]
                        elif animal_type == "fox":
                            img_url = data["image"]
                        elif animal_type in ["panda", "bird"]:
                            img_url = data["link"]
                        else:
                            img_url = None

                        if img_url:
                            client = getattr(self, "client", getattr(message, "client", None))
                            if client:
                                await client.send_file(
                                    message.chat_id,
                                    img_url,
                                    caption=self.strings(f"{animal_type}_caption"),
                                    reply_to=getattr(message, "reply_to_msg_id", None)
                                )
                            return
            await utils.answer(message, self.strings("error"))
        except Exception:
            await utils.answer(message, self.strings("error"))

    @loader.watcher()
    async def watcher(self, message):
        if not self.config["allow_all_users"]:
            return

        if getattr(message, "out", False):
            return

        text = getattr(message, "raw_text", "") or getattr(message, "text", "") or ""
        prefix = self.get_prefix() if hasattr(self, "get_prefix") else "."
        if not text.startswith(prefix):
            return

        body = text[len(prefix):].strip()
        if not body:
            return

        cmd_name = body.split()[0].lower()
        commands = {
            "cat": self.catcmd,
            "dog": self.dogcmd,
            "fox": self.foxcmd,
            "panda": self.pandacmd,
            "bird": self.birdcmd,
        }
        
        if cmd_name in commands:
            try:
                await commands[cmd_name](message)
            except Exception:
                pass

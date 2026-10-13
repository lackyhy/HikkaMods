# meta developer: @lackyhyyy666
# meta version: 1.1.0
# requires: yt-dlp pillow

import os
import re
import asyncio
import tempfile
import shutil
import yt_dlp
from PIL import Image
from telethon.tl.types import DocumentAttributeAudio
from .. import loader, utils

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


@loader.tds
class YTMusicDownloaderMod(loader.Module):
    """Модуль для скачивания треков с YouTube Music и YouTube"""

    __version__ = (1, 1, 0)

    strings = {
        "name": "YTMusicDownloader",
        "no_url": "⚠️ <b>Не удалось определить трек!</b>\nОтветьте на аудиозапись/пост с музыкой в канале или укажите ссылку/название.\nПример: <code>.dy https://music.youtube.com/watch?v=...</code> или <code>.dy Исполнитель - Трек</code>",
        "downloading": "⏳ <b>Загрузка и обработка аудио...</b>",
        "error": "❌ <b>Ошибка при скачивании:</b>\n<code>{}</code>",
    }

    strings_ru = {
        "no_url": "⚠️ <b>Не удалось определить трек!</b>\nОтветьте на аудиозапись/пост с музыкой в канале или укажите ссылку/название.\nПример: <code>.dy https://music.youtube.com/watch?v=...</code> или <code>.dy Исполнитель - Трек</code>",
        "downloading": "⏳ <b>Загрузка и обработка аудио...</b>",
        "error": "❌ <b>Ошибка при скачивании:</b>\n<code>{}</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "allowed_ids",
                [],
                "ID пользователей, которым разрешено использовать команду .dy",
                validator=loader.validators.Series(loader.validators.Integer()),
            ),
            loader.ConfigValue(
                "max_duration",
                1200,
                "Максимальная длительность трека в секундах (0 — без ограничений)",
                validator=loader.validators.Integer(minimum=0),
            ),
        )

    def _is_allowed(self, message) -> bool:
        if getattr(message, "out", False):
            return True

        sender_id = getattr(message, "sender_id", None)
        if not sender_id:
            return False

        owner_id = getattr(self, "tg_id", None) or getattr(getattr(self, "_client", None), "tg_id", None)
        if owner_id and sender_id == owner_id:
            return True

        raw_allowed = self.config["allowed_ids"]
        if not raw_allowed:
            return False

        if isinstance(raw_allowed, (int, str)):
            raw_allowed = [raw_allowed]

        allowed_set = set()
        for item in raw_allowed:
            if isinstance(item, int):
                allowed_set.add(item)
            elif isinstance(item, str):
                for sub in str(item).replace(",", " ").split():
                    if sub.lstrip("-").isdigit():
                        allowed_set.add(int(sub))

        return sender_id in allowed_set

    @loader.watcher(only_messages=True)
    async def watcher(self, message):
        """Позволяет пользователям из allowed_ids вызывать .dy (раньше настройка ни на что не влияла)"""
        if getattr(message, "out", False) or not self.config["allowed_ids"]:
            return
        text = (getattr(message, "raw_text", "") or "").strip()
        prefix = self.get_prefix()
        if not text.startswith(prefix):
            return
        parts = text[len(prefix):].split(maxsplit=1)
        if not parts or parts[0].lower() != "dy":
            return
        owner_id = getattr(self, "tg_id", None)
        if getattr(message, "sender_id", None) != owner_id and self._is_allowed(message):
            await self.dycmd(message)

    @loader.command(
        ru_doc="[ссылка / название / реплай / в комментариях] - Скачать аудиозапись/трек с YouTube Music или YouTube",
        en_doc="[link / title / reply / in comments] - Download audio/track from YouTube Music or YouTube",
    )
    async def dycmd(self, message):
        """[link / title / reply / in comments] - Download track from YouTube Music / YouTube"""
        if not self._is_allowed(message):
            return
        args = utils.get_args_raw(message).strip()
        url = ""
        reply_to = None

        if args:
            if args.startswith("http://") or args.startswith("https://"):
                url = args.split()[0]
            else:
                url = f"ytsearch1:{args}"
        else:
            candidates = []
            reply = await message.get_reply_message()
            if reply:
                candidates.append(reply)
                reply_to = reply.id

            top_id = (
                getattr(message, "reply_to_top_id", None)
                or getattr(getattr(message, "reply_to", None), "reply_to_top_id", None)
                or getattr(message, "reply_to_msg_id", None)
            )
            if top_id:
                if not reply or reply.id != top_id:
                    try:
                        top_msg = await message.client.get_messages(message.chat_id, ids=top_id)
                        if top_msg:
                            candidates.append(top_msg)
                            if not reply_to:
                                reply_to = top_msg.id
                    except Exception:
                        pass

            for target_msg in candidates:
                if not target_msg:
                    continue

                text = target_msg.raw_text or target_msg.text or ""
                url_match = re.search(r'https?://[^\s]+', text)
                if url_match:
                    url = url_match.group(0)
                    break

                if target_msg.media:
                    document = getattr(target_msg.media, "document", None)
                    if document and hasattr(document, "attributes"):
                        for attr in document.attributes:
                            if hasattr(attr, "title") or hasattr(attr, "performer"):
                                performer = getattr(attr, "performer", "") or ""
                                title = getattr(attr, "title", "") or ""
                                if performer or title:
                                    query = f"{performer} - {title}".strip(" -")
                                    url = f"ytsearch1:{query}"
                                    break
                if url:
                    break

                if text:
                    clean_text = text.split("\n")[0].strip()
                    if clean_text:
                        url = f"ytsearch1:{clean_text}"
                        break

        if not url:
            await utils.answer(message, self.strings("no_url"))
            return

        if not reply_to:
            if getattr(message, "reply_to_msg_id", None):
                reply_to = message.reply_to_msg_id
            elif not getattr(message, "out", False):
                reply_to = message.id

        # Меняем текст исходного сообщения на статус загрузки
        message = await utils.answer(message, self.strings("downloading"))

        if url.startswith("http") and "music.youtube.com" in url:
            url = url.replace("music.youtube.com", "www.youtube.com")

        loop = asyncio.get_running_loop()
        # Папку создаём здесь, чтобы удалить её даже если скачивание упало
        # (раньше при ошибке внутри executor временная папка оставалась навсегда)
        temp_dir = tempfile.mkdtemp(prefix="dy_")

        try:
            audio_path, title, performer, duration, thumb_path = await loop.run_in_executor(
                None, self._download_audio, url, temp_dir, int(self.config["max_duration"] or 0)
            )
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raw_err = utils.escape_html(ANSI_ESCAPE.sub('', str(e))[:1000])
            await utils.answer(message, self.strings("error").format(raw_err))
            return

        try:
            attributes = [
                DocumentAttributeAudio(
                    duration=duration,
                    title=title,
                    performer=performer,
                    voice=False,
                )
            ]

            valid_thumb = None
            if thumb_path and os.path.exists(thumb_path):
                # Telegram принимает обложку только JPEG до 320x320 и ~200 КБ,
                # иначе молча её игнорирует — обрезаем по центру в квадрат
                try:
                    jpg_thumb = os.path.splitext(thumb_path)[0] + "_thumb.jpg"
                    with Image.open(thumb_path) as im:
                        im = im.convert("RGB")
                        side = min(im.size)
                        left = (im.width - side) // 2
                        top = (im.height - side) // 2
                        im = im.crop((left, top, left + side, top + side))
                        im.thumbnail((320, 320))
                        im.save(jpg_thumb, "JPEG", quality=85)
                    valid_thumb = jpg_thumb
                except Exception:
                    valid_thumb = None

            # Отправляем файл
            await message.client.send_file(
                entity=message.chat_id,
                file=audio_path,
                caption="",
                attributes=attributes,
                supports_streaming=True,
                reply_to=reply_to,
                thumb=valid_thumb,
            )

            # Удаляем сообщение со статусом загрузки
            try:
                await message.delete()
            except Exception:
                pass

        except Exception as e:
            raw_err = utils.escape_html(ANSI_ESCAPE.sub('', str(e))[:1000])
            await utils.answer(message, self.strings("error").format(raw_err))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _download_audio(self, url: str, temp_dir: str, max_duration: int = 0):
        out_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": out_template,
            "writethumbnail": True,
            "noplaylist": True,
            "cachedir": False,
            "source_address": "0.0.0.0",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Сначала узнаём метаданные без скачивания — чтобы не качать часовые стримы
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("Не удалось получить информацию о треке.")

            if "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                if not entries:
                    raise ValueError("Не удалось найти результаты по запросу.")
                info = entries[0]

            if info.get("is_live"):
                raise ValueError("Прямые трансляции скачивать нельзя.")
            duration = int(info.get("duration") or 0)
            if max_duration and duration > max_duration:
                raise ValueError(
                    f"Трек слишком длинный ({duration // 60} мин). "
                    f"Лимит: {max_duration // 60} мин (.cfg YTMusicDownloader max_duration)."
                )

            info = ydl.process_ie_result(info, download=True)

            filename = ydl.prepare_filename(info)
            audio_path = os.path.splitext(filename)[0] + ".mp3"

            if not os.path.exists(audio_path):
                if os.path.exists(filename):
                    audio_path = filename
                else:
                    raise FileNotFoundError("Не удалось извлечь и сохранить аудиофайл.")

            title = info.get("title") or info.get("track") or "Audio Track"
            performer = info.get("artist") or info.get("uploader") or info.get("channel") or ""
            duration = int(info.get("duration") or 0)

            thumb_path = None
            for ext in ["jpg", "jpeg", "webp", "png"]:
                candidate = os.path.splitext(filename)[0] + f".{ext}"
                if os.path.exists(candidate):
                    thumb_path = candidate
                    break

            return audio_path, title, performer, duration, thumb_path

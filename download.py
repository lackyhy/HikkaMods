# meta developer: @lackyhyyy666

import os
import re
import time
import asyncio
import tempfile
import shutil
import yt_dlp
from .. import loader, utils

@loader.tds
class YTMusicDownloaderMod(loader.Module):
    """Модуль для скачивания треков с YouTube Music и YouTube"""

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

    @loader.command(
        ru_doc="[ссылка / название / реплай / в комментариях] - Скачать аудиозапись/трек с YouTube Music или YouTube",
        en_doc="[link / title / reply / in comments] - Download audio/track from YouTube Music or YouTube",
    )
    async def dycmd(self, message):
        """[link / title / reply / in comments] - Download track from YouTube Music / YouTube"""
        args = utils.get_args_raw(message).strip()
        url = ""
        reply_to = None

        if args:
            if args.startswith("http://") or args.startswith("https://"):
                url = args.split()[0]
            else:
                url = f"ytsearch1:{args}"
        else:
            # Ищем сообщения-кандидаты: сначала прямой реплай, затем главный пост ветки комментариев
            candidates = []
            reply = await message.get_reply_message()
            if reply:
                candidates.append(reply)
                reply_to = reply.id

            top_id = getattr(message, "reply_to_top_id", None) or getattr(getattr(message, "reply_to", None), "reply_to_top_id", None) or getattr(message, "reply_to_msg_id", None)
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

                # 1. Извлекаем URL из текста сообщения (YouTube, YT Music, Spotify и др.)
                text = target_msg.raw_text or target_msg.text or ""
                url_match = re.search(r'https?://[^\s]+', text)
                if url_match:
                    url = url_match.group(0)
                    break

                # 2. Проверяем теги / атрибуты аудио файла
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

                # 3. Берем первую строчку текста или описание
                if text:
                    clean_text = text.split("\n")[0].strip()
                    if clean_text:
                        url = f"ytsearch1:{clean_text}"
                        break

        if not url:
            await utils.answer(message, self.strings("no_url"))
            return

        if not reply_to and getattr(message, "reply_to_msg_id", None):
            reply_to = message.reply_to_msg_id

        # Изменяем сообщение на статус загрузки
        message = await utils.answer(message, self.strings("downloading"))

        loop = asyncio.get_event_loop()
        last_edit_time = 0

        def progress_hook(d):
            nonlocal last_edit_time
            if d['status'] == 'downloading':
                now = time.time()
                if now - last_edit_time > 3:
                    last_edit_time = now
                    percent_str = d.get('_percent_str', '').strip()
                    speed_str = d.get('_speed_str', '').strip()
                    eta_str = d.get('_eta_str', '').strip()
                    
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    percent = ansi_escape.sub('', percent_str)
                    speed = ansi_escape.sub('', speed_str)
                    eta = ansi_escape.sub('', eta_str)

                    try:
                        p = float(percent.replace('%', ''))
                    except ValueError:
                        p = 0.0
                    
                    filled = int(p / 10)
                    bar = "█" * filled + "▒" * (10 - filled)

                    text = f"⏳ <b>Скачивание...</b>\n\n[{bar}] {percent}\n<b>Скорость:</b> <code>{speed}</code>\n<b>Осталось:</b> <code>{eta}</code>"
                    
                    async def safe_edit():
                        try:
                            await message.edit(text)
                        except Exception:
                            pass
                    
                    asyncio.run_coroutine_threadsafe(safe_edit(), loop)

        if url.startswith("http") and "music.youtube.com" in url:
            url = url.replace("music.youtube.com", "www.youtube.com")

        temp_dir = None
        audio_path = None
        thumb_path = None
        try:
            temp_dir, audio_path, title, performer, duration, thumb_path = await loop.run_in_executor(
                None, self._download_audio, url, progress_hook
            )
        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))
            return

        try:
            from telethon.tl.types import DocumentAttributeAudio

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
                if thumb_path.lower().endswith((".jpg", ".jpeg")):
                    valid_thumb = thumb_path
                else:
                    try:
                        from PIL import Image
                        jpg_thumb = os.path.splitext(thumb_path)[0] + "_conv.jpg"
                        with Image.open(thumb_path) as im:
                            im.convert("RGB").save(jpg_thumb, "JPEG")
                        valid_thumb = jpg_thumb
                    except Exception:
                        valid_thumb = None

            # Отправляем аудио файл отдельным новым сообщением
            await message.client.send_file(
                entity=message.chat_id,
                file=audio_path,
                caption=f"",
                attributes=attributes,
                supports_streaming=True,
                reply_to=reply_to,
                thumb=valid_thumb,
            )

            # Удаляем исходное сообщение с прогрессом
            try:
                await message.delete()
            except Exception:
                pass

        except Exception as e:
            await message.respond(self.strings("error").format(str(e)))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _download_audio(self, url: str, progress_hook=None):
        temp_dir = tempfile.mkdtemp()
        out_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": out_template,
            "writethumbnail": True,
            "nocheckcertificate": True,
            "cachedir": False,
            "source_address": "0.0.0.0",
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                    "client": ["android", "web"]
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

        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Не удалось получить информацию о треке.")

            if "entries" in info:
                entries = info.get("entries") or []
                if not entries:
                    raise ValueError("Не удалось найти результаты по запросу.")
                info = entries[0]

            filename = ydl.prepare_filename(info)
            audio_path = os.path.splitext(filename)[0] + ".mp3"

            if not os.path.exists(audio_path):
                # Фолбэк, если расширение не mp3
                if os.path.exists(filename):
                    audio_path = filename
                else:
                    raise FileNotFoundError("Не удалось извлечь и сохранить аудиофайл.")

            title = info.get("title") or info.get("track") or "Audio Track"
            performer = info.get("artist") or info.get("uploader") or info.get("channel") or ""
            duration = int(info.get("duration") or 0)

            # Ищем обложку (thumbnail)
            thumb_path = None
            for ext in ["jpg", "jpeg", "webp", "png"]:
                candidate = os.path.splitext(filename)[0] + f".{ext}"
                if os.path.exists(candidate):
                    thumb_path = candidate
                    break

            return temp_dir, audio_path, title, performer, duration, thumb_path


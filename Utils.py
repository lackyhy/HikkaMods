# meta developer: @lackyhyyy666
# scope: hikka_only
# scope: hikka_min 1.6.2

import html
import io
import logging
from urllib.parse import quote

import aiohttp
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class UtilsMod(loader.Module):
    """Утилиты от @lackyhyyy666"""

    strings = {
        "name": "Utils",
    }

    def _generate_styled_qr(self, text: str, target_size: int = 600) -> bytes:
        try:
            import qrcode
            from PIL import Image, ImageDraw
        except ImportError:
            import subprocess
            import sys
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "qrcode"], check=True)
            import qrcode
            from PIL import Image, ImageDraw

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=1,
            border=0,
        )
        qr.add_data(text)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        N = len(matrix)

        scale = 4
        module_size = 24 * scale
        padding = 4 * module_size
        grid_size = N * module_size
        img_size = grid_size + 2 * padding

        img = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        BLACK = (18, 18, 18, 255)
        PURPLE = (123, 31, 162, 255)
        WHITE = (255, 255, 255, 255)

        def in_finder(r, c):
            if r < 7 and c < 7:
                return True
            if r < 7 and c >= N - 7:
                return True
            if r >= N - 7 and c < 7:
                return True
            return False

        dot_radius = module_size * 0.42
        for r in range(N):
            for c in range(N):
                if matrix[r][c] and not in_finder(r, c):
                    cx = padding + (c + 0.5) * module_size
                    cy = padding + (r + 0.5) * module_size
                    draw.ellipse(
                        [cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius],
                        fill=BLACK,
                    )

        finders = [(0, 0), (0, N - 7), (N - 7, 0)]
        for r_start, c_start in finders:
            x0 = padding + c_start * module_size
            y0 = padding + r_start * module_size

            box7 = 7 * module_size
            r_outer = 2.0 * module_size
            draw.rounded_rectangle([x0, y0, x0 + box7, y0 + box7], radius=r_outer, fill=PURPLE)

            x1 = x0 + 1 * module_size
            y1 = y0 + 1 * module_size
            box5 = 5 * module_size
            r_middle = 1.3 * module_size
            draw.rounded_rectangle([x1, y1, x1 + box5, y1 + box5], radius=r_middle, fill=WHITE)

            x2 = x0 + 2 * module_size
            y2 = y0 + 2 * module_size
            box3 = 3 * module_size
            r_inner = 0.8 * module_size
            draw.rounded_rectangle([x2, y2, x2 + box3, y2 + box3], radius=r_inner, fill=PURPLE)

        card_radius = 6.0 * module_size
        mask = Image.new("L", (img_size, img_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, img_size, img_size], radius=card_radius, fill=255)

        final_card = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        final_card.paste(img, (0, 0), mask)

        final_img = final_card.resize((target_size, target_size), Image.Resampling.LANCZOS)

        bio = io.BytesIO()
        final_img.save(bio, format="PNG")
        return bio.getvalue()

    @loader.command(
        ru_doc="<ссылка / текст / реплай> — Сгенерировать QR-код из ссылки или текста",
        en_doc="<link / text / reply> — Generate QR code from link or text",
    )
    async def qrcodecmd(self, message: Message):
        """<ссылка / текст / реплай> — Сгенерировать QR-код из ссылки или текста"""
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()

        target_text = ""
        if args:
            target_text = args
        elif reply:
            target_text = (getattr(reply, "raw_text", None) or getattr(reply, "text", "") or "").strip()

        if not target_text:
            await utils.answer(
                message,
                "<b>📱 Укажите ссылку/текст или ответьте реплаем на сообщение!</b>\n"
                "<i>Пример: <code>.qrcode https://t.me/lackyhyyy666</code></i>",
            )
            return

        status_msg = await utils.answer(message, "📱 <b>Генерирую QR-код...</b>")

        qr_bytes = None
        try:
            qr_bytes = self._generate_styled_qr(target_text)
        except Exception as e:
            logger.error(f"[Utils/QRCode] Custom QR error: {e}")
            try:
                api_url = f"https://api.qrserver.com/v1/create-qr-code/?data={quote(target_text)}&size=500x500&format=png&color=7B1FA2"
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, timeout=10) as resp:
                        if resp.status == 200:
                            qr_bytes = await resp.read()
            except Exception as api_err:
                logger.error(f"[Utils/QRCode] API error: {api_err}")

        if not qr_bytes:
            await utils.answer(status_msg, "<b>❌ Ошибка при генерации QR-кода!</b>")
            return

        bio = io.BytesIO(qr_bytes)
        bio.name = "qrcode.png"

        try:
            client = getattr(self, "_client", None) or getattr(self, "client", None)
            await client.send_file(
                utils.get_chat_id(message),
                bio,
                reply_to=message.id,
            )
            if status_msg and hasattr(status_msg, "delete"):
                try:
                    await status_msg.delete()
                except Exception:
                    pass
        except Exception as exc:
            await utils.answer(status_msg, f"<b>❌ Ошибка отправки QR-кода:</b> <code>{html.escape(str(exc))}</code>")

    @loader.command(
        ru_doc="[username/link/reply] — Получить ID чата, пользователя или топика",
        en_doc="[username/link/reply] — Get ID of chat, user or topic",
    )
    async def chatidcmd(self, message: Message):
        """[username/link/reply] — Получить ID чата, пользователя или топика"""
        await self._get_id_info(message)

    @loader.command(
        ru_doc="[username/link/reply] — Алиас для .chatid",
        en_doc="[username/link/reply] — Alias for .chatid",
    )
    async def chidcmd(self, message: Message):
        """[username/link/reply] — Alias for .chatid"""
        await self._get_id_info(message)

    async def _get_id_info(self, message: Message):
        args = utils.get_args_raw(message).strip()
        reply = await message.get_reply_message()

        out = "<b>ℹ️ Информация об ID:</b>\n\n"

        chat_id = utils.get_chat_id(message)
        out += f"💬 <b>ID Чата:</b> <code>{chat_id}</code>\n"

        topic_id = None
        if message.reply_to and getattr(message.reply_to, "forum_topic", False):
            topic_id = getattr(message.reply_to, "reply_to_top_id", None) or getattr(message.reply_to, "reply_to_msg_id", None)
        
        if topic_id:
            out += f"🏷 <b>ID Топика:</b> <code>{topic_id}</code>\n"

        out += f"✉️ <b>ID Сообщения:</b> <code>{message.id}</code>\n"

        if reply:
            out += "\n<b>[Реплай]</b>\n"
            out += f"✉️ <b>ID Сообщения:</b> <code>{reply.id}</code>\n"
            sender = await reply.get_sender()
            if sender:
                out += f"👤 <b>ID Отправителя:</b> <code>{getattr(sender, 'id', 'Неизвестно')}</code>\n"
            
            fwd = getattr(reply, "fwd_from", None)
            if fwd:
                if getattr(fwd, "from_id", None):
                    peer = fwd.from_id
                    fwd_id = getattr(peer, "user_id", None) or getattr(peer, "channel_id", None) or getattr(peer, "chat_id", None)
                    if fwd_id:
                        out += f"🔄 <b>ID Оригинала (форвард):</b> <code>{fwd_id}</code>\n"
                elif getattr(fwd, "from_name", None):
                    out += f"🔄 <b>Автор форварда:</b> <code>{html.escape(fwd.from_name)}</code> (Скрыт)\n"

        if args:
            out += f"\n<b>[Поиск: {html.escape(args)}]</b>\n"
            try:
                entity = await message.client.get_entity(args)
                ent_type = "Пользователя" if getattr(entity, "first_name", None) is not None else ("Канала" if getattr(entity, "broadcast", False) else "Группы")
                out += f"🔍 <b>ID {ent_type}:</b> <code>{entity.id}</code>\n"
            except Exception as e:
                out += f"❌ <b>Ошибка поиска:</b> <code>{html.escape(str(e))}</code>\n"

        await utils.answer(message, out)

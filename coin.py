# meta developer: @lackyhyyy666

import asyncio
import random
from .. import loader, utils


@loader.tds
class CoinFlipMod(loader.Module):
    """Модуль для быстрой анимированной игры в подбрасывание монетки (Орёл или Решка)."""

    strings = {
        "name": "CoinFlip",
        "heads": "🦅 <b>Орёл</b>",
        "tails": "🪙 <b>Решка</b>",
        "edge": "🪙 <b>Монетка встала на ребро! 🤯</b>",
        "result_single": (
            "🪙 <b>Результат подбрасывания:</b> {}\n\n"
            "{}"
        ),
        "guess_correct": "🎉 <b>Вы угадали!</b> (Ваш выбор: {})",
        "guess_wrong": "❌ <b>Вы не угадали!</b> (Ваш выбор: {})",
        "multi_result": (
            "🪙 <b>Результат подбрасывания {} монет:</b>\n\n"
            "🦅 <b>Орёл:</b> {}\n"
            "🪙 <b>Решка:</b> {}\n"
            "{}"
        ),
    }

    @loader.command(
        ru_doc="[орёл/решка / количество] — Быстрое анимированное подбрасывание монетки (1-2 сек)",
        en_doc="[heads/tails / amount] — Fast animated coin flip (1-2 sec)",
    )
    async def coincmd(self, message):
        """[орёл/решка / количество] — Подбросить монетку"""
        raw_args = utils.get_args_raw(message).strip().lower()

        # Проверка на количество монет N
        if raw_args.isdigit():
            count = int(raw_args)
            if count <= 0:
                await utils.answer(message, "⚠️ Укажите количество монет больше 0!")
                return
            if count > 100:
                await utils.answer(message, "⚠️ Максимальное количество монет за раз — 100!")
                return

            frames = [
                f"🪙 <b>Подбрасываем {count} монет...</b>\n<i>🌕 (монетки взлетают вверх)...</i>",
                f"🪙 <b>Подбрасываем {count} монет...</b>\n<i>🌖 (крутятся в воздухе)...</i>",
                f"🪙 <b>Подбрасываем {count} монет...</b>\n<i>🌘 (падают обратно)...</i>",
            ]
            for frame in frames:
                await utils.answer(message, frame)
                await asyncio.sleep(0.2)

            heads_count = 0
            tails_count = 0
            edge_count = 0

            for _ in range(count):
                roll = random.random()
                if roll < 0.001:
                    edge_count += 1
                elif roll < 0.5:
                    heads_count += 1
                else:
                    tails_count += 1

            edge_str = f"\n🤯 <b>На ребро:</b> {edge_count}" if edge_count > 0 else ""
            res_text = self.strings("multi_result").format(
                count, heads_count, tails_count, edge_str
            )

            await utils.answer(message, res_text)

            markup = [
                [
                    {
                        "text": "🔄 Подбросить еще раз",
                        "callback": self._flip_callback,
                        "args": (f"multi_{count}",),
                    }
                ]
            ]

            try:
                await self.inline.form(
                    text=res_text,
                    message=message,
                    reply_markup=markup,
                    always_allow=True,
                )
            except Exception:
                pass
            return

        # Поддержка любых вариантов названия: "орел", "орёл", "орелик", "о", "h", "heads" и др.
        args_clean = raw_args.replace("ё", "е")
        guess = None
        guess_title = None

        if args_clean:
            if any(args_clean.startswith(x) for x in ["орел", "орл", "head", "о", "h"]):
                guess = "heads"
                guess_title = "🦅 Орёл"
            elif any(args_clean.startswith(x) for x in ["решк", "tail", "р", "t"]):
                guess = "tails"
                guess_title = "🪙 Решка"

        # Быстрая анимация полета монетки (4 кадра по 0.20 сек = 0.8 сек)
        frames = [
            "🪙 <b>Подбрасываем монетку...</b>\n<i>🌕 (монетка взлетает вверх)...</i>",
            "🪙 <b>Подбрасываем монетку...</b>\n<i>🌖 (крутится в воздухе)...</i>",
            "🪙 <b>Подбрасываем монетку...</b>\n<i>🌗 (переворачивается)...</i>",
            "🪙 <b>Подбрасываем монетку...</b>\n<i>🌘 (приземляется)...</i>",
        ]
        for frame in frames:
            await utils.answer(message, frame)
            await asyncio.sleep(0.20)

        roll = random.random()
        if roll < 0.001:
            outcome = "edge"
            outcome_text = self.strings("edge")
        elif roll < 0.5:
            outcome = "heads"
            outcome_text = self.strings("heads")
        else:
            outcome = "tails"
            outcome_text = self.strings("tails")

        guess_status = ""
        if guess:
            if outcome == guess:
                guess_status = self.strings("guess_correct").format(guess_title)
            else:
                guess_status = self.strings("guess_wrong").format(guess_title)

        text = self.strings("result_single").format(outcome_text, guess_status).strip()

        # Моментальная гарантированная сменяемость текста результат
        await utils.answer(message, text)

        cb_arg = f"single_{guess}" if guess else "single_none"
        markup = [
            [
                {
                    "text": "🔄 Подбросить еще раз",
                    "callback": self._flip_callback,
                    "args": (cb_arg,),
                }
            ]
        ]

        try:
            await self.inline.form(
                text=text,
                message=message,
                reply_markup=markup,
                always_allow=True,
            )
        except Exception:
            pass

    async def _flip_callback(self, call, mode: str):
        await call.answer("🪙 Монетка крутится...")

        if mode.startswith("multi_"):
            count = int(mode.split("_")[1])
            heads_count = 0
            tails_count = 0
            edge_count = 0

            for _ in range(count):
                roll = random.random()
                if roll < 0.001:
                    edge_count += 1
                elif roll < 0.5:
                    heads_count += 1
                else:
                    tails_count += 1

            edge_str = f"\n🤯 <b>На ребро:</b> {edge_count}" if edge_count > 0 else ""
            res_text = self.strings("multi_result").format(
                count, heads_count, tails_count, edge_str
            )
            markup = [
                [
                    {
                        "text": "🔄 Подбросить еще раз",
                        "callback": self._flip_callback,
                        "args": (mode,),
                    }
                ]
            ]
            await call.edit(text=res_text, reply_markup=markup)
            return

        guess = mode.split("_")[1]
        if guess == "none":
            guess = None

        guess_title = (
            "🦅 Орёл" if guess == "heads" else ("🪙 Решка" if guess == "tails" else None)
        )

        roll = random.random()
        if roll < 0.001:
            outcome = "edge"
            outcome_text = self.strings("edge")
        elif roll < 0.5:
            outcome = "heads"
            outcome_text = self.strings("heads")
        else:
            outcome = "tails"
            outcome_text = self.strings("tails")

        guess_status = ""
        if guess:
            if outcome == guess:
                guess_status = self.strings("guess_correct").format(guess_title)
            else:
                guess_status = self.strings("guess_wrong").format(guess_title)

        text = self.strings("result_single").format(outcome_text, guess_status).strip()

        markup = [
            [
                {
                    "text": "🔄 Подбросить еще раз",
                    "callback": self._flip_callback,
                    "args": (mode,),
                }
            ]
        ]
        await call.edit(text=text, reply_markup=markup)

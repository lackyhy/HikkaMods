# meta developer: @lackyhyyy666

import aiohttp
import ast
import operator
import re
import time
from .. import loader, utils

# Безопасный парсер для .calc
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

MAX_RESULT_DIGITS = 1000


def safe_eval(expr):
    """Безопасное вычисление математических выражений без eval()"""
    def _eval(node):
        # ast.Num удалён в Python 3.14 — используем только ast.Constant
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise ValueError("Недопустимое значение")
        elif isinstance(node, ast.BinOp):
            op = OPERATORS.get(type(node.op))
            if op is None:
                raise TypeError("Неподдерживаемая операция")
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Pow) and (abs(right) > 100 or abs(left) > 1000000):
                raise ValueError("Слишком большая степень!")
            result = op(left, right)
            if isinstance(result, int) and result.bit_length() > MAX_RESULT_DIGITS * 3.33:
                raise ValueError("Слишком большое число!")
            return result
        elif isinstance(node, ast.UnaryOp):
            op = OPERATORS.get(type(node.op))
            if op is None:
                raise TypeError("Неподдерживаемая операция")
            return op(_eval(node.operand))
        else:
            raise TypeError("Неподдерживаемая операция")

    parsed = ast.parse(expr, mode='eval')
    return _eval(parsed.body)


_rate_cache = {"value": None, "source": None, "time": 0.0}
RATE_CACHE_TTL = 60


async def get_usdt_rub_rate():
    """
    Курс USDT/RUB. Сначала пробуем настоящий курс USDT (CoinGecko),
    затем — курс доллара (USD ≈ USDT) как запасной вариант.
    Возвращает (курс, название_источника) или (None, None).
    """
    if _rate_cache["value"] and time.time() - _rate_cache["time"] < RATE_CACHE_TTL:
        return _rate_cache["value"], _rate_cache["source"]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    timeout = aiohttp.ClientTimeout(total=5)
    sources = [
        (
            "CoinGecko (USDT)",
            "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub",
            lambda d: d.get("tether", {}).get("rub"),
        ),
        (
            "ЦБ РФ (USD)",
            "https://www.cbr-xml-daily.ru/daily_json.js",
            lambda d: d.get("Valute", {}).get("USD", {}).get("Value"),
        ),
        (
            "Open ER API (USD)",
            "https://open.er-api.com/v6/latest/USD",
            lambda d: d.get("rates", {}).get("RUB"),
        ),
    ]

    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        for name, url, extract in sources:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json(content_type=None)
                    rate = extract(data)
                    if rate and float(rate) > 0:
                        _rate_cache.update(value=float(rate), source=name, time=time.time())
                        return float(rate), name
            except Exception:
                continue

    return None, None


def parse_args_with_custom_rate(args_raw):
    """
    Разбор аргументов на сумму и кастомный курс.
    Примеры: "20 (75)", "20.5 (78.2)", "20", "20 ( 75.5 )", "1 000,5"
    """
    if not args_raw:
        return None, None

    # Запятые → точки, убираем пробелы-разделители тысяч внутри чисел
    args_raw = args_raw.replace(",", ".").strip()

    match = re.search(r"^([\d.\s]+?)\s*\(\s*([\d.]+)\s*\)$", args_raw)
    if match:
        try:
            amount = float(match.group(1).replace(" ", ""))
            custom_rate = float(match.group(2))
            return amount, custom_rate
        except ValueError:
            return None, None

    try:
        amount = float(args_raw.replace(" ", ""))
        return amount, None
    except ValueError:
        return None, None


@loader.tds
class USDTRUBMod(loader.Module):
    """Конвертер USDT <-> RUB + Калькулятор"""
    strings = {"name": "USDTRUB"}

    async def _resolve(self, message, default_amount, example):
        args = utils.get_args_raw(message)

        if not args:
            amount, custom_rate = default_amount, None
        else:
            amount, custom_rate = parse_args_with_custom_rate(args)
            if amount is None or amount < 0:
                await utils.answer(message, f"<b>⚠️ Укажите число корректно (например: {example})</b>")
                return None

        if custom_rate is not None:
            if custom_rate <= 0:
                await utils.answer(message, "<b>⚠️ Курс должен быть больше нуля</b>")
                return None
            return amount, custom_rate, f"Ручной курс: 1 USDT = {custom_rate:.2f} RUB"

        rate, source = await get_usdt_rub_rate()
        if rate is None:
            await utils.answer(message, "<b>❌ Ошибка при запросе к API курсов</b>")
            return None
        return amount, rate, f"Курс {source}: 1 USDT ≈ {rate:.2f} RUB"

    @loader.command()
    async def usdtcmd(self, message):
        """<сумма> [(курс)] — Перевести USDT в RUB"""
        res = await self._resolve(message, 1.0, ".usdt 20 или .usdt 20 (75)")
        if not res:
            return
        amount, rate, rate_note = res

        await utils.answer(
            message,
            f"<b>💵 {amount:,.2f} USDT</b> = <b>{amount * rate:,.2f} RUB</b>\n"
            f"<i>{rate_note}</i>"
        )

    @loader.command()
    async def usdtrcmd(self, message):
        """<сумма> [(курс)] — Перевести RUB в USDT"""
        res = await self._resolve(message, 100.0, ".usdtr 5000 или .usdtr 5000 (75)")
        if not res:
            return
        amount, rate, rate_note = res

        await utils.answer(
            message,
            f"<b>💳 {amount:,.2f} RUB</b> = <b>{amount / rate:,.2f} USDT</b>\n"
            f"<i>{rate_note}</i>"
        )

    @loader.command()
    async def calccmd(self, message):
        """<выражение> — Математический калькулятор (+ - * / // % ^)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>⚠️ Укажите выражение для расчёта (например: .calc 2+2*2)</b>")
            return

        safe_args = utils.escape_html(args)
        try:
            expr = (
                args.replace("×", "*").replace("x", "*").replace("X", "*")
                .replace("÷", "/").replace(":", "/")
                .replace(",", ".").replace("^", "**")
            )
            res = safe_eval(expr)
            if isinstance(res, float):
                res = round(res, 8)
                if res.is_integer():
                    res = int(res)
            await utils.answer(message, f"<b>🧮 Выражение:</b> <code>{safe_args}</code>\n<b>📊 Результат:</b> <code>{res}</code>")
        except ZeroDivisionError:
            await utils.answer(message, "<b>❌ Ошибка: деление на ноль!</b>")
        except OverflowError:
            await utils.answer(message, "<b>❌ Ошибка: слишком большое число!</b>")
        except ValueError as ve:
            await utils.answer(message, f"<b>❌ Ошибка: {utils.escape_html(str(ve))}</b>")
        except Exception:
            await utils.answer(message, "<b>❌ Некорректное математическое выражение!</b>")

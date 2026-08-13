# meta developer: @lackyhyyy666

import aiohttp
import ast
import operator
import re
from .. import loader, utils

# Безопасный парсер для .calc
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval(expr):
    """Безопасное вычисление математических выражений без eval()"""
    def _eval(node):
        if isinstance(node, ast.Num):  # Поддержка старых версий Python
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Недопустимое значение")
        elif isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow):
                left = _eval(node.left)
                right = _eval(node.right)
                if abs(right) > 100 or abs(left) > 1000000:
                    raise ValueError("Слишком большая степень!")
                return OPERATORS[ast.Pow](left, right)
            left = _eval(node.left)
            right = _eval(node.right)
            return OPERATORS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            return OPERATORS[type(node.op)](_eval(node.operand))
        else:
            raise TypeError("Неподдерживаемая операция")

    parsed = ast.parse(expr, mode='eval')
    return _eval(parsed.body)

async def get_coingecko_rate():
    """Получение курса USDT/RUB с CoinGecko API с фолбэком на Binance API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        # 1. Запрос к CoinGecko
        try:
            async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=rub") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rate = data.get("tether", {}).get("rub")
                    if rate:
                        return float(rate)
        except Exception:
            pass

        # 2. Фолбэк к Binance API
        try:
            async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTRUB") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    price = data.get("price")
                    if price:
                        return float(price)
        except Exception:
            pass

        return None

def parse_args_with_custom_rate(args_raw):
    """
    Разбор аргументов на сумму и кастомный курс.
    Примеры: "20 (75)", "20.5 (78.2)", "20", "20 ( 75.5 )"
    """
    if not args_raw:
        return None, None

    # Заменяем запятые на точки для дробных чисел
    args_raw = args_raw.replace(",", ".")

    # Ищем паттерн вида: <число_суммы> (<число_курса>)
    match = re.search(r"^([\d.]+)\s*\(\s*([\d.]+)\s*\)$", args_raw.strip())
    if match:
        try:
            amount = float(match.group(1))
            custom_rate = float(match.group(2))
            return amount, custom_rate
        except ValueError:
            return None, None

    # Если скобок нет, пробуем спарсить просто сумму
    try:
        amount = float(args_raw.strip())
        return amount, None
    except ValueError:
        return None, None


@loader.tds
class USDTRUBMod(loader.Module):
    """Конвертер USDT <-> RUB + Калькулятор"""
    strings = {"name": "USDTRUB"}

    @loader.command()
    async def usdtcmd(self, message):
        """<сумма> [(курс)] — Перевести USDT в RUB"""
        args = utils.get_args_raw(message)
        
        if not args:
            amount, custom_rate = 1.0, None
        else:
            amount, custom_rate = parse_args_with_custom_rate(args)
            if amount is None:
                await utils.answer(message, "<b>⚠️ Укажите число корректно (например: .usdt 20 или .usdt 20 (75))</b>")
                return

        if custom_rate is not None:
            rate = custom_rate
            is_custom = True
        else:
            rate = await get_coingecko_rate()
            is_custom = False
            if rate is None:
                await utils.answer(message, "<b>❌ Ошибка при запросе к API курсов</b>")
                return

        result = amount * rate
        rate_note = f"Ручной курс: 1 USDT = {rate:.2f} RUB" if is_custom else f"Курс API: 1 USDT ≈ {rate:.2f} RUB"
        
        await utils.answer(
            message,
            f"<b>💵 {amount:,.2f} USDT</b> = <b>{result:,.2f} RUB</b>\n"
            f"<i>{rate_note}</i>"
        )

    @loader.command()
    async def usdtrcmd(self, message):
        """<сумма> [(курс)] — Перевести RUB в USDT"""
        args = utils.get_args_raw(message)
        
        if not args:
            amount, custom_rate = 100.0, None
        else:
            amount, custom_rate = parse_args_with_custom_rate(args)
            if amount is None:
                await utils.answer(message, "<b>⚠️ Укажите число корректно (например: .usdtr 5000 или .usdtr 5000 (75))</b>")
                return

        if custom_rate is not None:
            rate = custom_rate
            is_custom = True
        else:
            rate = await get_coingecko_rate()
            is_custom = False
            if rate is None:
                await utils.answer(message, "<b>❌ Ошибка при запросе к API курсов</b>")
                return

        result = amount / rate if rate > 0 else 0
        rate_note = f"Ручной курс: 1 USDT = {rate:.2f} RUB" if is_custom else f"Курс API: 1 USDT ≈ {rate:.2f} RUB"

        await utils.answer(
            message,
            f"<b>💳 {amount:,.2f} RUB</b> = <b>{result:,.2f} USDT</b>\n"
            f"<i>{rate_note}</i>"
        )

    @loader.command()
    async def calccmd(self, message):
        """<выражение> — Математический калькулятор"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>⚠️ Укажите выражение для расчёта (например: .calc 2+2*2)</b>")
            return

        try:
            expr = args.replace("x", "*").replace("X", "*").replace(",", ".").replace("^", "**")
            res = safe_eval(expr)
            if isinstance(res, float):
                res = round(res, 8)
                if res.is_integer():
                    res = int(res)
            await utils.answer(message, f"<b>🧮 Выражение:</b> <code>{args}</code>\n<b>📊 Результат:</b> <code>{res}</code>")
        except ZeroDivisionError:
            await utils.answer(message, "<b>❌ Ошибка: деление на ноль!</b>")
        except ValueError as ve:
            await utils.answer(message, f"<b>❌ Ошибка: {str(ve)}</b>")
        except Exception:
            await utils.answer(message, "<b>❌ Некорректное математическое выражение!</b>")


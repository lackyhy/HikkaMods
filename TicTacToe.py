# meta developer: @lackyhyyy666
# scope: inline

import copy
import enum
from random import choice
from typing import List

from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils
from ..inline.types import InlineCall

phrases = [
    "Твой мозг — просто шутка... Используй его!",
    "Неплохой ход...",
    "Попробуй победить меня!",
    "Я неотразим, у тебя нет шансов!",
    "Часики тикают... Торопись.",
    "Не спеши, подумай!",
    "Это был твой выбор, не мой...",
]


class Player(enum.Enum):
    x = 1
    o = 2

    @property
    def other(self):
        return Player.x if self == Player.o else Player.o


class Choice:
    def __init__(self, move, value, depth):
        self.move = move
        self.value = value
        self.depth = depth

    def __str__(self):
        return f"{str(self.move)}: {str(self.value)}"


class AbBot:
    def __init__(self, player):
        self.player = player

    def alpha_beta_search(self, board, is_max, current_player, depth, alpha, beta):
        winner = board.has_winner()
        if winner == self.player:
            return Choice(board.last_move(), 10 - depth, depth)
        elif winner == self.player.other:
            return Choice(board.last_move(), -10 + depth, depth)
        elif len(board.moves) == 9:
            return Choice(board.last_move(), 0, depth)

        candidates = board.get_legal_moves()
        max_choice = None
        min_choice = None
        for i in range(len(candidates)):
            row = candidates[i][0]
            col = candidates[i][1]
            newboard = copy.deepcopy(board)
            newboard.make_move(row, col, current_player)
            result = self.alpha_beta_search(
                newboard, not is_max, current_player.other, depth + 1, alpha, beta
            )
            result.move = newboard.last_move()

            if is_max:
                alpha = max(result.value, alpha)
                if alpha >= beta:
                    return result

                if max_choice is None or result.value > max_choice.value:
                    max_choice = result
            else:
                beta = min(result.value, beta)
                if alpha >= beta:
                    return result

                if min_choice is None or result.value < min_choice.value:
                    min_choice = result

        return max_choice if is_max else min_choice

    def select_move(self, board):
        choice = self.alpha_beta_search(board, True, self.player, 0, -100, 100)
        return choice.move if choice else None


MARKER_TO_CHAR = {
    None: " . ",
    Player.x: " x ",
    Player.o: " o ",
}


class Board:
    def __init__(self):
        self.dimension = 3
        self.grid = [
            [None for _ in range(self.dimension)] for _ in range(self.dimension)
        ]
        self.moves = []

    def make_move(self, row, col, player):
        self.grid[row][col] = player
        self.moves.append((row, col))

    def last_move(self):
        return self.moves[-1] if self.moves else None

    def get_legal_moves(self):
        moves = []
        for r in range(self.dimension):
            for c in range(self.dimension):
                if self.grid[r][c] is None:
                    moves.append((r, c))
        return moves

    def has_winner(self):
        if len(self.moves) < 5:
            return None

        for row in range(self.dimension):
            unique_rows = set(self.grid[row])
            if len(unique_rows) == 1:
                value = unique_rows.pop()
                if value is not None:
                    return value

        for col in range(self.dimension):
            unique_cols = {self.grid[row][col] for row in range(self.dimension)}
            if len(unique_cols) == 1:
                value = unique_cols.pop()
                if value is not None:
                    return value

        backwards_diag = {self.grid[0][0], self.grid[1][1], self.grid[2][2]}
        if len(backwards_diag) == 1:
            value = backwards_diag.pop()
            if value is not None:
                return value

        forwards_diag = {self.grid[0][2], self.grid[1][1], self.grid[2][0]}
        if len(forwards_diag) == 1:
            value = forwards_diag.pop()
            if value is not None:
                return value

        return None


@loader.tds
class TicTacToeMod(loader.Module):
    """Крестики-Нолики против человека или ИИ."""

    strings = {
        "name": "TicTacToe",
        "gamestart": "🎮 <b>Крестики-Нолики</b>\n<i>Нажмите кнопку ниже, чтобы начать игру!</i>",
        "gamestart_ai": "🤖 <b>Крестики-Нолики против ИИ</b>\n<i>Нажмите кнопку ниже, чтобы начать игру!</i>",
        "not_with_yourself": "❌ Нельзя играть с самим собой!",
        "not_your_turn": "❌ Сейчас не ваш ход!",
        "normal_game": (
            "<b>🎮 Крестики-Нолики</b>\n\n"
            "<i>\"{}\"</i>\n\n"
            "👤 <b>Противник:</b> {}\n"
            "👉 <b>Сейчас ход:</b> {}"
        ),
        "ai_game": (
            "<b>🤖 Игра против ИИ</b>\n\n"
            "<i>\"{}\"</i>\n\n"
            "👤 <b>Игрок:</b> {}\n"
            "❌ <b>Вы играете за:</b> {}"
        ),
        "win": (
            "🏆 <b>Победитель: {} ({})!</b>\n"
            "<code>{}</code>"
        ),
        "draw": "🤝 <b>Игра завершилась ничьей!</b>",
    }

    def __init__(self):
        self._games = {}

    async def client_ready(self, client, db):
        self._client = client
        self._me = await client.get_me()

    async def _process_click(self, call: InlineCall, i: int, j: int, char: str):
        if call.form["uid"] not in self._games:
            await call.answer("❌ Игра завершена или не найдена!")
            return

        game = self._games[call.form["uid"]]

        if call.from_user.id not in game["mapping"]:
            await call.answer("❌ Вы не участник этой игры!")
            return

        if game["turn"] != call.from_user.id:
            await call.answer(self.strings("not_your_turn"))
            return

        score = [list(line) for line in game["score"].split("|")]
        if score[i][j] != ".":
            await call.answer("⚠️ Клетка уже занята!")
            return

        score[i][j] = game["mapping"][call.from_user.id]
        game["score"] = "|".join(["".join(line) for line in score])

        other_player = [k for k in game["mapping"] if k != call.from_user.id][0]
        game["turn"] = other_player

        await call.edit(**self._render(call.form["uid"]))

    async def _process_click_ai(self, call: InlineCall, i: int, j: int, char: str):
        if call.form["uid"] not in self._games:
            await call.answer("❌ Игра завершена или не найдена!")
            return

        game = self._games[call.form["uid"]]

        if call.from_user.id != game["user"].id:
            await call.answer("❌ Это не ваша игра!")
            return

        if game["board"].grid[i][j] is not None:
            await call.answer("⚠️ Клетка уже занята!")
            return

        game["board"].make_move(i, j, game["human_player"])

        try:
            ai_move = game["bot"].select_move(game["board"])
            if ai_move:
                game["board"].make_move(
                    *ai_move,
                    game["ai_player"],
                )
        except Exception:
            pass

        await call.edit(**self._render_ai(call.form["uid"]))

    def win_indexes(self, n):
        return (
            [[(r, c) for r in range(n)] for c in range(n)]
            + [[(r, c) for c in range(n)] for r in range(n)]
            + [[(i, i) for i in range(n)]]
            + [[(i, n - 1 - i) for i in range(n)]]
        )

    def is_winner(self, board, decorator):
        n = len(board)
        return any(
            all(board[r][c] == decorator for r, c in indexes)
            for indexes in self.win_indexes(n)
        )

    def _render_text(self, board_raw: List[List[str]]) -> str:
        board = [[char.replace(".", " ") for char in line] for line in board_raw]
        return f"""
{board[0][0]} | {board[0][1]} | {board[0][2]}
----------
{board[1][0]} | {board[1][1]} | {board[1][2]}
----------
{board[2][0]} | {board[2][1]} | {board[2][2]}"""

    def _render(self, uid: str) -> dict:
        if uid not in self._games or uid not in self.inline._units:
            return

        game = self._games[uid]
        text = self.strings("normal_game").format(
            choice(phrases),
            game["name"],
            (
                utils.escape_html(get_display_name(self._me))
                if game["turn"] == self._me.id
                else game["name"]
            ),
        )
        score = [list(line) for line in game["score"].split("|")]
        kb = []
        rmap = {v: k for k, v in game["mapping"].items()}

        win_x, win_o = self.is_winner(score, "x"), self.is_winner(score, "o")

        if win_o or win_x:
            try:
                del self._games[uid]
            except KeyError:
                pass

            winner = rmap["x" if win_x else "o"]

            return {
                "text": self.strings("win").format(
                    (
                        game["name"]
                        if winner != self._me.id
                        else utils.escape_html(get_display_name(self._me))
                    ),
                    "❌" if win_x else "⭕️",
                    self._render_text(score),
                )
            }

        if game["score"].count("."):
            for i, row in enumerate(score):
                kb_row = [
                    {
                        "text": line.replace(".", " ").replace("x", "❌").replace("o", "⭕️"),
                        "callback": self._process_click,
                        "args": (i, j, line),
                    }
                    for j, line in enumerate(row)
                ]
                kb += [kb_row]
        else:
            try:
                del self._games[uid]
            except KeyError:
                pass

            return {"text": self.strings("draw")}

        return {"text": text, "reply_markup": kb}

    def _render_ai(self, uid: str) -> dict:
        if uid not in self._games or uid not in self.inline._units:
            return

        game = self._games[uid]
        text = self.strings("ai_game").format(
            choice(phrases),
            utils.escape_html(get_display_name(game["user"])),
            "❌" if game["amifirst"] else "⭕️",
        )
        score = [
            [MARKER_TO_CHAR[char].strip() for char in line]
            for line in game["board"].grid
        ]
        kb = []
        rmap = {v: k for k, v in game["mapping"].items()}

        win_x, win_o = self.is_winner(score, "x"), self.is_winner(score, "o")

        if win_o or win_x:
            try:
                del self._games[uid]
            except KeyError:
                pass

            winner = rmap["x" if win_x else "o"]

            return {
                "text": self.strings("win").format(
                    (
                        "🤖 ИИ"
                        if winner != game["user"].id
                        else utils.escape_html(get_display_name(game["user"]))
                    ),
                    "❌" if win_x else "⭕️",
                    self._render_text(score),
                )
            }

        if "".join(["".join(line) for line in score]).count("."):
            for i, row in enumerate(score):
                kb_row = [
                    {
                        "text": line.replace(".", " ").replace("x", "❌").replace("o", "⭕️"),
                        "callback": self._process_click_ai,
                        "args": (i, j, line),
                    }
                    for j, line in enumerate(row)
                ]
                kb += [kb_row]
        else:
            try:
                del self._games[uid]
            except KeyError:
                pass

            return {"text": self.strings("draw")}

        return {"text": text, "reply_markup": kb}

    async def inline__start_game(self, call: InlineCall):
        if call.from_user.id == self._me.id:
            await call.answer(self.strings("not_with_yourself"))
            return

        uid = call.form["uid"]
        first = choice([call.from_user.id, self._me.id])
        self._games[uid] = {
            "2_player": call.from_user.id,
            "turn": first,
            "mapping": {
                first: "x",
                (call.from_user.id if call.from_user.id != first else self._me.id): "o",
            },
            "name": utils.escape_html(
                get_display_name(await self._client.get_entity(call.from_user.id))
            ),
            "score": "...|...|...",
        }

        await call.edit(**self._render(uid))

    async def inline__start_game_ai(self, call: InlineCall):
        uid = call.form["uid"]
        user = await self._client.get_entity(call.from_user.id)

        first = choice(["ai", user.id])
        self._games[uid] = {
            "2_player": "ai",
            "turn": user.id,
            "mapping": {first: "x", "ai" if first != "ai" else user.id: "o"},
            "amifirst": first == user.id,
            "user": user,
            "ai_player": Player.x if first == "ai" else Player.o,
            "human_player": Player.o if first == "ai" else Player.x,
            "bot": AbBot(Player.x if first == "ai" else Player.o),
            "board": Board(),
        }

        if first == "ai":
            ai_move = self._games[uid]["bot"].select_move(self._games[uid]["board"])
            if ai_move:
                self._games[uid]["board"].make_move(
                    *ai_move,
                    self._games[uid]["ai_player"],
                )

        await call.edit(**self._render_ai(uid))

    @loader.command()
    async def cccmd(self, message: Message):
        """[@username / ID / reply] — Играть в крестики-нолики (без аргументов — с ИИ, с аргументом/реплаем — с человеком)"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if args or reply:
            await self.inline.form(
                self.strings("gamestart"),
                message=message,
                reply_markup={"text": "⚔️ Играть", "callback": self.inline__start_game},
                ttl=15 * 60,
                disable_security=True,
            )
        else:
            await self.inline.form(
                self.strings("gamestart_ai"),
                message=message,
                reply_markup={
                    "text": "🧠 Играть с ИИ",
                    "callback": self.inline__start_game_ai,
                },
                ttl=15 * 60,
                disable_security=True,
            )

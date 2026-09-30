# ⚡️ HikkaMods

Коллекция полезных и оптимизированных модулей для юзербота **[Hikka](https://github.com/hikkaru/Hikka)**.

> **Developer:** `@lackyhyyy666`

---

## 📦 Список модулей и установка

Для установки любого из модулей отправьте соответствующую команду `.dlm <ссылка>` в любой чат Telegram с установленным юзерботом Hikka.

---

### 💋 1. Kiss (`kiss.py`)

**Описание:** Модуль милых и весёлых RP-взаимодействий с пользователями (поцелуи, обнимашки, поглаживания по голове, пощёчины и т.д.). В ЛС собеседник выбирается автоматически, а в группах можно указывать через `@username`, ID или ответом на сообщение. Поддерживает настройку разрешённых пользователей в `.cfg Kiss allowed_users`.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/kiss.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.kis [@username / reply / текст]` — Поцеловать в лобик.
- `.kiss [@username / reply / текст]` — Поцеловать в щёчку.
- `.kisss [@username / reply / текст]` — Поцеловать в засос.
- `.patt [@username / reply / текст]` — Погладить по голове.
- `.pat [@username / reply / текст]` — Погладить по голове.
- `.hug [@username / reply / текст]` — Обнять.
- `.hig [@username / reply / текст]` — Приобнять.
- `.huga [текст]` — Обнять всех.
- `.lick [@username / reply / текст]` — Облизать.
- `.slap [@username / reply / текст]` — Дать пощёчину.
- `.bite [@username / reply / текст]` — Укусить.
- `.gbite [@username / reply / текст]` — Нежный кусь.
- `.cuddle [@username / reply / текст]` — Прижался(ась).
- `.boop [@username / reply / текст]` — Тыкнуть в носик.
- `.handhold [@username / reply / текст]` — Взять за ручку.
- `.hold [@username / reply / текст]` — Взять за ручку.
- `.feed [@username / reply / текст]` — Покормить вкусняшкой.
- `.poke [@username / reply / текст]` — Потыкать пальцем.
- `.ots [@username / reply / текст]` — Отсосать.
- `.otsa [текст]` — Отсосать всем.
- `.otl [@username / reply / текст]` — Отлизать.
- `.otla [текст]` — Отлизать всем.
- `.hit [@username / reply / текст]` — Ударить.
- `.rape [@username / reply / текст]` — Изнасиловать.
- `.fkick [@username / reply / текст]` — Пнуть.
- `.tickle [@username / reply / текст]` — Пощекотать.
- `.sitface [@username / reply / текст]` — Сесть на лицо.
- `.spank [@username / reply / текст]` — Шлёпнуть за попку.
- `.grope [@username / reply / текст]` — Полапать за интимные места.
- `.wink [@username / reply / текст]` — Подмигнуть.
- `.headslap [@username / reply / текст]` — Дать подзатыльник.
- `.fuck [@username / reply / текст]` — Трахнуть.
- `.fucka [текст]` — Трахнуть всех.
- `.feel [@username / reply / текст]` — Помацать.
- `.laugh [@target1] [@target2 / reply] [текст]` — Посмеяться вместе с @target1 над @target2.
- `.ship [@target1] [@target2 / reply] [текст]` — Зашипперить @target1 с @target2.
- `.gossip [@target1] [@target2 / reply] [текст]` — Посплетничать с @target1 о @target2.
- `.blanket [@username / reply / текст]` — Укутать в пледик.
- `.tea [@username / reply / текст]` — Угостить горячим чаем.
- `.squish [@username / reply / текст]` — Потискать за щёчки.
- `.pinch [@username / reply / текст]` — Игриво ущипнуть.
- `.burn [@username / reply / текст]` — Испепелить взглядом.
- `.incinerate [@username / reply / текст]` — Испепелить взглядом.
- `.kisshelp` — Показать красивую шпаргалку RP-команд.

</details>

---

### 🛠 2. Utils (`Utils.py`)

**Описание:** Модуль полезных утилит. Содержит генератор QR-кодов с уникальным визуальным стилем (скруглённые фиолетовые рамки глазков, чёрные круглые точки и белая карточка).

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/Utils.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.qrcode [ссылка / текст / реплай]` — Сгенерировать стильный QR-код без лишнего текста.

</details>

---

### 📧 3. TempMail (`TempMail.py`)

**Описание:** Временная почта прямо в Telegram на базе сервиса `mail.tm`. Позволяет создавать анонимные почтовые ящики, проверять входящие письма и просматривать данные авторизации.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/TempMail.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.mail` — Создать новый временный email-адрес.
- `.mailrefresh` — Сгенерировать новый email (перезаписать текущий ящик чата).
- `.mailcheck` — Проверить входящие письма в текущем ящике.
- `.mailinfo` — Показать текущий email и пароль.

</details>

---

### 🎵 4. YTMusicDownloader (`download.py`)

**Описание:** Быстрое скачивание музыкальных треков с **YouTube Music** и **YouTube** в формате MP3. Автоматически извлекает названия, исполнителей, длительность и обложки.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/download.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.dy [ссылка / название / реплай / в комментариях]` — Скачать и отправить трек в чат.

</details>

---

### 🚩 5. Flags (`flags.py`)

**Описание:** Получение эмодзи-флагов стран в моноширинном формате для удобного копирования.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/flags.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.flag [страна / код]` — Показать флаг указанной страны.

</details>

---

### 🎙 6. TrackLyrics (`text.py`)

**Описание:** Поиск и нормализация текстов песен.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/text.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.ttx [название / реплай / в комментариях]` — Найти текст песни и отформатировать его.

</details>

---

### 💵 7. USDTRUB (`usdt2rub.py`)

**Описание:** Быстрый конвертер валютных пар **USDT ↔ RUB** по актуальному курсу API или вручную + калькулятор.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/usdt2rub.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.usdt [сумма] [(ручной_курс)]` — Конвертировать USDT в RUB.
- `.usdtr [сумма] [(ручной_курс)]` — Конвертировать RUB в USDT.
- `.calc [выражение]` — Вычислить математическое выражение.

</details>

---

### 🌐 8. Sinf (`sinf.py`)

**Описание:** Информация по IP, доменам, гео-координатам, крипто-кошелькам и MAC-адресам.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/sinf.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.sinf [адрес / IP / домен / кошелек / координаты / реплай]` — Собрать всю доступную информацию об адресе.
- `.ip6 [IPv6 / реплай]` — Конвертация IPv6 в IPv4.

</details>

---

### ❌⭕️ 9. TicTacToe (`TicTacToe.py`)

**Описание:** Интерактивные Крестики-Нолики на инлайн-кнопках в Telegram.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/TicTacToe.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.cc` — Играть в Крестики-Нолики с ИИ или человеком.

</details>

---

### 🪙 10. CoinFlip (`coin.py`)

**Описание:** Анимированный модуль для подбрасывания монетки (Орёл или Решка).

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/coin.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.coin` — Подбросить монетку (Орёл / Решка).

</details>

---

### 🔘 11. InlineButtons (`btn.py`)

**Описание:** Сообщения с интерактивными инлайн-кнопками снизу.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/btn.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.btn [текст / реплай] [1. Название - https://ссылка.com]` — Создать сообщение с инлайн-кнопками.

</details>

---

### 🗑 12. DeletedLogger (`MessageLogger.py`)

**Описание:** Логирование удаленных и отредактированных сообщений с мгновенной пересылкой в лог-чат.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/MessageLogger.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.setlogchat` — Установить целевой чат для логов.
- `.ignorechat` — Добавить или удалить чат/ЛС из игнорируемых.
- `.togglelogself` — Включить или выключить логирование собственных сообщений.
- `.logstatus` — Показать настройки и статус логгера.

</details>

---

### 📝 13. EditHistory (`EditHistory.py`)

**Описание:** Отслеживание истории редактирования сообщений и вывод исходных версий.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/EditHistory.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.edits` — Ответьте на отредактированное сообщение, чтобы увидеть всю историю его изменений.
- `.clearhistory` — Очистить сохраненную историю изменений из памяти.
- `.histstats` — Показать статистику сохраненных изменений.

</details>

---

### 📢 14. SmartBroadcast (`SmartBroadcast.py`)

**Описание:** Модуль для умной персональной рассылки сообщений участникам чатов.

#### 📥 Команда установки:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/SmartBroadcast.py
```

<details>
<summary>📋 Список команд (нажмите, чтобы развернуть)</summary>

- `.smartcast [текст / реплай]` — Запустить умную рассылку всем реальным участникам чата.
- `.scstatus` — Проверить статус текущей рассылки.
- `.scstop` — Принудительно остановить текущую рассылку.

</details>

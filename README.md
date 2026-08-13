# ⚡️ HikkaMods

Коллекция полезных и оптимизированных модулей для юзербота **[Hikka](https://github.com/hikkaru/Hikka)**.

> **Developer:** `@lackyhyyy666`

---

## 📦 Список модулей и установка

Для установки любого из модулей отправьте соответствующую команду `.dlm <ссылка>` в любой чат Telegram с установленным юзерботом Hikka.

---

### 📧 1. TempMail (`TempMail.py`)

**Описание:** Временная почта прямо в Telegram на базе сервиса `mail.tm`. Позволяет создавать анонимные почтовые ящики, проверять входящие письма и просматривать данные авторизации.

#### 📥 Команда установки:
```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/TempMail.py
```

#### 🛠 Команды:
* `.mail` — Создать новый временный email-адрес.
* `.mailrefresh` — Сгенерировать новый email (перезаписать текущий ящик чата).
* `.mailcheck` — Проверить входящие письма в текущем ящике.
* `.mailinfo` — Показать текущий email и пароль.

---

### 🎵 2. YTMusicDownloader (`download.py`)

**Описание:** Быстрое скачивание музыкальных треков с **YouTube Music** и **YouTube** в формате MP3. Автоматически извлекает названия, исполнителей, длительность и обложки. Умеет искать по названию, прямой ссылке, реплай на аудио/сообщение или в ветках комментариев каналов.

#### 📥 Команда установки:
```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/download.py
```

#### 🛠 Команды:
* `.dy [ссылка / название / реплай / в комментариях]` — Скачать и отправить трек в чат.

---

### 🚩 3. Flags (`flags.py`)

**Описание:** Получение эмодзи-флагов стран в моноширинном формате для удобного копирования. Поддерживает поиск по русским названиям, синонимам, а также 2-буквенным (`RU`, `US`) и 3-буквенным (`RUS`, `DEU`) кодам ISO.

#### 📥 Команда установки:
```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/flags.py
```

#### 🛠 Команды:
* `.flag [страна / код]` — Показать флаг указанной страны.
  * *Примеры:* `.flag ru`, `.flag россия`, `.flag usa`

---

### 🎙 4. TrackLyrics (`text.py`)

**Описание:** Поиск и нормализация текстов песен. Выполняет молниеносный параллельный поиск по нескольким базам (Genius, AZLyrics, LRCLIB, Text-pesni и др.), автоматически нормализует «кривые» юникод-шрифты и распознает транслит русскоязычных песен.

#### 📥 Команда установки:
```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/text.py
```

#### 🛠 Команды:
* `.ttx [название / реплай / в комментариях]` — Найти текст песни и отформатировать его.

---

### 💵 5. USDTRUB (`usdt2rub.py`)

**Описание:** Быстрый конвертер валютных пар **USDT ↔ RUB** по актуальному курсу API (CoinGecko с фолбэком на Binance) или по указанному вручную курсу + встроенный безопасный математический калькулятор.

#### 📥 Команда установки:
```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/usdt2rub.py
```

#### 🛠 Команды:
* `.usdt [сумма] [(ручной_курс)]` — Конвертировать USDT в RUB.
  * *Примеры:* `.usdt 20` или `.usdt 20 (75)`
* `.usdtr [сумма] [(ручной_курс)]` — Конвертировать RUB в USDT.
  * *Примеры:* `.usdtr 5000` или `.usdtr 5000 (75)`
* `.calc [выражение]` — Вычислить математическое выражение.
  * *Пример:* `.calc 2+2*2`

---

## 🚀 Быстрая установка всех модулей разом

Отправьте в Telegram следующие команды по очереди:

```text
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/TempMail.py
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/download.py
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/flags.py
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/text.py
.dlm https://raw.githubusercontent.com/lackyhy/HikkaMods/main/usdt2rub.py
```

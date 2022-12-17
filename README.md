<a id="anchor"></a>
# Бот-ассистент

## Описание:
Telegram-бот, который обращается к API сервису Практикум.Домашка и узнёт статус вашей домашней работы: взята ли ваша домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.

## Используемые технологии:
Python, logging, python-telegram-bot

## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:ase77/homework_bot.git

cd homework_bot
```

Cоздать и активировать виртуальное окружение:

* Если у вас Linux/MacOS

    ```
    python3 -m venv venv
    source venv/bin/activate
    ```

* Если у вас Windows

    ```
    python -m venv venv
    source venv/Scripts/activate
    ```

Установить зависимости из файла `requirements.txt`:

```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

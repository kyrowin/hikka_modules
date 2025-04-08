# meta developer: @mainkyrowin

from deep_translator import GoogleTranslator
from telethon import events
from .. import loader, utils

__version__ = (1, 0, 0)

@loader.tds
class TranslateEnglishChatMod(loader.Module):
    """Переводит сообщения с английского на русский. (Работает по принципу: новое сообщение -> проверка на английскую букву -> если она есть = переводим)"""

    strings = {
        "name": "TranslateEnglishChat",
        "enabled": (
            "✅ <b>Module enabled. Translation will work in chat with ID: {}</b>"
        ),
        "disabled": (
            "⛔️ <b>Module disabled. Translation is no longer active.</b>"
        ),
        "translated": (
            "🌐 <b>Translation:</b>\n\n{}"
        ),
        "chat_set": (
            "💬 <b>Chat ID set to: {}</b>"
        ),
        "current_chat": (
            "ℹ️ <b>Currently monitoring chat ID: {}</b>"
        ),
        "no_chat": (
            "⚠️ <b>No chat ID configured! Use </b><code>.fcfg TranslateEnglishChat chat_id YOUR_CHAT_ID</code>"
        ),
        "no_id_provided": (
            "❌ <b>Please, send chat id. (int)</b>"
        )
    }

    strings_ru = {
        "enabled": (
            "✅ <b>Модуль включен. Перевод будет работать в чате с ID: {}</b>"
        ),
        "disabled": (
            "⛔️ <b>Модуль отключен. Перевод больше не работает.</b>"
        ),
        "translated": (
            "🌐 <b>Перевод:</b>\n\n{}"
        ),
        "chat_set": (
            "💬 <b>ID чата установлен: {}</b>"
        ),
        "current_chat": (
            "ℹ️ <b>Текущий отслеживаемый чат: {}</b>"
        ),
        "no_chat": (
            "⚠️ <b>ID чата не настроен! Используйте </b><code>.fcfg TranslateEnglishChat chat_id ID_ЧАТА</code>"
        ),
        "no_id_provided": (
            "❌ <b>Пожалуйста, укажите айди чата (число)</b>"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "chat_id",
            None,
            lambda: "Chat ID where translation will work",
        )
        self.enabled = False

    async def client_ready(self, client, db):
        self.client = client

    async def oncmd(self, message):
        """Включает проверку на новые сообщения"""
        if not self.config["chat_id"]:
            await utils.answer(message, self.strings("no_chat"))
            return
            
        self.enabled = True
        await utils.answer(
            message, 
            self.strings("enabled").format(self.config["chat_id"])
        )

    async def offcmd(self, message):
        """Выключает проверку на новые сообщения"""
        self.enabled = False
        await utils.answer(message, self.strings("disabled"))

    async def chatcmd(self, message):
        """Показывает айди чата в котором работает модуль"""
        if not self.config["chat_id"]:
            await utils.answer(message, self.strings("no_chat"))
            return
            
        await utils.answer(
            message,
            self.strings("current_chat").format(self.config["chat_id"])
        )

    async def watcher(self, event):
        """Смотрит есть ли английские буквы в сообщении."""
        if not self.enabled or not self.config["chat_id"]:
            return

        if event.chat_id != int(self.config["chat_id"]):
            return

        text_to_translate = event.raw_text

        if not text_to_translate:
            return

        if not any(char.isalpha() and ord(char) < 128 for char in text_to_translate):
            return

        try:
            translated = GoogleTranslator(source='auto', target='ru').translate(text_to_translate)
            await event.reply(
                self.strings("translated").format(translated)
            )
        except Exception as e:
            await utils.answer(
                event,
                f"<b>{self.strings('error')}:</b> {str(e)}"
            )

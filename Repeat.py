# meta developer: @mainkyrowin

from hikkatl.types import Message
from .. import loader, utils

__version__ = (1, 0, 2)

@loader.tds
class RepeatMod(loader.Module):
    """Повторяет введённый текст и может отправлять в указанный чат"""
    
    strings = {
        "name": "Repeater",
        "no_text": "🚫 <b>Write the text after the command that you need to repeat.</b>",
        "invalid_id": "🚫 <b>Invalid chat ID format or you're not member of this chat</b>",
        "sent": "✅ <b>Message sent to chat ID: {}</b>",
    }

    strings_ru = {
        "name": "Repeater",
        "no_text": "🚫 <b>Напишите текст после команды который нужно повторить.</b>",
        "invalid_id": "🚫 <b>Неверный ID чата или вы не состоите в этом чате</b>",
        "sent": "✅ <b>Сообщение отправлено в чат с ID: {}</b>",
    }

    async def repeatcmd(self, message: Message):
        """Повторяет текст и может отправлять в указанный чат"""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings["no_text"])
            return
        
        if "id=(" in args and args.endswith(")"):
            try:
                text, chat_id_part = args.rsplit("id=(", 1)
                chat_id = int(chat_id_part[:-1])
                
                try:
                    await self.client.send_message(chat_id, text.strip())
                    await utils.answer(
                        message, 
                        self.strings["sent"].format(chat_id)
                    )
                except Exception:
                    await utils.answer(message, self.strings["invalid_id"])
                return
            except ValueError:
                await utils.answer(message, self.strings["invalid_id"])
                return
        
        await utils.answer(message, args)
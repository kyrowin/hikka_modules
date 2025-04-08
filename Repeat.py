# meta developer: @mainkyrowin

from hikkatl.types import Message
from .. import loader, utils

__version__ = (1, 0, 1)

@loader.tds
class RepeatMod(loader.Module):
    """Повторяет введённый текст (Модуль БЫЛ предназначен для одновременной отправки сообщения от большого количества аккаунтов.)"""
    
    strings = {
        "name": "Repeater",
        "no_text": "🚫 <b>Write the text after the command that you need to repeat.</b>",
    }

    strings_ru = {
        "name": "Repeater",
        "no_text": "🚫 <b>Напишите текст после команды который нужно поторить.</b>",
    }

    async def repeatcmd(self, message: Message):
        """Повторяет текст после комманды .repeat"""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings["no_text"])
            return
            
        await utils.answer(message, args)
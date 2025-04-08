# meta developer: @mainkyrowin

from telethon.tl.types import Message  # type: ignore

from .. import loader, utils


@loader.tds
class Yandex(loader.Module):
    strings = {
        "name": "Yandex",
        "yandex": (
            "<emoji document_id=5300882244842300470>👩‍💻</emoji><b> I yandexed for"
            " you</b>\n"
        ),
        "no_args": "❌ No text to search",
    }
    strings_ru = {
        "yandex": (
            "<emoji document_id=5300882244842300470>👩‍💻</emoji><b> Я заяндексил за"
            " тебя</b>\n"
        ),
        "no_args": "❌ Нет текста для поиска",
    }

    @loader.command(
        ru_doc="Заяндексить ссылку",
        en_doc="Yandexed link",
    )
    async def yandexcmd(self, message: Message):
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return
        y = args.replace(" ", "+")
        yandex = f"https://yandex.ru/search/?text={y}"
        await utils.answer(message, self.strings("yandex") + yandex)

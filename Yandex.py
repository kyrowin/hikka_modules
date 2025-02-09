from telethon.tl.types import Message  # type: ignore

from .. import loader, utils


@loader.tds
class Yandex(loader.Module):
    strings = {
        "name": "Yandex",
        "Yandex": (
            "<emoji document_id=5300882244842300470>👩‍💻</emoji><b> I yandexed for"
            " you</b>\n"
        ),
        "no_args": "❌ No args",
    }
    strings_ru = {
        "Yandex": (
            "<emoji document_id=5300882244842300470>👩‍💻</emoji><b> Я заяндексил за"
            " тебя</b>\n"
        ),
        "no_args": "❌ Нет аргументов",
    }

    async def yandexcmd(self, message: Message):
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return
        g = args.replace(" ", "+")
        yandex = f"https://yandex.ru/search/?text={g}"
        await utils.answer(message, self.strings("Yandex") + yandex)

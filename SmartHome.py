# meta developer: @mainkyrowin

from hikkatl.types import Message
from .. import loader, utils
import logging
import requests
import json

logger = logging.getLogger(__name__)

__version__ = (1, 0, 0)

@loader.tds
class AliceSmartHomeMod(loader.Module):
    """Данный модуль позволяет управлять вашим умным домом!"""
    strings = {
        "name": "AliceSmartHome",
        "no_token": "🚫 Токен API не установлен. Используй <code>.fcfg AliceSmartHome token ваш_токен</code>",
        "token_saved": "🔑 Токен успешно сохранен",
        "devices_loaded": "✅ Устройства загружены",
        "error": "❌ Ошибка: {}",
        "no_devices": "🤷‍♂️ Устройства не найдены",
        "controlling": "🛠 Управление устройствами",
        "install_msg": (
            "🔧 <b>Как получить API токен?</b>\n\n"
            "Для работы модуля вам необходимо получить токен Яндекс API. "
            "Вся информация по получению токена доступна по ссылке:\n"
            "<a href='https://habr.com/ru/articles/789200/'>Инструкция на Habr</a>\n\n"
            "После получения токена установите его командой:\n"
            "<code>.fcfg AliceSmartHome token ваш_токен</code>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "token",
            None,
            lambda: "Токен API Яндекс (y0_...)",
        )
        self._message_id = None

    async def client_ready(self, client, db):
        self._client = client
        # Отправляем сообщение с инструкцией при первой загрузке
        if not self.config["token"]:
            await self._client.send_message(
                self._client.loader.inline.bot_username,
                self.strings("install_msg"),
                parse_mode="HTML"
            )

    async def smarthomecmd(self, message: Message):
        """Вызывает сообщение с inline кнопками через которые вы сможете управлять устройствами."""
        if not self.config["token"]:
            await utils.answer(message, self.strings("no_token"))
            return

        try:
            devices = await self._get_devices()
            if not devices:
                await utils.answer(message, self.strings("no_devices"))
                return

            self._message_id = message.id
            
            await self.inline.form(
                text=self.strings("controlling"),
                reply_markup=self._generate_markup(devices),
                message=message,
            )
        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))

    async def _get_devices(self):
        headers = {
            "Authorization": f"Bearer {self.config['token']}",
            "X-Request-Id": "telegram-hikka-module",
        }
        
        try:
            response = requests.get(
                "https://api.iot.yandex.net/v1.0/user/info",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, dict):
                raise ValueError("Некорректный ответ от API")
            
            devices = []
            
            for device in data.get("devices", []):
                if not isinstance(device, dict):
                    continue
                
                capabilities = []
                
                for cap in device.get("capabilities", []):
                    if not isinstance(cap, dict):
                        continue
                        
                    if cap.get("type") == "devices.capabilities.on_off":
                        state = cap.get("state", {})
                        if isinstance(state, dict):
                            capabilities.append({
                                "type": "on_off",
                                "state": state.get("value", False)
                            })
                
                if capabilities and device.get("id") and device.get("name"):
                    devices.append({
                        "id": device["id"],
                        "name": device["name"],
                        "type": device.get("type", "unknown"),
                        "capabilities": capabilities,
                    })
            
            logger.debug(f"Найдены устройства: {devices}")
            return devices
            
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if hasattr(e, 'response') else str(e)
            logger.error(f"Ошибка API: {e}\nResponse: {error_text}")
            raise Exception(f"Ошибка API: {str(e)}")
        except Exception as e:
            logger.exception("Неизвестная ошибка при получении устройств")
            raise Exception(f"Ошибка: {str(e)}")

    def _generate_markup(self, devices):
        buttons = []
        
        for device in devices:
            for capability in device["capabilities"]:
                if capability["type"] == "on_off":
                    buttons.append([{
                        "text": f"🟢 {device['name']} (Вкл)" if capability["state"] else f"🔴 {device['name']} (Выкл)",
                        "callback": self._toggle_device,
                        "args": (device["id"], not capability["state"])
                    }])
        
        return buttons

    async def _toggle_device(self, query, device_id, new_state):
        try:
            headers = {
                "Authorization": f"Bearer {self.config['token']}",
                "X-Request-Id": "telegram-hikka-module",
                "Content-Type": "application/json",
            }
            
            payload = {
                "devices": [{
                    "id": device_id,
                    "actions": [{
                        "type": "devices.capabilities.on_off",
                        "state": {
                            "instance": "on",
                            "value": new_state
                        }
                    }]
                }]
            }
            
            response = requests.post(
                "https://api.iot.yandex.net/v1.0/devices/actions",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            if self._message_id:
                devices = await self._get_devices()
                await query.edit(
                    text=self.strings("controlling"),
                    reply_markup=self._generate_markup(devices)
                )
            
            await query.answer(f"Устройство {'включено' if new_state else 'выключено'}")
            
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if hasattr(e, 'response') else str(e)
            logger.error(f"Ошибка переключения: {e}\nResponse: {error_text}")
            await query.answer(f"❌ Ошибка API: {str(e)}")
        except Exception as e:
            logger.exception("Ошибка в обработчике кнопки")
            await query.answer(f"❌ Ошибка: {str(e)}")
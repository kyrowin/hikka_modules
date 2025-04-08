# meta developer: @mainkyrowin

from hikkatl.types import Message
from .. import loader, utils
import logging
import requests
import json
import abc

logger = logging.getLogger(__name__)

__version__ = (1, 0, 1)

@loader.tds
class AliceSmartHomeMod(loader.Module):
    """Module for controlling Yandex Smart Home devices"""
    

    __metaclass__ = abc.ABCMeta
    
    strings = {
        "name": "AliceSmartHome",
        "desc": "This module allows you to control your Yandex Smart Home devices",
        "no_token": "🚫 API token is not set. Use <code>.fcfg AliceSmartHome token your_token</code>",
        "token_saved": "🔑 Token successfully saved",
        "devices_loaded": "✅ Devices loaded successfully",
        "error": "❌ Error: {}",
        "no_devices": "🤷‍♂️ No devices found",
        "controlling": "🛠 Device control",
        "install_msg": (
            "🔧 <b>How to get API token?</b>\n\n"
            "For module work you need to get Yandex API token.\n"
            "All information is available at:\n"
            "<a href='https://habr.com/ru/articles/789200/'>Habr instruction</a>\n\n"
            "After getting token set it with command:\n"
            "<code>.fcfg AliceSmartHome token your_token</code>"
        ),
        "device_toggled": "Device {}",
        "api_error": "❌ API error: {}",
        "invalid_response": "Invalid API response",
        "unknown_error": "Unknown error",
    }

    strings_ru = {
        "name": "AliceSmartHome",
        "desc": "Данный модуль позволяет управлять вашим умным домом Яндекс",
        "no_token": "🚫 Токен API не установлен. Используй <code>.fcfg AliceSmartHome token ваш_токен</code>",
        "token_saved": "🔑 Токен успешно сохранен",
        "devices_loaded": "✅ Устройства загружены",
        "error": "❌ Ошибка: {}",
        "no_devices": "🤷‍♂️ Устройства не найдены",
        "controlling": "🛠 Управление устройствами",
        "install_msg": (
            "🔧 <b>Как получить API токен?</b>\n\n"
            "Для работы модуля вам необходимо получить токен Яндекс API.\n"
            "Вся информация по получению токена доступна по ссылке:\n"
            "<a href='https://habr.com/ru/articles/789200/'>Инструкция на Habr</a>\n\n"
            "После получения токена установите его командой:\n"
            "<code>.fcfg AliceSmartHome token ваш_токен</code>"
        ),
        "device_toggled": "Устройство {}",
        "api_error": "❌ Ошибка API: {}",
        "invalid_response": "Некорректный ответ от API",
        "unknown_error": "Неизвестная ошибка",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "token",
            None,
            lambda: "Yandex API Token (y0_...)",
        )
        self._message_id = None

    async def client_ready(self, client, db):
        self._client = client
        if not self.config["token"]:
            await self._client.send_message(
                self._client.loader.inline.bot_username,
                self.strings("install_msg"),
                parse_mode="HTML"
            )

    async def smarthomecmd(self, message: Message):
        """Show control panel with inline buttons"""
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
                raise ValueError(self.strings("invalid_response"))
            
            devices = []
            
            for device in data.get("devices", []):
                if not isinstance(device, dict):
                    logger.warning("Invalid device format: %s", device)
                    continue
                
                capabilities = []
                
                for cap in device.get("capabilities", []):
                    if not isinstance(cap, dict):
                        logger.warning("Invalid capability format: %s", cap)
                        continue
                        
                    if cap.get("type") == "devices.capabilities.on_off":
                        state = cap.get("state", {})
                        if isinstance(state, dict):
                            capabilities.append({
                                "type": "on_off",
                                "state": state.get("value", False)
                            })
                        else:
                            logger.warning("Invalid state format for device %s", device.get("id"))
                
                if capabilities and device.get("id") and device.get("name"):
                    devices.append({
                        "id": device["id"],
                        "name": device["name"],
                        "type": device.get("type", "unknown"),
                        "capabilities": capabilities,
                    })
                else:
                    logger.warning("Device missing required fields: %s", device)
            
            logger.debug("Found %d devices", len(devices))
            return devices
            
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if hasattr(e, 'response') else str(e)
            logger.error("API request failed: %s\nResponse: %s", e, error_text)
            raise Exception(self.strings("api_error").format(str(e)))
        except Exception as e:
            logger.exception("Failed to get devices")
            raise Exception(self.strings("unknown_error"))

    def _generate_markup(self, devices):
        buttons = []
        
        for device in devices:
            for capability in device["capabilities"]:
                if capability["type"] == "on_off":
                    status = "🟢" if capability["state"] else "🔴"
                    text = f"{status} {device['name']} ({'On' if capability['state'] else 'Off'})"
                    buttons.append([{
                        "text": text,
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
            
            status = "enabled" if new_state else "disabled"
            await query.answer(self.strings("device_toggled").format(status))
            
        except requests.exceptions.RequestException as e:
            error_text = e.response.text if hasattr(e, 'response') else str(e)
            logger.error("Failed to toggle device: %s\nResponse: %s", e, error_text)
            await query.answer(self.strings("api_error").format(str(e)))
        except Exception as e:
            logger.exception("Button handler error")
            await query.answer(self.strings("error").format(str(e)))
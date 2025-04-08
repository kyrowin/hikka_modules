# meta developer: @kyrowin

from hikkatl.types import Message
from .. import loader, utils
import aiohttp
import logging

logger = logging.getLogger(__name__)

class PterodactylMod(loader.Module):
    """Управляет вашими серверами через pterodactyl api"""
    strings = {
        "name": "Pterodactyl",
        "cfg_ptero_url": "URL панели Pterodactyl",
        "cfg_api_key": "API ключ Pterodactyl",
        "start": "👋 Добро пожаловать в панель управления серверами!",
        "server_list": "📋 Список серверов:\n\n",
        "server_info": """
⚙️ Сервер: {name}
Статус: {emoji} {state}

📊 Статистика:
CPU: {cpu_current:.1f}%/{cpu_max}%
RAM: {ram_current:.1f}MB/{ram_max}MB ({ram_percent:.1f}%)
Диск: {disk_current:.1f}MB/{disk_max}MB ({disk_percent:.1f}%)

🌐 IP: {ip}
🔌 Порт: {port}
""",
        "action_started": "Выполняется {action}...",
        "action_error": "Ошибка выполнения команды",
        "data_error": "Ошибка получения данных сервера (Скорее всего, вы не указали данные в .cfg Pterodactyl)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ptero_url",
                "https://panel.example.com",
                lambda: self.strings["cfg_ptero_url"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "api_key",
                None,
                lambda: self.strings["cfg_api_key"],
                validator=loader.validators.String(),
            ),
        )

    async def api_request(self, method, endpoint, json=None):
        headers = {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json',
            'Accept': 'Application/vnd.pterodactyl.v1+json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                f'{self.config["ptero_url"]}/api/client/{endpoint}',
                headers=headers,
                json=json
            ) as response:
                if response.status == 204:
                    return True
                return await response.json()

    async def get_servers(self):
        return await self.api_request('GET', '')

    async def get_server_status(self, server_id):
        return await self.api_request('GET', f'servers/{server_id}/resources')

    async def get_server_details(self, server_id):
        return await self.api_request('GET', f'servers/{server_id}')

    async def power_action(self, server_id, action):
        return await self.api_request('POST', f'servers/{server_id}/power', {'signal': action})

    @loader.command()
    async def pterocmd(self, message: Message):
        """Открыть панель управления серверами"""
        await self.list_servers(message)

    def _build_button(self, text, callback, *args):
        return {"text": text, "callback": callback, "args": args}

    async def list_servers(self, call):
        try:
            servers_data = await self.get_servers()
            servers_list = self.strings["server_list"]
            buttons = []

            for server in servers_data['data']:
                attrs = server['attributes']
                server_id = attrs['identifier']

                status_data = await self.get_server_status(server_id)
                current_state = status_data['attributes']['current_state']
                state_emoji = await self._get_state_emoji(current_state)

                servers_list += f"{state_emoji} {attrs['name']} | {current_state.upper()}\n\n"

                buttons.append([
                    self._build_button(
                        f"⚙️ Управление {attrs['name']}",
                        self.server_menu,
                        server_id
                    )
                ])

            buttons.append([
                self._build_button("🔄 Обновить", self.list_servers)
            ])

            await utils.answer(call, servers_list, reply_markup=buttons)

        except Exception as e:
            logger.error(f"Error listing servers: {e}")
            await utils.answer(call, self.strings["data_error"])


    async def server_menu(self, call, server_id):
        try:
            server_data = await self.get_server_details(server_id)
            status_data = await self.get_server_status(server_id)
            
            if 'attributes' in server_data and 'attributes' in status_data:
                attrs = server_data['attributes']
                status_attrs = status_data['attributes']
                
                current_ram = status_attrs['resources']['memory_bytes'] / 1024 / 1024
                max_ram = attrs['limits']['memory']
                ram_percent = (current_ram / max_ram * 100) if max_ram > 0 else 0
                
                current_disk = status_attrs['resources']['disk_bytes'] / 1024 / 1024
                max_disk = attrs['limits']['disk']
                disk_percent = (current_disk / max_disk * 100) if max_disk > 0 else 0
                
                current_cpu = status_attrs['resources']['cpu_absolute']
                max_cpu = attrs['limits']['cpu']
                
                current_state = status_attrs['current_state']
                state_emoji = await self._get_state_emoji(current_state)
                
                server_info = self.strings["server_info"].format(
                    name=attrs['name'],
                    emoji=state_emoji,
                    state=current_state.upper(),
                    cpu_current=current_cpu,
                    cpu_max=max_cpu,
                    ram_current=current_ram,
                    ram_max=max_ram,
                    ram_percent=ram_percent,
                    disk_current=current_disk,
                    disk_max=max_disk,
                    disk_percent=disk_percent,
                    ip=attrs['relationships']['allocations']['data'][0]['attributes'].get('alias', attrs['relationships']['allocations']['data'][0]['attributes']['ip']),
                    port=attrs['relationships']['allocations']['data'][0]['attributes']['port']
                )
                
                buttons = [
                    [
                        self._build_button("▶️ Запуск", self.handle_power_action, server_id, "start"),
                        self._build_button("⏹ Стоп", self.handle_power_action, server_id, "stop"),
                    ],
                    [
                        self._build_button("🔄 Рестарт", self.handle_power_action, server_id, "restart"),
                        self._build_button("🔄 Обновить", self.server_menu, server_id),
                    ],
                    [
                        self._build_button("⬅️ Назад", self.list_servers),
                    ]
                ]
                
                await call.edit(server_info, reply_markup=buttons)
            else:
                await call.answer(self.strings["data_error"])
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            await call.answer(self.strings["data_error"])

    async def handle_power_action(self, call, server_id, action):
        try:
            action_text = await self._get_action_text(action)
            await call.answer(self.strings["action_started"].format(action=action_text))
            
            success = await self.power_action(server_id, action)
            
            if success:
                await self.server_menu(call, server_id)
            else:
                await call.answer(self.strings["action_error"])
        except Exception as e:
            logger.error(f"Error performing power action: {e}")
            await call.answer(self.strings["action_error"])

    async def _get_state_emoji(self, state):
        return {
            'running': '🟢',
            'starting': '🟡',
            'stopping': '🟡',
            'offline': '⚫'
        }.get(state, '⚪')

    async def _get_action_text(self, action):
        return {
            'start': 'запуск',
            'stop': 'остановка',
            'restart': 'перезапуск'
        }.get(action, 'действие')

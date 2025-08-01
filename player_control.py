import asyncio
import sys
import random

from control import Control
from unit import ByteButtonUnit

class PlayerControl(Control):
    LENGTH = 8
    def __init__(self, i2c, controller, pollrate=0.01):
        self.controller = controller
        self.bytebutton = ByteButtonUnit(i2c)
        self.bytebutton.set_led_show_mode(ByteButtonUnit.BYTEBUTTON_LED_USER_MODE)
        self.bytebutton.set_indicator_color(0x33FF33)
        self.pollrate = pollrate
        asyncio.create_task(self.poll())

    async def poll(self):
        while True:
            try:
                for index in range(8):
                    if self.bytebutton.get_button_state(index):
                        await self.action(index)
                    await asyncio.sleep(self.pollrate)
            except Exception as e:
                print("Uncaught exception in PlayerControl poll:", e)
                sys.print_exception(e)
    
    def active_players_index(self):
        return [(id in self.controller.player_ids) for id in self.controller.sorted_player_ids]
    
    async def action(self, index):
        print(f"Player button {index} pressed")
        if index >= len(self.controller.sorted_player_ids):
            await self.controller.disco()
            await asyncio.sleep(2)
        else:
            self.bytebutton.set_led_color(index,0xFFA500,ByteButtonUnit.BYTEBUTTON_LED_USER_MODE)
            player_ids = [self.controller.sorted_player_ids[index]]
            if self.active_players_index()[index]:
                await self.controller.modify_group_members(player_ids_to_remove=player_ids)
            else:
                await self.controller.modify_group_members(player_ids_to_add=player_ids)
            await self.update()
    
    async def update(self):
        for index,status in enumerate(self.active_players_index()):
            color = 0xBF40BF if self.controller.playback_state == "PLAYBACK_STATE_PAUSED" and status else 0x33FF33 if status else 0xFF0000
            self.bytebutton.set_led_color(index,color,ByteButtonUnit.BYTEBUTTON_LED_USER_MODE)
        for index in range(len(self.active_players_index()),self.LENGTH):
            self.bytebutton.set_led_color(index,0x000000,ByteButtonUnit.BYTEBUTTON_LED_USER_MODE)
            
    async def disco(self):
        try:
            while True:
                color = random.getrandbits(24)
                for led in range(self.LENGTH):
                    self.bytebutton.set_led_color(led, color, ByteButtonUnit.BYTEBUTTON_LED_USER_MODE)
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            await self.update()
            raise

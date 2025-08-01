import asyncio
import random

from control import Control
from unit import FaderUnit


class VolumeControl(Control):
    def __init__(self, controller, pins, volume_ceiling=0.6, pollrate=0.1):
        self.controller = controller
        self.fader = FaderUnit(pins)
        self.volume_ceiling = volume_ceiling
        self.current_volume = None
        self.pollrate = pollrate
        asyncio.create_task(self.poll())

    def set_color(self, leds, volume, reverse=False):
        start, end = leds
        length = end - start
        color = 0xBF40BF if self.controller.playback_state == "PLAYBACK_STATE_PAUSED" else (0x00FF00 if volume <= 0.55 else 0xFFA500 if volume <= 0.85 else 0xFF0000)

        for i in range(length):
            relative_pos = i / length
            led_index = end - 1 - i if reverse else start + i
            final_color = color if relative_pos < volume else 0x000000
            self.fader.set_color(led_index, final_color)

    @property
    def volume(self):
        sample_number = 10
        volume = sum(1 - (self.fader.get_raw() / 65535) for _ in range(sample_number))
        return round(volume / sample_number, 1)

    async def poll(self):
        counter = 0
        while True:
            volume = self.volume
            if volume != self.current_volume:
                self.set_color((0, 7), volume)
            counter += 1
            if counter > 1 / self.pollrate:
                counter = 0
                if volume != self.current_volume:
                    await self.controller.set_group_volume(volume * 100 * self.volume_ceiling)
                    print(f"Volume changed: {volume}")
                    self.set_color((7, 14), volume, True)
                self.current_volume = volume
            await asyncio.sleep(self.pollrate)

    async def update(self, error=False):
        self.set_color((7, 14), self.controller.volume / 100 / self.volume_ceiling, True)

    async def disco(self):
        try:
            counter = 0
            length = len(self.fader)
            while True:
                for led in range(length):
                    color = random.getrandbits(24) if led == counter % length else 0x000000
                    self.fader.set_color(led, color)
                counter += 1
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            self.set_color((0, 7), self.volume)
            await self.update()
            raise

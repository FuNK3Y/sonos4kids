import asyncio
import sys

from control import Control
from unit import ScrollUnit


class FavoriteControl(Control):
    PAGE_SIZE = 8
    LINE_HEIGHT = 16
    LED_COLOR = 0x33FF33

    def __init__(self, i2c, controller, display, pollrate=0.1):
        self.controller = controller
        self.display = display
        self.scroll_unit = ScrollUnit(i2c)
        self._last_rotary_value = self.scroll_unit.get_rotary_value()
        self.selected_favorite = None
        self.scroll_unit.fill_color(self.LED_COLOR)
        self.pollrate = pollrate
        self.cancelation_tick = None
        asyncio.create_task(self.poll())

    async def poll(self):
        while True:
            try:
                if self._last_rotary_value != self.scroll_unit.get_rotary_value():
                    self._last_rotary_value = self.scroll_unit.get_rotary_value()
                    self.cancelation_tick = 5 / self.pollrate
                    self.display.locked = True
                    await self.update_display(self._last_rotary_value)
                elif self.scroll_unit.get_button_status():
                    await self.action()
                elif self.display.locked:
                    self.cancelation_tick -= 1
                    if self.cancelation_tick <= 0:
                        self.selected_favorite = None
                        self.display.locked = False
                        await self.display.update(dirty=True)
                await asyncio.sleep(self.pollrate)
            except Exception as e:
                print("Uncaught exception in FavoriteControl poll:", e)
                sys.print_exception(e)

    async def action(self):
        print(f"Scroll button pressed")
        await self.controller.load_favorite(favorite_id=self.selected_favorite["id"])
        self.display.locked = False
        self.selected_favorite = None

    async def update_display(self, selected_index):
        if not self.controller.favorites:
            return
        self.display.lcd.clear(0)
        selected_index = -selected_index % len(self.controller.favorites)
        self.selected_favorite = self.controller.favorites[selected_index]
        page = selected_index // self.PAGE_SIZE
        start = page * self.PAGE_SIZE
        end = min(start + self.PAGE_SIZE, len(self.controller.favorites))

        for row, idx in enumerate(range(start, end)):
            self.display.lcd.setCursor(0, row * self.LINE_HEIGHT)
            self.display.lcd.print(
                self.display.remove_accents(f'{self.controller.favorites[idx]["name"]} [{self.controller.favorites[idx]["service"]["name"]}]'[:20]),
                0xE86100 if idx == selected_index else 0xFFFFFF,
            )

    def refresh_started(self):
        self.scroll_unit.fill_color(0x0000FF)

    def refresh_finished(self):
        self.scroll_unit.fill_color(self.LED_COLOR)

    async def update(self):
        pass

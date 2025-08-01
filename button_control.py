import machine
import asyncio
import sys

from control import Control

class ButtonControl(Control):
    def __init__(self, pin, debounce=0.05):
        self._downCounter = 0
        self.pin = machine.Pin(pin, machine.Pin.IN)
        self.debounce = debounce
        asyncio.create_task(self.poll())

    async def poll(self):
        while True:
            if self._downCounter > 0 and self.pin.value() == 1:
                self._downCounter = 0
                try:
                    await self.action()
                except Exception as e:
                    print("Uncaught exception in callback:", e)
                    sys.print_exception(e)
            elif self.pin.value() == 0:
                self._downCounter += 1
            await asyncio.sleep(self.debounce)
            
    async def action(self):
        print(f"Button {self.pin} pressed")
    
    async def update(self):
        pass

class RedButton(ButtonControl):
    def __init__(self, pin, controller, debounce=0.05):
        super().__init__(pin, debounce)
        self.controller=controller

    async def action(self):
        await super().action()
        await self.controller.skip_to_previous_track()
        
class BlueButton(ButtonControl):
    def __init__(self, pin, controller, debounce=0.05):
        super().__init__(pin, debounce)
        self.controller=controller

    async def action(self):
        await super().action()
        await self.controller.skip_to_next_track()
        
class ScreenButton(ButtonControl):
    def __init__(self, pin, controller, favorite, debounce=0.05):
        super().__init__(pin, debounce)
        self.controller=controller
        self.favorite=favorite

    async def action(self):
        await super().action()
        if self.favorite.selected_favorite:
            await self.favorite.action()
        elif self.controller.playback_state == "PLAYBACK_STATE_PLAYING":
            await self.controller.pause()
        else:
            await self.controller.play()
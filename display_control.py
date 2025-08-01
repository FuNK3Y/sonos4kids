import aiohttp
import asyncio
import random

from control import Control


class DisplayControl(Control):
    def __init__(self, controller, lcd, disco_text):
        super().__init__(controller)
        self._last_text = None
        self._last_image_url = None
        self.locked = False
        self.disco_text = disco_text
        self.lcd = lcd
        self.lcd.setBrightness(64)

    async def update(self, error=False, dirty=False):
        if self.locked:
            return
        current_item = self.controller.current_item
        current_image_url = self.controller.current_image_url
        if (dirty or current_item != self._last_text or current_image_url != self._last_image_url) and current_image_url:
            self._last_text = current_item
            self._last_image_url = current_image_url
            async with aiohttp.ClientSession() as session:
                async with session.get(self.controller.current_image_url) as response:
                    data = await response.read()
            self.lcd.clear(0)
            scale = 0.2 if "spotify" in current_image_url or "i.scdn.co" in current_image_url else 0.42
            self.lcd.drawImage(data, 0, 0, 0, 0, 0, 0, scale)
            self.lcd.setCursor(0, 120)
            self.lcd.print(self.remove_accents(current_item)[:20])

    def remove_accents(self, text):
        replacements = {
            # Lowercase
            "á": "a",
            "à": "a",
            "â": "a",
            "ä": "a",
            "ã": "a",
            "å": "a",
            "ç": "c",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ï": "i",
            "ñ": "n",
            "ó": "o",
            "ò": "o",
            "ô": "o",
            "ö": "o",
            "õ": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ý": "y",
            "ÿ": "y",
            # Uppercase
            "Á": "A",
            "À": "A",
            "Â": "A",
            "Ä": "A",
            "Ã": "A",
            "Å": "A",
            "Ç": "C",
            "É": "E",
            "È": "E",
            "Ê": "E",
            "Ë": "E",
            "Í": "I",
            "Ì": "I",
            "Î": "I",
            "Ï": "I",
            "Ñ": "N",
            "Ó": "O",
            "Ò": "O",
            "Ô": "O",
            "Ö": "O",
            "Õ": "O",
            "Ú": "U",
            "Ù": "U",
            "Û": "U",
            "Ü": "U",
            "Ý": "Y",
        }
        for accented, plain in replacements.items():
            text = text.replace(accented, plain)
        return text

    async def disco(self):
        height = self.lcd.height()
        width = self.lcd.width()
        while True:
            try:
                action = random.choice(["rect", "ellipse", "text"])
                color = random.getrandbits(24)
                w = random.randint(10, height // 2)
                h = random.randint(10, width // 2)
                x = random.randint(0, width)
                y = random.randint(0, height)
                if action == "rect":
                    self.lcd.fillRect(x, y, w, h, color)
                elif action == "ellipse":
                    self.lcd.fillEllipse(x, y, w, h, color)
                else:
                    self.lcd.setCursor(x, y)
                    self.lcd.print(self.disco_text, color)
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                await self.update(dirty=True)
                raise

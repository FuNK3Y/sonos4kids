import asyncio
import network
import time
import gc
import machine

from machine import I2C, Pin
from unit import ScrollUnit
from M5 import Lcd
from config import Config
from display_control import DisplayControl
from volume_control import VolumeControl
from controller import Controller
from player_control import PlayerControl
from favorite_control import FavoriteControl
from button_control import *

Lcd.setRotation(2)
Lcd.clear()
Lcd.setCursor(0, 0)
Lcd.print("Starting\r\n")

Config.load()
wlan = network.WLAN(network.STA_IF)
network.hostname(Config.wireless_network["hostname"])
wlan.active(True)
wlan.config(pm=network.WLAN.PM_NONE)
while not wlan.isconnected():
    print("Waiting for wifi")
    Lcd.print("Waiting for wifi\r\n")
    wlan.connect(Config.wireless_network["SSID"], Config.wireless_network["password"])
    time.sleep(10)


async def main():
    Lcd.print("Main loop starting\r\n")
    controller = Controller()
    display = DisplayControl(controller, Lcd, Config.disco_text)
    i2c = I2C(0, scl=Pin(39), sda=Pin(38), freq=100000)
    favorite = FavoriteControl(i2c, controller, display)
    controller.controls.append(display)
    controller.controls.append(VolumeControl(controller, (8, 7), 0.5))
    controller.controls.append(RedButton(5, controller))
    controller.controls.append(BlueButton(6, controller))
    controller.controls.append(ScreenButton(41, controller, favorite))
    controller.controls.append(PlayerControl(i2c, controller))
    controller.controls.append(favorite)
    await controller.connect()
    await controller.initialize_group()

    while True:
        print("### Refresh ###")
        print(f"{gc.mem_free()=}")
        print(f"{gc.mem_alloc()=}")
        favorite.refresh_started()
        await controller.refresh()
        favorite.refresh_finished()
        await asyncio.sleep(10)


asyncio.run(main())

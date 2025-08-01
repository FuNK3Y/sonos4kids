import aiohttp
import asyncio
import binascii
import sys

from config import Config


class Controller:
    def __init__(self):
        self.group = None
        self.volume = None
        self.playback_state = None
        self.current_item = None
        self.current_image_url = None
        self._disco_tasks = []
        self.sorted_player_ids = []
        self.player_ids = []
        self.controls = []
        self.favorites = []

    async def connect(self):
        encoded = binascii.b2a_base64(f"{Config.sonos['client_id']}:{Config.sonos['client_secret']}".encode()).decode().strip()
        auth_headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Length": "0",
            "Connection": "close",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.sonos.com/login/v3/oauth/access?grant_type=refresh_token&refresh_token={Config.sonos['refresh_token']}",
                headers=auth_headers,
            ) as response:
                data = await response.json()
        self.access_token = data["access_token"]
        Config.sonos["refresh_token"] = data["refresh_token"]  # If the refresh token gets refreshed - it gets saved
        Config.save()

    async def initialize_group(self):
        data = await self.get_groups()
        for group in data["groups"]:
            if Config.sonos["favorite_player"] in group["playerIds"]:
                self.group = group["id"]

        self.sorted_player_ids = sorted([player["id"] for player in data["players"]])

    async def _request(self, method, url, payload=None):
        await self.disco_stop()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Connection": "close",
        }
        async with aiohttp.ClientSession(base_url="https://api.ws.sonos.com/control/api/v1/", headers=headers) as session:
            async with session.request(method, url, json=payload) as response:
                return await response.json()

    async def get_groups(self):
        data = await self._request("GET", f"households/{Config.sonos['household_id']}/groups")
        for group in data["groups"]:
            if self.group and group["id"] == self.group:
                self.playback_state = group["playbackState"]
                self.player_ids = group["playerIds"]
        return data

    async def get_group_volume(self):
        data = await self._request("GET", f"groups/{self.group}/groupVolume")
        self.volume = data["volume"]
        return data

    async def set_group_volume(self, volume):
        data = await self._request("POST", f"groups/{self.group}/groupVolume", payload={"volume": volume})
        self.volume = volume
        return data

    async def get_playback_status(self):
        return await self._request("GET", f"groups/{self.group}/playback")

    async def get_metadata_status(self):
        data = await self._request("GET", f"groups/{self.group}/playbackMetadata")
        try:
            if data["container"]["type"] == "station":
                self.current_item = data["container"]["name"]
                self.current_image_url = data["container"]["imageUrl"]
                if "streamInfo" in data:
                    self.current_item += " - " + data["streamInfo"]
            else:
                self.current_item = data["currentItem"]["track"]["name"]
                self.current_image_url = data["currentItem"]["track"]["imageUrl"]
        except:
            pass
        return data

    async def play(self):
        data = await self._request("POST", f"groups/{self.group}/playback/play")
        self.playback_state = "PLAYBACK_STATE_PLAYING"
        await self.notify()
        return data

    async def pause(self):
        data = await self._request("POST", f"groups/{self.group}/playback/pause")
        self.playback_state = "PLAYBACK_STATE_PAUSED"
        await self.notify()
        return data

    async def skip_to_next_track(self):
        data = await self._request("POST", f"groups/{self.group}/playback/skipToNextTrack")
        await self.refresh()
        return data

    async def skip_to_previous_track(self):
        data = await self._request("POST", f"groups/{self.group}/playback/skipToPreviousTrack")
        await self.refresh()
        return data

    async def get_favorites(self):
        data = await self._request("GET", f"households/{Config.sonos['household_id']}/favorites")
        self.favorites = data["items"]
        return data

    async def load_favorite(self, favorite_id, action="REPLACE", play_on_completion=True):
        payload = {
            "favoriteId": favorite_id,
            "action": action,
            "playOnCompletion": play_on_completion,
        }
        data = await self._request("POST", f"groups/{self.group}/favorites", payload=payload)
        return data

    async def modify_group_members(self, player_ids_to_add=[], player_ids_to_remove=[]):
        payload = {
            "playerIdsToAdd": player_ids_to_add,
            "playerIdsToRemove": player_ids_to_remove,
        }
        data = await self._request("POST", f"groups/{self.group}/groups/modifyGroupMembers", payload=payload)
        self.player_ids = data["group"]["playerIds"]
        return data

    async def notify(self):
        for control in self.controls:
            await control.update()

    async def disco(self):
        if not self._disco_tasks:
            self._disco_tasks = [asyncio.create_task(control.disco()) for control in self.controls]
        else:
            await self.disco_stop()

    async def disco_stop(self):
        while self._disco_tasks:
            try:
                task = self._disco_tasks.pop(0)
                task.cancel()
                await task
            except:
                pass

    async def refresh(self):
        if not self._disco_tasks:
            try:
                await self.get_groups()
                await self.get_group_volume()
                await self.get_metadata_status()
                await self.get_favorites()
                await self.notify()
            except Exception as e:
                print("Uncaught exception during refresh:", e)
                sys.print_exception(e)

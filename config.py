import json


class Config:
    wireless_network = {"SSID": "ssid", "hostname": "Sonos4Kids", "password": "yourpasswordhere"}
    sonos = {"refresh_token": "", "household_id": "", "client_id": "", "client_secret": "", "favorite_player": ""}
    disco_text = ""
    _configFile = "config.json"

    def save():
        attributes_to_save = {k: v for k, v in Config.__dict__.items() if not callable(v) and not k.startswith("_")}
        with open(Config._configFile, "w") as file:
            file.write(json.dumps(attributes_to_save))

    def load():
        with open(Config._configFile, "r") as file:
            content = json.loads(file.read())
        for key in (k for k in content.keys()):
            setattr(Config, key, content[key])

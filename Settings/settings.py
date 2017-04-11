import json
import os
import logging
import argparse
from copy import deepcopy
from random import randint
default_path = "data/settings.json"


class Settings:
    def __init__(self, path=default_path):
        self.path = path
        self.default_settings = {
            "TOKEN": None,
            "EMAIL": None,
            "PASSWORD": None,
            "OWNER": None,
            "PREFIXES": [],
            "default": {"ADMIN_ROLE": ["Daddy"],
                        "MOD_ROLE": ["Deds"],
                        "PREFIXES": []}
        }
        self.logger = logging.getLogger("Conf")
        self.current = self._load_json()
        self.self_bot = False

    def parse_cmd_arguments(self):
        parser = argparse.ArgumentParser(description="FociePlays - Deds Bot")
        parser.add_argument("--owner", help="ID of the owner. Only who hosts "
                                            "FociePlaysDeds should be owner, this has "
                                            "security implications")
        parser.add_argument("--admin-role", help="Role seen as admin role by the bot")
        parser.add_argument("--mod-role", help="Role seen as mod role by the bot")

    def _load_json(self):
        current = None
        try:
            with open(self.path, encoding='utf-8', mode="r") as f:
                current = json.load(f)
        except: #Assume data is crap and recreate
            self.current = deepcopy(self.default_settings)
            self._save_json()

        if current.keys() != self.default_settings.keys():
            for key in self.default_settings.keys():
                if key not in current.keys():
                    current[key] = self.default_settings[key]
                    print("Adding " + str(key) +
                          " field to red settings.json")
            self.current = current
            self._save_json()
        return current

    def _save_json(self):
        rnd = randint(1000, 9999)
        fpath, ext = os.path.splitext(self.path)
        tmp_file = "{}-{}.tmp".format(fpath, rnd)
        try:
            with open(tmp_file, encoding='utf-8', mode="w") as f:
                json.dump(self.current, f, indent=4, sort_keys=True,
                          separators=(',', ' : '))
        except json.decoder.JSONDecodeError:
            self.logger.exception("Attempted to write file {} but JSON "
                                  "integrity check on tmp file has failed. "
                                  "The original file is unaltered."
                                  "".format(self.path))
            return False
        os.replace(tmp_file, self.path)

    @property
    def mod_role(self):
        return self.current["MOD_ROLE"]

    @property
    def admin_role(self):
        return self.current["ADMIN_ROLE"]

    @property
    def spec_roles(self):
        return set(self.mod_role) | set(self.admin_role)

    @property
    def owner(self):
        return self.current["OWNER"]

    @owner.setter
    def owner(self, value):
        self.current["OWNER"] = value

    @property
    def token(self):
        return os.environ.get("RED_TOKEN", self.current["TOKEN"])

    @token.setter
    def token(self, value):
        self.current["TOKEN"] = value
        self.current["EMAIL"] = None
        self.current["PASSWORD"] = None

    @property
    def email(self):
        return os.environ.get("RED_EMAIL", self.current["EMAIL"])

    @email.setter
    def email(self, value):
        self.current["EMAIL"] = value
        self.current["TOKEN"] = None

    @property
    def password(self):
        return os.environ.get("RED_PASSWORD", self.current["PASSWORD"])

    @password.setter
    def password(self, value):
        self.current["PASSWORD"] = value

    @property
    def login_credentials(self):
        if self.token:
            return (self.token,)
        elif self.email and self.password:
            return (self.email, self.password)
        else:
            return tuple()


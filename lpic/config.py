# -*- coding: utf-8 -*-
import os
from collections import OrderedDict
from pprint import pprint

import yaml

from .utils import iter_hosts, open_yaml
from .const import Constant
from .singleton import Singleton


class Config(Singleton):

    def __init__(self):
        self.default_config = {
            "storage": None,
            "storages": [
                
            ],
            "adjust": [
                {"name": "convert", "format": "jpg"},
                {"name": "resize", "maxWidth": None, "maxHeight": None},
                {"name": "blend", },
                {"name": "text", },
                {"name": "optimize", },
            ],
            "conf": {
                "format": "markdown",
                "customFormat": None,
                "rename": "uuid",
            }
        }

        # for module in iter_hosts():
        #     self.default_config[module.USE] = {
        #         "access": None,
        #         "secret": None,
        #         "region": None,
        #         "bucket": None,
        #         "url": None,
        #         "prefix": None,
        #     }

        self.path = Constant.config_path
        self.config = {}
        if not os.path.isfile(self.path):
            self.generate_config_file()

        try:
            self.config = open_yaml(self.path)
        except yaml.YAMLError:
            self.generate_config_file()

    def generate_config_file(self):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump(self.default_config, f, default_flow_style=False)

    def save_config_file(self):
        with open(self.path, "w", encoding="utf-8") as f:
            yaml.dump_all(self.config, f, default_flow_style = False)
    
    def get(self, name):
        pass



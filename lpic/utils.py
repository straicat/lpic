# -*- coding: utf-8 -*-
import importlib
import logging
import os
import pkgutil
import traceback
from functools import wraps

import yaml

logger = logging.getLogger(__name__)


def mute_log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        root = logging.getLogger()
        level = root.getEffectiveLevel()
        root.setLevel(logging.ERROR)
        ret = func(*args, **kwargs)
        root.setLevel(level)
        return ret

    return wrapper


def iter_hosts(pkgname="storage"):
    pkgpath = os.path.join(os.path.dirname(__file__), pkgname)
    for _, file, _ in pkgutil.iter_modules([pkgpath]):
        yield importlib.import_module(pkgname + "." + file)


def open_yaml(yml):
    for ec in ("utf-8", "gb18030", "gb2312", "gbk", "utf_8_sig"):
        try:
            with open(yml, "r", encoding=ec) as fp:
                if hasattr(yaml, "FullLoader"):
                    data = yaml.load(fp, Loader=yaml.FullLoader)
                else:
                    data = yaml.load(fp)
            return data
        except UnicodeDecodeError:
            pass

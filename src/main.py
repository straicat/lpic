#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import os
import sys

sys.path.append(os.path.dirname(__file__))

from base import LPic


def _main():
    lp = LPic()
    lp.load_config()
    if hasattr(lp, 'use'):
        for p in os.listdir(os.path.abspath(os.path.dirname(__file__))):
            basepart, ext = os.path.splitext(os.path.basename(p))
            if ext.startswith('.py') and lp.use == basepart.rstrip('_'):
                module = __import__(basepart)
                for cls in inspect.getmembers(module, inspect.isclass):
                    if cls[1] != LPic:
                        for attr in inspect.getmembers(cls[1]):
                            if attr[0] == 'main':
                                cls[1]().main()


if __name__ == '__main__':
    _main()

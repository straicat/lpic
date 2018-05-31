#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

sys.path.append(os.path.dirname(__file__))

from base import LPic
from cos import TencentLPic
from kodo import QiniuLPic


def _main():
    lp = LPic()
    if lp.use == 'tencent':
        TencentLPic().main()
    elif lp.use == 'qiniu':
        QiniuLPic().main()


if __name__ == '__main__':
    _main()

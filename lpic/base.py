#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os
import re
import shutil
import sys
import webbrowser
from functools import cmp_to_key

import yaml
from PIL import Image


class LPic:
    """用法: lpic [<command>] [<args>]

可用命令:
    help, -h, --help    显示帮助
    del                 删除Bucket中最新的文件
    web                 打开Bucket内容管理页面
    put <filename>      上传文件
    use [<option>]      切换云服务

省略命令时，上传最新文件。"""

    def __init__(self, conf=None):
        self.cloud_name = '云'
        self.conf_file = conf or os.path.join(os.path.dirname(__file__), 'lpic.yml')
        with open(self.conf_file) as fp:
            self._conf = yaml.load(fp)
        self.use = self._conf['use']
        self.available_clouds = sorted([c for c in self._conf if c != 'use'])
        self.conf = self._conf[self.use]
        self.web_url = None

    def preprocess(self, file):
        suffix = os.path.splitext(os.path.abspath(file))[1].lower()
        tmp_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_dir = self.conf.get('TmpDir') or '/tmp/lpic'
        os.makedirs(tmp_dir, exist_ok=True)
        new_file = os.path.join(tmp_dir, tmp_name)

        if suffix in ['.jpg', '.jpeg', '.png', '.bmp'] and self.conf.get('AutoCompress'):
            new_file += '.jpg'
            with Image.open(file) as im:
                im.save(new_file, format='JPEG', optimize=True, progressive=True)
        else:
            new_file += suffix
            shutil.copyfile(file, new_file)
        return new_file

    def upload(self, file):
        pass

    def delete(self):
        pass

    def _upload_default(self):
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        if files:
            files.sort(key=cmp_to_key(lambda a, b: os.stat(b).st_mtime - os.stat(a).st_mtime))
            ans = input('上传 %s 至%s？([y]/n) ' % (files[0], self.cloud_name))
            if ans in ['y', 'Y', '']:
                new_file = self.preprocess(files[0])
                self.upload(new_file)
        else:
            print('当前目录没有文件')

    def web(self):
        if self.web_url:
            webbrowser.open(self.web_url)

    def main(self):
        if len(sys.argv) == 1:
            self._upload_default()
        else:
            command = sys.argv[1]
            if command in ['help', '-h', '--help']:
                print(LPic.__doc__)
            elif command == 'del':
                self.delete()
            elif command == 'web':
                self.web()
            elif command == 'put':
                if len(sys.argv) == 2:
                    print('没有指定要上传的文件！')
                else:
                    self.upload(sys.argv[2])
            elif command == 'use':
                if len(sys.argv) == 2:
                    for c in self.available_clouds:
                        print('%s %s' % ('*' if c == self.use else ' ', c))
                elif sys.argv[2] in self.available_clouds:
                    with open(self.conf_file) as fp:
                        raw = fp.read()
                    with open(self.conf_file, 'w') as fp:
                        fp.write(re.sub('^use:\s+\S+', 'use: %s' % sys.argv[2], raw, flags=re.M))
            else:
                print('未知的命令：%s' % command)

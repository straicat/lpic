#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os
import re
import shutil
import sys
import tempfile
import webbrowser
from functools import cmp_to_key

import pyperclip
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

        if not os.path.isfile(self.conf_file):
            print('配置文件 %s 不存在！' % self.conf_file)
            return

        self._conf = self.load_yaml(self.conf_file)
        if self._conf is None:
            return

        self.use = self._conf['use']
        self.available_clouds = sorted([c for c in self._conf if c != 'use' and c != 'conf'])
        if 'conf' in self._conf:
            self.conf = self._conf['conf']
        else:
            self.conf = self._conf[self.use]
        self.cloud = self._conf[self.use]

        self.tmp_dir = self.conf.get('TmpDir')
        if self.tmp_dir:
            os.makedirs(self.tmp_dir, exist_ok=True)
            self._tmp_dir = None
        else:
            self._tmp_dir = tempfile.TemporaryDirectory()
            self.tmp_dir = self._tmp_dir.name

    @staticmethod
    def load_yaml(yml):
        data = None
        for ec in ('utf-8', 'gb18030', 'gb2312', 'gbk'):
            try:
                with open(yml, encoding=ec) as fp:
                    data = yaml.load(fp)
                break
            except UnicodeDecodeError:
                continue
            except yaml.YAMLError:
                print('文件不符合YAML格式规范：%s' % yml)
                return data
        return data

    @property
    def web_url(self):
        raise NotImplementedError

    def __del__(self):
        # noinspection PyBroadException
        try:
            if hasattr(self, '_tmp_dir') and self._tmp_dir:
                self._tmp_dir.cleanup()
        except Exception:
            pass

    def _preprocess(self, file):
        img = Image.open(file)
        suffix = os.path.splitext(os.path.abspath(file))[1].lower()
        tmp_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file = os.path.join(self.tmp_dir, tmp_name)
        compressible = False
        if self.conf.get('AutoCompress'):
            if suffix in ['.jpg', '.jpeg', '.png', '.bmp']:
                compressible = True
            if suffix == '.png' and 'A' in img.mode.upper():
                compressible = False
        if compressible:
            new_file += '.jpg'
            with Image.open(file) as im:
                im.save(new_file, format='JPEG', optimize=True, progressive=True)
        else:
            new_file += suffix
            shutil.copyfile(file, new_file)
        img.close()
        return new_file

    def upload(self, file):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def _upload_process(self, file):
        self.upload(file)
        file_link = os.path.basename(file)
        if self.cloud.get('UrlPrefix'):
            file_link = self.cloud.get('UrlPrefix') + file_link
            if self.conf.get('AutoCopy'):
                if self.conf.get('MarkdownFormat'):
                    file_link = '![](%s)' % file_link
                pyperclip.copy(file_link)
        print('已上传：%s  %sK' % (os.path.basename(file), round(os.path.getsize(file) / 1024, 1)))
        print(file_link)

    def _upload_default(self):
        pic_suffix = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tga', '.ppm']
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        files = list(filter(lambda f: os.path.splitext(os.path.abspath(f))[1].lower() in pic_suffix, files))
        files.sort(key=cmp_to_key(lambda a, b: os.stat(b).st_mtime - os.stat(a).st_mtime))
        if files:
            ans = input('上传 %s 至%s？([y]/n) ' % (files[0], self.cloud_name))
            if ans in ['y', 'Y', '']:
                new_file = self._preprocess(files[0])
                self._upload_process(new_file)
        else:
            print('当前目录没有图片文件')

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
                    self._upload_process(sys.argv[2])
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

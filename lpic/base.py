#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import re
import tempfile
import traceback
import uuid
import webbrowser
from datetime import datetime
from urllib.parse import quote, urlparse

import pyperclip
import yaml
from PIL import Image

from .interface import Storage

logger = logging.getLogger(__name__)


class LPic:
    LPIC_EXAMPLE = os.path.join(os.path.dirname(__file__), 'lpic.example.yml')
    LPIC_YML = os.path.join(os.path.dirname(__file__), 'lpic.yml')
    NOW = datetime.now()
    MAX_KEYS = 100
    ENCODINGS = ('utf-8', 'gb18030', 'gb2312', 'gbk', 'utf_8_sig')

    def __init__(self, conf, storage=None, option=None):
        self._conf = conf
        self.storage = storage  # type: Storage
        self.client = None

        self.conf = {}
        self.cloud = {}
        self.tmp_dir = None
        self.option = option

    @property
    def use(self):
        use = self.option.get('backend') or self._conf.get('backend')
        if use not in self._conf:
            raise ValueError("Invalid backend '{}', please config it first.".format(use))
        else:
            return use

    def _create_temp_dir(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def open_yaml(self, yml):
        data = {}
        for ec in self.ENCODINGS:
            try:
                with open(yml, encoding=ec) as fp:
                    if hasattr(yaml, 'FullLoader'):
                        data = yaml.load(fp, Loader=yaml.FullLoader)
                    else:
                        data = yaml.load(fp)
                break
            except UnicodeDecodeError:
                pass
            except yaml.YAMLError:
                logger.error(traceback.format_exc())
                return data
        return data

    # noinspection PyBroadException
    def exit(self):
        try:
            self.storage.close()
        except Exception:
            logger.debug(traceback.format_exc())
        try:
            if hasattr(self, 'tmp_dir') and self.tmp_dir:
                self.tmp_dir.cleanup()
        except Exception:
            logger.debug(traceback.format_exc())

    def preprocess_resize(self, img):
        """调整图片大小"""
        max_size = self.conf.get('MaxSize')
        if max_size:
            # 确定最大尺寸
            if isinstance(max_size, int):
                max_w, max_h = max_size, max_size
            elif isinstance(max_size, list):
                max_w, max_h = map(int, max_size)
            else:
                max_w, max_h = map(int, re.findall(r'\d+', str(max_size)))

            # 等比缩放
            ratio = img.size[0] / img.size[1]
            new_w, new_h = img.size
            if img.size[0] > max_w:
                new_w = min(new_w, max_w)
                new_h = min(new_h, int(max_w / ratio))
            if img.size[1] > max_h:
                new_w = min(new_w, int(max_h * ratio))
                new_h = min(new_h, max_h)

            logger.debug('max_w: {}, max_h: {}, new_w: {}, new_h: {}'.format(max_w, max_h, new_w, new_h))
            return img.resize((new_w, new_h), Image.BICUBIC)

    def preprocess_fill_alpha(self, img):
        """填充Alpha通道"""
        fa = self.conf.get('FillAlpha')
        color = fa
        # 确定背景色
        if isinstance(fa, bool) and fa:
            color = '#FFFFFF'
        elif isinstance(fa, str) and not fa.startswith('#'):
            color = '#' + fa
        logger.debug('background color: {}'.format(color))

        if 'A' in img.mode.upper() and isinstance(color, (str, int)):
            bg = Image.new('RGB', img.size, color)
            bg.paste(img, mask=img)
            return bg
        else:
            return img

    def generate_picname(self, filename):
        """生成图片名（不要后缀）"""
        mode = str(self.conf.get('NameMode')).lower()
        if mode not in ('md5', 'uuid', 'sha1', 'sha256', 'datetime', 'hex-timestamp'):
            mode = 'uuid'

        if mode in ('md5', 'sha1', 'sha256'):
            fb = open(filename, 'rb').read()
            algorithm = getattr(hashlib, mode)()
            algorithm.update(fb)
            return algorithm.hexdigest()
        elif mode == 'uuid':
            return str(uuid.uuid1()).replace('-', '')
        elif mode == 'datetime':
            return self.NOW.strftime('%Y%m%d%H%M%S%f')
        elif mode == 'hex-timestamp':
            return hex(int(1000000 * self.NOW.timestamp()))[2:]

    def preprocess(self, filename, adjust):
        img = Image.open(filename)
        suffix = os.path.splitext(os.path.abspath(filename))[1].lower()
        tmp_name = self.generate_picname(filename)
        self._create_temp_dir()
        new_file = os.path.abspath(os.path.join(self.tmp_dir.name, tmp_name))
        compress = False
        if self.conf.get('AutoCompress'):
            if suffix in ['.jpg', '.jpeg', '.png', '.bmp']:
                compress = True
            # 如果带Alpha通道，且不填充Alpha通道，则不进行压缩
            if 'A' in img.mode.upper() and not self.conf.get('FillAlpha'):
                compress = False

        if adjust:
            img = self.preprocess_resize(img)
        else:
            compress = False

        if compress:
            new_file += '.jpg'
            # 填充背景色
            if 'A' in img.mode.upper():
                img = self.preprocess_fill_alpha(img)
            img.save(new_file, format='JPEG', optimize=True, progressive=True)
        else:
            new_file += suffix
            img.save(new_file)
        img.close()
        return new_file

    @staticmethod
    def replace_datetime(string, datetime_):
        datetimes = re.findall(r'\$DATETIME(?:\(.*?\))?', string)
        for dt in datetimes:
            t = re.findall(r'\((.*?)\)', dt)
            if t:
                fmt = t[0]
            else:
                fmt = '%Y-%m-%d_%H%M%S'
            string = string.replace(dt, datetime_.strftime(fmt))

        dates = re.findall(r'\$DATE(?:\(.*?\))?', string)
        for d in dates:
            t = re.findall(r'\((.*?)\)', d)
            if t:
                fmt = t[0]
            else:
                fmt = '%Y-%m-%d'
            string = string.replace(d, datetime_.date().strftime(fmt))

        return string

    def parse_url_prefix(self):
        url_prefix = self.conf.get('UrlPrefix', '')
        url_prefix = self.replace_datetime(url_prefix, self.NOW)
        if urlparse(url_prefix).scheme in ('http', 'https') and url_prefix.count('/') > 2:
            if not url_prefix.endswith('/'):
                url_prefix += '/'

            i, j = -1, 0
            for i, c in enumerate(url_prefix):
                j += c == '/'
                if j == 3:
                    break
            host = url_prefix[:i]
            prefix = quote(url_prefix[i + 1:])
        else:
            host = url_prefix.rstrip('/')
            prefix = ''

        return host, prefix

    def generate_file_link(self, local_file, key_name):
        if '/' in key_name:
            key_name = os.path.basename(key_name)
            logger.warning("参数'key_name'值错误，自动转换为'{}'".format(key_name))

        # noinspection PyDictCreation
        env = {}
        host, prefix = self.parse_url_prefix()
        env['PREFIX'] = prefix
        env['KEY'] = prefix + key_name
        env['FILENAME'] = key_name
        env['FILEPART'], env['FILEEXT'] = os.path.splitext(key_name)
        env['URL'] = host + '/' + env['KEY']
        env['BASENAME'] = os.path.basename(local_file)
        env['BASEPART'], env['BASEEXT'] = os.path.splitext(env['BASENAME'])
        env['FULLPATH'] = os.path.abspath(local_file)
        env['DIRNAME'] = os.path.dirname(local_file)

        link = self.conf.get('LinkFormat')

        if link is None:
            if self.conf.get('MarkdownFormat'):
                return '![]({})'.format(env['URL'])
            else:
                return env['URL']

        link = self.replace_datetime(link, self.NOW)
        for k, v in env.items():
            if k not in ('DATE', 'DATETIME'):
                link = link.replace('$' + k, v)
        return link

    @staticmethod
    def get_default_pic():
        pic_suffix = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tga', '.ppm']
        files = [f for f in os.listdir('.') if os.path.isfile(f)]
        files = list(filter(lambda f: os.path.splitext(os.path.abspath(f))[1].lower() in pic_suffix, files))
        if files:
            return max(files, key=lambda x: os.stat(x).st_mtime)

    def upload_process(self, pic):
        file = self.preprocess(pic, self.option.get('adjust'))
        _, prefix = self.parse_url_prefix()
        ret = self.storage.upload(file, prefix)
        if ret:
            size = round(os.path.getsize(file) / 1024, 1)
            logger.info('已上传至{}：{}  {}K'.format(self.storage.name, os.path.basename(file), size))
            file_key = os.path.basename(file)
            link = self.generate_file_link(pic, file_key)
            if self.conf.get('AutoCopy'):
                pyperclip.copy(link)
            logger.info(link)
            return link
        else:
            logger.error('上传失败！')

    def ask_yn(self, prompt):
        if self.option.get('yes'):
            return True
        while True:
            ans = input(prompt).strip()
            if not ans:
                if '[y]' in prompt or '[Y]' in prompt:
                    return True
                if '[n]' in prompt or '[N]' in prompt:
                    return False
                logger.warning('请输入y或n')
            else:
                if ans in ('y', 'Y'):
                    return True
                if ans in ('n', 'N'):
                    return False
                logger.warning("输入无效：'{}'，请重新输入".format(ans))

    def handle_default(self, _):
        pic = self.get_default_pic()
        if pic:
            self.handle_put(pic)
        else:
            logger.error('当前目录没有图片文件')

    def hosts(self):
        return [c for c in self._conf if c != 'backend' and c != 'conf']

    def handle_use(self, dest):
        if dest is None:
            for h in self.hosts():
                logger.info('{} {}'.format('->' if h == self.use else '  ', h))
        else:
            if dest in self.hosts():
                for ec in self.ENCODINGS:
                    try:
                        with open(self.conf_file, 'r', encoding=ec) as fp:
                            raw = fp.read()
                        break
                    except UnicodeDecodeError:
                        pass
                raw = re.sub(r'^backend:\s+\S+', 'backend: {}'.format(dest), raw, flags=re.M)
                with open(self.conf_file, 'w', encoding='utf-8') as fp:
                    fp.write(raw)
            else:
                logger.error("不支持使用'{}'".format(dest))

    def handle_put(self, dest):
        if dest:
            if os.path.isfile(dest):
                if self.ask_yn('上传 {} 至{}？([y]/n) '.format(dest, self.storage.name)):
                    self.upload_process(dest)
            else:
                logger.error('当前目录没有指定的文件：{}'.format(dest))
        else:
            self.handle_default(dest)

    def handle_del(self, dest):
        prefix = dest or ''
        key = self.storage.find(prefix)
        if key:
            if self.ask_yn('从{}删除 {} ?([y]/n) '.format(self.storage.name, key)):
                if self.storage.delete(key):
                    logger.info('已从{}删除：{}'.format(self.storage.name, key))
                else:
                    logger.error('从{}删除失败：{}'.format(self.storage.name, key))
        else:
            logger.error("{}的存储库里没有以'{}'开头的文件".format(self.storage.name, prefix))

    def handle_web(self, _):
        if self.storage.web_url:
            webbrowser.open(self.storage.web_url)

    def main(self, cmd, dest):
        if self.use is not None:
            self.storage.auth()
            if cmd is None:
                self.handle_default(dest)
            else:
                if hasattr(self, 'handle_' + cmd):
                    getattr(self, 'handle_' + cmd)(dest)
                else:
                    logger.error('不支持的命令：{}'.format(cmd))

        self.exit()

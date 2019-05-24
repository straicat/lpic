#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import re
import sys
import tempfile
import traceback
import uuid
import webbrowser
from datetime import datetime

import pyperclip
import yaml
from PIL import Image

logger = logging.getLogger(__name__)


class LPic:
    """用法: lpic [<command>] [<args>]

可用命令:
    help, -h, --help    显示帮助
    del <prefix>        删除Bucket中的文件
    web                 打开Bucket内容管理页面
    put <filename>      上传文件
    use [<cloud>]       切换云服务

省略命令时，上传最新图片。"""

    LPIC_EXAMPLE = os.path.join(os.path.dirname(__file__), 'lpic.example.yml')
    LPIC_YML = os.path.join(os.path.dirname(__file__), 'lpic.yml')
    MAX_KEYS = 100

    def __init__(self, conf=None):
        self.cloud_name = '云'
        self.client = None

        self.conf_file = conf or self.LPIC_YML
        self._conf = {}
        self.conf = {}
        self.use = None
        self.cloud = {}
        self._tmp_dir = None
        self.tmp_dir = None

    def auth(self):
        raise NotImplementedError

    @property
    def web_url(self):
        raise NotImplementedError

    def upload(self, file):
        raise NotImplementedError

    def list(self, prefix):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def close(self):
        pass

    def load_config(self, use=None):
        try:
            self._conf.update(self.open_yaml(self.LPIC_EXAMPLE))
        except FileNotFoundError:
            pass
        try:
            self._conf.update(self.open_yaml(self.conf_file))
        except FileNotFoundError:
            logger.error('找不到配置文件：%s' % self.conf_file)
            return False

        self.use = use or self._conf['use']
        if 'conf' in self._conf:
            self.conf.update(self._conf['conf'])
        self.conf.update(self._conf[self.use])
        self.cloud = self._conf[self.use]
        return True

    def create_temp_dir(self):
        self.tmp_dir = self.conf.get('TmpDir')
        if self.tmp_dir:
            os.makedirs(self.tmp_dir, exist_ok=True)
        else:
            self._tmp_dir = tempfile.TemporaryDirectory()
            self.tmp_dir = self._tmp_dir.name

    @staticmethod
    def open_yaml(yml):
        data = {}
        for ec in ('utf-8', 'gb18030', 'gb2312', 'gbk'):
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
            self.close()
        except Exception:
            logger.error(traceback.format_exc())
        try:
            if hasattr(self, '_tmp_dir') and self._tmp_dir:
                self._tmp_dir.cleanup()
        except Exception:
            logger.error(traceback.format_exc())

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
        if mode not in ('md5', 'uuid', 'sha1', 'datetime', 'hex-timestamp'):
            mode = 'md5'

        if mode in ('md5', 'sha1'):
            fb = open(filename, 'rb').read()
            algorithm = getattr(hashlib, mode)()
            algorithm.update(fb)
            return algorithm.hexdigest()
        elif mode == 'uuid':
            return str(uuid.uuid1()).replace('-', '')
        elif mode == 'datetime':
            return datetime.now().strftime('%Y%m%d%H%M%S')
        elif mode == 'hex-timestamp':
            return hex(int(1000000 * datetime.now().timestamp()))[2:]

    def preprocess(self, filename):
        img = Image.open(filename)
        suffix = os.path.splitext(os.path.abspath(filename))[1].lower()
        tmp_name = self.generate_picname(filename)
        self.create_temp_dir()
        new_file = os.path.abspath(os.path.join(self.tmp_dir, tmp_name))
        compressible = False
        if self.conf.get('AutoCompress'):
            if suffix in ['.jpg', '.jpeg', '.png', '.bmp']:
                compressible = True
            # 如果带Alpha通道，且不填充Alpha通道，则不进行压缩
            if 'A' in img.mode.upper() and not self.conf.get('FillAlpha'):
                compressible = False

        img = self.preprocess_resize(img)
        if compressible:
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

    def delete_process(self, prefix):
        keys = self.list(prefix)
        if keys:
            key = keys[0]
            ans = input('删除 %s ?([y]/n) ' % key)
            if ans in ('y', 'Y', ''):
                if self.delete(key):
                    logger.info('已删除：%s' % key)
                else:
                    logger.error('删除失败：%s' % key)
        else:
            logger.error("存储库里没有以%s开头的文件" % prefix)

    @staticmethod
    def replace_date_datetime(string, date_, datetime_):
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
            string = string.replace(d, date_.strftime(fmt))

        return string

    def generate_file_link(self, local_file, file_key):
        # noinspection PyDictCreation
        env = {}
        env['FILENAME'] = file_key
        env['FILEPART'], env['FILEEXT'] = os.path.splitext(file_key)
        env['PREFIX'] = self.conf.get('UrlPrefix', '')
        env['URL'] = env['PREFIX'] + env['FILENAME']
        env['BASENAME'] = os.path.basename(local_file)
        env['BASEPART'], env['BASEEXT'] = os.path.splitext(env['BASENAME'])
        env['FULLPATH'] = os.path.abspath(local_file)
        env['DIRNAME'] = os.path.dirname(local_file)
        now = datetime.now()
        env['DATETIME'] = now
        env['DATE'] = now.date()

        link = self.conf.get('LinkFormat')

        if link is None:
            if self.conf.get('MarkdownFormat'):
                return '![](%s)' % env['URL']
            else:
                return env['URL']

        link = self.replace_date_datetime(link, env['DATE'], env['DATETIME'])
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
        file = self.preprocess(pic)
        ret = self.upload(file)
        if ret:
            logger.info('已上传：%s  %sK' % (os.path.basename(file), round(os.path.getsize(file) / 1024, 1)))
            file_key = os.path.basename(file)
            link = self.generate_file_link(pic, file_key)
            if self.conf.get('AutoCopy'):
                pyperclip.copy(link)
            logger.info(link)
            return link
        else:
            logger.error('上传失败！')

    def web(self):
        if self.web_url:
            webbrowser.open(self.web_url)

    def main(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        root.addHandler(sh)

        if self.load_config():
            self.auth()
            # 上传默认文件
            if len(sys.argv) == 1:
                pic = self.get_default_pic()
                if pic:
                    ans = input('上传 %s 至%s？([y]/n) ' % (pic, self.cloud_name))
                    if ans in ('y', 'Y', ''):
                        self.upload_process(pic)
                else:
                    logger.error('当前目录没有图片文件')
            else:
                cmd = sys.argv[1]
                if cmd in ['help', '-h', '--help']:
                    logger.info(LPic.__doc__)
                elif cmd == 'del':
                    if len(sys.argv) == 2:
                        logger.error('没有指定要删除的文件')
                    else:
                        self.delete_process(sys.argv[2])
                elif cmd == 'web':
                    self.web()
                elif cmd == 'put':
                    if len(sys.argv) == 2:
                        logger.error('没有指定要上传的文件！')
                    else:
                        pic = sys.argv[2]
                        if os.path.isfile(pic):
                            ans = input('上传 %s 至%s？([y]/n) ' % (pic, self.cloud_name))
                            if ans in ('y', 'Y', ''):
                                self.upload_process(pic)
                        else:
                            logger.error('当前目录没有指定的文件：%s' % pic)
                elif cmd == 'use':
                    available_clouds = sorted([c for c in self._conf if c != 'use' and c != 'conf'])
                    if len(sys.argv) == 2:
                        for c in available_clouds:
                            logger.info('%s %s' % ('*' if c == self.use else ' ', c))
                    elif sys.argv[2] in available_clouds:
                        with open(self.conf_file) as fp:
                            raw = fp.read()
                        with open(self.conf_file, 'w') as fp:
                            fp.write(re.sub(r'^use:\s+\S+', 'use: %s' % sys.argv[2], raw, flags=re.M))
                else:
                    logger.error('未知的命令：%s' % cmd)

        self.exit()

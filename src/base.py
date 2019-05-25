#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
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

logger = logging.getLogger(__name__)


class LPic:
    LPIC_EXAMPLE = os.path.join(os.path.dirname(__file__), 'lpic.example.yml')
    LPIC_YML = os.path.join(os.path.dirname(__file__), 'lpic.yml')
    NOW = datetime.now()
    MAX_KEYS = 100
    ENCODINGS = ('utf-8', 'gb18030', 'gb2312', 'gbk', 'utf_8_sig')

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

    def upload(self, file, prefix=''):
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
            logger.error('找不到配置文件：{}'.format(self.conf_file))
            return False

        self.use = use or self._conf['use']
        if self.use not in self._conf:
            logger.error("不支持使用'{}'".format(self.use))
            return False

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
        self.create_temp_dir()
        new_file = os.path.abspath(os.path.join(self.tmp_dir, tmp_name))
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

    def upload_process(self, pic, adjust):
        file = self.preprocess(pic, adjust)
        _, prefix = self.parse_url_prefix()
        ret = self.upload(file, prefix)
        if ret:
            size = round(os.path.getsize(file) / 1024, 1)
            logger.info('已上传至{}：{}  {}K'.format(self.cloud_name, os.path.basename(file), size))
            file_key = os.path.basename(file)
            link = self.generate_file_link(pic, file_key)
            if self.conf.get('AutoCopy'):
                pyperclip.copy(link)
            logger.info(link)
            return link
        else:
            logger.error('上传失败！')

    @staticmethod
    def set_logger():
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        root.addHandler(sh)

    def handle_default(self, args):
        pic = self.get_default_pic()
        if pic:
            args.cmd = 'put'
            args.dest = pic
            self.handle_put(args)
        else:
            logger.error('当前目录没有图片文件')

    def handle_use(self, args):
        clouds = sorted([c for c in self._conf if c != 'use' and c != 'conf'])
        if args.dest is None:
            for c in clouds:
                logger.info('{} {}'.format('->' if c == self.use else '  ', c))
        else:
            if args.dest in clouds:
                for ec in self.ENCODINGS:
                    try:
                        with open(self.conf_file, 'r', encoding=ec) as fp:
                            raw = fp.read()
                        break
                    except UnicodeDecodeError:
                        pass
                raw = re.sub(r'^use:\s+\S+', 'use: {}'.format(args.dest), raw, flags=re.M)
                with open(self.conf_file, 'w', encoding='utf-8') as fp:
                    fp.write(raw)
            else:
                logger.error("不支持使用'{}'".format(args.dest))

    def handle_put(self, args):
        if args.dest:
            pic = args.dest
            if os.path.isfile(pic):
                ans = input('上传 {} 至{}？([y]/n) '.format(pic, self.cloud_name))
                if ans in ('y', 'Y', ''):
                    self.upload_process(pic, args.no_adjust)
            else:
                logger.error('当前目录没有指定的文件：{}'.format(pic))
        else:
            self.handle_default(args)

    def handle_del(self, args):
        prefix = args.dest or ''
        keys = self.list(prefix)
        if keys:
            key = keys[0]
            ans = input('从{}删除 {} ?([y]/n) '.format(self.cloud_name, key))
            if ans in ('y', 'Y', ''):
                if self.delete(key):
                    logger.info('已从{}删除：{}'.format(self.cloud_name, key))
                else:
                    logger.error('从{}删除失败：{}'.format(self.cloud_name, key))
        else:
            logger.error("{}的存储库里没有以'{}'开头的文件".format(self.cloud_name, prefix))

    def handle_web(self, _):
        if self.web_url:
            webbrowser.open(self.web_url)

    def main(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description='''终端图床神器！支持阿里云、腾讯云和七牛云。
可用命令:
    help                显示帮助
    use [<cloud>]       查看/切换云服务
    put [<filename>]    上传文件。默认上传当前目录最新修改的图片。
    del [<prefix>]      删除Bucket中最新的指定前缀的文件
    web                 打开Bucket内容管理网页
省略命令时，上传当前目录最新修改的图片。''', epilog='''GitHub: https://github.com/jlice/lpic。欢迎start、提交PR。''')
        parser.add_argument('cmd', nargs='?', help='命令。支持：help, use, put, del, web')
        parser.add_argument('dest', nargs='?', help='')
        parser.add_argument('-n', action='store_true', dest='no_adjust', help='不进行预处理')
        args = parser.parse_args()

        self.set_logger()
        if self.load_config():
            self.auth()
            if args.cmd is None:
                self.handle_default(args)
            elif args.cmd == 'help':
                parser.print_help()
            else:
                if hasattr(self, 'handle_' + args.cmd):
                    getattr(self, 'handle_' + args.cmd)(args)
                else:
                    logger.error('不支持的命令：{}'.format(args.cmd))

        self.exit()

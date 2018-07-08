#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os

import pyperclip
from qiniu import Auth, put_file, BucketManager

from base import LPic


class QiniuLPic(LPic):
    def __init__(self, conf=None):
        super().__init__(conf)
        self.cloud_name = '七牛云'
        self.client = Auth(self.conf['AccessKey'], self.conf['SecretKey'])
        self.web_url = 'https://portal.qiniu.com/bucket/%s/resource' % self.conf['Bucket']

    def upload(self, file):
        _token = self.client.upload_token(self.conf['Bucket'], os.path.basename(file), 600)
        put_file(_token, os.path.basename(file), file)
        file_link = os.path.basename(file)
        if self.conf.get('UrlPrefix'):
            file_link = self.conf.get('UrlPrefix') + file_link
            if self.conf.get('AutoCopy'):
                if self.conf.get('MarkdownFormat'):
                    pyperclip.copy('![](%s)' % file_link)
                else:
                    pyperclip.copy(file_link)
        print('已上传：%s  %sK' % (file_link, round(os.path.getsize(file) / 1024, 1)))

    def delete(self):
        prefix = datetime.datetime.now().strftime("%Y%m%d")
        bucket = BucketManager(self.client)
        ret, _, _ = bucket.list(self.conf['Bucket'], prefix=prefix,limit=100)
        files = sorted([content['key'] for content in ret['items']], reverse=True)
        if files:
            if input('删除 %s ?([y]/n) ' % files[0]) in ['y', 'Y', '']:
                bucket.delete(self.conf['Bucket'], files[0])
                print('已删除：%s' % files[0])
        else:
            print("存储库里没有以%s开头的文件" % prefix)

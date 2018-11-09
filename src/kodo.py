#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os

from qiniu import Auth, put_file, BucketManager

from base import LPic


class QiniuLPic(LPic):
    def __init__(self, conf=None):
        super().__init__(conf)
        self.cloud_name = '七牛云'
        self.client = Auth(self.cloud['AccessKey'], self.cloud['SecretKey'])

    def web_url(self):
        return 'https://portal.qiniu.com/bucket/%s/resource' % self.cloud['Bucket']

    def upload(self, file):
        _token = self.client.upload_token(self.cloud['Bucket'], os.path.basename(file), 600)
        put_file(_token, os.path.basename(file), file)

    def delete(self):
        prefix = datetime.datetime.now().strftime("%Y%m%d")
        bucket = BucketManager(self.client)
        ret, _, _ = bucket.list(self.cloud['Bucket'], prefix=prefix, limit=100)
        files = sorted([content['key'] for content in ret['items']], reverse=True)
        if files:
            if input('删除 %s ?([y]/n) ' % files[0]) in ['y', 'Y', '']:
                bucket.delete(self.cloud['Bucket'], files[0])
                print('已删除：%s' % files[0])
        else:
            print("存储库里没有以%s开头的文件" % prefix)

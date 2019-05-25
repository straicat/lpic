#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from qiniu import Auth, put_file, BucketManager

from lpic import LPic


class QiniuLPic(LPic):
    def __init__(self, conf=None, **option):
        super(QiniuLPic, self).__init__(conf, **option)
        self.cloud_name = '七牛云'

    def auth(self):
        self.client = Auth(self.cloud['AccessKey'], self.cloud['SecretKey'])

    @property
    def web_url(self):
        return 'https://portal.qiniu.com/bucket/{}/resource'.format(self.cloud['Bucket'])

    def upload(self, file, prefix=''):
        _token = self.client.upload_token(self.cloud['Bucket'], os.path.basename(file), 600)
        _, ret = put_file(_token, prefix + os.path.basename(file), file)
        return ret.ok()

    def list(self, prefix):
        bucket = BucketManager(self.client)
        ret, _, _ = bucket.list(self.cloud['Bucket'], prefix=prefix, limit=self.MAX_KEYS)
        return [i['key'] for i in sorted([i for i in ret['items']], key=lambda x: -x['putTime'])]

    def delete(self, key):
        bucket = BucketManager(self.client)
        _, ret = bucket.delete(self.cloud['Bucket'], key)
        return ret.ok()

    def close(self):
        cache = '.qiniu_pythonsdk_hostscache.json'
        if os.path.isfile(cache):
            os.remove(cache)

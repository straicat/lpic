#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

import oss2

from lpic.interface import Storage


class AliyunLPic(Storage):
    def __init__(self, access=None, secret=None, region=None, bucket=None):
        super(AliyunLPic, self).__init__(access, secret, region, bucket)
        self.client = None

    @property
    @classmethod
    def backend(cls):
        return 'aliyun'

    @property
    def web_url(self):
        return "https://oss.console.aliyun.com/bucket/{}/{}/object".format(self.region, self.bucket)

    def auth(self):
        auth = oss2.Auth(self.access, self.secret)
        endpoint = self.region + '.aliyuncs.com'
        self.client = oss2.Bucket(auth, endpoint, self.bucket)

    def upload(self, file, prefix=''):
        ret = self.client.put_object_from_file(prefix + os.path.basename(file), file)
        return 200 <= ret.status < 300

    def find(self, prefix):
        ret = self.client.list_objects(prefix=prefix, max_keys=100)
        keys = [obj.key for obj in sorted([obj for obj in ret.object_list], key=lambda o: -o.last_modified)]
        return keys[0] if keys else None

    def delete(self, key):
        ret = self.client.delete_object(key)
        return 200 <= ret.status < 300

    def close(self):
        self.client.session.session.close()

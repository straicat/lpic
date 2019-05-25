#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import oss2

from lpic import LPic


class AliyunLPic(LPic):
    def __init__(self, conf=None, **option):
        super(AliyunLPic, self).__init__(conf, **option)
        self.cloud_name = '阿里云'

    def auth(self):
        auth = oss2.Auth(self.cloud['AccessKeyId'], self.cloud['AccessKeySecret'])
        endpoint = self.cloud['Region'] + '.aliyuncs.com'
        self.client = oss2.Bucket(auth, endpoint, self.cloud['Bucket'])

    @property
    def web_url(self):
        return 'https://oss.console.aliyun.com/bucket/{}/{}/object'.format(self.cloud['Region'], self.cloud['Bucket'])

    def upload(self, file, prefix=''):
        ret = self.client.put_object_from_file(prefix + os.path.basename(file), file)
        return 200 <= ret.status < 300

    def list(self, prefix):
        ret = self.client.list_objects(prefix=prefix, max_keys=self.MAX_KEYS)
        return [obj.key for obj in sorted([obj for obj in ret.object_list], key=lambda o: -o.last_modified)]

    def delete(self, key):
        ret = self.client.delete_object(key)
        return 200 <= ret.status < 300

    def close(self):
        self.client.session.session.close()

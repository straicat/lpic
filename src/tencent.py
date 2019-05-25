#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from urllib.parse import urlencode

# noinspection PyPackageRequirements
from qcloud_cos import CosConfig, CosS3Client

from base import LPic


class TencentLPic(LPic):
    def __init__(self, conf=None):
        super().__init__(conf)
        self.cloud_name = '腾讯云'

    def auth(self):
        config = CosConfig(Secret_id=self.cloud['SecretId'],
                           Secret_key=self.cloud['SecretKey'],
                           Region=self.cloud['Region'])
        self.client = CosS3Client(config)

    @property
    def web_url(self):
        params = {
            'type': 'filelist',
            'bucketName': self.cloud['Bucket'],
            'path': '',
            'region': self.cloud['Region']
        }
        return 'https://console.cloud.tencent.com/cos5/bucket/setting?{}'.format(urlencode(params))

    def upload(self, file):
        ret = self.client.put_object_from_local_file(
            Bucket=self.cloud['Bucket'],
            LocalFilePath=file,
            Key=os.path.basename(file)
        )
        return bool(ret.get('ETag'))

    def list(self, prefix):
        response = self.client.list_objects(
            Bucket=self.cloud['Bucket'],
            Prefix=prefix,
            MaxKeys=self.MAX_KEYS
        )
        if 'Contents' in response:
            def cmp(x):
                return -datetime.strptime(x['LastModified'], '%Y-%m-%dT%H:%M:%S.000Z').timestamp()

            return [c['Key'] for c in sorted([c for c in response['Contents']], key=cmp)]
        else:
            return []

    def delete(self, key):
        ret = self.client.delete_objects(
            Bucket=self.cloud['Bucket'],
            Delete={
                'Object': [{'Key': key}],
                'Quiet': 'false'
            }
        )
        return 'Deleted' in ret and len(ret['Deleted']) == 1

    def close(self):
        # noinspection PyProtectedMember
        self.client._session.close()

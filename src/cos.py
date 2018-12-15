#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from qcloud_cos import CosConfig, CosS3Client

from base import LPic


class TencentLPic(LPic):
    def __init__(self, conf=None):
        super().__init__(conf)
        self.cloud_name = '腾讯云'
        config = CosConfig(Secret_id=self.cloud['SecretId'],
                           Secret_key=self.cloud['SecretKey'],
                           Region=self.cloud['Region'])
        self.client = CosS3Client(config)

    def web_url(self):
        return 'https://console.cloud.tencent.com/cos5/bucket/setting?type=filelist&bucketName=%s&path=&region=%s' % (
            self.cloud['Bucket'], self.cloud['Region'])

    def upload(self, file):
        self.client.put_object_from_local_file(
            Bucket=self.cloud['Bucket'],
            LocalFilePath=file,
            Key=os.path.basename(file)
        )

    def delete(self, name):
        response = self.client.list_objects(
            Bucket=self.cloud['Bucket'],
            Prefix=name,
            MaxKeys=100
        )
        if 'Contents' in response:
            files = sorted([content['Key'] for content in response['Contents']], reverse=True)
            if input('删除 %s ?([y]/n) ' % files[0]) in ['y', 'Y', '']:
                self.client.delete_object(
                    Bucket=self.cloud['Bucket'],
                    Key=name
                )
                print('已删除：%s' % files[0])
        else:
            print("存储库里没有以%s开头的文件" % name)

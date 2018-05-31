#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os

import pyperclip
from qcloud_cos import CosConfig, CosS3Client

from base import LPic


class TencentLPic(LPic):
    def __init__(self, conf=None):
        super().__init__(conf)
        self.cloud_name = '腾讯云'
        config = CosConfig(Secret_id=self.conf['SecretId'],
                           Secret_key=self.conf['SecretKey'],
                           Region=self.conf['Region'])
        self.client = CosS3Client(config)
        self.web_url = 'https://console.cloud.tencent.com/cos5/bucket/setting?type=filelist&bucketName=%s&path=&region=%s' % (
            self.conf['Bucket'], self.conf['Region'])

    def upload(self, file):
        self.client.put_object_from_local_file(
            Bucket=self.conf['Bucket'],
            LocalFilePath=file,
            Key=os.path.basename(file)
        )
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
        response = self.client.list_objects(
            Bucket=self.conf['Bucket'],
            Prefix=prefix,
            MaxKeys=100
        )
        if 'Contents' in response:
            files = sorted([content['Key'] for content in response['Contents']], reverse=True)
            if input('删除 %s ?([y]/n) ' % files[0]) in ['y', 'Y', '']:
                self.client.delete_object(
                    Bucket=self.conf['Bucket'],
                    Key=files[0]
                )
                print('已删除：%s' % files[0])
        else:
            print("存储库里没有以%s开头的文件" % prefix)

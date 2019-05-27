# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class Storage(ABC):
    def __init__(self, access=None, secret=None, region=None, bucket=None):
        self.access = access
        self.secret = secret
        self.region = region
        self.bucket = bucket

    @property
    @classmethod
    @abstractmethod
    def backend(cls):
        return NotImplemented

    @property
    @abstractmethod
    def web_url(self):
        return NotImplemented

    @abstractmethod
    def auth(self):
        return NotImplemented

    @abstractmethod
    def upload(self, file, prefix=''):
        return NotImplemented

    @abstractmethod
    def find(self, prefix):
        return NotImplemented

    @abstractmethod
    def delete(self, key):
        return NotImplemented

    @abstractmethod
    def close(self):
        return NotImplemented


class Adjust(ABC):
    pass

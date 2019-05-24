import os
import unittest
from time import sleep

from PIL import Image

from qiniu_ import QiniuLPic


@unittest.skipUnless(os.path.isfile('lpic.yml'), '没有lpic.yml')
class QiniuLPicTestCase(unittest.TestCase):
    def setUp(self):
        self.lpic = QiniuLPic('lpic.yml')
        self.lpic.load_config(use='qiniu')
        self.lpic.auth()
        self.tmp = 'tmp{}.jpg'
        for i in range(2):
            im = Image.new('RGB', (1, 1))
            im.save(self.tmp.format(i))
            sleep(0.1)

    def tearDown(self):
        self.lpic.exit()
        for i in range(2):
            os.remove(self.tmp.format(i))

        cache = '.qiniu_pythonsdk_hostscache.json'
        if os.path.isfile(cache):
            os.remove(cache)

    def test(self):
        t = 'tmp'
        ret = self.lpic.list(t)
        self.assertListEqual([], ret)

        ret = self.lpic.upload(self.tmp.format(0))
        self.assertEqual(True, ret)
        ret = self.lpic.list(t)
        self.assertListEqual([self.tmp.format(0)], ret)
        sleep(1)
        ret = self.lpic.upload(self.tmp.format(1))
        self.assertEqual(True, ret)
        ret = self.lpic.list(t)
        self.assertListEqual([self.tmp.format(1), self.tmp.format(0)], ret)

        ret = self.lpic.delete(self.tmp.format(0))
        self.assertEqual(True, ret)
        ret = self.lpic.delete(self.tmp.format(1))
        self.assertEqual(True, ret)


if __name__ == '__main__':
    unittest.main()

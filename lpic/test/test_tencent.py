import os
import unittest
from time import sleep

from PIL import Image

from lpic.storage.tencent import TencentLPic


@unittest.skipUnless(os.path.isfile('lpic.yml'), '没有lpic.yml')
class TencentLPicTestCase(unittest.TestCase):
    def setUp(self):
        self.lpic = TencentLPic('lpic.yml', use='tencent')
        self.lpic.load_config()
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

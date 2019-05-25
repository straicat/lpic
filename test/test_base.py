import os
import unittest
from datetime import datetime
from time import sleep

from PIL import Image

from base import LPic


class LPicTestCase(unittest.TestCase):
    def setUp(self):
        self.lpic = LPic()

    def test_preprocess_resize(self):
        im = Image.new('RGB', (5, 5))
        self.lpic.conf.update({'MaxSize': '8x4'})
        im = self.lpic.preprocess_resize(im)
        self.assertEqual(4, im.size[0])
        self.assertEqual(4, im.size[1])

        im = Image.new('RGB', (5, 5))
        self.lpic.conf.update({'MaxSize': '3x6'})
        im = self.lpic.preprocess_resize(im)
        self.assertEqual(3, im.size[0])
        self.assertEqual(3, im.size[1])

        im = Image.new('RGB', (5, 5))
        self.lpic.conf.update({'MaxSize': '4x2'})
        im = self.lpic.preprocess_resize(im)
        self.assertEqual(2, im.size[0])
        self.assertEqual(2, im.size[1])

    def test_preprocess_fill_alpha(self):
        im = Image.new('RGBA', (2, 1), 0)
        block = Image.new('RGB', (1, 1), '#FF0000')
        im.paste(block)

        self.assertEqual(4, len(im.getdata()[0]))
        self.assertEqual(4, len(im.getdata()[1]))
        self.assertEqual(0, im.getdata()[0][2])
        self.assertEqual(0, im.getdata()[1][2])
        self.assertEqual(255, im.getdata()[0][3])
        self.assertEqual(0, im.getdata()[1][3])

        self.lpic.conf.update({'FillAlpha': True})
        im = self.lpic.preprocess_fill_alpha(im)

        self.assertEqual(3, len(im.getdata()[0]))
        self.assertEqual(3, len(im.getdata()[1]))
        self.assertEqual(0, im.getdata()[0][2])
        self.assertEqual(255, im.getdata()[1][2])

    def test_replace_date_datetime(self):
        s = 'aa$DATE(%Y/%m/%d)$DATETIME(-%Y-%m-%d %H:%M:%S-)'
        dt = datetime(2020, 5, 10, 22, 23, 00)
        self.assertEqual('foo', self.lpic.replace_datetime('foo', dt))
        self.assertEqual('aa2020/05/10-2020-05-10 22:23:00-', self.lpic.replace_datetime(s, dt))

    def test_generate_file_link(self):
        self.lpic.conf = {'MarkdownFormat': True, 'UrlPrefix': 'https://foo.org/'}
        local = '/tmp/test.png'
        remote = 'qwer.jpg'
        self.assertEqual('![](https://foo.org/qwer.jpg)', self.lpic.generate_file_link(local, remote))
        self.lpic.conf.update({'LinkFormat': '{% img $URL $BASEPART %}'})
        self.assertEqual('{% img https://foo.org/qwer.jpg test %}', self.lpic.generate_file_link(local, remote))

    def test_get_default_pic(self):
        tmp = 'tmp{}.jpg'
        for i in range(2):
            im = Image.new('RGB', (1, 1))
            im.save(tmp.format(i))
            # 等待保存完毕
            sleep(0.1)

        self.assertEqual('tmp1.jpg', self.lpic.get_default_pic())

        for i in range(2):
            os.remove(tmp.format(i))


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-
"""
Lpic Entry
"""
import argparse
import inspect
import logging
import sys

from lpic.__about__ import __version__ as version
from lpic.base import LPic
from lpic.utils import iter_hosts


def start():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''终端图床神器！支持阿里云、腾讯云和七牛云。
可用命令:
    help                显示帮助
    backend [<cloud>]       查看/切换云服务
    put [<filename>]    上传文件。默认上传当前目录最新修改的图片。
    del [<prefix>]      删除Bucket中最新的指定前缀的文件
    web                 打开Bucket内容管理网页
省略命令时，上传当前目录最新修改的图片。''', epilog='''GitHub: https://github.com/jlice/lpic。欢迎start、提交PR。''')
    parser.add_argument('cmd', nargs='?', help='命令。支持：help, backend, put, del, web')
    parser.add_argument('dest', nargs='?', help='')
    parser.add_argument('-n', action='store_false', dest='adjust', help='不进行预处理')
    parser.add_argument('-u', '--backend', dest='backend', help='使用指定的云服务')
    parser.add_argument('-y', '--yes', action='store_true', dest='yes', help='始终选择y')
    parser.add_argument('-a', '--all', action='store_true', dest='use_all', help='使用全部云服务')
    parser.add_argument(
        "-v", "--version", action="store_true", help="show this version and exit"
    )
    args = parser.parse_args()

    if args.version:
        print("lpic version: {}".format(version))
        sys.exit()

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    root.addHandler(sh)

    if args.cmd == 'help':
        parser.print_help()
    else:
        options = {
            k: v for k, v in args.__dict__.items() if k not in ('cmd', 'dest')
        }
        lp = LPic(**options)
        lp.load_config()
        if args.cmd == 'backend':
            lp.main(args.cmd, args.dest)
        else:
            for module in iter_hosts():
                if (args.use_all and module.USE in lp.hosts()) or (args.use or lp.use) == module.USE:
                    for cls in inspect.getmembers(module, inspect.isclass):
                        if cls[1] != LPic:
                            for attr in inspect.getmembers(cls[1]):
                                if attr[0] == 'main':
                                    options['backend'] = module.USE
                                    cls[1](**options).main(args.cmd, args.dest)
                                    break


if __name__ == '__main__':
    start()

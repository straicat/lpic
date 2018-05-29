# lpic

Linux下的七牛云图床神器，简单方便好用！

![](http://p9h7r5xkw.bkt.clouddn.com/20180529_221201.gif)

## 用法

```
用法: lpic [<command>] [<args>]

可用命令:
    help, -h, --help    显示帮助
    del                 删除Bucket中最新的文件
    web                 打开Bucket内容管理页面
    put                 上传文件

省略命令时，上传最新文件。
```

用Markdown写作时，插入图片比较麻烦。上传图片前要先压缩，然后上传，复制外链。如果用`lpic`就非常方便了，只需`lpic put <file>`即可，会自动压缩、上传、复制外链。

为了更方便，`lpic`默认上传最新文件。当你想要在Markdown里贴截图时，只需在保存截图之后到截图所在目录运行`lpic`，然后粘贴外链到你的文章里即可。

另外，`lpic del`能删除Bucket中当日最新的文件（根据文件名判断，而不是上传时间），方便撤销刚刚上传的图。`lpic web`能召唤默认浏览器打开Bucket内容管理页面，方便手动管理。

## 安装

``` Bash
$ curl -L https://github.com/jlice/cli-tools/raw/master/lpic/install | bash
```

会自动下载七牛云命令行工具`qrsctl`。复制外链到剪贴板功能需要安装`xsel`，Debian/Ubuntu下安装：

``` Bash
$ sudo apt-get install xsel
```


# lpic

Linux下的终端图床神器！

![](https://github.com/jlice/lpic/raw/master/assets/lpic.gif)

## 用法

```
用法: lpic [<command>] [<args>]

可用命令:
    help, -h, --help    显示帮助
    del                 删除Bucket中最新的文件
    web                 打开Bucket内容管理页面
    put <filename>      上传文件
    use [<option>]      切换云服务

省略命令时，上传最新文件。
```

用Markdown写作时，插入图片比较麻烦。上传图片前要先压缩，然后上传，复制外链。如果用`lpic`就非常方便了，只需`lpic put <file>`即可，会自动压缩、上传、复制外链。

为了更方便，`lpic`默认上传最新文件。当你想要在Markdown里贴截图时，只需在保存截图之后到截图所在目录运行`lpic`，然后粘贴外链到你的文章里即可。

另外，`lpic del`能删除Bucket中当日最新的文件（根据文件名判断，而不是上传时间），方便撤销刚刚上传的图。`lpic web`能召唤默认浏览器打开Bucket内容管理页面，方便手动管理。

支持腾讯云和七牛云。

## 安装

下载该项目：

``` Shell
$ git clone https://github.com/jlice/lpic.git
```

安装依赖：

``` Shell
$ pip3 install -r lpic/requirements.txt
```

将`lpic.yml.example`复制一份为`lpic.yml`，此为配置文件，修改之：

``` Shell
$ cd lpic/lpic
$ cp lpic.yml.example lpic.yml
$ vim lpic.yml
```

为了能在终端使用`lpic`命令直接调用，可以创建一个软链接：

``` Shell
$ chmod +x main.py
$ sudo ln -s $PWD/main.py /usr/local/bin/lpic
```

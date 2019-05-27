# lpic

Linux下的终端图床神器！

![](https://user-images.githubusercontent.com/9983385/58353491-34ab8080-7ea1-11e9-895d-00d402f44c01.gif)

## 用法

```
用法: lpic [<command>] [<args>]

可用命令:
    help, -h, --help    显示帮助
    del <prefix>        删除Bucket中的文件
    web                 打开Bucket内容管理页面
    put <filename>      上传文件
    backend [<cloud>]       切换云服务

省略命令时，上传最新图片。
```

用Markdown写作时，插入图片比较麻烦。上传图片前要先压缩，然后上传，复制外链。如果用`lpic`就非常方便了，只需`lpic put <filename>`即可，会自动压缩、上传、复制外链。

为了更方便，`lpic`默认上传最新文件。当你想要在Markdown里贴截图时，只需在保存截图之后到截图所在目录运行`lpic`，然后粘贴外链到你的文章里即可。

另外，`lpic del <prefix>`能删除Bucket中的文件。`lpic web`能召唤默认浏览器打开Bucket内容管理页面，方便手动管理。

支持阿里云、腾讯云和七牛云。

## 安装

下载该项目：

``` Shell
$ git clone https://github.com/jlice/lpic.git
```

安装依赖：

``` Shell
$ pip3 install -r lpic/requirements.txt
```

将`lpic.example.yml`复制一份为`lpic.yml`，此为配置文件，修改之：

``` Shell
$ cd lpic/src
$ cp lpic.example.yml lpic.yml
$ vim lpic.yml
```

为了能在终端使用`lpic`命令直接调用，可以创建一个软链接：

``` Shell
$ chmod +x main.py
$ sudo ln -s $PWD/main.py /usr/local/bin/lpic
```

更多细节[详见Wiki](https://github.com/jlice/lpic/wiki)。

## 变更日志

### 2019.05.25

  1. 增加支持阿里云
  2. 允许限制图片大小
  3. 支持多种重命名格式
  4. 允许自定义输出形式
  5. 支持透明区域填色

### 2018.11.09

  1. 增加Windows支持
  2. 修复了转换带Alpha通道PNG的BUG
  3. 优化配置文件结构（兼容之前的格式）

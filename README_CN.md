![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本，它同样兼容XMODEM模式。

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)


## YMODEM for Python功能演示

### 单独测试发送与接收功能 

如果想运行测试例子，请执行以下操作：
1. 利用串口虚拟工具在本地生成可相互通信的COM1与COM2
2. 在命令行中分别运行FileReceiver.py与FileSender.py文件

具体的传输过程如下图所示：
![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/cmd_test.gif)

### 与SecureCRT交互

作为发送者与SecureCRT交互
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_sender.gif)

作为接收者与SecureCRT交互
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_receiver.gif)

## 如何使用YMODEM for Python

1. 引入MODEM模块
```python
from Modem import Modem
```

2. 定义必要的reader与writer（或read与write函数），并以此创建Modem对象
```python
def sender_read(size, timeout=3):
    serial_io.timeout = timeout
    return serial_io.read(size) or None

def sender_write(data, timeout=3):
    serial_io.writeTimeout = timeout
    return serial_io.write(data)

sender = Modem(sender_read, sender_write)
```

3. 开始传输数据
```python
sender.send(stream, info=file_info)
```

4. 开始接收数据
```python
receiver.recv(stream, info=file_info)
```

## YMODEM for Python API

### 创建MODEM对象
```python
def __init__(self, reader, writer, mode='ymodem1k', program="rzsz")
```
- reader： 读对象或者读函数。
- writer： 写对象或者写函数。
- mode： 默认使用数据长度为1k字节的YMODEM模式。
- program： YMODEM的标准（不同标准有不同特性）。

### 发送数据
```python
def send(self, stream, retry=10, timeout=10, callback=None, info=None):
```
- stream： 文件（数据）流。
- retry： 最大重传次数。
- timeout： reader和writer的超时时间。
- callback： 回调函数，参数见下表。
- info： 文件信息字典。字段见下表。

回调参数：
参数（按顺序） | 描述
-|-
total packets | 预发送的包总数
success packets | 发送成功的包数量
failed packets | 发送失败的包数量

文件信息属性：
字段 | 描述
-|- 
name | 文件名称
length | 文件大小（字节）
mtime | 文件修改时间 (GMT)
source | 文件原始所属的系统

### 接收数据
```python
def recv(self, stream, crc_mode=1, retry=10, timeout=10, delay=1, callback=None, info=None)
```
- stream： 文件（数据）流。
- crc_mode： 由接收者指定的校验模式。
- retry： 最大重传次数。
- timeout： reader和writer的超时时间。
- delay： 延迟时间。
- callback： 回调函数，参数见下表。
- info： 文件信息字典，字段见下表。

回调参数：
参数（按顺序） | 描述
-|-
received length | 已接收的文件字节
remaining length | 剩余未接收的文件字节

文件信息属性：
字段 | 描述
-|- 
save_path | 保存接收文件的文件夹路径

## 更新日志
### v1.2 (2022/8/10 14:00 +00:00)
- 修复了接收函数的bug

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
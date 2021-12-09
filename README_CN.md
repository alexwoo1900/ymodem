![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本，它同样兼容XMODEM模式。

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)


## YMODEM for Python到底能不能用
如果想运行测试例子，请执行以下操作：
1. 利用串口虚拟工具在本地生成可相互通信的COM1与COM2
2. 在命令行中分别运行test\FileReceiver.py与test\FileSender.py文件

具体的传输过程如下图所示：
![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/sr.png)
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_sender.png)
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_receiver.png)

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
- reader 读对象或者读函数
- writer 写对象或者写函数
- mode 默认使用数据长度为1k字节的YMODEM模式
- program YMODEM的标准（不同标准有不同特性）

### 发送数据
```python
def send(self, stream, retry=10, timeout=10, quiet=False, callback=None, info=None):
```
- stream 文件（数据）流
- retry 最大重传次数
- timeout reader和writer的超时时间
- callback 回调函数，接收三个有关发送进度的参数total_packets、success_count、error_count
- info 文件信息字典，提供给接收者使用，成员包括name、length、mtime、source

### 接收数据
```python
def recv(self, stream, crc_mode=1, retry=10, timeout=10, delay=1, quiet=0, callback=None, info=None)
```
- stream 文件（数据）流
- crc_mode 由接收者指定的校验模式
- retry 最大重传次数
- timeout reader和writer的超时时间
- delay 延迟时间
- callback 回调函数，接收两个有关发送进度的参数received_length, remaining_length

## 更新日志
### v1.0.1 (2021/12/9 14:00 +00:00)
- 增加了YMODEM的完整版实现
- 简化版的代码已移至Legacy文件夹下

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
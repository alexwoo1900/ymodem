![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/YModem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XModem项目的YModem版本。除了遵从YModem协议外，还加入了超时处理机制。

[![Build Status](https://www.travis-ci.org/alexwoo1900/YModem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/YModem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/YModem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/README_CN.md)

YModem Protocol: [ENGLISH](https://github.com/alexwoo1900/YModem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/YMODEM_CN.md)

## 如何使用YModem for Python
1. 将ymodem.py放入protocol文件夹，将YModem类引入你的工程
```python
from protocol.ymodem import YModem
```

2. 定义必要的getc()与putc(),并创建YModem对象
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

modem = YModem(getc, putc)
```

3. 开始传输数据
```python
modem.send(file_stream, file_size, file_name, displayMessage)
```
## YModem for Python API

### 创建modem对象
```python
def __init__(self, getc, putc, header_pad=b'\x00', pad=b'\x1a')
```
getc：自定义函数，YModem对象内部通过它获取size个数据（size为get的唯一参数，但是在协议内部固定为1） \
putc: 自定义函数，YModem对象内部通过它发送size个数据

### 发送数据
```python
def send(self, file_stream, file_size, file_name, func)
```
- file_stream: 文件数据流
- file_size：文件大小
- file_name: 文件名
- func：自定义函数，只有一个参数，为消息，用于处理内部提示消息


## 更新日志
### v0.5.0 (2018/3/30 15:00 +00:00)
- 项目初版上线

### v0.7.0 (2018/4/3 11:15 +00:00)
- 重写超时机制
- 去除冗余信息
- 编写测试用例

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
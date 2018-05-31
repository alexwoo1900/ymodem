![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本。

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)

YMODEM Protocol: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM_CN.md)

## 如何使用YMODEM for Python
1. 将ymodem.py放入protocol文件夹，将YMODEM类引入你的工程
```python
from protocol.ymodem import YMODEM
```

2. 定义必要的getc()与putc(),并创建YModem对象
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

tester = YMODEM(getc, putc)
```

3. 开始传输数据
```python
tester.send(file_stream, file_name)
```

4. 开始接收数据
```python
tester.recv(file_stream)
```

## YMODEM for Python API

### 创建modem对象
```python
def __init__(self, getc, putc, mode='ymodem', header_pad=b'\x00', pad=b'\x1a')
```
getc：自定义函数，YModem对象内部通过它获取size个数据（size为get的唯一参数，但是在协议内部固定为1） \
putc: 自定义函数，YModem对象内部通过它发送size个数据
mode: 传输模式，分ymodem、ymodem128，前者数据包的数据长度为1024，后者为128

### 发送数据
```python
def send(self, file_stream, file_name, retry=20, timeout=15, callback=None)
```
- file_stream: 文件数据流
- file_name: 文件名
- retry: 收发数据最大重试次数
- timeout: 收发数据最大超时
- callback: 传输过程中的回调，接收三个参数--数据包的总数，数据包发送成功数，数据包发送失败数

### 接收数据
```python
def recv(self, file_stream, retry=20, timeout=15, delay=0.01)
```
- file_stream: 文件数据流
- retry: 收发数据最大重试次数
- timeout: 收发数据最大超时
- delay: 重发字符C的延迟

## 更新日志
### v0.5.0 (2018/3/30 15:00 +00:00)
- 项目初版上线

### v0.7.0 (2018/4/3 11:15 +00:00)
- 重写超时机制
- 去除冗余信息
- 编写测试用例

### v0.8.0 (2018/4/4 15:06 +00:00)
- 去除超时机制，采用旧有的重试机制
- 增加接受数据的部分
- 改写测试用例

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
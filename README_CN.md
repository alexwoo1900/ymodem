![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本。

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)

YMODEM Protocol: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM_CN.md)

## YMODEM for Python到底能不能用
如果想运行测试例子，请执行以下操作：
1. 利用串口虚拟工具在本地生成可相互通信的COM1与COM2
2. 在命令行中分别运行test_receiver.py与test_sender.py文件

具体的传输过程如下图所示（左边为发送者，右边为接收者）：
![cmd_test](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/cmd_test.png)
![hash_result](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/hash_result.png)

## 如何使用YMODEM for Python
1. 在目标模块中引入YModem
```python
from YModem import YModem
```

2. 定义必要的getc()与putc(),并创建YModem对象
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

tester = YModem(getc, putc)
```

3. 开始传输数据
```python
tester.send_file(file_path)
```

4. 开始接收数据
```python
tester.recv_file(root_path)
```

## YMODEM for Python API

### 创建modem对象
```python
def __init__(self, getc, putc, header_pad=b'\x00', data_pad=b'\x1a')
```
- getc：自定义函数，YModem对象内部通过它获取size个byte的数据
- putc: 自定义函数，YModem对象内部通过它发送size个byte的数据

### 发送数据
```python
def send_file(self, file_path, retry=20, callback=None)
```
- file_path: 待发送文件路径
- retry: 最大重新发送次数
- callback: 回调函数，由开发者自行实现，一般用来获取进度等信息

### 接收数据
```python
def recv_file(self, root_path, callback=None)
```
- root_path: 存储文件夹路径
- callback: 回调函数，由开发者自行实现，一般用来获取进度信息

## 更新日志
### v1.0.0 (2020/5/14 14:00 +00:00)
- 简化了原版的YModem实现

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
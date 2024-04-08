![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本，它同样兼容XMODEM模式。

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)

- [**安装**](#安装)
- [**使用方法**](#使用方法)
  - [命令行](#命令行) 
    - [发送文件](#发送文件)
    - [接收文件](#接收文件)
  - [源代码](#源代码)
  - [API](#api)
    - [创建MODEM对象](#创建MODEM对象)
    - [发送数据](#发送数据)
    - [接收数据](#接收数据)
- [调试](#调试)
- [更新日志](#更新日志)
- [许可证](#许可证)

## 功能演示

### 单独测试发送与接收功能 

![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/console_test.gif)

### 与SecureCRT交互

作为发送者与SecureCRT交互
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/sender.gif)

作为接收者与SecureCRT交互
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/receiver.gif)

## 安装
```Bash
pip install ymodem
```

## 使用方法

### 命令行

```Bash
# To get help
ymodem -h
# or
python -m ymodem -h
```

#### 发送文件
```Bash
ymodem send ./file.bin ./file2.bin -p COM4 -b 115200
# or
python -m ymodem send ./file.bin ./file2.bin -p COM4 -b 115200
```

#### 接收文件
```Bash
ymodem recv ./ -p COM4 -b 115200
# or
python -m ymodem recv ./ -p COM4 -b 115200
```

### 源代码

```python
from ymodem.Socket import ModemSocket

# define read
def read(size, timeout=3):
    # implementation

# define write
def write(data, timeout=3):
    # implementation

# create socket
cli = ModemSocket(read, write)

# send multi files
cli.send([file_path1, file_path2, file_path3 ...])

# receive multi files
cli.recv(folder_path)
```

更详细的使用方式见__main__.py。

### API

#### 创建MODEM对象

```python
def __init__(self, 
             read: Callable[[int, Optional[float]], Any], 
             write: Callable[[Union[bytes, bytearray], Optional[float]], Any], 
             protocol_type: int = ProtocolType.YMODEM, 
             protocol_type_options: List[str] = [],
             packet_size: int = 1024,
             style_id: int = _psm.get_available_styles()[0]):
```
- protocol_type: 协议类型，参见Protocol.py
- protocol_type_options: 协议选项，如g表示YMODEM协议中的YMODEM-G功能。
- packet_size: 单个包大小，128/1024字节，根据protocol style的不同可能会进行调整
- style_id: 协议风格，不同的风格对功能特性有不同的支持

#### 发送数据

```python
def send(self, 
         paths: List[str], 
         callback: Optional[Callable[[int, str, int, int], None]] = None
        ) -> bool:
```
- callback： 回调函数，见下表。

    参数（按顺序） | 描述
    -|-
    task index | 任务索引
    task (file) name | 任务（文件）名称
    total packets | 总包数
    success packets | 成功包数


#### 接收数据

```python
def recv(self, 
         path: str, 
         callback: Optional[Callable[[int, str, int, int], None]] = None
        ) -> bool:
```
- path: 用于保存目标文件的文件夹路径
- callback： 回调函数，格式同send的callback。

#### 注意事项

根据通讯环境不同，开发者可能需要手动调整_read_and_wait或_write_and_wait的超时参数。

## 调试

如果想要输出调试信息，请把日志等级设成DEBUG。

```python
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
```

## 更新日志

### v1.5 (2024/02/03)

- 增加命令行使用方式

### v1.5 (2023/05/20 11:00 +00:00)

- 重写了send方法和recv方法
- 支持YMODEM-G模式。
    基于pyserial的YMODEM-G的成功率取决于用户的操作系统，经过测试，在不加延时的情况下成功率非常低。

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
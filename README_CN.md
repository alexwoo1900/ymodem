![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

本项目是基于tehmaze的XMODEM项目的YMODEM版本，它同样兼容XMODEM模式。

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

README: [ENGLIST](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)


## 功能演示

### 单独测试发送与接收功能 

如果想运行测试例子，请执行以下操作：
1. 利用串口虚拟工具在本地生成可相互通信的COM1与COM2
2. 在命令行中分别运行FileReceiver.py与FileSender.py文件

具体的传输过程如下图所示：
![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/console_test.gif)

### 与SecureCRT交互

作为发送者与SecureCRT交互
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/sender.gif)

作为接收者与SecureCRT交互
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/receiver.gif)

## 快速上手

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

更详细的使用方式见FileReceiver.py与FileSender.py文件。

## API

### 创建MODEM对象

```python
def __init__(self, 
             read: Callable[[int, Optional[float]], Any], 
             write: Callable[[Union[bytes, bytearray], Optional[float]], Any], 
             protocol_type: int = ProtocolType.YMODEM, 
             packet_size: int = 1024,
             style_id: int = _psm.get_available_styles()[0]):
```
- protocol_type: 协议类型，参见Protocol.py
- packet_size: 单个包大小，128/1024字节，根据protocol style的不同可能会进行调整
- style_id: 协议风格，不同的风格对功能特性有不同的支持

### 发送数据

```python
def send(self, 
         paths: List[str], 
         retry: int = 10, 
         timeout: float = 10, 
         callback: Optional[Callable[[int, str, int, int, int], None]] = None
        ) -> bool:
```
- callback： 回调函数，见下表。

    参数（按顺序） | 描述
    -|-
    task index | 任务索引
    task (file) name | 任务（文件）名称
    total packets | 总包数
    success packets | 成功包数
    failed packets | 失败包数


### 接收数据

```python
def recv(self, 
         path: str, 
         crc_mode: int = 1, 
         retry: int = 10, 
         timeout: float = 10, 
         delay: float = 1, 
         callback: Optional[Callable[[int, str, int, int, int], None]] = None
        ) -> bool:
```
- callback： 回调函数，格式同send的callback。

## 调试

如果想要输出调试信息，请把日志等级设成DEBUG。

```python
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
```

## 更新日志
### v1.4 (2023/05/13 14:00 +00:00)

- 重写了部分参数处理的逻辑

## 许可证
[MIT许可证](https://opensource.org/licenses/MIT)
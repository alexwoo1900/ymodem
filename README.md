![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

The YMODEM project is based on XMODEM implementation written by tehmaze. It is also compatible with XMODEM mode.

[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)


README: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)


## Demo

### Test the sending and receiving functions

If you want to run the test sample, please do the following:
1. use virtual serial port tool to generate COM1 and COM2 that can communicate
2. run the FileReceiver.py and FileSender.py on the command line

The specific transmission process is shown in the following figure:
![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/console_test.gif)

### Interact with SecureCRT

Interact with SecureCRT as sender
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/sender.gif)

Interact with SecureCRT as Finder
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/receiver.gif)

## Quick start

```python
from ymodem.Socket import ModemSocket

# define read
def read(size, timeout = 3):
    # implementation

# define write
def write(data, timeout = 3):
    # implementation

# create socket
cli = ModemSocket(read, write)

# send multi files
cli.send([file_path1, file_path2, file_path3 ...])

# receive multi files
cli.recv(folder_path)
```

For more detailed usage, please refer to the FileReceiver. py and FileSender. py files.

## API

### Create MODEM Object

```python
def __init__(self, 
             read: Callable[[int, Optional[float]], Any], 
             write: Callable[[Union[bytes, bytearray], Optional[float]], Any], 
             protocol_type: int = ProtocolType.YMODEM, 
             packet_size: int = 1024,
             style_id: int = _psm.get_available_styles()[0]):
```
- protocol_type: Protocol type, see Protocol.py
- packet_size: The size of a single packet, 128/1024 bytes, may be adjusted depending on the protocol style
- style_id: Protocol style, different styles have different support for functional features

### Send files

```python
def send(self, 
         paths: List[str], 
         retry: int = 10, 
         timeout: float = 10, 
         callback: Optional[Callable[[int, str, int, int, int], None]] = None
        ) -> bool:
```

- callback: callback function. see below.

    Parameter | Description
    -|-
    task index | index of current task
    task (file) name | name of the file
    total packets | number of packets plan to send
    success packets | number of packets successfully sent
    failed packets | number of packets failed to send

### Receive files

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

- callback: callback function. Same as the callback of send().

## Debug

If you want to output debugging information, set the log level to DEBUG.

```python
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
```

## Changelog
### v1.4 (2023/05/13 14:00 +00:00)

- Rewritten the logic for handling some parameters

## License 
[MIT License](https://opensource.org/licenses/MIT)
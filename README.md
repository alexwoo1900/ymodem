![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

The YMODEM project is based on XMODEM implementation written by tehmaze. It is also compatible with XMODEM mode.

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
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
from Modem import Modem

'''
Sender
'''
# define read function for sender
def sender_read(size, timeout=3):
    pass

# define write function for sender
def sender_write(data, timeout=3):
    pass

# create sender
sender = Modem(sender_read, sender_write)

# send multi files
sender.send([file_path1, file_path2, file_path3 ...])

'''
Receiver
'''

# define read function for receiver
def receiver_read(size, timeout=3):
    pass

# define write function for receiver
def receiver_write(data, timeout=3):
    pass

# create receiver
receiver = Modem(receiver_read, receiver_write)

# receive multi files
receiver.recv(folder_path)
```

## API

### Create MODEM Object

```python
def __init__(self, reader, writer, mode='ymodem1k', program="rzsz")
```
- reader, reader(object) or read(function)
- writer, writer(object) or write(function)
- mode, support xmodem, xmodem1k, ymodem, ymodem1k(by default)
- program, YMODEM of different program have different features

### Send files

```python
def send(self, file_paths, retry=10, timeout=10, callback=None)
```
- file_paths: file path list.
- retry: max retry count.
- timeout: timeout of reader or writer in second.
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
def recv(self, folder_path, crc_mode=1, retry=10, timeout=10, delay=1, callback=None)
```

- folder_path: folder path for saving.
- crc_mode: checksum or crc mode.
- retry: max retry count.
- timeout: timeout of reader or writer in second.
- delay: delay in second.
- callback: callback function. see below.

    Parameter | Description
    -|-
    task index | index of current task
    task (file) name | name of the file
    total packets | number of packets plan to send
    success packets | number of packets successfully sent
    failed packets | number of packets failed to send

## Debug

If you want to output debugging information, set the log level to DEBUG.

```python
logging.basicConfig(level=logging.DEBUG, format='%(message)s')
```

## Changelog
### v1.3 (2022/11/21 14:00 +00:00)

- Support batch transmission
- Simplify the API

## License 
[MIT License](https://opensource.org/licenses/MIT)
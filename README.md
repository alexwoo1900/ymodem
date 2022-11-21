![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

The YMODEM project is based on XMODEM implementation written by tehmaze. It is also compatible with XMODEM mode.

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)


README: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)


## YMODEM for Python Demo

### Test the sending and receiving functions

If you want to run the test sample, please do the following:
1. use virtual serial port tool to generate COM1 and COM2 that can communicate
2. run the FileReceiver.py and FileSender.py on the command line

The specific transmission process is shown in the following figure:
![SenderAndReceiver](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/cmd_test.gif)

### Interact with SecureCRT

Interact with SecureCRT as sender
![SecureCRT1](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_sender.gif)

Interact with SecureCRT as Finder
![SecureCRT2](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem_receiver.gif)

## How to use YMODEM for Python

1. Import MODEM module

```python
from Modem import Modem
```

2. Define the reader and writer (or read() and write()), then create MODEM object

```python
def sender_read(size, timeout=3):
    serial_io.timeout = timeout
    return serial_io.read(size) or None

def sender_write(data, timeout=3):
    serial_io.writeTimeout = timeout
    return serial_io.write(data)

ymodem = Modem(sender_read, sender_write)
```

3. Send file

```python
sender.send([file_path1, file_path2, file_path3 ...])
```

4. Receive file

```python
receiver.recv(folder_path)
```

## YMODEM for Python API

### Create MODEM Object
```python
def __init__(self, reader, writer, mode='ymodem1k', program="rzsz")
```
- reader, reader(object) or read(function)
- writer, writer(object) or write(function)
- mode, support xmodem, xmodem1k, ymodem, ymodem1k(by default)
- program, YMODEM of different program have different features

### Send file

```python
def send(self, file_paths, retry=10, timeout=10, callback=None)
```
- file_paths: file path list.
- retry: max retry count.
- timeout: timeout of reader or writer in second.
- callback: callback function. see below.

callback parameters:
Parameter | Description
-|-
task index | index of current task
task (file) name | name of the file
total packets | number of packets plan to send
success packets | number of packets successfully sent
failed packets | number of packets failed to send

### Receive file

```python
def recv(self, folder_path, crc_mode=1, retry=10, timeout=10, delay=1, callback=None)
```
- folder_path: folder path for saving.
- crc_mode: checksum or crc mode.
- retry: max retry count.
- timeout: timeout of reader or writer in second.
- delay: delay in second.
- callback: callback function. see below.

callback parameters:
Parameter | Description
-|-
task index | index of current task
task (file) name | name of the file
total packets | number of packets plan to send
success packets | number of packets successfully sent
failed packets | number of packets failed to send

## Changelog
### v1.3 (2022/11/21 14:00 +00:00)
- Support batch transmission
- Simplify the API

## License 
[MIT License](https://opensource.org/licenses/MIT)
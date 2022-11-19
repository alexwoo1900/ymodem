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
ymodem.send(stream, info=file_info)
```

4. Receive single file

```python
received = ymodem.recv(stream=None, info=file_info)
```

5. Receive multiple files in batch mode by calling `recv()` until it returns `None`

```python
received = 0
while received != None:
    received = ymodem.recv(stream=None, info=file_info)
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

### Send file (stream)

```python
def send(self, stream, retry=10, timeout=10, callback=None, info=None)
```
- stream, data stream.
- retry, max retry count.
- timeout, timeout of reader or writer in second.
- callback, callback function. see below.
- info, file information dictionary. see below.

callback parameters:
Parameter | Description
-|-
total packets | number of packets plan to send
success packets | number of packets successfully sent
failed packets | number of packets failed to send

info properties:
Field | Description
-|- 
name | file name
length | file length
mtime | file modification date (GMT)
source | operation system the file original from

### Receive file (stream)

```python
def recv(self, stream, crc_mode=1, retry=10, timeout=10, delay=1, callback=None, info=None)
```
- stream, data stream.
- crc_mode, checksum or crc mode.
- retry, max retry count.
- timeout, timeout of reader or writer in second.
- delay, delay in second.
- callback, callback function. see below.
- info, file information dictionary. see below.

callback parameters:
Parameter | Description
-|-
received length | received file bytes
remaining length | remaining file bytes

info properties:
Field | Description
-|- 
save_path | folder path where the file are saved

return value:

- Size of received file in bytes if successful
- `None` otherwise

## Changelog
### v1.2 (2022/8/10 14:00 +00:00)
- Fixed receiver bug

## License 
[MIT License](https://opensource.org/licenses/MIT)
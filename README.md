![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

The project is based on XMODEM implementation written by tehmaze. 

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)


README: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)

YModem Protocol: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM_CN.md)

## How to use YMODEM for Python
1. Put ymodem.py to the folder named 'protocol' and then import main class to your project
```python
from protocol.ymodem import YMODEM
```

2. Define your own get() and put() and create YMODEM object
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

tester = YMODEM(getc, putc)
```

3. Send file!
```python
tester.send(file_stream, file_name)
```

4. Recv file!
```python
tester.recv(file_stream)
```

## YMODEM for Python API

### Create YMODEM object
```python
def __init__(self, getc, putc, mode='ymodem', header_pad=b'\x00', pad=b'\x1a')
```
get(): Custom function. Getting data bytes from this function in YModem implementation according to the parameter(size)
put(): Custom function. Sending data bytes to this function in YModem implementation according to the parameter(size)
mode: optional parameter, 'ymodem' to choose 1024 bytes packet for transmission and 'ymodem128' to choose 128 bytes

### Send data
```python
def send(self, file_stream, file_name, retry=20, timeout=15, callback=None)
```
- file_stream: file data stream
- file_name: name of the file
- retry: max time of retry for getc or putc
- timeout: max second for getc or putc waiting
- callback: callback in packet transfer, accepting 3 parameters: total_count, success_count and error_count

### Recv data
```python
def recv(self, file_stream, retry=20, timeout=15, delay=0.01)
```
- file_stream: file data stream
- retry: max time of retry for getc or putc
- timeout: max second for getc or putc waiting
- delay: max second waiting for sending next char 'C'

## Change logs
### v0.5.0 (2018/3/30 15:00 +00:00)
- First edition goes live 

### v0.7.0 (2018/4/3 11:15 +00:00)
- rewrite timeout mechanism
- remove unnecessary information
- add testing for ymodem

### v0.8.0 (2018/4/4 15:06 +00:00)
- remove timeout mechanism and back to retry function
- add recv entry
- modify testing file

## License 
[MIT License](https://opensource.org/licenses/MIT)
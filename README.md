![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/YModem/master/docs/assets/ymodem-logo.png)

The project is based on XModem implementation written by tehmaze. 
YModem for Python complied YModem protocol and timeout mechanism was added to the implementation. 

[![Build Status](https://www.travis-ci.org/alexwoo1900/YModem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/YModem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)


README: [ENGLISH](https://github.com/alexwoo1900/YModem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/README_CN.md)

YModem Protocol: [ENGLISH](https://github.com/alexwoo1900/YModem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/YMODEM_CN.md)

## How to use YModem for Python
1. Put ymodem.py to the folder named 'protocol' and then import main class to your project
```python
from protocol.ymodem import YModem
```

2. Define your own get() and put() and create YModem object
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

modem = YModem(getc, putc)
```

3. Send file now!
```python
modem.send(file_stream, file_size, file_name, displayMessage)
```
## YModem for Python API

### Create YModem object
```python
def __init__(self, getc, putc, header_pad=b'\x00', pad=b'\x1a')
```
get(): Custom function. Getting data bytes from this function in YModem implementation according to the parameter(size)
put(): Custom function. Sending data bytes to this function in YModem implementation according to the parameter(size)

### Send data
```python
def send(self, file_stream, file_size, file_name, func)
```
- file_stream: file data stream
- file_size：size of the file
- file_name: name of the file
- func：handler for debug message

## Change logs
### v0.5.0 (2018/3/30 15:00 +00:00)
- First edition goes live 

### v0.7.0 (2018/4/3 11:15 +00:00)
- rewrite timeout mechanism
- remove unnecessary information
- add testing for ymodem

## License 
[MIT License](https://opensource.org/licenses/MIT)
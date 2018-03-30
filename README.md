![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/YModem/master/docs/assets/ymodem-logo.png)

The project is based on XModem implementation written by tehmaze. 
YModem for Python complied YModem protocol and timeout mechanism was added to the implementation. 

[![Build Status](https://www.travis-ci.org/alexwoo1900/YModem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/YModem)

README: [ENGLISH](https://github.com/alexwoo1900/YModem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/README_CN.md)

YModem Protocol: [ENGLISH]() | [简体中文](https://github.com/alexwoo1900/YModem/blob/master/YMODEM_CN.md)

## How to use YModem for Python
1. Put ymodem.py to the folder named 'protocol' and then import main class to your project
```python
from protocol.ymodem import YModem
```

2. Define your own get() and put() and create YModem object
```python
def getc(size):
    return parent.ser._serial.read(size) or None

def putc(data):
    return parent.ser._serial.write(data)

modem = YModem(getc, putc)
```

3. Send file now!
```python
modem.send(stream, length, self.data_received_handler, 8, self.record_progress)
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
def send(self, stream, length, func, retry=8, callback=None)
```
- stream: data stream
- length：data length
- func：handler for debug message
- retry: times of resend
- callback: callback after packet received by the other side

## Change logs
### v0.5.0 (2018/3/30 15:00 +00:00)
- First edition goes live 

## License 
[MIT License](https://opensource.org/licenses/MIT)
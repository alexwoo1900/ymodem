![ymodem-logo](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/ymodem-logo.png)

The project is based on XMODEM implementation written by tehmaze. 

[![Build Status](https://www.travis-ci.org/alexwoo1900/ymodem.svg?branch=master)](https://www.travis-ci.org/alexwoo1900/ymodem)
[![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)


README: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/README.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/README_CN.md)

YMODEM Protocol: [ENGLISH](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM.md) | [简体中文](https://github.com/alexwoo1900/ymodem/blob/master/YMODEM_CN.md)

## Can YMODEM for Python work
If you want to run the test sample, please do the following:
1. use virtual serial port tool to generate COM1 and COM2 that can communicate
2. run the test_receiver.py and test_sender.py on the command line
The specific transmission process is shown in the following figure (sender on the left and receiver on the right)
![cmd_test](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/cmd_test.png)
![hash_result](https://raw.githubusercontent.com/alexwoo1900/ymodem/master/docs/assets/hash_result.png)

## How to use YMODEM for Python
1. Import YModem in your target file
```python
from YModem import YModem
```

2. Define your own get() and put() and create YMODEM object
```python
def getc(size):
    return serial_io.read(size) or None

def putc(data):
    return serial_io.write(data)

tester = YModem(getc, putc)
```

3. Send file
```python
tester.send_file(file_path)
```

4. Receive file
```python
tester.recv_file(root_path)
```

## YMODEM for Python API

### Create YMODEM object
```python
def __init__(self, getc, putc, header_pad=b'\x00', data_pad=b'\x1a')
```
get(): Custom function. Get size bytes of data from data source(size)
put(): Custom function. Send size bytes to destination


### Send data
```python
def send_file(self, file_path, retry=20, callback=None)
```
- file_path: target file path
- retry: max resend tries
- callback: implemented by the developer

### Recv data
```python
def recv_file(self, root_path, callback=None)
```
- root_path: root path for storing the file
- callback: implemented by the developer

## Change logs
### v1.0.0 (2020/5/14 14:00 +00:00)
- Simplified the implementation of the original version of ymodem

## License 
[MIT License](https://opensource.org/licenses/MIT)
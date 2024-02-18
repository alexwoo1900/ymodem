import logging
import os
import serial
import sys

from ymodem.Protocol import ProtocolType
from ymodem.Socket import ModemSocket
from ymodem.__main__ import TaskProgressBar

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    serial_io = serial.Serial()
    serial_io.port = "COM2"
    serial_io.baudrate = "115200"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        serial_io.open()
    except Exception as e:
        raise Exception("Failed to open serial port!")

    def read(size, timeout = 3):
        serial_io.timeout = timeout
        return serial_io.read(size)

    def write(data, timeout = 3):
        serial_io.write_timeout = timeout
        serial_io.write(data)
        serial_io.flush()
        return
    
    receiver = ModemSocket(read, write, ProtocolType.YMODEM)
    # receiver = ModemSocket(read, write, ProtocolType.YMODEM, ['g'])

    os.chdir(sys.path[0])
    folder_path = os.path.abspath("remote")
    progress_bar = TaskProgressBar()
    received = receiver.recv(folder_path, progress_bar.show)

    serial_io.close()

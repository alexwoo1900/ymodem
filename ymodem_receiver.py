import os
import sys
import time
import random
import serial
from YModem import YModem

if __name__ == '__main__':
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
    
    def receiver_getc(size):
        return serial_io.read(size) or None

    def receiver_putc(data, timeout=15):
        return serial_io.write(data)

    receiver = YModem(receiver_getc, receiver_putc)
    os.chdir(sys.path[0])
    root_path = os.path.abspath('test_receive_data')
    received = receiver.recv_file(root_path)
    serial_io.close()

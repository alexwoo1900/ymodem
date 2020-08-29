import os
import sys
import time
import random
import serial
from YModem import YModem

if __name__ == '__main__':
    serial_io = serial.Serial()
    serial_io.port = "/dev/ttyUSB0"
    serial_io.baudrate = "115200"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        serial_io.open()
    except Exception as e:
        raise Exception("Failed to open serial port!")
    
    def sender_getc(size):
        return serial_io.read(size) or None

    def sender_putc(data, timeout=15):
        return serial_io.write(data)

    sender = YModem(sender_getc, sender_putc)
    os.chdir(sys.path[0])
    file_path = os.path.abspath('/home/robo/trapv2/DN_TRAP_HWv2_CubeIDE/Binary/TrapV2.0.sfb')
    sent = sender.send_file(file_path)
    serial_io.close()

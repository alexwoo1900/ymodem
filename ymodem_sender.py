import os
import sys
import time
import random
import serial
from YModem import YModem

def main(argv):
    serial_io = serial.Serial()
    try:
        filename = argv[0]
        serial_io.port = argv[1]
        serial_io.baudrate = argv[2]
    except Exception as e:
        print ('python ymodem_sender.py <filename> <device> <baudrate>')
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

    os.chdir(sys.path[0])
    file_path = os.path.abspath(filename)
    sender = YModem(sender_getc, sender_putc)
    sent = sender.send_file(file_path)
    serial_io.close()


if __name__ == '__main__':
    main(sys.argv[1:])

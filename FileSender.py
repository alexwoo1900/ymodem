import os
import sys
import serial
from ymodem.Modem import Modem

if __name__ == '__main__':
    serial_io = serial.Serial()
    serial_io.port = "COM1"
    serial_io.baudrate = "115200"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        serial_io.open()
    except Exception as e:
        raise Exception("Failed to open serial port!")
    
    def sender_read(size, timeout=3):
        serial_io.timeout = timeout
        return serial_io.read(size) or None

    def sender_write(data, timeout=3):
        serial_io.writeTimeout = timeout
        return serial_io.write(data)

    sender = Modem(sender_read, sender_write)

    os.chdir(sys.path[0])

    file_path1 = os.path.abspath('local/sample.stl')
    file_path2 = os.path.abspath('local/sample2.stl')
    file_path3 = os.path.abspath('local/sample3.stl')

    try:
        sender.send([file_path1, file_path2, file_path3])
    except IOError as e:
        pass

    serial_io.close()

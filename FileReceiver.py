import os
import sys
import serial
from ymodem.Modem import Modem

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

    def receiver_read(size, timeout=3):
        serial_io.timeout = timeout
        return serial_io.read(size) or None

    def receiver_write(data, timeout=3):
        serial_io.writeTimeout = timeout
        return serial_io.write(data)

    receiver = Modem(receiver_read, receiver_write)
    os.chdir(sys.path[0])

    file_info = {
        "save_path"    :   os.path.abspath("remote")
    }
    received = receiver.recv(stream=None, info=file_info)

    serial_io.close()

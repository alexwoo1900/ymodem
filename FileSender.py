import os
import sys
import serial
import logging
from ymodem.Modem import Modem

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

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
    file_path = os.path.abspath('local/sample.stl')
    try:
        file_stream = open(file_path, 'rb')
        file_info = {
            "name"      :   os.path.basename(file_path),
            "length"    :   os.path.getsize(file_path),
            "mtime"     :   os.path.getmtime(file_path),
            "source"    :   "win"
        }
        sender.send(file_stream, info=file_info)
    except IOError as e:
        pass
    finally:
        file_stream.close()

    serial_io.close()

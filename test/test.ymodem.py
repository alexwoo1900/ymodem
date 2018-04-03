import os
import sys
import time
import serial
from ymodem import YModem

if __name__ == '__main__':
    '''
    Serial port testing

    serial_io = serial.Serial()
    serial_io.port = "COM3"
    serial_io.baudrate = "115200"
    serial_io.parity = "N"
    serial_io.bytesize = 8
    serial_io.stopbits = 1
    serial_io.timeout = 2

    try:
        serial_io.open()
    except Exception as e:
        raise Exception("Failed to open serial port!")
    '''
    def getc(size):
        # return serial_io.read(size) or None
        time.sleep(0.03)
        return 'C'

    def putc(data):
        # return serial_io.write(data)
        print("Finish")
    modem = YModem(getc, putc)

    os.chdir(sys.path[0])

    file_path = os.path.abspath('sample.stl')
    print(file_path)
    try:
        file_stream = open(file_path, 'rb')
    except IOError as e:
        raise Exception("Failed to open file!")
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    def displayMessage(msg):
        print(msg)

    try:
        modem.send(file_stream, file_size, file_name, displayMessage)
    except Exception as e:
        file_stream.close()
        raise
    file_stream.close()

    # serial_io.close()
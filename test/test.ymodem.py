import os
import sys
import time
import random
import serial
from ymodem import YMODEM

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
    def sender_getc(size, timeout=15):
        # return serial_io.read(size) or None
        time.sleep(0.02)
        if random.random() > 0.5:
            return b'\x06'
        else:
            return 'C'

    def sender_putc(data, timeout=15):
        # return serial_io.write(data)
        if isinstance(data, str):
            data_in_hexstring = hex(ord(data))
        else:
            # data_in_hexstring = "".join("%02x" % b for b in data)
            data_in_hexstring = "Finish"
        print(data_in_hexstring)
    
    sender_tester = YMODEM(sender_getc, sender_putc)

    os.chdir(sys.path[0])

    file_path = os.path.abspath('sample.stl')
    try:
        file_stream = open(file_path, 'rb')
    except IOError as e:
        raise Exception("Failed to open file!")
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    try:
        sender_tester.send(file_stream, file_name)
    except Exception as e:
        file_stream.close()
        raise
    file_stream.close()

    # serial_io.close()

    def receiver_getc(size, timeout=15):
        pass
    def receiver_putc(data, timeout=15):
        pass
    receiver_tester = YMODEM(receiver_getc, receiver_putc)

    os.chdir(sys.path[0])

    file_path = os.path.abspath('sample_recv.stl')

    try:
        file_stream = open(file_path, 'wb')
    except IOError as e:
        raise Exception("Failed to open file!")

    try:
        receiver_tester.recv(file_stream)
    except Exception as e:
        file_stream.close()
        raise
    file_stream.close()
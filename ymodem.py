#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import math
import platform
import threading
import logging

# protocol header byte
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
NAK = b'\x15'
CAN = b'\x18'
CRC = b'C'

class YModem(object):
    crctable = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
    ]
    ymodem_first_packet_size = 128
    ymodem_packet_size = 1024

    # initialize
    def __init__(self, getc, putc, header_pad=b'\x00', pad=b'\x1a'):
        self.getc = getc
        self.putc = putc
        self.header_pad = header_pad
        self.pad = pad
        self.log = logging.getLogger('ymodem')

    # send abort(CAN)
    def abort(self, count=2):
        for _ in range(count):
            self.putc(CAN)

    def send(self, stream, length, func, retry=8, callback=None):
        packet_size = self.ymodem_packet_size

        def check_receive_timeout():
            global timer
            global timeout_count
            timeout_count += 1
            timer = threading.Timer(1, check_receive_timeout)
            timer.start()
        timeout_count = 0
        timer = threading.Timer(1, check_receive_timeout)

        error_count = 0
        cancel = 0
        while True:
            if timeout_count > 2:
                timer.cancel()
                raise Exception("Receiving 1st character timeout!")
            # try to get first char, send file when the char is CRC 
            char = self.getc(1)
            if char:
                if char == CRC:
                    func("<<< CRC")
                    timer.cancel()
                    break
                elif char == CAN:
                    # exit after receiving second CAN
                    func("<<< CAN")
                    timer.cancel()
                    raise Exception("Remote end stopped 1st character response!")
                elif char == None:
                    continue
                else:
                    func("Error, expected CRC or CAN, but its " + char)

        # First packet
        header = self._make_send_header(self.ymodem_first_packet_size, 0)
        data = "Firmware"
        data = data.ljust(self.ymodem_first_packet_size, self.header_pad)
        checksum = self._make_send_checksum(data)
        data_for_send = header + data + checksum
        self.putc(data_for_send)
        # data_in_hexstring = "".join("%02x" % b for b in data_for_send)
        func(">>> Packet 0")
        
        timeout_count = 0
        timer = threading.Timer(1, check_receive_timeout)
        error_count = 0
        cancel = 0
        while True:
            if timeout_count > 5:
                timer.cancel()
                raise Exception("Receiving 2nd character timeout!")
            # try to get second char, send file when the char is CRC
            char = self.getc(1)
            if char:
                if char == CRC:
                    func("<<< CRC")
                    timer.cancel()
                    break
                elif char == ACK:
                    func("<<< ACK")
                    char2 = self.getc(1)
                    if char2 == CRC:
                        func("<<< CRC")
                    timer.cancel()
                    break
                elif char == CAN:
                    func("<<< CAN")
                    timer.cancel()
                    raise Exception("Remote end stopped 2nd character response!")
                elif char == None:
                    continue
                else:
                    func("Error, expected CRC or CAN, but its " + char)
            
        success_count = 0
        total_packets = math.ceil(length / 1024.0)
        func("Total packets: " + str(total_packets))
        sequence = 1
        while True:
            error_count = 0
            # read data from stream
            data = stream.read(packet_size)
            if not data:
                break

            header = self._make_send_header(packet_size, sequence)
            data = data.ljust(packet_size, self.pad)
            checksum = self._make_send_checksum(data)

            while True:
                data_for_send = header + data + checksum
                # data_in_hexstring = "".join("%02x" % b for b in data_for_send)
                func(">>> Packet " + str(sequence))
                # send data packet
                self.putc(data_for_send)

                timeout_count = 0
                timer = threading.Timer(1, check_receive_timeout)
                while True:
                    if timeout_count > 3:
                        timer.cancel()
                        raise Exception("Receiving data response timeout!")
                    # Success: Packet received by the other side
                    char = self.getc(1)
                    if char == ACK:
                        func('<<< ACK')
                        success_count += 1
                        timer.cancel()
                        if callable(callback):
                            callback(total_packets, success_count)
                        break
                    # Fail
                    elif char == NAK:
                        func('<<< NAK')
                        error_count += 1
                        if error_count > retry:
                            self.abort()
                            timer.cancel()
                            raise Exception("Retry times is up to the limit!")
                    elif char == CAN:
                        func('<<< CAN')
                        timer.cancel()
                        raise Exception("Remote end stopped data response")
                    elif char == None:
                        continue
                    else:
                        # Unrecognized char
                        func("Error, expected ACK NAK or CAN, but its " + char)
                        continue
                break

            sequence = (sequence + 1) % 0x100

        # Send EOT and expect ACK
        while True:
            self.putc(EOT)
            func(">>> EOT")
            char = self.getc(1)
            if char == ACK:
                break
            else:
                error_count += 1
                if error_count > retry:
                    self.abort()

    # header byte
    def _make_send_header(self, packet_size, sequence):
        _bytes = []
        if packet_size == 128:
            _bytes.append(ord(SOH))
        elif packet_size == 1024:
            _bytes.append(ord(STX))
        _bytes.extend([sequence, 0xff - sequence])
        return bytearray(_bytes)

    # CRC algorithm
    def _make_send_checksum(self, data):
        _bytes = []
        crc = self.calc_crc(data)
        _bytes.extend([crc >> 8, crc & 0xff])
        return bytearray(_bytes)
    
    # CCITT-0
    def calc_crc(self, data, crc=0):
        for char in bytearray(data):
            crctbl_idx = ((crc >> 8) ^ char) & 0xff
            crc = ((crc << 8) ^ self.crctable[crctbl_idx]) & 0xffff
        return crc & 0xffff

if __name__ == '__main__':
    pass
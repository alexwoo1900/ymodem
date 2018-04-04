#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import math
import string
import logging
logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s')

# ymodem data header byte
SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
NAK = b'\x15'
CAN = b'\x18'
CRC = b'C'

class YMODEM(object):

    # initialize
    def __init__(self, getc, putc, mode='ymodem', header_pad=b'\x00', pad=b'\x1a'):
        self.getc = getc
        self.putc = putc
        self.mode = mode
        self.header_pad = header_pad
        self.pad = pad
        self.log = logging.getLogger('YReporter')

    # send abort(CAN) twice
    def abort(self, count=2, timeout=15):
        for _ in range(count):
            self.putc(CAN, timeout)
         
    '''
    send entry
    '''
    def send(self, file_stream, file_name, retry=20, timeout=15, callback=None):
        try:
            packet_size = dict(
                ymodem = 1024,
                ymodem128 = 128
            )[self.mode]
        except KeyError:
            raise ValueError("Invalid mode specified: {self.mode!r}".format(self=self))

        self.log.debug('Begin start sequence, packet_size=%d', packet_size)

        # Receive first character
        error_count = 0
        cancel = 0
        while True:
            char = self.getc(1, timeout)
            if char:
                if char == CRC:
                    # Expected CRC
                    self.log.info("<<< CRC")
                    break
                elif char == CAN:
                    self.log.info("<<< CAN")
                    if cancel:
                        return False
                    else:
                        cancel = 1
                else:
                    self.log.error("send error, expected CRC or CAN, but got " + hex(ord(char)))

            error_count += 1
            if error_count > retry:
                self.abort(timeout=timeout)
                self.log.error("send error: error_count reached %d aborting", retry)
                return False

        # Send first packet
        header = self._make_send_header(packet_size, 0)
        data = file_name
        data = data.ljust(packet_size, self.header_pad)
        checksum = self._make_send_checksum(data)
        data_for_send = header + data + checksum
        self.putc(data_for_send)
        # data_in_hexstring = "".join("%02x" % b for b in data_for_send)
        self.log.info("Packet 0 >>>")

        error_count = 0
        cancel = 0
        # Receive reponse of first packet
        while True:
            char = self.getc(1, timeout)
            if char:
                if char == ACK:
                    self.log.info("<<< ACK")
                    char2 = self.getc(1, timeout)
                    if char2 == CRC:
                        self.log.info("<<< CRC")
                        break
                    else:
                        self.log.warn("ACK wasnt CRCd")
                        break
                elif char == CAN:
                    self.log.info("<<< CAN")
                    if cancel:
                        return False
                    else:
                        cancel = 1
                else:
                    self.log.error("send error, expected ACK or CAN, but got " + hex(ord(char)))
        
        error_count = 0
        cancel = 0
        success_count = 0
        total_packets = 1
        sequence = 1
        while True:
            # Read raw data from file stream
            data = file_stream.read(packet_size)
            if not data:
                self.log.debug('send: at EOF')
                break
            total_packets += 1

            header = self._make_send_header(packet_size, sequence)
            data = data.ljust(packet_size, self.pad)
            checksum = self._make_send_checksum(data)

            while True:
                data_for_send = header + data + checksum
                # data_in_hexstring = "".join("%02x" % b for b in data_for_send)

                # Send file data packet
                self.putc(data_for_send)
                self.log.info("Packet " + str(sequence) + " >>>")

                char = self.getc(1, timeout)
                if char == ACK:
                    # Expected response
                    self.log.info("<<< ACK")
                    success_count += 1
                    if callable(callback):
                        callback(total_packets, success_count, error_count)
                    error_count = 0
                    break
                
                error_count += 1
                if callable(callback):
                    callback(total_packets, success_count, error_count)

                if error_count > retry:
                    self.abort(timeout=timeout)
                    self.log.error('send error: NAK received %d , aborting', retry)
                    return False

            sequence = (sequence + 1) % 0x100

        # Send EOT and expect final ACK
        while True:
            self.putc(EOT)
            self.log.info(">>> EOT")
            char = self.getc(1, timeout)
            if char == ACK:
                self.log.info("<<< ACK")
                break
            else:
                error_count += 1
                if error_count > retry:
                    self.abort(timeout=timeout)
                    self.log.warn('EOT wasnt ACKd, aborting transfer')
                    return False

        self.log.info('Transmission successful (ACK received)')
        return True

    '''
    recv entry
    '''
    def recv(self, file_stream, retry=20, timeout=15, delay=0.01):
        error_count = 0 
        cancel = 0
        char = ""
        while True:
            if error_count >= retry:
                self.abort(timeout=timeout)
                self.log.error('error_count reached %d, aborting.', retry)
                return None
            else:
                if not self.putc(CRC):
                    time.sleep(delay)
                    error_count += 1
                self.log.info("CRC >>>")

            # Get First response
            char = self.getc(1, timeout)
            # First packet arrived
            if char == SOH:
                self.log.info("<<< SOH")
                break
            elif char == STX:
                self.log.info("<<< STX")
                break
            elif char == CAN:
                self.log.info("<<< CAN")
                if cancel:
                    return None
                else:
                    cancel = 1
            else:
                error_count += 1

        error_count = 0
        cancel = 0
        file_size = 0
        packet_size = 1024
        sequence = 0
        while True:
            while True:
                if char == SOH:
                    packet_size = 128
                    break
                elif char == STX:
                    packet_size = 1024
                    break
                elif char == EOT:
                    self.putc(ACK)
                    return file_size
                elif char == CAN:
                    if cancel:
                        return None
                    else:
                        cancel = 1
                else:
                    error_count += 1
                    if error_count > retry:
                        self.abort(timeout=timeout)
                        return None

                error_count = 0
                cancel = 0 
                seq = self.getc(1)
                if seq is None:
                    seq_oc = None
                else:
                    seq = ord(seq)
                    seq_oc = self.getc(1)
                    if seq_oc is None:
                        pass
                    else:
                        seq_oc = 0xFF - ord(seq_oc)

                if not (seq == seq_oc == sequence):
                    self.getc(packet_size + 1)
                else:
                    data = self.getc(packet_size + 1)
                    valid, _ = self._verify_recv_checksum(data)

                    if valid:
                        if seq == 0:
                            file_name = string.strip(data[-1:])
                            self.putc(ACK)
                            self.log.info("ACK >>>")
                            self.putc(CRC)
                            self.log.info("CRC >>>")
                            sequence = (sequence + 1) % 0x100
                            char = self.getc(1)
                            continue
                        else:
                            file_size += len(packet_size)
                            file_stream.write(data[-1:])
                            self.putc(ACK)
                            sequence = (sequence + 1) % 0x100
                            char = self.getc(1)
                            continue

                while True:
                    data = self.getc(1)
                    if data is None:
                        break
                
                self.putc(NAK)
                char = self.getc(1)
                continue


    # Header byte
    def _make_send_header(self, packet_size, sequence):
        assert packet_size in (128, 1024), packet_size
        _bytes = []
        if packet_size == 128:
            _bytes.append(ord(SOH))
        elif packet_size == 1024:
            _bytes.append(ord(STX))
        _bytes.extend([sequence, 0xff - sequence])
        return bytearray(_bytes)

    # Make check code
    def _make_send_checksum(self, data):
        _bytes = []
        crc = self.calc_crc(data)
        _bytes.extend([crc >> 8, crc & 0xff])
        return bytearray(_bytes)

    def _verify_recv_checksum(self, data):
        _checksum = bytearray(data[-2:])
        their_sum = (_checksum[0] << 8) + _checksum[1]
        data = data[:-2]

        our_sum = self.calc_crc(data)
        valid = bool(their_sum == our_sum)
        return valid, data

    # For CRC algorithm
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

    # CRC algorithm: CCITT-0
    def calc_crc(self, data, crc=0):
        for char in bytearray(data):
            crctbl_idx = ((crc >> 8) ^ char) & 0xff
            crc = ((crc << 8) ^ self.crctable[crctbl_idx]) & 0xffff
        return crc & 0xffff

if __name__ == '__main__':
    pass
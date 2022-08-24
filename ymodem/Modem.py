import os
import sys
import time
import logging
import platform

from .Protocol import Protocol

logging.basicConfig(level = logging.DEBUG, format = '%(message)s')

SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
NAK = b'\x15'
CAN = b'\x18'
CRC = b'\x43'

USE_LENGTH_FIELD    = 0b100000
USE_DATE_FIELD      = 0b010000
USE_MODE_FIELD      = 0b001000
USE_SN_FIELD        = 0b000100
ALLOW_1K_BLOCK      = 0b000010
ALLOW_YMODEM_G      = 0b000001

class Modem(Protocol):
    def __init__(self, reader, writer, mode='ymodem1k', program="rzsz"):
        self.logger = logging.getLogger('Modem')

        self.reader = reader
        self.writer = writer
        self.mode   = mode

        '''
        YMODEM Header Information and Features
        _____________________________________________________________
        | Program   | Length | Date | Mode | S/N | 1k-Blk | YMODEM-g |
        |___________|________|______|______|_____|________|__________|
        |Unix rz/sz | yes    | yes  | yes  | no  | yes    | sb only  |
        |___________|________|______|______|_____|________|__________|
        |VMS rb/sb  | yes    | no   | no   | no  | yes    | no       |
        |___________|________|______|______|_____|________|__________|
        |Pro-YAM    | yes    | yes  | no   | yes | yes    | yes      |
        |___________|________|______|______|_____|________|__________|
        |CP/M YAM   | no     | no   | no   | no  | yes    | no       |
        |___________|________|______|______|_____|________|__________|
        |KMD/IMP    | ?      | no   | no   | no  | yes    | no       |
        |___________|________|______|______|_____|________|__________|

        '''
        try:
            self.program_features = dict(
                rzsz    = USE_LENGTH_FIELD | USE_DATE_FIELD | USE_MODE_FIELD | ALLOW_1K_BLOCK,
                rbsb    = USE_LENGTH_FIELD | ALLOW_1K_BLOCK,
                pyam    = USE_LENGTH_FIELD | USE_DATE_FIELD | USE_SN_FIELD | ALLOW_1K_BLOCK | ALLOW_YMODEM_G,
                cyam    = ALLOW_1K_BLOCK,
                kimp    = ALLOW_1K_BLOCK,
            )[program]
        except KeyError:
            raise ValueError("Invalid program specified: {}".format(program))
        
    def abort(self, count=2, timeout=60):
        for _ in range(count):
            self.writer.write(CAN, timeout)

    def send(self, stream, retry=10, timeout=10, callback=None, info=None):
        try:
            packet_size = dict(
                xmodem    = 128,
                xmodem1k  = 1024,
                ymodem    = 128,
                # Not all but most programs support 1k length
                ymodem1k  = (128, 1024)[(self.program_features & ALLOW_1K_BLOCK) != 0],
            )[self.mode]
        except KeyError:
            raise ValueError("Invalid mode specified: {self.mode}".format(self=self))
        
        '''
        The first package for YMODEM Batch Transmission
        It will contain some important information about the source file
        '''
        if self.mode.startswith("ymodem"):

            self.logger.debug('[Sender]: Waiting the mode request...')

            error_count = 0
            crc_mode = 0
            cancel = 0
            while True:
                # Blocking may occur here, the reader needs to have a timeout mechanism
                char = self.reader.read(1, timeout)

                if char:
                    if char == NAK:
                        crc_mode = 0
                        self.logger.debug("[Sender]: Received checksum request (NAK)")
                        break
                    elif char == CRC:
                        crc_mode = 1
                        self.logger.debug("[Sender]: Received CRC request (C/CRC)")
                        break
                    elif char == CAN:
                        if cancel == 1:
                            self.logger.info("[Sender]: Transmission cancelled (CAN)")
                            return False
                        else:
                            cancel = 1
                            self.logger.debug("[Sender]: Ready for transmission cancellation (CAN)")
                    elif char == EOT:
                        self.logger.info("[Sender]: Transmission cancelled (EOT)")
                        return False
                    else:
                        self.logger.error("[Sender]: Error, expected NAK, CRC, EOT or CAN but got %r", char)
                else:
                    self.logger.debug("[Sender]: No valid data was read")

                error_count += 1
                if error_count > retry:
                    self.logger.error("[Sender]: Error, error_count reached {}, aborting...".format(retry))
                    self.abort(timeout=timeout)
                    return False


            self.logger.debug("[Sender]: Preparing info block")

            header = self._make_send_header(packet_size, 0)

            # Required field: Name
            data = info["name"].encode("utf-8")
            
            # Optional field: Length
            if self.program_features & USE_LENGTH_FIELD:
                data += bytes(1)
                data += str(info["length"]).encode("utf-8")

            '''
            Optional field: Modification Date
            oct() has different representations of octal numbers in different versions of Python:
            Python 2+: 0123456
            Python 3+: 0o123456
            '''
            if self.program_features & USE_DATE_FIELD:
                mtime = oct(int(info["mtime"]))
                if mtime.startswith("0o"):
                    data += (" " + mtime[2:]).encode("utf-8")
                else:
                    data += (" " + mtime[1:]).encode("utf-8")

            # Optional field: Mode
            if self.program_features & USE_MODE_FIELD:
                if info["source"] == "Unix":
                    data += (" " + oct(0x8000)).encode("utf-8")
                else:
                    data += (" 0").encode("utf-8")

            # Optional field: Serial Number
            if self.program_features & USE_MODE_FIELD:
                data += (" 0").encode("utf-8")

            data = data.ljust(packet_size, b"\x00")
            checksum = self._make_send_checksum(crc_mode, data)
            
            error_count = 0
            while True:
                # Blocking may occur here, the writer needs to have a timeout mechanism
                self.writer.write(header + data + checksum)
                self.logger.debug("[Sender]: Info block sent")

                # Blocking may occur here, the reader needs to have a timeout mechanism
                char = self.reader.read(1, timeout)
                if char == ACK:
                    error_count = 0
                    break
                else:
                    self.logger.error("[Sender]: Error, expected ACK but got %r for info block", char)
                    error_count += 1
                    if error_count > retry:
                        self.logger.error("[Sender]: Error, NAK received {} times, aborting...".format(error_count))
                        self.abort(timeout=timeout)
                        return False

        # Data packets
        self.logger.debug("[Sender]: Waiting the mode request...")

        error_count = 0
        crc_mode = 0
        cancel = 0
        while True:
            # Blocking may occur here, the reader needs to have a timeout mechanism
            char = self.reader.read(1, timeout)
            if char:
                if char == NAK:
                    crc_mode = 0
                    self.logger.debug("[Sender]: Received checksum request (NAK)")
                    break
                elif char == CRC:
                    crc_mode = 1
                    self.logger.debug("[Sender]: Received CRC request (C/CRC)")
                    break
                elif char == CAN:
                    if cancel:
                        self.logger.info("[Sender]: Transmission cancelled (CAN)")
                        return False
                    else:
                        cancel = 1
                        self.logger.debug("[Sender]: Ready for transmission cancellation (CAN)")
                elif char == EOT:
                    self.logger.info("[Sender]: Transmission cancelled (EOT)")
                    return False
                else:
                    self.logger.error("[Sender]: Expected NAK, CRC, EOT or CAN but got %r", char)

            error_count += 1
            if error_count > retry:
                self.logger.info("[Sender]: Error, error_count reached {}, aborting...".format(retry))
                self.abort(timeout=timeout)
                return False

        error_count = 0
        success_count = 0
        total_packets = 0
        sequence = 1
        while True:
            data = stream.read(packet_size)
            if not data:
                self.logger.debug("[Sender]: Reached EOF")
                break

            total_packets += 1

            header = self._make_send_header(packet_size, sequence)
            # fill with 1AH(^z)
            data = data.ljust(packet_size, b"\x1a")
            checksum = self._make_send_checksum(crc_mode, data)

            while True:
                # Blocking may occur here, the writer needs to have a timeout mechanism
                self.writer.write(header + data + checksum)
                self.logger.debug("[Sender]: Block {} (Seq {}) sent".format(success_count, sequence))

                # Blocking may occur here, the reader needs to have a timeout mechanism
                char = self.reader.read(1, timeout)
                if char == ACK:
                    success_count += 1
                    if callable(callback):
                        callback(total_packets, success_count, error_count)
                    error_count = 0
                    break
                else:
                    self.logger.error('[Sender]: Error, expected ACK but got %r for block %d', char, sequence)
                    error_count += 1
                    if callable(callback):
                        callback(total_packets, success_count, error_count)
                    if error_count > retry:
                        self.logger.error("[Sender]: Error, NAK received {} times, aborting...".format(error_count))
                        self.abort(timeout=timeout)
                        return False

            sequence = (sequence + 1) % 0x100


        # Blocking may occur here, the writer needs to have a timeout mechanism
        self.writer.write(EOT)
        self.logger.debug("[Sender]: EOT sent and awaiting NAK")
        
        while True:
            char = self.reader.read(1, timeout)
            if char == NAK:
                self.logger.debug("[Sender]: Received NAK")
                break
            else:
                self.logger.error("[Sender]: Error, expected NAK but got %r", char)
                error_count += 1
                if error_count > retry:
                    self.logger.warning("[Sender]: Warning, EOT was not NAKd, aborting transfer...")
                    self.abort(timeout=timeout)
                    return False

        self.writer.write(EOT)
        self.logger.debug("[Sender]: EOT sent and awaiting ACK")

        while True:
            # Blocking may occur here, the reader needs to have a timeout mechanism
            char = self.reader.read(1, timeout)
            if char == ACK:
                self.logger.debug("[Sender]: Received ACK")
                break
            else:
                self.logger.error("[Sender]: Error, expected ACK but got %r", char)
                error_count += 1
                if error_count > retry:
                    self.logger.warning("[Sender]: Warning, EOT was not ACKd, aborting transfer...")
                    self.abort(timeout=timeout)
                    return False

        self.logger.info("[Sender]: Transmission finished (ACK)")
        return True

    def _make_send_header(self, packet_size, sequence):
        assert packet_size in (128, 1024), packet_size
        _bytes = []
        if packet_size == 128:
            _bytes.append(ord(SOH))
        elif packet_size == 1024:
            _bytes.append(ord(STX))
        _bytes.extend([sequence, 0xff - sequence])
        return bytearray(_bytes)

    def _make_send_checksum(self, crc_mode, data):
        _bytes = []
        if crc_mode:
            crc = self.calc_crc(data)
            _bytes.extend([crc >> 8, crc & 0xff])
        else:
            crc = self.calc_checksum(data)
            _bytes.append(crc)
        return bytearray(_bytes)

    def recv(self, stream, crc_mode=1, retry=10, timeout=10, delay=1, callback=None, info=None):
        self._recv_file_name = ""
        self._remaining_data_length = 0
        self._recv_file_mtime = 0
        self._recv_mode = 0
        self._recv_sn = 0

        '''
        Parse the first package of YMODEM Batch Transmission to get the target file information
        '''
        if self.mode.startswith("ymodem"):
            error_count = 0
            char = 0
            cancel = 0
            while True:
                if error_count >= retry:
                    self.logger.info("[Receiver]: Error, error_count reached {}, aborting...".format(retry))
                    self.abort(timeout=timeout)
                    return None
                elif crc_mode and error_count < (retry // 2):
                    if not self.writer.write(CRC):
                        self.logger.debug("[Receiver]: Error, write failed, sleeping for {}".format(delay))
                        time.sleep(delay)
                        error_count += 1
                else:
                    crc_mode = 0
                    if not self.writer.write(NAK):
                        self.logger.debug("[Receiver]: Error, write failed, sleeping for {}".format(delay))
                        time.sleep(delay)
                        error_count += 1

                char = self.reader.read(1, timeout=3)
                if char is None:
                    self.logger.warning("[Receiver]: Error, read timeout in info block")
                    error_count += 1
                    continue
                elif char == SOH:
                    self.logger.debug("[Receiver]: Received valid header (SOH)")
                    break
                elif char == STX:
                    self.logger.debug("[Receiver]: Received valid header (STX)")
                    break
                elif char == CAN:
                    if cancel:
                        self.logger.info("[Receiver]: TRANSMISSION Cancelled (CAN)")
                        return None
                    else:
                        self.logger.debug("[Receiver]: Ready for transmission cancellation (CAN)")
                        cancel = 1
                else:
                    error_count += 1

            error_count = 0
            packet_size = 128
            cancel = 0
            while True:
                while True:
                    if char == SOH:
                        if packet_size != 128:
                            packet_size = 128
                            self.logger.debug("[Receiver]: Set 128 bytes for packet_size")
                        break
                    elif char == STX:
                        if packet_size != 1024:
                            packet_size = 1024
                            self.logger.debug("[Receiver]: Set 1024 bytes for packet_size")
                        break
                    elif char == CAN:
                        if cancel:
                            self.logger.info("[Receiver]: TRANSMISSION Cancelled (CAN)")
                            return None
                        else:
                            cancel = 1
                            self.logger.debug("[Receiver]: Ready for transmission cancellation (CAN)")
                    else:
                        err_msg = ("[Receiver]: Error, expected SOH, EOT but got {0}".format(char))

                        self.logger.warning(err_msg)
                        error_count += 1
                        if error_count > retry:
                            self.logger.info("[Receiver]: Error, error_count reached %d, aborting...".format(retry))
                            self.abort()
                            return None
                
                self.logger.debug('[Receiver]: Preparing for data packets....')
                error_count = 0
                cancel = 0
                seq1 = self.reader.read(1, timeout)
                if seq1 is None:
                    seq2 = None
                    self.logger.warning("[Receiver]: Warning, read failed to get first sequence byte")
                else:
                    seq1 = ord(seq1)
                    seq2 = self.reader.read(1, timeout)
                    if seq2 is None:
                        self.logger.warning("[Receiver]: Warning, read failed to get second sequence byte")
                    else:
                        seq2 = 0xff - ord(seq2)

                if not (seq1 == seq2 == 0):
                    self.logger.error("[Receiver]: Error, expected seq 0, got (seq1 %r, seq2 %r), receiving next block...", seq1, seq2)
                    # skip this packet
                    self.reader.read(packet_size + 1 + crc_mode)
                    self.logger.warning("[Receiver]: a wrong packet dropped")
                else:
                    self.logger.debug("[Receiver]: Read a packet")
                    data = self.reader.read(packet_size + 1 + crc_mode, timeout)

                    if data and len(data) == (packet_size + 1 + crc_mode):
                        valid, data = self._verify_recv_checksum(crc_mode, data)

                        if valid:
                            data = data.lstrip(b"\x00")
                            self._recv_file_name = bytes.decode(data.split(b"\x00")[0], "utf-8")
                            self.logger.debug("[Receiver]: File - {}".format(self._recv_file_name))

                            try:
                                stream = open(os.path.join(info["save_path"], self._recv_file_name), "wb+")
                            except IOError as e:
                                stream.close()
                                self.logger.error("[Receiver]: Error, cannot open save path")
                                return
                            data = bytes.decode(data.split(b"\x00")[1], "utf-8")

                            if self.program_features & USE_LENGTH_FIELD:
                                space_index = data.find(" ")
                                self._remaining_data_length = int(data if space_index == -1 else data[:space_index])
                                self.logger.debug("[Receiver]: Size - {} bytes".format(self._remaining_data_length))
                                data = data[space_index + 1:]

                            if self.program_features & USE_DATE_FIELD:
                                space_index = data.find(" ")
                                self._recv_file_mtime = int(data if space_index == -1 else data[:space_index], 8)
                                self.logger.debug("[Receiver]: Mtime - {} seconds".format(self._recv_file_mtime))
                                data = data[space_index + 1:]

                            if self.program_features & USE_MODE_FIELD:
                                space_index = data.find(" ")
                                self._recv_mode = int(data if space_index == -1 else data[:space_index])
                                self.logger.debug("[Receiver]: Mode - {}".format(self._recv_mode))
                                data = data[space_index + 1:]

                            if self.program_features & USE_SN_FIELD:
                                space_index = data.find(" ")
                                self._recv_sn = int(data if space_index == -1 else data[:space_index])
                                self.logger.debug("[Receiver]: SN - {}".format(self._recv_sn))

                            self.writer.write(ACK)
                            break

                        # broken packet
                        else:
                            pass
                    
                    # bad read
                    else:
                        pass

                # Receive failed handler: ask for retransmission
                self.logger.warning('[Receiver]: Warning, requesting retransmission (NAK)')
                while True:
                    data = self.reader.read(1, timeout=1)
                    if data is None:
                        break
                self.writer.write(NAK)
                char = self.reader.read(1, timeout)
                continue

        error_count = 0
        char = 0
        cancel = 0
        while True:
            if error_count >= retry:
                self.logger.info("[Receiver]: Error, error_count reached %d, aborting...".format(retry))
                self.abort(timeout=timeout)
                return None
            elif crc_mode and error_count < (retry // 2):
                if not self.writer.write(CRC):
                    self.logger.debug("[Receiver]: Error, write failed, sleeping for {}".format(delay))
                    time.sleep(delay)
                    error_count += 1
            else:
                crc_mode = 0
                if not self.writer.write(NAK):
                    self.logger.debug("[Receiver]: Error, write failed, sleeping for {}".format(delay))
                    time.sleep(delay)
                    error_count += 1

            char = self.reader.read(1, timeout=3)
            if char is None:
                self.logger.warning("[Receiver]: Warning, read timeout in start sequence")
                error_count += 1
                continue
            elif char == SOH:
                self.logger.debug("[Receiver]: Received valid header (SOH)")
                break
            elif char == STX:
                self.logger.debug("[Receiver]: Received valid header (STX)")
                break
            elif char == CAN:
                if cancel:
                    self.logger.info("[Receiver]: Transmission cancelled (CAN)")
                    return None
                else:
                    cancel = 1
                    self.logger.debug("[Receiver]: Ready for transmission cancellation (CAN)")
            else:
                error_count += 1
                
        error_count = 0
        success_count = 0
        income_size = 0
        packet_size = 128
        sequence = 1
        cancel = 0
        while True:
            while True:
                if char == SOH:
                    if packet_size != 128:
                        packet_size = 128
                        self.logger.debug("[Receiver]: Set 128 bytes for packet_size")
                    break
                elif char == STX:
                    if packet_size != 1024:
                        packet_size = 1024
                        self.logger.debug("[Receiver]: Set 1024 bytes for packet_size")
                    break
                elif char == EOT:
                    if cancel:
                        self.writer.write(ACK)
                        self.logger.info("[Receiver]: Transmission finished (%d bytes)", income_size)
                        return income_size
                    else:
                        cancel = 1
                        self.writer.write(NAK)
                        self.logger.debug("[Receiver]: Ready for transmission cancellation (EOT) at data block {} (seq {})".format(success_count, sequence))
                elif char == CAN:
                    if cancel:
                        self.logger.info("[Receiver]: Transmission cancelled (CAN) at data block {} (seq {})".format(success_count, sequence))
                        return None
                    else:
                        cancel = 1
                        self.logger.debug("[Receiver]: Ready for transmission cancellation (CAN) at data block {} (seq {})".format(success_count, sequence))
                else:
                    err_msg = ("[Receiver]: Error, expected SOH, EOT but got {0!r}".format(char))

                    self.logger.warning(err_msg)
                    error_count += 1
                    if error_count > retry:
                        self.logger.info("[Receiver]: Error, error_count reached {}, aborting...".format(retry))
                        self.abort()
                        return None

            seq1 = self.reader.read(1, timeout)
            if seq1 is None:
                seq2 = None
                self.logger.warning("[Receiver]: Warning, read failed to get first sequence byte")
            else:
                seq1 = ord(seq1)
                seq2 = self.reader.read(1, timeout)
                if seq2 is None:
                    self.logger.warning("[Receiver]: Warning, read failed to get second sequence byte")
                else:
                    seq2 = 0xff - ord(seq2)

            # Packet received in wrong number
            if not (seq1 == seq2 == sequence):
                self.logger.error("[Receiver]: Error, expected seq %d but got (seq1 %r, seq2 %r), receiving next block...", sequence, seq1, seq2)
                # skip this packet
                self.reader.read(packet_size + 1 + crc_mode)
                self.logger.warning("[Receiver]: a wrong packet dropped")
            
            # Packet received
            else:
                data = self.reader.read(packet_size + 1 + crc_mode, timeout)

                if data and len(data) == (packet_size + 1 + crc_mode):
                    valid, data = self._verify_recv_checksum(crc_mode, data)

                    # Write the original data to the target file
                    if valid:
                        success_count += 1
                        self.logger.debug('[Receiver]: Data block %d (seq=%d) OK', success_count, sequence)

                        valid_length = packet_size

                        # The last package adjusts the valid data length according to the file length
                        if (self._remaining_data_length > 0):
                            valid_length = min(valid_length, self._remaining_data_length)
                            self._remaining_data_length -= valid_length
                        data = data[:valid_length]

                        income_size += len(data)
                        stream.write(data)

                        if callable(callback):
                            callback(income_size, self._remaining_data_length)

                        self.writer.write(ACK)

                        sequence = (sequence + 1) % 0x100

                        char = self.reader.read(1, timeout)
                        continue

                    # broken packet
                    else:
                        pass

                # bad read
                else:
                    pass

            # Receive failed handler: ask for retransmission
            self.logger.warning("[Receiver]: Error, requesting retransmission (NAK)")
            while True:
                data = self.reader.read(1, timeout=1)
                if data is None:
                    break
            self.writer.write(NAK)
            char = self.reader.read(1, timeout)
            continue

    def _verify_recv_checksum(self, crc_mode, data):
        if crc_mode:
            _checksum = bytearray(data[-2:])
            remote_sum = (_checksum[0] << 8) + _checksum[1]
            data = data[:-2]

            local_sum = self.calc_crc(data)
            valid = bool(remote_sum == local_sum)
            if not valid:
                self.logger.warning("[Receiver]: Error, checksum failed (remote %04x, local %04x)", remote_sum, local_sum)
        else:
            _checksum = bytearray([data[-1]])
            remote_sum = _checksum[0]
            data = data[:-1]

            local_sum = self.calc_checksum(data)
            valid = remote_sum == local_sum
            if not valid:
                self.logger.warning("[Receiver]: Error, checksum failed (remote %02x, local %02x)", remote_sum, local_sum)
        return valid, data

    def calc_checksum(self, data, checksum=0):
        if platform.python_version_tuple() >= ('3', '0', '0'):
            return (sum(data) + checksum) % 256
        else:
            return (sum(map(ord, data)) + checksum) % 256

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

    # CRC-16-CCITT
    def calc_crc(self, data, crc=0):
        for char in bytearray(data):
            crctbl_idx = ((crc >> 8) ^ char) & 0xff
            crc = ((crc << 8) ^ self.crctable[crctbl_idx]) & 0xffff
        return crc & 0xffff

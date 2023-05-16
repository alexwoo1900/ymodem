from abc import ABC, abstractmethod
import logging
import math
import os
import time
from typing import Any, Callable, List, Optional, Union

from ymodem.Checksum import calc_crc, calc_checksum
from ymodem.Platform import Platform
from ymodem.Protocol import ProtocolType, ProtocolStyleManagement, YMODEM

SOH = b'\x01'
STX = b'\x02'
EOT = b'\x04'
ACK = b'\x06'
NAK = b'\x15'
CAN = b'\x18'
CRC = b'\x43'

class Channel(ABC):

    @abstractmethod
    def read(self, *arg, **kwargs):
        pass

    @abstractmethod
    def write(self, *arg, **kwargs):
        pass

_psm = ProtocolStyleManagement()

class ModemSocket(Channel):
    def __init__(self, 
                 read: Callable[[int, Optional[float]], Any], 
                 write: Callable[[Union[bytes, bytearray], Optional[float]], Any], 
                 protocol_type: int = ProtocolType.YMODEM, 
                 packet_size: int = 1024,
                 style_id: int = _psm.get_available_styles()[0]):

        self.logger = logging.getLogger('Socket')

        self._read = read
        self._write = write
        self.set_protocol_type(protocol_type)
        self.set_protocol_style(style_id, packet_size)
        

    def read(self, size: int, timeout: float = 2):
        return self._read(size, timeout)
    
    def write(self, data: Union[bytes, bytearray], timeout: float = 2):
        return self._write(data, timeout)
    
    def set_protocol_type(self, protocol_type: int):
        if protocol_type not in ProtocolType.all():
            raise ValueError(f"Invalid mode specified: {protocol_type}")
        self.protocol_type = protocol_type

    def set_protocol_style(self, style_id: int, packet_size: int):
        if self.protocol_type == ProtocolType.YMODEM:

            if style_id not in _psm.get_available_styles():
                raise ValueError(f"Invalid style specified: {style_id}")        
            style = _psm.get_available_style(style_id)
            self._protocol_features = style.get_protocol_features(ProtocolType.YMODEM)

            if packet_size not in [128, 1024]:
                raise ValueError(f"Invalid packet size specified: {packet_size}")
            self._packet_size = packet_size
            if (self._protocol_features & YMODEM.ALLOW_1K_PACKET) == 0:
                self._packet_size = 128
        
    def abort(self, count: int = 2, timeout: float = 60) -> None:
        '''
        Send CAN

        param count: the number of times to send, default to 2
        param timeout: write timeout
        '''

        for _ in range(count):
            self.write(CAN, timeout)

    def send(self, 
             paths: List[str], 
             retry: int = 10, 
             timeout: float = 10, 
             callback: Optional[Callable[[int, str, int, int, int], None]] = None
             ) -> bool:
        '''
        Send files

        param paths: List of file paths to be sent
        param retry: Number of retries when communication error occur
        param timeout: read/write timeout
        param callback: 
        '''
        
        tasks = []      # type: List[_ModemFile]
        stream = None   # type: BufferedReader

        for path in paths:
            if os.path.isfile(path):
                tasks.append(_ModemFile(path))

        for task_index, task in enumerate(tasks):

            try:
                stream = open(task.path, "rb")
            except IOError:
                self.logger.warning(f"[Sender]: Cannot open the file: {task.path}.")
                continue

            if self.protocol_type == ProtocolType.YMODEM:
                '''
                Info packet
                '''
                crc_mode = 0
                cancel_count = 0
                error_count = 0
                while True:
                    # Blocking may occur here, the reader needs to have a timeout mechanism
                    char = self.read(1, timeout)

                    if char == NAK:
                        crc_mode = 0
                        self.logger.debug("[Sender]: Received checksum request (NAK).")
                        break
                    elif char == CRC:
                        crc_mode = 1
                        self.logger.debug("[Sender]: Received CRC request (C/CRC).")
                        break
                    elif char == CAN:
                        if cancel_count == 0:
                            cancel_count += 1
                        else:
                            self.logger.debug("[Sender]: Cancel transfer (CAN).")
                            return False
                    else:
                        self.logger.debug("[Sender]: No valid data read.")

                    error_count += 1
                    if error_count > retry:
                        self.abort(timeout = timeout)
                        if stream:
                            stream.close()
                        self.logger.debug(f"[Sender]: Aborted, the number of errors has reached {retry}.")
                        return False

                header = self._make_send_header(self._packet_size, 0)

                # Required field: Name
                data = task.name.encode("utf-8")
                
                # Optional field: Length
                if self._protocol_features & YMODEM.USE_LENGTH_FIELD:
                    data += bytes(1)
                    data += str(task.total).encode("utf-8")

                
                # Optional field: Modification Date
                # oct() has different representations of octal numbers in different versions of Python:
                # Python 2+: 0123456
                # Python 3+: 0o123456
                if self._protocol_features & YMODEM.USE_DATE_FIELD:
                    mtime = oct(int(task.mtime))
                    if mtime.startswith("0o"):
                        data += (" " + mtime[2:]).encode("utf-8")
                    else:
                        data += (" " + mtime[1:]).encode("utf-8")

                # Optional field: Mode
                if self._protocol_features & YMODEM.USE_MODE_FIELD:
                    if Platform.is_Linux():
                        data += (" " + oct(0x8000)).encode("utf-8")
                    else:
                        data += (" 0").encode("utf-8")

                # Optional field: Serial Number
                if self._protocol_features & YMODEM.USE_SN_FIELD:
                    data += (" 0").encode("utf-8")

                data = data.ljust(self._packet_size, b"\x00")
                checksum = self._make_send_checksum(crc_mode, data)
                
                error_count = 0
                while True:
                    # Blocking may occur here, the writer needs to have a timeout mechanism
                    self.write(header + data + checksum)
                    self.logger.debug("[Sender]: Info packet sent")

                    # Blocking may occur here, the reader needs to have a timeout mechanism
                    char = self.read(1, timeout)
                    if char == ACK:
                        error_count = 0
                        break
                    else:
                        error_count += 1
                        self.logger.debug("[Sender]: No valid data read.")

                    if error_count > retry:
                        self.abort(timeout = timeout)
                        if stream:
                            stream.close()
                        self.logger.debug(f"[Sender]: Aborted, the number of errors has reached {retry}.")
                        return False

            '''
            Data packet
            '''
            crc_mode = 0
            cancel_count = 0
            error_count = 0
            while True:
                # Blocking may occur here, the reader needs to have a timeout mechanism
                char = self.read(1, timeout)

                if char == NAK:
                    crc_mode = 0
                    self.logger.debug("[Sender]: Received checksum request (NAK).")
                    break
                elif char == CRC:
                    crc_mode = 1
                    self.logger.debug("[Sender]: Received CRC request (C/CRC).")
                    break
                elif char == CAN:
                    if cancel_count == 0:
                        cancel_count += 1
                    else:
                        self.logger.debug("[Sender]: Cancel transfer (CAN).")
                        return False
                else:
                    self.logger.debug("[Sender]: No valid data read.")

                error_count += 1
                if error_count > retry:
                    self.abort(timeout = timeout)
                    if stream:
                        stream.close()
                    self.logger.debug(f"[Sender]: Aborted, the number of errors has reached {retry}.")
                    return False

            sequence = 1
            total_packet_count = math.ceil(task.total / self._packet_size)
            success_packet_count = 0
            error_packet_count = 0
            while True:
                try:
                    data = stream.read(self._packet_size)
                except Exception as e:
                    stream.close()
                    self.logger.debug("[Sender]: Failed to read file.")
                    return False

                if not data:
                    self.logger.debug("[Sender]: Reached EOF")
                    break

                header = self._make_send_header(self._packet_size, sequence)
                # fill with 1AH(^z)
                data = data.ljust(self._packet_size, b"\x1a")
                checksum = self._make_send_checksum(crc_mode, data)

                while True:
                    # Blocking may occur here, the writer needs to have a timeout mechanism
                    self.write(header + data + checksum)
                    self.logger.debug(f"[Sender]: Packet {sequence} sent.")

                    # Blocking may occur here, the reader needs to have a timeout mechanism
                    char = self.read(1, timeout)
                    if char == ACK:
                        success_packet_count += 1

                        if callable(callback):
                            callback(task_index, task.name, total_packet_count, success_packet_count, error_packet_count)

                        error_packet_count = 0
                        break
                    else:
                        error_packet_count += 1
                        self.logger.debug(f"[Sender]: Ready to resend packet {sequence}.")

                        if callable(callback):
                            callback(task_index, task.name, total_packet_count, success_packet_count, error_packet_count)

                        if error_packet_count > retry:
                            self.abort(timeout=timeout)
                            if stream:
                                stream.close()
                            self.logger.debug(f"[Sender]: Aborted, the number of errors has reached {retry}.")
                            return False

                sequence = (sequence + 1) % 0x100

            self.logger.debug("[Sender]: %d of %d - %s completed.", task_index+1, len(tasks), task.name)

            '''
            EOT 
            '''
            self.write(EOT)
            self.logger.debug("[Sender]: EOT sent.")

            char = self.read(1, timeout)
            if char != ACK:
                self.write(EOT)
                self.logger.debug("[Sender]: EOT resent.")

                while True:
                    char = self.read(1, timeout)
                    if char == ACK:
                        break
                    else:
                        error_count += 1
                        self.logger.debug("[Sender]: No valid data read.")

                    if error_count > retry:
                        self.abort(timeout = timeout)
                        if stream:
                            stream.close()
                        self.logger.debug(f"[Sender]: Aborted, the number of errors has reached {retry}.")
                        return False

        if stream:
            stream.close()

        '''
        batch end packet
        '''
        header = self._make_send_header(self._packet_size, 0)
        data = bytearray().ljust(self._packet_size, b"\x00")
        checksum = self._make_send_checksum(crc_mode, data)
        self.write(header + data + checksum)
        self.logger.debug("[Sender]: Batch end packet sent.")

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
            crc = calc_crc(data)
            _bytes.extend([crc >> 8, crc & 0xff])
        else:
            crc = calc_checksum(data)
            _bytes.append(crc)
        return bytearray(_bytes)

    def recv(self, 
             path: str, 
             crc_mode: int = 1, 
             retry: int = 10, 
             timeout: float = 10, 
             delay: float = 1, 
             callback: Optional[Callable[[int, str, int, int, int], None]] = None
             ) -> bool:

        # task index
        task_index = -1

        while True:

            task = _ModemFile()
            
            '''
            Parse info packet
            '''
            if self.protocol_type == ProtocolType.YMODEM:

                char = 0
                cancel_count = 0
                error_count = 0
                while True:
                    if error_count >= retry:
                        self.abort(timeout = timeout)
                        self.logger.debug(f"[Receiver]: Aborted, the number of errors has reached {retry}.")
                        return False
                    elif crc_mode and error_count < (retry // 2):
                        if not self.write(CRC):
                            time.sleep(delay)
                            error_count += 1
                            self.logger.debug(f"[Receiver]: Failed to write CRC, sleep for {delay}s.")
                    else:
                        crc_mode = 0
                        if not self.write(NAK):
                            time.sleep(delay)
                            error_count += 1
                            self.logger.debug(f"[Receiver]: Failed to write NAK, sleep for {delay}s")

                    char = self.read(1, timeout = 3)
                    if char == SOH or char == STX:
                        break
                    elif char == CAN:
                        if cancel_count == 0:
                            cancel_count += 1
                        else:
                            self.logger.debug("[Receiver]: Cancel transfer (CAN).")
                            return False
                    else:
                        error_count += 1
                        self.logger.debug("[Receiver]: No valid data received.")

                packet_size = 128
                cancel_count = 0
                error_count = 0
                while True:
                    while True:
                        if char == SOH:
                            packet_size = 128
                            self.logger.debug("[Receiver]: Set 128 bytes as packet size.")
                            break
                        elif char == STX:
                            packet_size = 1024
                            self.logger.debug("[Receiver]: Set 1024 bytes as packet size.")
                            break
                        elif char == CAN:
                            if cancel_count == 0:
                                cancel_count += 1
                            else:
                                self.logger.debug("[Receiver]: Cancel transfer (CAN).")
                                return False
                        else:
                            error_count += 1
                            self.logger.debug("[Receiver]: No valid data received.")

                        if error_count > retry:
                            self.abort(timeout = timeout)
                            self.logger.debug(f"[Receiver]: Aborted, the number of errors has reached {retry}.")
                            return False

                    error_count = 0
                    seq1 = self.read(1, timeout)
                    if seq1:
                        seq1 = ord(seq1)
                        seq2 = self.read(1, timeout)
                        if seq2:
                            seq2 = 0xff - ord(seq2)
                    else:
                        seq2 = None

                    if not (seq1 == seq2 == 0):
                        self.logger.debug("[Receiver]: Expected seq 0 but got (seq1 %r, seq2 %r).", seq1, seq2)
                        # skip this packet
                        self.read(packet_size + 1 + crc_mode)
                        self.logger.debug("[Receiver]: Dropped the broken packet.")
                    else:
                        data = self.read(packet_size + 1 + crc_mode, timeout)

                        if data and len(data) == (packet_size + 1 + crc_mode):
                            valid, data = self._verify_recv_checksum(crc_mode, data)

                            if valid:

                                file_name = bytes.decode(data.split(b"\x00")[0], "utf-8")
                                
                                # batch end packet received
                                if not file_name:
                                    self.logger.debug("[Receiver]: Received batch end packet.")
                                    self.write(ACK)
                                    return True

                                # info packet received
                                else:
                                    self.logger.debug("[Receiver]: Received info packet.")

                                task_index += 1
                                task.name = file_name
                                self.logger.debug(f"[Receiver]: File - {task.name}")

                                data = bytes.decode(data.split(b"\x00")[1], "utf-8")

                                if self._protocol_features & YMODEM.USE_LENGTH_FIELD:
                                    space_index = data.find(" ")
                                    task.total = int(data if space_index == -1 else data[:space_index])
                                    self.logger.debug(f"[Receiver]: Size - {task.total} bytes")
                                    data = data[space_index + 1:]

                                if self._protocol_features & YMODEM.USE_DATE_FIELD:
                                    space_index = data.find(" ")
                                    task.mtime = int(data if space_index == -1 else data[:space_index], 8)
                                    self.logger.debug(f"[Receiver]: Mtime - {task.mtime} seconds")
                                    data = data[space_index + 1:]

                                if self._protocol_features & YMODEM.USE_MODE_FIELD:
                                    space_index = data.find(" ")
                                    task.mode = int(data if space_index == -1 else data[:space_index])
                                    self.logger.debug(f"[Receiver]: Mode - {task.mode}")
                                    data = data[space_index + 1:]

                                if self._protocol_features & YMODEM.USE_SN_FIELD:
                                    space_index = data.find(" ")
                                    task.sn = int(data if space_index == -1 else data[:space_index])
                                    self.logger.debug(f"[Receiver]: SN - {task.sn}")

                                self.write(ACK)
                                break

                            # broken packet
                            else:
                                pass
                        
                        # bad read
                        else:
                            pass

                    # Receive failed handler: ask for retransmission
                    while True:
                        if not self.read(1, timeout=1):
                            break
                    self.write(NAK)
                    self.logger.debug("[Receiver]: Requesting retransmission (NAK).")

                    char = self.read(1, timeout)

            # create file in saving folder
            p = os.path.join(path, task.name)
            try:
                stream = open(p, "wb+")
            except IOError:
                self.logger.debug(f"[Receiver]: Cannot open the save path: {p}.")
                return False

            '''
            Parse data packet
            '''
            char = 0
            cancel_count = 0
            error_count = 0
            while True:
                if error_count >= retry:
                    self.abort(timeout=timeout)
                    if stream:
                        stream.close()
                    self.logger.debug(f"[Receiver]: Aborted, the number of errors has reached {retry}.")
                    return False
                elif crc_mode and error_count < (retry // 2):
                    if not self.write(CRC):
                        self.logger.debug(f"[Receiver]: Failed to write CRC, sleep for {retry}s.")
                        time.sleep(delay)
                        error_count += 1
                else:
                    crc_mode = 0
                    if not self.write(NAK):
                        self.logger.debug(f"[Receiver]: Failed to write NAK, sleep for {delay}s.")
                        time.sleep(delay)
                        error_count += 1

                char = self.read(1, timeout=3)
                if char == SOH or char == STX:
                    break
                elif char == CAN:
                    if cancel_count == 0:
                        cancel_count += 1
                    else:
                        self.logger.debug("[Receiver]: Cancel transfer (CAN).")
                        return False
                else:
                    error_count += 1
                    self.logger.debug("[Receiver]: No valid data read.")
                    
            
            eot_received = False
            packet_size = 128
            sequence = 1
            cancel_count = 0
            error_count = 0
            success_packet_count = 0
            error_packet_count = 0
            while True:
                while True:
                    if char == SOH:
                        packet_size = 128
                        self.logger.debug("[Receiver]: Set 128 bytes as packet size.")
                        break
                    elif char == STX:
                        packet_size = 1024
                        self.logger.debug("[Receiver]: Set 1024 bytes as packet size.")
                        break
                    elif char == EOT:
                        self.write(ACK)
                        eot_received = True
                        self.logger.debug("[Receiver]: %d - %s completed.", task_index+1, task.name)
                        break
                    elif char == CAN:
                        if cancel_count == 0:
                            cancel_count += 1
                        else:
                            if stream:
                                stream.close()
                            self.logger.debug(f"[Receiver]: Cancel transfer (CAN) at data packet {success_packet_count} (seq {sequence}).")
                            return False           
                    else:
                        error_count += 1
                        self.logger.debug("[Receiver]: No valid data received.")

                    if error_count > retry:
                        self.abort(timeout=timeout)
                        if stream:
                            stream.close()
                        self.logger.debug(f"[Receiver]: Aborted, the number of errors has reached {retry}.")
                        return False
                
                if eot_received:
                    break

                total_packet_count = math.ceil(task.total / packet_size)

                seq1 = self.read(1, timeout)
                if seq1:
                    seq1 = ord(seq1)
                    seq2 = self.read(1, timeout)
                    if seq2:
                        seq2 = 0xff - ord(seq2)
                else:
                    seq2 = None

                # Packet received in wrong number
                if not (seq1 == seq2 == sequence):
                    self.logger.debug("[Receiver]: Expected seq %d but got (seq1 %r, seq2 %r).", sequence, seq1, seq2)
                    # skip this packet
                    self.read(packet_size + 1 + crc_mode)
                    self.logger.debug("[Receiver]: Dropped the broken packet.")
                
                # Packet received
                else:
                    data = self.read(packet_size + 1 + crc_mode, timeout)

                    if data and len(data) == (packet_size + 1 + crc_mode):
                        valid, data = self._verify_recv_checksum(crc_mode, data)

                        # Write the original data to the target file
                        if valid:
                            success_packet_count += 1
                            self.logger.debug(f"[Receiver]: Received data packet {sequence}.")

                            valid_length = packet_size

                            # The last package adjusts the valid data length according to the file length
                            remaining_length = task.total - task.received
                            if (remaining_length > 0):
                                valid_length = min(valid_length, remaining_length)
                            data = data[:valid_length]

                            task.received += len(data)

                            try:
                                stream.write(data)
                            except Exception as e:
                                stream.close()
                                self.logger.debug(f"[Receiver]: Failed to write data packet {sequence} to file.")
                                return False

                            self.logger.debug(f"[Receiver]: Successfully write data packet {sequence} to file.")

                            if callable(callback):
                                callback(task_index, task.name, total_packet_count, success_packet_count, error_packet_count)

                            self.write(ACK)

                            sequence = (sequence + 1) % 0x100
                            char = self.read(1, timeout)
                            continue

                        # broken packet
                        else:
                            error_packet_count += 1
                            self.logger.debug("[Receiver]: Received broken data packet.")

                            if callable(callback):
                                callback(task_index, task.name, total_packet_count, success_packet_count, error_packet_count)

                    # bad read
                    else:
                        pass

                # Receive failed handler: ask for retransmission
                while True:
                    if not self.read(1, timeout = 1):
                        break
                self.write(NAK)
                self.logger.debug("[Receiver]: Requested retransmission (NAK).")

                char = self.read(1, timeout)

            if stream:
                stream.close()
        

    def _verify_recv_checksum(self, crc_mode, data):
        if crc_mode:
            _checksum = bytearray(data[-2:])
            remote_sum = (_checksum[0] << 8) + _checksum[1]
            data = data[:-2]

            local_sum = calc_crc(data)
            valid = bool(remote_sum == local_sum)
            if not valid:
                self.logger.debug("[Receiver]: CRC verification failed. Sender: %04x, Receiver: %04x.", remote_sum, local_sum)
        else:
            _checksum = bytearray([data[-1]])
            remote_sum = _checksum[0]
            data = data[:-1]

            local_sum = calc_checksum(data)
            valid = remote_sum == local_sum
            if not valid:
                self.logger.debug("[Receiver]: CRC verification failed. Sender: %02x, Receiver: %02x.", remote_sum, local_sum)
        return valid, data
    

class _ModemFile:
    def __init__(self, path: Optional[str] = None):
        self._path = path or ""
        self._name = os.path.basename(path) if path else ""
        self._total_length = os.path.getsize(path) if path else 0
        self._mtime = os.path.getmtime(path) if path else 0
        self._received_length = 0
        self._mode = 0
        self._sn = 0

    @property
    def path(self) -> str:
        return self._path

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, v: str):
        self._name = v

    @property
    def total(self) -> int:
        return self._total_length
    
    @total.setter
    def total(self, v: int):
        self._total_length = v

    @property
    def received(self) -> int:
        return self._received_length
    
    @received.setter
    def received(self, v: int):
        self._received_length = v

    @property
    def mtime(self) -> int:
        return self._mtime
    
    @mtime.setter
    def mtime(self, v: int):
        self._mtime = v

    @property
    def mode(self) -> int:
        return self._mode
    
    @mode.setter
    def mode(self, v: int):
        self._mode = v

    @property
    def sn(self) -> int:
        return self._sn
    
    @sn.setter
    def sn(self, v: int):
        self._sn = v


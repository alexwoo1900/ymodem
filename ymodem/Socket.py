from abc import ABC, abstractmethod
import logging
import math
import os
import time
from typing import Any, Callable, List, Optional, Union

from ymodem.CRC import calc_crc16, calc_checksum
from ymodem.Platform import Platform
from ymodem.Protocol import ProtocolType, ProtocolSubType, ProtocolStyleManagement, XMODEM, YMODEM

ACK = b'\x06'
CAN = b'\x18'
CRC = b'\x43'
EOT = b'\x04'
G   = b'\x67'
NAK = b'\x15'
SOH = b'\x01'
STX = b'\x02'

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
                 protocol_type_options: List[str] = [],
                 packet_size: int = 1024,
                 style_id: int = _psm.get_available_styles()[2]):

        self.logger = logging.getLogger('ModemSocket')

        self._read = read
        self._write = write
        self.set_protocol(protocol_type, protocol_type_options, style_id, packet_size)
        
    '''
    7.3.2 Receive_Program_Considerations

    Once into a receiving a block, the receiver goes into a one-second timeout
    for each character and the checksum.
    '''
    def read(self, size: int, timeout: float = 1) -> Any:
        try:
            return self._read(size, timeout)
        except Exception:
            self.logger.warning("[Modem]: Read timeout!")
            return None
    
    def write(self, data: Union[bytes, bytearray], timeout: float = 1) -> Any:
        try:
            return self._write(data, timeout)
        except Exception:
            self.logger.warning("[Modem]: Write timeout!")
            return None
    
    def set_protocol(self, 
                     protocol_type: int, 
                     protocol_type_options: List[str], 
                     style_id: int, 
                     packet_size: int):
        if protocol_type not in ProtocolType.all():
            raise ValueError(f"Invalid mode specified: {protocol_type}")
        
        self.protocol_type = protocol_type

        if style_id not in _psm.get_available_styles():
            raise ValueError(f"Invalid style specified: {style_id}")        
        style = _psm.get_available_style(style_id)

        self._protocol_features = style.get_protocol_features(self.protocol_type)

        if packet_size not in [128, 1024]:
            raise ValueError(f"Invalid packet size specified: {packet_size}")
        self._packet_size = packet_size
        if (self._protocol_features & XMODEM.ALLOW_1K_PACKET) == 0:
            self._packet_size = 128
        
        if self.protocol_type == ProtocolType.YMODEM:
            if 'g' in protocol_type_options and (self._protocol_features & YMODEM.ALLOW_YMODEM_G) != 0:
                self.protocol_subtype = ProtocolSubType.YMODEM_G_FILE_TRANSMISSION
            else:
                self.protocol_subtype = ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION
    
    def send(self, 
             paths: List[str], 
             callback: Optional[Callable[[int, str, int, int], None]] = None
             ) -> bool:
        '''
        Send files

        param paths: List of file paths to be sent
        param retry: Number of retries when communication error occur
        param timeout: read/write timeout
        param callback: 
        '''
        # XYMODEM process
        if self.protocol_type == ProtocolType.XMODEM or self.protocol_type == ProtocolType.YMODEM:

            tasks = []      # type: List[_TransmissionTask]
            stream = None   # type: BufferedReader

            # XMODEM and XMODEM_1K only supports single file transfer
            if self.protocol_type == ProtocolType.XMODEM:
                if len(paths) > 0:
                    paths = paths[:1]

            #############################################################################################
            #
            #                                 XYMODEM common processing
            #
            #############################################################################################
            for path in paths:
                if os.path.isfile(path):
                    tasks.append(_TransmissionTask(path))

            for task_index, task in enumerate(tasks):

                try:
                    stream = open(task.path, "rb")
                except IOError:
                    self.logger.error(f"[Sender]: Cannot open the file: {task.path}, skip.")
                    continue

                if self.protocol_type == ProtocolType.YMODEM:
                    '''
                    7.3.3 Sending_program_considerations

                    While waiting for transmission to begin, the sender has only a single very
                    long timeout, say one minute.
                    '''

                    c = self._read_and_wait([NAK, CRC, G, CAN], 60)

                    if c:
                        if c == CAN:
                            self.logger.debug("[Sender]: <- CAN")
                            self.logger.warning("[Sender]: Received a request from the Receiver to cancel the transmission, exit.")
                            if stream:
                                stream.close()
                            return True
                    else:
                        self.logger.error("[Sender]: Waiting for command from Receiver has timed out, abort and exit!")
                        self._abort()
                        self.logger.debug("[Sender]: CAN ->")
                        if stream:
                            stream.close()
                        return False
                    
                    if c == NAK:
                        self.logger.debug("[Sender]: <- NAK")
                        crc = 0
                    else:
                        self.logger.debug("[Sender]: <- CRC / G")
                        crc = 1
                    
                    header = self._make_send_header(self._packet_size, 0)
                    self.logger.debug(f"[Sender]: {'SOH' if self._packet_size == 128 else 'STX'} ->")

                    '''
                    Pathname 
                    
                    The pathname (conventionally, the file name) is sent as a null
                    terminated ASCII string. This is the filename format used by the
                    handle oriented MSDOS(TM) functions and C library fopen functions.
                    An assembly language example follows:
                    DB 'foo.bar',0
                    No spaces are included in the pathname. Normally only the file name
                    stem (no directory prefix) is transmitted unless the sender has
                    selected YAM's f option to send the full pathname. The source drive
                    (A:, B:, etc.) is not sent.
                    '''
                    # Python's handling is case compatible
                    data = task.name.encode("utf-8")
                    
                    '''
                    Length 

                    The file length and each of the succeeding fields are optional.[3]
                    The length field is stored in the block as a decimal string counting
                    the number of data bytes in the file. The file length does not
                    include any CPMEOF (^Z) or other garbage characters used to pad the
                    last block.
                    If the file being transmitted is growing during transmission, the
                    length field should be set to at least the final expected file
                    length, or not sent.
                    The receiver stores the specified number of characters, discarding
                    any padding added by the sender to fill up the last block.
                    '''
                    if self._protocol_features & YMODEM.USE_LENGTH_FIELD:
                        data += bytes(1)
                        data += str(task.total).encode("utf-8")

                    '''
                    Modification 
                    
                    Date The mod date is optional, and the filename and length
                    may be sent without requiring the mod date to be sent.
                    If the modification date is sent, a single space separates the
                    modification date from the file length.
                    The mod date is sent as an octal number giving the time the contents
                    of the file were last changed, measured in seconds from Jan 1 1970
                    Universal Coordinated Time (GMT). A date of 0 implies the
                    modification date is unknown and should be left as the date the file
                    is received.
                    This standard format was chosen to eliminate ambiguities arising from
                    transfers between different time zones.
                    '''
                    # Python 2+: 0123456
                    # Python 3+: 0o123456
                    if self._protocol_features & YMODEM.USE_DATE_FIELD:
                        mtime = oct(int(task.mtime))
                        if mtime.startswith("0o"):
                            data += (" " + mtime[2:]).encode("utf-8")
                        else:
                            data += (" " + mtime[1:]).encode("utf-8")

                    '''
                    Mode 

                    If the file mode is sent, a single space separates the file mode
                    from the modification date. The file mode is stored as an octal
                    string. Unless the file originated from a Unix system, the file mode
                    is set to 0. rb(1) checks the file mode for the 0x8000 bit which
                    indicates a Unix type regular file. Files with the 0x8000 bit set
                    are assumed to have been sent from another Unix (or similar) system
                    which uses the same file conventions. Such files are not translated
                    in any way.
                    '''
                    if self._protocol_features & YMODEM.USE_MODE_FIELD:
                        if Platform.is_Linux():
                            data += (" " + oct(0x8000)).encode("utf-8")
                        else:
                            data += (" 0").encode("utf-8")

                    '''
                    Serial Number 
                    
                    If the serial number is sent, a single space separates the
                    serial number from the file mode. The serial number of the
                    transmitting program is stored as an octal string. Programs which do
                    not have a serial number should omit this field, or set it to 0. The
                    receiver's use of this field is optional.
                    '''
                    # This program does not set serial number
                    if self._protocol_features & YMODEM.USE_SN_FIELD:
                        data += (" 0").encode("utf-8")

                    data = data.ljust(self._packet_size, b"\x00")
                    checksum = self._make_send_checksum(crc, data)
                    
                    retries = 0
                    while True:
                        if self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                            if retries < 10:
                                self.write(header + data + checksum)
                                self.logger.debug("[Sender]: Filename packet ->")

                                '''
                                7.3.3 Sending_program_considerations

                                In the current protocol, the sender has a
                                10 second timeout before retrying. I suggest NOT doing this, and letting
                                the protocol be completely receiver-driven. This will be compatible with
                                existing programs.
                                '''
                                # expect for ACK and NAK, but only distinguish between ack and other characters
                                c = self._read_and_wait([ACK])
                                if c:
                                    self.logger.debug("[Sender]: <- ACK")
                                    break
                                else:
                                    self.logger.warning("[Sender]: No ACK from Receiver, preparing to retransmit.")
                                    retries += 1
                            else:
                                self.logger.error("[Sender]: The number of retransmissions has reached the maximum limit, abort and exit!")
                                self._abort()
                                self.logger.debug("[Sender]: CAN ->")
                                if stream:
                                    stream.close()
                                return False
                        # self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION
                        else:
                            self.write(header + data + checksum)
                            self.logger.debug("[Sender]: Filename packet ->")
                            break

                #############################################################################################
                #
                #                                 XYMODEM common processing
                #
                #############################################################################################
                           
                c = self._read_and_wait([NAK, CRC, G, CAN], 60)

                if c:
                    if c == CAN:
                        self.logger.debug("[Sender]: <- CAN")
                        self.logger.warning("[Sender]: Received a request from the Receiver to cancel the transmission, exit.")
                        if stream:
                            stream.close()
                        return True
                else:
                    self.logger.error("[Sender]: Waiting for command from Receiver has timed out, abort and exit!")
                    self._abort()
                    self.logger.debug("[Sender]: CAN ->")
                    if stream:
                        stream.close()
                    return True
                
                if c == NAK:
                    self.logger.debug("[Sender]: <- NAK")
                    crc = 0
                else:
                    self.logger.debug("[Sender]: <- CRC / G")
                    crc = 1

                sequence = 1
                task.success_packet_count = 0
                while True:
                    try:
                        data = stream.read(self._packet_size)
                    except Exception:
                        self.logger.error("[Sender]: Failed to read file, abort and exit!")
                        self._abort()
                        self.logger.debug("[Sender]: CAN ->")
                        if stream:
                            stream.close()
                        return False

                    if not data:
                        self.logger.debug("[Sender]: Reached EOF")
                        if stream:
                            stream.close()
                        break

                    header = self._make_send_header(self._packet_size, sequence)
                    self.logger.debug(f"[Sender]: {'SOH' if self._packet_size == 128 else 'STX'} ->")
                    # fill with 1AH(^z)
                    data_length = len(data)
                    data = data.ljust(self._packet_size, b"\x1a")
                    checksum = self._make_send_checksum(crc, data)

                    retries = 0
                    while True:
                        if self.protocol_type == ProtocolType.XMODEM or self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                            if retries < 10:
                                self.write(header + data + checksum)
                                self.logger.debug(f"[Sender]: Data packet {sequence} ->")

                                # expect for ACK and NAK, but only distinguish between ack and other characters
                                c = self._read_and_wait([ACK])
                                if c:
                                    self.logger.debug("[Sender]: <- ACK")
                                    task.sent += data_length
                                    task.success_packet_count += 1
                                    if callable(callback):
                                        callback(task_index, task.name, task.total, task.sent)
                                    break
                                else:
                                    self.logger.warning("[Sender]: No ACK from Receiver, preparing to retransmit.")
                                    retries += 1
                            else:
                                self.logger.error("[Sender]: The number of retransmissions has reached the maximum limit, abort and exit!")
                                self._abort()
                                self.logger.debug("[Sender]: CAN ->")
                                if stream:
                                    stream.close()
                                return False
                        # self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION
                        else:
                            self.write(header + data + checksum)
                            self.logger.debug(f"[Sender]: Data packet {sequence} ->")
                            task.sent += self._packet_size
                            task.success_packet_count += 1
                            if callable(callback):
                                callback(task_index, task.name, task.total, task.sent)
                            # 500 microseconds, high success rate delay
                            # self._delay(0.0005)
                            break

                    sequence = (sequence + 1) % 256

                '''
                2. YMODEM MINIMUM REQUIREMENTS

                + At the end of each file, the sending program shall send EOT up to ten
                times until it receives an ACK character. (This is part of the
                XMODEM spec.)

                7.3.3 Sending_program_considerations

                When the sender has no more data, it sends an <eot>, and awaits an <ack>,
                resending the <eot> if it doesn't get one. Again, the protocol could be
                receiver-driven, with the sender only having the high-level 1-minute
                timeout to abort.
                '''
                retries = 0
                while True:
                    if retries < 10:
                        c = self._write_and_wait(EOT, [ACK])
                        self.logger.debug("[Sender]: EOT ->")

                        if c:
                            self.logger.debug("[Sender]: <- ACK")
                            break
                        else:
                            self.logger.warning("[Sender]: No ACK from Receiver, preparing to retransmit.")
                            retries += 1
                    else:
                        self.logger.error("[Sender]: The number of retransmissions has reached the maximum limit, abort and exit!")
                        self._abort()
                        return False
                    
            '''
            5. YMODEM Batch File Transmission

            Transmission of a null pathname terminates batch file transmission.
            '''

            if self.protocol_type == ProtocolType.YMODEM:
                header = self._make_send_header(self._packet_size, 0)
                data = bytearray().ljust(self._packet_size, b"\x00")
                checksum = self._make_send_checksum(crc, data)
                self.write(header + data + checksum)
                self.logger.debug("[Sender]: Batch end packet ->")

            return True

    def recv(self, 
             path: str, 
             callback: Optional[Callable[[int, str, int, int], None]] = None
             ) -> bool:

        # XYMODEM process
        if self.protocol_type == ProtocolType.XMODEM or self.protocol_type == ProtocolType.YMODEM:

            # task index
            task_index = -1

            while True:

                task = _TransmissionTask()
                
                if self.protocol_type == ProtocolType.YMODEM:
                    '''
                    5. YMODEM Batch File Transmission

                    As in the case of single a file transfer, the receiver initiates batch
                    file transmission by sending a "C" character (for CRC-16).

                    7.3.2 Receive_Program_Considerations

                    The receiver has a 10-second timeout. It sends a <nak> every time it
                    times out. The receiver's first timeout, which sends a <nak>, signals the
                    transmitter to start. Optionally, the receiver could send a <nak>
                    immediately, in case the sender was ready. This would save the initial 10
                    second timeout. However, the receiver MUST continue to timeout every 10
                    seconds in case the sender wasn't ready.
                    '''
                    for _ in range(10):
                        if self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                            c = self._write_and_wait(CRC, [SOH, STX, CAN], 10)
                            self.logger.debug("[Receiver]: CRC ->")
                        # self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION:
                        else:
                            c = self._write_and_wait(G, [SOH, STX, CAN], 10)
                            self.logger.debug("[Receiver]: G ->")
                        if c:
                            break

                    retries = 0
                    while True:
                        if c:
                            if c == CAN:
                                self.logger.debug("[Receiver]: <- CAN")
                                self.logger.warning("[Receiver]: Received a request from the Sender to cancel the transmission, exit.")
                                return True
                            else:
                                pass
                        else:
                            self.logger.error("[Receiver]: Waiting for response from Sender has timed out, abort and exit!")
                            self._abort()
                            self.logger.debug("[Receiver]: CAN ->")
                            return False
                        
                        if c == SOH:
                            self.logger.debug("[Receiver]: <- SOH")
                            packet_size = 128
                        else: 
                            self.logger.debug("[Receiver]: <- STX")
                            packet_size = 1024

                        seq1 = self.read(1)
                        if seq1:
                            seq1 = ord(seq1)
                            seq2 = self.read(1)
                            if seq2:
                                seq2 = 0xff - ord(seq2)
                        else:
                            seq2 = None

                        received = False

                        if seq1 == seq2 == 0:
                            data = self.read(packet_size + 2)

                            if data and len(data) == (packet_size + 2):
                                
                                valid, data = self._verify_recv_checksum(1, data)

                                if valid:

                                    file_name = bytes.decode(data.split(b"\x00")[0], "utf-8")
                                    
                                    # batch end packet received
                                    if not file_name:
                                        self.logger.debug("[Receiver]: <- Batch end packet")
                                        if self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                                            self.write(ACK)
                                            self.logger.debug("[Receiver]: ACK ->")
                                        return True

                                    # filename packet received
                                    else:
                                        self.logger.debug("[Receiver]: <- Filename packet.")

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

                                    received = True

                                # broken packet
                                else:
                                    self.logger.warning("[Receiver]: Checksum failed.")
                            
                            # timeout received data
                            else:
                                self.logger.warning("[Receiver]: Received data timed out.")

                        # invalid header: wrong sequence
                        else:
                            # skip this packet
                            self.logger.warning("[Receiver]: Wrong sequence, drop the whole packet.")
                            self.read(packet_size + 2)

                        '''
                        5. YMODEM Batch File Transmission

                        If the filename block is received with a CRC or other error, a
                        retransmission is requested. After the filename block has been received,
                        it is ACK'ed if the write open is successful. If the file cannot be
                        opened for writing, the receiver cancels the transfer with CAN characters
                        as described above.
                        '''
                        if self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION and not received:
                            '''
                            7.3.1 Common_to_Both_Sender_and_Receiver

                            All errors are retried 10 times.
                            '''
                            if retries < 10:
                                self.logger.warning("[Receiver]: Send a request for retransmission.")

                                '''
                                7.4 Programming Tips
                                
                                + When the receiver wishes to <nak>, it should call a "PURGE"
                                subroutine, to wait for the line to clear. Recall the sender tosses
                                any characters in its UART buffer immediately upon completing sending
                                a block, to ensure no glitches were mis- interpreted.
                                '''
                                self._purge()
                                c = self._write_and_wait(NAK, [SOH, STX, CAN])
                                self.logger.debug("[Receiver]: NAK ->")
                                retries += 1
                            else:
                                self.logger.error("[Receiver]: The number of retransmissions has reached the maximum limit, abort and exit!")
                                self._abort()
                                self.logger.debug("[Receiver]: CAN ->")
                                return False
                        elif self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION and not received:
                            '''
                            If an error is detected in a YMODEM-g transfer, the receiver aborts the
                            transfer with the multiple CAN abort sequence.
                            '''
                            self.logger.error("[Receiver]: An error occurred during the transfer process using YMODEM_G, abort and exit!")
                            self._abort()
                            self.logger.debug("[Receiver]: CAN ->")
                            return False
                        else:
                            p = os.path.join(path, task.name)

                            '''
                            5. YMODEM Batch File Transmission

                            After the filename block has been received,
                            it is ACK'ed if the write open is successful. If the file cannot be
                            opened for writing, the receiver cancels the transfer with CAN characters
                            as described above.
                            '''
                            try:
                                stream = open(p, "wb+")
                                if self.protocol_type == ProtocolType.YMODEM:
                                    self.write(ACK)
                                    self.logger.debug("[Receiver]: ACK ->")
                                break
                            except IOError:
                                self.logger.error(f"[Receiver]: Cannot open the save path: {p}, abort and exit!")
                                self._abort()
                                self.logger.debug("[Receiver]: CAN ->")
                                if stream:
                                    stream.close()
                                return False

                #############################################################################################
                #
                #                                 XYMODEM common processing
                #
                #############################################################################################
                '''
                7.4 Programming Tips

                + The character-receive subroutine should be called with a parameter
                specifying the number of seconds to wait. The receiver should first
                call it with a time of 10, then <nak> and try again, 10 times.
                '''
                for _ in range(10):
                    if self.protocol_type == ProtocolType.XMODEM or self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                        c = self._write_and_wait(CRC, [SOH, STX, CAN], 10)
                        self.logger.debug("[Receiver]: CRC ->")
                    elif self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION:
                        c = self._write_and_wait(G, [SOH, STX, CAN], 10)
                        self.logger.debug("[Receiver]: G ->")
                    if c:
                        if c == CAN:
                            self.logger.debug("[Receiver]: <- CAN")
                            self.logger.warning("[Receiver]: Received a request from the Sender to cancel the transmission, exit.")
                            if stream:
                                stream.close()
                            return True
                        else:
                            # YMODEM enter here
                            crc = 1
                            break
                
                if (self.protocol_type == ProtocolType.XMODEM or self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION) and not c:
                    self.logger.warning("[Receiver]: No response in crc mode, try checksum mode...")
                    for _ in range(10):
                        c = self._write_and_wait(NAK, [SOH, STX, CAN], 10)
                        self.logger.debug(f"[Receiver]: received {c}")
                        if c:
                            if c == CAN:
                                self.logger.debug("[Receiver]: <- CAN")
                                self.logger.warning("[Receiver]: Received a request from the Sender to cancel the transmission, exit.")
                                if stream:
                                    stream.close()
                                return True
                            else:
                                crc = 0
                                break

                if not c:
                    self.logger.error("[Receiver]: No response in checksum mode, abort and exit!")
                    self._abort()
                    self.logger.debug("[Receiver]: CAN ->")
                    if stream:
                        stream.close()
                    return False

                retries = 0
                sequence = 1
                task.success_packet_count = 0
                while True:
                    if c == SOH:
                        self.logger.debug("[Receiver]: <- SOH")
                        packet_size = 128
                    elif c == STX: 
                        self.logger.debug("[Receiver]: <- STX")
                        packet_size = 1024
                    elif c == CAN:
                        self.logger.debug("[Receiver]: <- CAN")
                        if stream:
                            stream.close()
                        return True
                    elif c == EOT:
                        self.logger.debug("[Receiver]: <- EOT")
                        self.write(ACK)
                        self.logger.debug("[Receiver]: ACK ->")
                        if stream:
                            stream.close()
                        break

                    seq1 = self.read(1)
                    if seq1:
                        seq1 = ord(seq1)
                        seq2 = self.read(1)
                        if seq2:
                            seq2 = 0xff - ord(seq2)
                    else:
                        seq2 = None

                    '''
                    7.3.2 Receive_Program_Considerations
                    
                    Synchronizing: If a valid block number is received, it will be: 
                    1) the expected one, in which case everything is fine;
                    2) a repeat of the previously received block. This should be considered OK, 
                    and only indicates that the receivers <ack> got glitched, and the sender retransmitted; 
                    3) any other block number indicates a fatal loss of synchronization, such as the rare case
                    of the sender getting a line-glitch that looked like an <ack>. Abort the transmission, sending a <can>
                    '''

                    # default no confirm and no forward
                    received = False
                    forward = False

                    if (seq1 == seq2 == sequence):
                        data = self.read(packet_size + 1 + crc)

                        if data and len(data) == (packet_size + 1 + crc):

                            valid, data = self._verify_recv_checksum(crc, data)

                            # Write the original data to the target file
                            if valid:
                                self.logger.debug(f"[Receiver]: <- Data packet {sequence}")

                                valid_length = packet_size

                                '''
                                5. YMODEM Batch File Transmission

                                The receiver stores the specified number of characters, discarding
                                any padding added by the sender to fill up the last block.
                                '''
                                remaining_length = task.total - task.received
                                if (remaining_length > 0):
                                    valid_length = min(valid_length, remaining_length)
                                data = data[:valid_length]

                                task.received += len(data)
                                task.success_packet_count += 1

                                try:
                                    stream.write(data)
                                except Exception:
                                    self.logger.error(f"[Receiver]: Failed to write data packet {sequence} to file, abort and exit!")
                                    self._abort()
                                    self.logger.debug("[Receiver]: CAN ->")
                                    if stream:
                                        stream.close()
                                    return False

                                if callable(callback):
                                    callback(task_index, task.name, task.total, task.received)

                                # confirm and forward
                                received = True
                                forward = True

                            # broken packet
                            else:
                                self.logger.warning("[Receiver]: Checksum failed.")
                        
                        # timeout received data
                        else:
                            self.logger.warning("[Receiver]: Received data timed out.")

                    # invalid header: expired sequence
                    elif 0 <= seq1 <= task.success_packet_count:
                        self.logger.warning("[Receiver]: Expired sequence, drop the whole packet.")
                        self.read(packet_size + 1 + crc)

                        # confirm but no forward
                        received = True

                    # invalid header: wrong sequence
                    else:
                        # skip this packet
                        self.logger.warning("[Receiver]: Wrong sequence, drop the whole packet.")
                        self.read(packet_size + 1 + crc)

                    if (self.protocol_type == ProtocolType.XMODEM or self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION) and not received:
                        if retries < 10:
                            # retransmisstion
                            self.logger.warning("[Receiver]: Send a request for retransmission.")
                            self._purge()
                            c = self._write_and_wait(NAK, [SOH, STX, CAN])
                            self.logger.debug("[Receiver]: NAK ->")
                            retries += 1
                        else:
                            self.logger.error("[Receiver]: The number of retransmissions has reached the maximum limit, abort and exit!")
                            self._abort()
                            self.logger.debug("[Receiver]: CAN ->")
                            if stream:
                                stream.close()
                            return False
                    elif self.protocol_subtype == ProtocolSubType.YMODEM_G_FILE_TRANSMISSION and not received:
                        self.logger.error("[Receiver]: An error occurred during the transfer process using YMODEM_G, abort and exit!")
                        self._abort()
                        self.logger.debug("[Receiver]: CAN ->")
                        return False
                    else:
                        if forward:
                            sequence = (sequence + 1) % 0x100
                        if self.protocol_type == ProtocolType.XMODEM or self.protocol_subtype == ProtocolSubType.YMODEM_BATCH_FILE_TRANSMISSION:
                            c = self._write_and_wait(ACK, [SOH, STX, CAN, EOT])
                            self.logger.debug("[Receiver]: ACK ->")
                            retries = 0
                        else:
                            c = self._read_and_wait([SOH, STX, CAN, EOT])
                        

    def _abort(self) -> None:
        '''
        4.1 Graceful Abort
        The YAM and Professional-YAM X/YMODEM routines recognize a sequence of two
        consecutive CAN (Hex 18) characters without modem errors (overrun,
        framing, etc.) as a transfer abort command. This sequence is recognized
        when is waiting for the beginning of a block or for an acknowledgement to
        a block that has been sent. The check for two consecutive CAN characters
        reduces the number of transfers aborted by line hits. YAM sends eight CAN
        characters when it aborts an XMODEM, YMODEM, or ZMODEM protocol file
        transfer. Pro-YAM then sends eight backspaces to delete the CAN
        characters from the remote's keyboard input buffer, in case the remote had
        already aborted the transfer and was awaiting a keyboarded command.
        '''
        for _ in range(2):
            self.write(CAN)

    def _purge(self) -> None:
        while True:
            c = self.read(1)
            if not c:
                break

    def _delay(self, duration):
        start_time = time.perf_counter()
        while True:
            t = time.perf_counter() - start_time
            if t > duration:
                break

    def _read_and_wait(self, 
                        wait_chars: List[str],
                        wait_time: int = 1
                        ) -> Optional[str]:
        start_time = time.perf_counter()
        while True:
            t = time.perf_counter() - start_time
            if t > wait_time:
                return None
            c = self.read(1)
            if c in wait_chars:
                return c
    
    def _write_and_wait(self, 
                        write_char: str, 
                        wait_chars: List[str],
                        wait_time: int = 1
                        ) -> Optional[str]:
        start_time = time.perf_counter()
        self.write(write_char)
        while True:
            t = time.perf_counter() - start_time
            if t > wait_time:
                return None
            c = self.read(1)
            if c in wait_chars:
                return c
            
    def _make_send_header(self, packet_size, sequence):
        assert packet_size in (128, 1024), packet_size
        _bytes = []
        if packet_size == 128:
            _bytes.append(ord(SOH))
        elif packet_size == 1024:
            _bytes.append(ord(STX))
        _bytes.extend([sequence, 0xff - sequence])
        return bytearray(_bytes)

    def _make_send_checksum(self, crc, data):
        _bytes = []
        if crc:
            crc = calc_crc16(data)
            _bytes.extend([crc >> 8, crc & 0xff])
        else:
            crc = calc_checksum(data)
            _bytes.append(crc)
        return bytearray(_bytes)

    def _verify_recv_checksum(self, crc, data):
        if crc:
            _checksum = bytearray(data[-2:])
            remote_sum = (_checksum[0] << 8) + _checksum[1]
            data = data[:-2]

            local_sum = calc_crc16(data)
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
    

class _TransmissionTask:
    def __init__(self, path: Optional[str] = None):
        self._path = path or ""
        self._name = os.path.basename(path) if path else ""
        self._mtime = os.path.getmtime(path) if path else 0
        self._mode = 0
        self._sn = 0

        self._total_length = os.path.getsize(path) if path else 0
        self._sent_length = 0
        self._received_length = 0
        self._total_packet_count = -1
        self._success_packet_count = -1

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
    def sent(self) -> int:
        return self._sent_length
    
    @sent.setter
    def sent(self, v: int):
        self._sent_length = v

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

    @property
    def total_packet_count(self) -> int:
        return self._total_packet_count
    
    @total_packet_count.setter
    def total_packet_count(self, v: int):
        self._total_packet_count = v

    @property
    def success_packet_count(self) -> int:
        return self._success_packet_count
    
    @success_packet_count.setter
    def success_packet_count(self, v: int):
        self._success_packet_count = v

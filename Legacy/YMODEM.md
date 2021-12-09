# YMODEM Batch Transmission Protocol
YMODEM BatchTransmission Protocol(YMODEM Protocol) is based on XMODEM-1K Protocol and added batch transmisson feature.

## Symbol
In the following introduction, we will use some symbols to define special hex data.

Symbol | Hex
---|---
SOH | \x01 
STX | \x02 
EOT | \x04
ACK | \x06 
NAK | \x15 
CAN | \x18 

## Data Format
### Sender
#### File information package(First package)
Type | Seq | Seq-OC | File | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---|---
1 Byte | 1 Byte | 1 Byte | n Bytes | m Bytes | 1 Byte | 1 Byte 
SOH / STX | 00 | FF | | NUL\[m\] | | 

- Type: The size of raw data can be 128 bytes or 1024 bytes. SOH in Type column means the packet taking 128 bytes(including File and Data, n+m == 128) and STX for 1024 bytes
- Seq：Sequence number of packet, starting from 0
- Seq-OC：One's complement of sequence number
- File：The name of file for transporting
- Data: First packet's Data part is NUL. In complete version of YModem, the header of Data part will take the file size and the rest filling by NUL
- CRC-high8：16 bits CRC high-byte
- CRC-low8：16 bits CRC low-byte

#### File data package
Type | Seq | Seq-OC | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---
1 Byte | 1 Byte | 1 Byte | n Bytes | 1 Byte | 1 Byte 
SOH / STX |  |  | | | 

## Procedure
### Stage one: Preparing
Receiver send char 'C' to sender
```
Receiver->>Sender: Char 'C'
```

### Stage two: First packet
Sender received char 'C' from receiver and start to send first packet and expect ACK and 'C'.
After sender get ACK and 'C' from receiver, sender will send raw data of file.
```
Sender->>Receiver: Packet 0
Receiver->>Sender: ACK
Receiver->>Sender: Char 'C'
```

### Stage three: File packet
Sender send a file packet and expect ACK.
```
Sender->>Receiver: Packet 1
Receiver->>Sender: ACK
Sender->>Receiver: Packet 2
Receiver->>Sender: ACK
```

### Handling exception
If sender received NAK from receiver during Stage three, last packet will be resend constantly until ACK comming or exit. 
```
Sender->>Receiver: Packet 1
Receiver->>Sender: NAK
Sender->>Receiver: Packet 1
Receiver->>Sender: ACK
Sender->>Receiver: Packet 2
```
If sender received CAN() from receiver during Stage three, sender will stop packet sending and exit.
```
Sender->>Receiver: Packet 1
Receiver->>Sender: CAN
```

### Stage four: Finish
At the end of transmission, sender send EOT to receiver and expect NAK. After NAK arrived, sender send EOT immediately and expect ACK.
The ACK means the task was finish successfully.
```
Sender->>Receiver: EOT
Receiver->>Sender: NAK
Sender->>Receiver: EOT
Receiver->>Sender: ACK
Receiver->>Sender: Char 'C'
...(next round)
```
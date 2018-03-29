# YModem协议

## 协议说明
YModem协议有几种常用版本，包括带文件大小信息的版本（官方版本、超级终端版本）以及不带文件大小信息的版本（SecureCRT版本）。就实现而言大同小异，并不需要太仔细地划分类型。

## 名称说明
在后续的协议说明中，将会用一些约定的标记来代表特殊的单字节十六进制数据
Symbol | Hex
---|---|
SOH | \x01 |
STX | \x02 |
EOT | \x04 |
ACK | \x06 |
NAK | \x15 |
CAN | \x18 |

## 协议格式
### 发送方
#### 首个数据包结构
Type | Seq | Seq-OC | File | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---|---|
1 Byte | 1 Byte | 1 Byte | n Bytes | m Bytes | 1 Byte | 1 Byte |
SOH / STX | 00 | FF | | NUL\[m\] | | | 
- Type：YModem中传输的数据长度可以是128字节也可以是1024字节，当Type为SOH时表示本数据包携带的数据长度（File加Data的部分，即n+m==128或1024）为128字节，为STX时表示本数据包携带的数据长度（同前）为1024字节。
- Seq：数据包的序列号，从00开始（即首个数据包的Seq部分为00）
- Seq-OC：Seq的反码，由0xFF-Seq得出
- File：传输文件的文件名
- Data：首个数据包的Data部分为NUL，填充满除File部分外剩余的数据空间。在带文件大小信息的YModem版本中，在Data的头部会带上文件大小，然后再由NUL填充
- CRC-high8：16位CRC校验的高字节
- CRC-low8：16位CRC校验的低字节

#### 文件数据包结构
Type | Seq | Seq-OC | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---|---|
1 Byte | 1 Byte | 1 Byte | n Bytes | 1 Byte | 1 Byte |
SOH / STX |  |  | | | | | 
与首个数据包的结构有些微不同，正式传输文件内容时并不需要再带上File部分（文件名信息），数据部分的所有空间用来存放文件内容，CRC校验也是只校验数据部分。

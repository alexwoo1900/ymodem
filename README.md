# YModem for Python

## YModem协议的Python实现

### 项目介绍
本项目是基于tehmaze的XModem项目的YModem版本。除了遵从YModem协议外，还加入了超时处理机制。

### YModem API

send函数
```python
def send(self, stream, length, func, retry=8, callback=None)
```
- stream: 待传输数据流
- length：数据长度
- func：自定义函数，只有一个参数，为消息，用于处理内部提示消息
- retry: 传输数据出错时允许重试的次数，默认为8
- callback: 成功发送文件数据包时的回调函数，接收一个数据包总数与成功数据包总数，一般用于统计YModem传输效率。默认为空

### 如何使用该项目
1. 假设将ymodem.py放入protocol文件夹中，用以下语句将YModem类引入你的工程
```python
from protocol.ymodem import YModem
```

2. 定义自己的get函数与put函数（分别对应以下的getc和putc）,并创建YModem对象
```python
def getc(size):
    return parent.ser._serial.read(size) or None

def putc(data):
    return parent.ser._serial.write(data)

modem = YModem(getc, putc)
```
get函数：自定义函数，YModem对象内部通过它获取size个数据（size为get的唯一参数，但是在协议内部固定为1） \
put函数: 自定义函数，YModem对象内部通过它发送size个数据

3. 传输数据到另一端
```python
modem.send(stream, length, self.data_received_handler, 8, self.record_progress)
```

## YModem协议详解

### 协议说明
YModem协议有几种常用版本，包括带文件大小信息的版本（官方版本、超级终端版本）以及不带文件大小信息的版本（SecureCRT版本）。就实现而言大同小异，并不需要太仔细地划分类型。

### 名称说明
在后续的协议说明中，将会用一些约定的标记来代表特殊的单字节十六进制数据

Symbol | Hex
---|---
SOH | \x01 
STX | \x02 
EOT | \x04 
ACK | \x06 
NAK | \x15 
CAN | \x18 

### 协议格式
#### 发送方
##### 文件信息数据包结构（第一个数据包）
Type | Seq | Seq-OC | File | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---|---
1 Byte | 1 Byte | 1 Byte | n Bytes | m Bytes | 1 Byte | 1 Byte 
SOH / STX | 00 | FF | | NUL\[m\] | | 

- Type：YModem中传输的数据长度可以是128字节也可以是1024字节，当Type为SOH时表示本数据包携带的数据长度（File加Data的部分，即n+m==128或1024）为128字节，为STX时表示本数据包携带的数据长度（同前）为1024字节。
- Seq：数据包的序列号，从00开始（即首个数据包的Seq部分为00）
- Seq-OC：Seq的反码，由0xFF-Seq得出
- File：传输文件的文件名
- Data：首个数据包的Data部分为NUL，填充满除File部分外剩余的数据空间。在带文件大小信息的YModem版本中，在Data的头部会带上文件大小，然后再由NUL填充
- CRC-high8：16位CRC校验的高字节
- CRC-low8：16位CRC校验的低字节

##### 文件数据包结构
Type | Seq | Seq-OC | Data | CRC-high8 | CRC-low8
---|---|---|---|---|---
1 Byte | 1 Byte | 1 Byte | n Bytes | 1 Byte | 1 Byte 
SOH / STX |  |  | | | 

与文件信息数据包的结构有些微不同，正式传输文件内容时并不需要再带上File部分（文件名信息），数据部分的所有空间用来存放文件内容，CRC校验也是只校验数据部分。

### 协议流程
#### 阶段一、接收方等待数据接收
接收方给发送方不断地发送字符'C'，以期望收到发送方的ACK。
当收到发送方的ACK标记后立刻又发送字符'C'，随后进入待接收状态。
```
接收方->>发送方: Char 'C'
发送方->>接收方: ACK
接收方->>发送方: Char 'C'
```
#### 阶段二、首个数据包的发送及确认
发送方收到接收方发来的第二个'C'字符，开始发送首个数据包。等待接收方响应ACK标记，发送方收到ACK标记后则开始正式传输文件内容。
```
发送方->>接收方: Packet 0
接收方->>发送方: ACK
```

#### 阶段三、文件内容的传输及确认
发送方每发一个文件内容数据包，就期待接收方响应一个ACK标记，以继续发送下一个包。
```
发送方->>接收方: Packet 1
接收方->>发送方: ACK
发送方->>接收方: Packet 2
接收方->>发送方: ACK
```

#### 传输过程中的异常处理
若发送方发完数据包后收到了接收方NAK标记的响应，则重发此包，直到收到ACK响应或者超时退出。
```
发送方->>接收方: Packet 1
接收方->>发送方: NAK
发送方->>接收方: Packet 1
接收方->>发送方: ACK
发送方->>接收方: Packet 2
```
若发送方发完数据包后收到了接收方CAN标记的响应，则停止数据包发送，结束传输。
```
发送方->>接收方: Packet 1
接收方->>发送方: CAN
```

#### 阶段四、数据传输结束
若发送方已将数据包全部发完，则发送EOT标记等待接收方的NAK响应，当发送方收到NAK后立刻再次发送EOT等待接收方的ACK响应，接收到ACK标记则表示本次传输完全成功
```
发送方->>接收方: EOT
接收方->>发送方: NAK
发送方->>接收方: EOT
接收方->>发送方: ACK
接收方->>发送方: Char 'C'
```
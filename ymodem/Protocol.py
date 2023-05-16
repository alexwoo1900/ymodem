from enum import IntEnum
from typing import Any, List, Optional

from ordered_set import OrderedSet

from ymodem.Version import Version

class ProtocolType(IntEnum):
    XMODEM = 0,
    YMODEM = 1,
    # not support yet
    ZMODEM = 2

    @classmethod
    def all(cls) -> List[int]:
        return [
            cls.XMODEM,
            cls.YMODEM,
            cls.ZMODEM
        ]
    
class ZMODEM:

    ZPAD                = '*'
    ZDLE                = 24        # 0o30
    ZDLEE               = ZDLE ^ 64 # 0o100
    ZBIN                = 'A'
    ZHEX                = 'B'
    ZBIN32              = 'C'

    #########################################
    #
    #             Frame type
    #
    #########################################

    ZRQINIT             = 0
    ZRINIT              = 1
    ZSINIT              = 2
    ZACK                = 3
    ZFILE               = 4
    ZSKIP               = 5
    ZNAK                = 6
    ZABORT              = 7
    ZFIN                = 8
    ZRPOS               = 9
    ZDATA               = 10
    ZEOF                = 11
    ZFERR               = 12
    ZCRC                = 13
    ZCHALLENGE          = 14
    ZCOMPL              = 15
    ZCAN                = 16
    ZFREECNT            = 17
    ZCOMMAND            = 18
    ZSTDERR             = 19

    #########################################
    #
    #              ZDLE sequence
    #
    #########################################

    ZCRCE               = 'h'
    ZCRCG               = 'i'
    ZCRCQ               = 'j'
    ZCRCW               = 'k'
    ZRUB0               = 'l'
    ZRUB1               = 'm'

    #########################################
    #
    #              Byte position
    #
    #########################################

    # Byte positions within header array
    ZF0                 = 3
    ZF1                 = 2
    ZF2                 = 1
    ZF3                 = 0
    ZP0                 = 0
    ZP1                 = 1
    ZP2                 = 2
    ZP3                 = 3

    #########################################
    #
    #                 ZRINIT
    #
    #########################################

    # Bit Masks for ZRINIT flags byte ZF0
    CANFDX              = 0b00000001
    CANOVIO             = 0b00000010
    CANBRK              = 0b00000100
    CANCRY              = 0b00001000
    CANLZW              = 0b00010000
    CANFC32             = 0b00100000
    ESCCTL              = 0b01000000
    ESC8                = 0b10000000

    # Bit Masks for ZRINIT flags byte ZF1
    ZF1_CANVHDR         = 0b00000001
    ZF1_TIMESYNC        = 0b00000010

    #########################################
    #
    #                 ZSINIT
    #
    #########################################

    # Parameters for ZSINIT frame
    ZATTNLEN            = 32

    # Bit Masks for ZSINIT flags byte ZF0
    TESCCTL             = 64    # 0o100
    TESC8               = 128   # 0o200

    #########################################
    #
    #                 ZFILE
    #
    #########################################

    ZCBIN               = 1
    ZCNL                = 2
    ZCRESUM             = 3

    #########################################
    #
    #                 Management
    #
    #########################################

    # Management include options, one of these ored in ZF1
    ZF1_ZMSKNOLOC       = 0x80

    # Management options, one of these ored in ZF1
    ZF1_ZMMASK          = 0x1f
    ZF1_ZMNEWL          = 1
    ZF1_ZMCRC           = 2
    ZF1_ZMAPND          = 3
    ZF1_ZMCLOB          = 4
    ZF1_ZMNEW           = 5
    ZF1_ZMDIFF          = 6
    ZF1_ZMPROT          = 7
    ZF1_ZMCHNG          = 8

    #########################################
    #
    #                 Transport
    #
    #########################################

    # Transport options, one of these in ZF2
    ZTLZW               = 1
    ZTCRYPT             = 2
    ZTRLE               = 3

    # Extended options for ZF3, bit encoded
    ZXSPARS             = 64

    #########################################
    #
    #                 ZCOMMAND
    #
    #########################################

    ZCACK1              = 1
    
class YMODEM:

    #########################################
    #
    #                 Feature
    #
    #########################################

    # Bit Masks for YMODEM features
    USE_LENGTH_FIELD    = 0b00000001
    USE_DATE_FIELD      = 0b00000010
    USE_MODE_FIELD      = 0b00000100
    USE_SN_FIELD        = 0b00001000
    ALLOW_1K_PACKET     = 0b00010000
    ALLOW_YMODEM_G      = 0b00100000

    @classmethod
    def features(cls) -> List[int]:
        return [
            cls.USE_LENGTH_FIELD,
            cls.USE_DATE_FIELD,
            cls.USE_MODE_FIELD,
            cls.USE_SN_FIELD,
            cls.ALLOW_1K_PACKET,
            cls.ALLOW_YMODEM_G
        ]
    
    @classmethod
    def full_features(cls) -> List[int]:
        PROTOCOL_TYPE = ProtocolType.YMODEM << 8
        return [
            PROTOCOL_TYPE + cls.USE_LENGTH_FIELD,
            PROTOCOL_TYPE + cls.USE_DATE_FIELD,
            PROTOCOL_TYPE + cls.USE_MODE_FIELD,
            PROTOCOL_TYPE + cls.USE_SN_FIELD,
            PROTOCOL_TYPE + cls.ALLOW_1K_PACKET,
            PROTOCOL_TYPE + cls.ALLOW_YMODEM_G
        ]
    
class _ProtocolStyle:
    def __init__(self):
        self._feature_dict = {}

    def set_protocol_features(self, protocol_type: int, features: Any):
        self._feature_dict[protocol_type] = features
    
    def get_protocol_features(self, protocol_type: int):
        return self._feature_dict[protocol_type]
    
class ProtocolStyle:
    def __init__(self, name: str):
        self._name = name
        self._id = self._name.upper().replace(' ', '_').replace('/', '_').replace('-', '_')
        self._registered_versions = OrderedSet()
        self._deprecated_versions = set()
        self._target_version = None
        self._cores = {}
        self._enabled = True

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enable(self, enabled: bool):
        self._enabled = enabled

    def is_available(self) -> bool:
        return self._enabled
    
    def get_latest_version(self) -> Optional[Version]:
        if bool(self._registered_versions):
            return max(self._registered_versions)
        else:
            return None
        
    def get_core(self, version: Version) -> Optional[_ProtocolStyle]:
        if str(version) in self._cores:
            return self._cores[str(version)]
        else:
            return None

    def register(self, versions: List[Version]) -> None:
        for version in versions:
            if version not in self._registered_versions:
                self._cores[str(version)] = _ProtocolStyle()
                self._registered_versions.add(version)
            else:
                # no warning and do nothing
                pass

    def deprecate(self, versions: List[Version]) -> None:
        for version in versions:
            if version in self._registered_versions:
                self._deprecated_versions.add(version)

    def unregister(self, versions: List[Version]) -> None:
        for version in versions:
            if version in self._registered_versions:
                del self._cores[str(version)]
                self._registered_versions.discard(version)
                # gc.collect()

    def select(self, version: Optional[Version] = None) -> None:
        if not version:
            version = self.get_latest_version()
            if version:
                self._target_version = version
            else:
                raise IndexError("No registered style!") 
        elif version not in self._registered_versions:
            raise KeyError(f"Style {self.name} - {str(version)} has not registered yet!")
        elif version in self._deprecated_versions:
            raise KeyError(f"Style {self.name} - {str(version)} has been deprecated!")
        else:
            self._target_version = version

    def update_protocol_features(self, protocol_type: int, features: Any) -> None:
        if not self._target_version:
            raise IndexError("Call select() before update!")
        elif protocol_type not in ProtocolType.all():
            raise TypeError(f"Parameter {protocol_type} does not belong to protocol type")
        else:
            self._cores[str(self._target_version)].set_protocol_features(protocol_type, features)
            

    def get_protocol_features(self, protocol_type: int) -> Any:
        if not self._target_version:
            raise IndexError("Call select() before get!")
        elif protocol_type not in ProtocolType.all():
            raise TypeError(f"Parameter {protocol_type} does not belong to protocol type")
        else:
            return self._cores[str(self._target_version)].get_protocol_features(protocol_type)


class ProtocolStyleManagement:
    def __init__(self):
        self._registered_styles = {}
        self.register_all()

    # Temporarily hard coding, change to configuration mode after the program is complete
    def register_all(self):
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
        p = ProtocolStyle("Unix rz/sz")
        p.register(["1.0.0"])
        p.select()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.USE_DATE_FIELD | YMODEM.USE_MODE_FIELD | YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("VMS rb/sb")
        p.register(["1.0.0"])
        p.select()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("Pro-YAM")
        p.register(["1.0.0"])
        p.select()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.USE_DATE_FIELD | YMODEM.USE_SN_FIELD | YMODEM.ALLOW_1K_PACKET | YMODEM.ALLOW_YMODEM_G)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("CP/M YAM")
        p.register(["1.0.0"])
        p.select()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("KMD/IMP")
        p.register(["1.0.0"])
        p.select()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

    def get_available_styles(self) -> List[ProtocolStyle]:
        available_programs = []

        for style_id, style in self._registered_styles.items():
            if style.is_available():
                available_programs.append(style_id)

        return available_programs

    def get_available_style(self, id) -> ProtocolStyle:
        if id in self.get_available_styles():
            return self._registered_styles[id]
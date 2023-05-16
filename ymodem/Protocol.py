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
    
class YMODEM:

    USE_LENGTH_FIELD    = 0b00100000
    USE_DATE_FIELD      = 0b00010000
    USE_MODE_FIELD      = 0b00001000
    USE_SN_FIELD        = 0b00000100
    ALLOW_1K_PACKET     = 0b00000010
    ALLOW_YMODEM_G      = 0b00000001

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
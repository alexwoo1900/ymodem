from enum import IntEnum
from typing import Any, List, Optional

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
    USE_LENGTH_FIELD    = 0b100000
    USE_DATE_FIELD      = 0b010000
    USE_MODE_FIELD      = 0b001000
    USE_SN_FIELD        = 0b000100
    ALLOW_1K_PACKET     = 0b000010
    ALLOW_YMODEM_G      = 0b000001

    @classmethod
    def all_features(cls) -> List[int]:
        return [
            cls.USE_LENGTH_FIELD,
            cls.USE_DATE_FIELD,
            cls.USE_MODE_FIELD,
            cls.USE_SN_FIELD,
            cls.ALLOW_1K_PACKET,
            cls.ALLOW_YMODEM_G
        ]
    
class ProtocolStyle:
    def __init__(self, name: str):
        self._name = name
        self._id = self._name.upper().replace(' ', '_').replace('/', '_').replace('-', '_')
        self._versions = []             # type: List[Version]
        self._deprecated_versions = []  # type: List[Version]
        self._target_version = Version("0.0.0")
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
    
    def get_versions(self) -> List[Version]:
        return self._versions
    
    def get_latest_version(self) -> Version:
        if len(self._versions) > 0:
            return sorted(self._versions)[-1]
        else:
            return Version("0.0.0")
        
    def get_core(self, version: Version):
        if str(version) in self._cores:
            return self._cores[str(version)]

    def release(self, versions: List[Version]) -> None:
        for version in versions:
            if str(version) not in self._cores:
                self._cores[str(version)] = _ProtocolStyle()
                self._versions.append(version)
            else:
                pass

    def delete(self, versions: List[Version]) -> None:
        for version in versions:
            if str(version) in self._cores:
                del self._cores[str(version)]
                # gc.collect()
                for stored_version in self._versions:
                    if version == stored_version:
                        self._versions.remove(stored_version)

    def switch(self, version: Optional[Version] = None):
        if not version:
            version = self.get_latest_version()
        
        if version not in self._deprecated_versions:
            self._target_version = version

    def update_protocol_features(self, protocol_type: int, features: Any):
        if str(self._target_version) in self._cores and protocol_type in ProtocolType.all():
            self._cores[str(self._target_version)].set_protocol_features(protocol_type, features)
        else:
            pass

    def get_protocol_features(self, protocol_type: int):
        if str(self._target_version) in self._cores:
            return self._cores[str(self._target_version)].get_protocol_features(protocol_type)

class ProtocolStyleManagement:
    def __init__(self):
        self._registered_styles = {}
        self.register_all_styles()

    # Temporarily hard coding, change to configuration mode after the program is complete
    def register_all_styles(self):
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
        p.release(["1.0.0"])
        p.switch()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.USE_DATE_FIELD | YMODEM.USE_MODE_FIELD | YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("VMS rb/sb")
        p.release(["1.0.0"])
        p.switch()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("Pro-YAM")
        p.release(["1.0.0"])
        p.switch()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.USE_LENGTH_FIELD | YMODEM.USE_DATE_FIELD | YMODEM.USE_SN_FIELD | YMODEM.ALLOW_1K_PACKET | YMODEM.ALLOW_YMODEM_G)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("CP/M YAM")
        p.release(["1.0.0"])
        p.switch()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

        p = ProtocolStyle("KMD/IMP")
        p.release(["1.0.0"])
        p.switch()
        p.update_protocol_features(ProtocolType.YMODEM, YMODEM.ALLOW_1K_PACKET)
        self._registered_styles[p.id] = p

    def get_available_styles(self):
        available_programs = []

        for style_id, style in self._registered_styles.items():
            if style.is_available():
                available_programs.append(style_id)

        return available_programs

    def get_available_style(self, id):
        if id in self.get_available_styles():
            return self._registered_styles[id]

class _ProtocolStyle:
    def __init__(self):
        self._feature_dict = {}

    def set_protocol_features(self, protocol_type: int, features: Any):
        self._feature_dict[protocol_type] = features
    
    def get_protocol_features(self, protocol_type: int):
        return self._feature_dict[protocol_type]
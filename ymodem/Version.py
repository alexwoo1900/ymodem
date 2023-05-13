import re
from typing import cast

class Version:
    def __init__(self, version):
        super().__init__()

        self._major = 0
        self._minor = 0
        self._revision = 0
        self._postfix_type = ''
        self._postfix_version = ''

        if type(version) == bytes:
            version = cast(bytes, version)
            version = version.decode('utf-8')

        if isinstance(version, str):
            version = cast(str, version)

            version = version.replace('-', '.')
            version = version.replace('_', '.')
            version = version.replace('"', '')
            version = version.replace('+', '.')
            version_list = version.split('.')

            try:
                version_list[0] = re.sub(r'[A-Z]+', '', version_list[0])
                version_list[0] = re.sub(r'[A-Z]+', '', version_list[1])
                version_list[0] = re.sub(r'[A-Z]+', '', version_list[2])
                version_list[0] = re.sub(r'[A-Z]+', '', version_list[4])
            except IndexError as err:
                pass
        elif isinstance(version, list):
            version_list = version
        elif isinstance(version, int):
            version_list = [version]
        elif isinstance(version, Version):
            version_list = [version.get_major(), version.get_minor(), version.get_revision(), version.get_postfix_type(), version.get_postfix_version()]
        else:
            # TODO LOG
            version_list = []

        try:
            self._major = int(version_list[0])
            self._minor = int(version_list[1])
            self._revision = int(version_list[2])
            self._postfix_type = version_list[3]
            self._postfix_version = int(version_list[4])
        except IndexError:
            pass
        except ValueError:
            pass

    
    def get_major(self):
        return self._major
    
    def get_minor(self):
        return self._minor
    
    def get_revision(self):
        return self._revision
    
    def get_postfix_type(self):
        return self._postfix_type

    def get_postfix_version(self):
        return self._postfix_version
    
    def has_postfix(self):
        return self._postfix_type != ''
    
    def __gt__(self, other):
        if isinstance(other, Version):
            return other.__lt__(self)
        elif isinstance(other, str):
            return Version(other).__lt__(self)
        else:
            return False
        
    def __lt__(self, other):
        if isinstance(other, Version):
            if self._major < other.get_major():
                return True
            if self._minor < other.get_minor():
                return True
            if self._revision < other.get_revision() \
                and self._major == other.get_major() \
                and self._minor == other.get_minor():
                return True
            if self.has_postfix() and other.has_postfix() \
                and self._postfix_version < other.get_postfix_version() \
                and self._postfix_type == other.get_postfix_type() \
                and self._revision == other.get_revision() \
                and self._minor == other.get_minor() \
                and self._major == other.get_major():
                return True
            if self.has_postfix() and not other.has_postfix():
                return Version('{}.{}.{}').format(self.get_major(), self.get_minor(), self.get_revision()) == other
        elif isinstance(other, str):
            return self < Version(other)
        else:
            return False


    def __eq__(self, other):
        if isinstance(other, Version):
            return self._major == other.get_major() \
                and self._minor == other.get_minor() \
                and self._revision == other.get_revision() \
                and self._postfix_type == other.get_postfix_type() \
                and self._postfix_version == other.get_postfix_version()

        if isinstance(other, str):
            return self == Version(other)
        
        return False

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __str__(self):
        if self._postfix_type:
            return '%s.%s.%s-%s.%s' % (self._major, self._minor, self._revision, self._postfix_type, self._postfix_version)
        return '%s.%s.%s' % (self._major, self._minor, self._revision)

    def __hash__(self):
        return hash(self.__str__())
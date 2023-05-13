import sys

class Platform:

    class PlatformType:
        Windows = 1
        Linux = 2
        OSX = 3
        Other = 4

    __platform_type = PlatformType.Other
    if sys.platform == 'win32':
        __platform_type = PlatformType.Windows
    elif sys.platform == 'linux':
        __platform_type = PlatformType.Linux
    elif sys.platform == 'darwin':
        __platform_type = PlatformType.OSX

    @classmethod
    def is_OSX(cls):
        return cls.__platform_type == cls.PlatformType.OSX
    
    @classmethod
    def is_Windows(cls):
        return cls.__platform_type == cls.PlatformType.Windows
    
    @classmethod
    def is_Linux(cls):
        return cls.__platform_type == cls.PlatformType.Linux
    
    @classmethod
    def get_type(cls):
        return cls.__platform_type
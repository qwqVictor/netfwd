from models.enum import tunnelType
import struct

class LoginStruct:
    __struct_fmt: str = '4sb16sHB'  # length 25
    _length: int = struct.calcsize(__struct_fmt)
    magic: bytes = b'wzq.'          # 4: wzq
    mode: int                       # 1: int8
    token: bytes                    # 16: md5 token
    remote_port: int                # 2: int16
    extendlen: int                  # 1: int8
    domain: str                     # 0-255 len

    def __init__(self, mode: int = 0, remote_port: int = 0, token: bytes = b'', domain: str = ''):
        self.mode = mode
        self.token = token
        self.remote_port = remote_port
        self.extendlen = len(str(domain).encode('utf-8'))
        self.domain = str(domain)
        
    def fill(self, src: bytes):
        self.magic, self.mode, self.token, self.remote_port, self.extendlen = struct.unpack(self.__struct_fmt, src[:self._length])
        self.domain = src[self._length : self._length+self.extendlen].decode('utf-8')

    def serialize(self):
        if self.mode == tunnelType.http or self.mode == tunnelType.ssl:
            self.extendlen = min(255, len(self.domain))
        return struct.pack(self.__struct_fmt, self.magic, self.mode, self.token, self.remote_port, self.extendlen) + self.domain.encode('utf-8')

class LoginReplyStruct:
    __struct_fmt: str = 'i'
    _length: int = struct.calcsize(__struct_fmt)
    errno: int                      # 4: int32
    def __init__(self, errno: int=0):
        self.errno = 0
        
    def fill(self, src: bytes):
        self.errno, = struct.unpack(self.__struct_fmt, src)

    def serialize(self):
        return struct.pack(self.__struct_fmt, self.errno)

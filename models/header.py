import struct

class ConnHeaderStruct:
    __struct_fmt: str = '4sQH'   # length 18
    _length: int = struct.calcsize(__struct_fmt)
    magic: bytes = b'vhng'       # 4
    conn_id: int                # 8 uint64
    chunksize: int              # 2 uint16
    def __init__(self, conn_id: int=0, chunksize: int=0):
        self.conn_id = conn_id
        self.chunksize = chunksize
        
    def fill(self, src: bytes):
        self.magic, self.conn_id, self.chunksize = struct.unpack(self.__struct_fmt, src)

    def serialize(self):
        return struct.pack(self.__struct_fmt, self.magic, self.conn_id, self.chunksize)

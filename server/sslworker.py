import socket
from server.tcp4 import TCP4Server
from server.basicworker import SLBWorkerServer
import models
import ssl

class SSLWorkerServer(SLBWorkerServer):
    type: int = models.tunnelType.ssl
    def __init__(self, master_socket: socket.socket, owner: TCP4Server, port: int, host: str, bufsize: int):
        super().__init__(master_socket, owner, port, host=host, bufsize=bufsize)
    
    def should_continue(self, buf: bytes):
        return super().should_continue(buf)

    def get_domain(self, buf: bytes):
        return super().get_domain(buf)

# FIXME: Feb 27th, 2021 01:11 CST -- Not implemented SNI sniffing yet.
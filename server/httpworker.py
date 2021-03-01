import socket
import logging
from server.tcp4 import TCP4Server
from server.basicworker import SLBWorkerServer
import models

class HTTPWorkerServer(SLBWorkerServer):
    type: int = models.tunnelType.http
    def __init__(self, master_socket: socket.socket, owner: TCP4Server, port: int, host: str, bufsize: int):
        super().__init__(master_socket, owner, port, host=host, bufsize=bufsize)
    
    def should_continue(self, buf: bytes):
        return buf.find(b'\r\n\r\n') == -1
    
    def get_domain(self, buf: bytes):
        headers = buf.split(b'\r\n')
        host = b''
        for header in headers:
            if header.lower().startswith(b'host:'):
                host = header[header.find(b':')+1:]
                break
        while host.startswith(b' '):
            host = host[host.find(b' ')+1:]

        if host.rfind(b']:') != -1:
            host = host[:host.rfind(']:')]
        elif host.rfind(b':') != -1:
            host = host[:host.rfind(':')]

        logging.debug('HTTPWorkerServer get domain %s' % (host.decode('utf-8')))
        return host.decode('utf-8')
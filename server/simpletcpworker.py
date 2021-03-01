from server.tcp4 import TCP4Server
import socket
import models
from server.basicworker import WorkerServer

class SimpleTCPWorkerServer(WorkerServer):
    type: int = models.tunnelType.tcp
    
    def __init__(self, master_socket: socket.socket, owner: TCP4Server, port: int, host: str, bufsize: int):
        super().__init__(master_socket, owner, port, host=host, bufsize=bufsize)
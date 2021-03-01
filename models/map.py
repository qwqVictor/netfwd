import socket
from typing import TypedDict

class UserInfoMap(TypedDict):
    workers: "list"
    connections: "dict[int, ConnectionInfoMap]"

class ConnectionInfoMap(TypedDict):
    master_socket: socket.socket
    worker_socket: socket.socket

import socket
def get_free_port():  
    sock = socket.socket()
    sock.bind(('', 0))
    ip, port = sock.getsockname()
    sock.close()
    port: int
    return port
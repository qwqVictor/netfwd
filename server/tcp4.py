import socket
import select
import threading
import logging

class TCP4Server:
    host: str
    port: int
    bufsize: int
    peer_conns: "list[socket.socket]"
    should_stop: bool

    def __init__(self, port: int, host: str='0.0.0.0', bufsize: int=1024):
        self.host = host
        self.port = port
        self.bufsize = bufsize
        self.peer_conns = []
        self.should_stop = True
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.socket.bind((host, port))
        self.socket.listen(10)

    def run(self):
        if not self.should_stop:
            return
        self.should_stop = False
        try:
            while not self.should_stop:
                conn: socket.socket
                addr: tuple(str, int)
                conn, addr = self.socket.accept()
                threading.Thread(target=self.conn_handler, args=(conn, addr)).start()
                self.peer_conns.append(conn)
        except Exception as e:
            logging.error("TCP4Server error: " + str(e))
    
    def stop(self):
        self.should_stop = True
        for conn in self.peer_conns:
            conn: socket.socket
            conn.close()
        self.socket.close()
    
    def conn_handler(self, conn: socket.socket, addr: "tuple(str, int)"):
        while True:
            try:
                rl, wl, _ = select.select([conn,], [conn,], [], 5)
                if conn in rl:                
                    data = conn.recv(self.bufsize)
                    if data == b'':
                        continue
                    conn.send('ACK\n')
            except select.error:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
import socket
import select
import random
import models
import logging
from server.tcp4 import TCP4Server

class WorkerServer(TCP4Server):
    master_socket: socket.socket
    owner: TCP4Server
    wait_for_min_size: int = 0

    def __init__(self, master_socket: socket.socket, owner: TCP4Server, port: int, host: str='0.0.0.0', bufsize: int=1024):
        self.master_socket = master_socket
        self.owner = owner
        super().__init__(port, host, bufsize)
    
    def decide_socket(self, buf: bytes):
        "This should be overidded non tcp usage"
        return self.master_socket

    def should_continue(self, buf: bytes):
        "This should be overidded non tcp usage"
        return False

    def conn_handler(self, conn: socket.socket, addr: "tuple(str, int)"):
        buf = b''
        conn_id = 0
        master_socket = None
        while True:
            try:
                rl, wl, _ = select.select([conn,], [conn,], [], 5)
                if conn in rl:                
                    buf += conn.recv(self.bufsize)
                    if buf == b'':
                        continue
                    if self.should_continue(buf):
                        continue
                    logging.debug("WorkerServer got:\n" + str(buf))
                    if conn_id == 0 or master_socket == None:
                        master_socket = self.decide_socket(buf)
                        conn_id = random.randint(1, 2**64)
                        logging.debug("WorkerServer new connection: [%s]:%d as uid %d , conn_id %d" % (conn.getpeername() + (id(master_socket), conn_id)) )
                        self.owner.user_info_map.get(id(master_socket), {})[conn_id] = {
                            'master_socket': master_socket,
                            'worker_socket': conn
                        }
                    while len(buf) > self.bufsize:
                        data = buf[:self.bufsize]
                        buf = buf[self.bufsize:]
                        chunksize = len(data)
                        if chunksize != 0:
                            conn_header = models.ConnHeaderStruct(conn_id=conn_id, chunksize=chunksize)
                            logging.debug("WorkerServer sent header {conn_id: %d, chunksize: %d}" % (conn_header.conn_id, conn_header.chunksize))
                            master_socket.sendall(conn_header.serialize() + data)
                    chunksize = len(buf)
                    if chunksize != 0:
                        conn_header = models.ConnHeaderStruct(conn_id=conn_id, chunksize=chunksize)
                        logging.debug("WorkerServer sent header {conn_id: %d, chunksize: %d}" % (conn_header.conn_id, conn_header.chunksize))
                        master_socket.sendall(conn_header.serialize() + buf)
                    buf = b''
            except select.error as e:
                logging.debug('WorkerServer: closed connection because ' + str(e))
                break
        if conn_id in self.owner.user_info_map.get(id(master_socket), {}):
            del self.owner.user_info_map.get(id(master_socket), {})[conn_id]
        logging.debug("WorkerServer closed connection: [%s]:%d as uid %d , conn_id %d" % (conn.getpeername() + (id(master_socket), conn_id)) )
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()
        self.peer_conns.remove(conn)

class SLBWorkerServer(WorkerServer):
    type: int
    domain_map: "dict[str: socket.socket]"

    def __init__(self, master_socket: socket.socket, owner: TCP4Server, port: int, host: str='0.0.0.0', bufsize: int=1024):
        self.domain_map = {}
        super().__init__(master_socket, owner, port, host, bufsize)

    def mod_domain(self, domain: str, sock: socket.socket):
        self.domain_map[domain] = sock

    def rm_domain(self, domain: str):
        if domain in self.domain_map:
            del self.domain_map[domain]
            return True
        else:
            return False

    def decide_socket(self, buf: bytes):
        default_socket: socket.socket
        default_socket = None
        for sock in self.domain_map.values():
            default_socket = sock
            break
        logging.debug('SLBWorkerServer decide socket now domain map is %s' % (str(self.domain_map)))
        return self.domain_map.get(self.get_domain(buf), default_socket)

    def get_domain(self, buf: bytes):
        "should be overidded"
        return ''
    
    def stop(self):
        del self.owner.slb_worker_map[self.port]
        return super().stop()
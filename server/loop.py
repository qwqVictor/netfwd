import logging
import socket
import select
import threading
from server.tcp4 import TCP4Server
from server.basicworker import WorkerServer, SLBWorkerServer
from server.simpletcpworker import SimpleTCPWorkerServer
from server.httpworker import HTTPWorkerServer
from server.sslworker import SSLWorkerServer
import models

IMPLEMENTED_WORKER_TYPES = {
    models.tunnelType.tcp: SimpleTCPWorkerServer,
    models.tunnelType.http: HTTPWorkerServer,
    models.tunnelType.ssl: SSLWorkerServer
}

class LoopServer(TCP4Server):
    
    user_info_map : "dict[int, models.UserInfoMap]"
    slb_worker_map : "dict[int, SLBWorkerServer]"
    valid_tokens: "list[bytes]"

    def __init__(self, port: int, host: str='0.0.0.0', valid_tokens: "list[bytes]"=[], bufsize: int=1024):
        self.user_info_map = {}
        self.slb_worker_map = {}
        self.valid_tokens = valid_tokens
        super().__init__(port, host=host, bufsize=bufsize)

    def run(self):
        logging.info("Netfwd server running on [%s]:%d" % (self.host, self.port))
        logging.info("Copyright (C) 2021 Victor Huang <i@qwq.ren>")
        return super().run()

    def spawn_new_worker(self, port: int, master_socket: socket.socket, host: str='0.0.0.0', domain='', worker_type: int=models.tunnelType.tcp):
        
        def _spawn_new_worker_thread():
            worker_server: WorkerServer
            worker_server = IMPLEMENTED_WORKER_TYPES[worker_type](master_socket=master_socket, owner=self, port=port, host=host, bufsize=self.bufsize)
            if domain != '':
                worker_server.mod_domain(domain, master_socket)
                self.slb_worker_map[port] = worker_server
            self.user_info_map.get(id(master_socket), {}).get('workers', []).append(worker_server)
            worker_server.run()
        
        logging.debug("LoopServer spawn new worker -- map: %s" % (str(self.slb_worker_map)))

        if port in self.slb_worker_map:
            logging.debug('LoopServer spawn new worker : port %d already in map' % (port))
            if self.slb_worker_map[port].type == worker_type:
                self.slb_worker_map[port].mod_domain(domain, master_socket)
                logging.debug('LoopServer spawn new worker : add domain %s to %d map' % (domain, port))
        else:
            threading.Thread(target=_spawn_new_worker_thread, args=()).start()

    def validate_token(self, token: bytes):
        return self.valid_tokens == [] or (token in self.valid_tokens)

    def conn_handler(self, conn: socket.socket, addr: "tuple(str, int)"):
        buf = b''
        uid = -1
        while True:
            try:
                rl, wl, _ = select.select([conn,], [conn,], [], 5)
                if conn in rl:                
                    buf += conn.recv(self.bufsize + models.ConnHeaderStruct._length)
                    if buf == b'':
                        continue
                    logging.debug('LoopServer got: \n' + str(buf))
                    if uid == -1:
                        login = models.LoginStruct()
                        login.fill(buf[:login._length])
                        assert login.magic == models.LoginStruct.magic
                        logging.debug('LoopServer new login: [%s]:%d with token %s' % (addr[0], addr[1], login.token))
                        buf = buf[login._length:]
                        
                        if self.validate_token(login.token):
                            domain=''
                            if login.mode == models.tunnelType.http or login.mode == models.tunnelType.ssl:
                                domain = buf[:login.extendlen].decode('utf-8')
                                buf = buf[login.extendlen:]
                            uid = id(conn)
                            self.user_info_map[uid] = {}
                            self.spawn_new_worker(port=login.remote_port, master_socket=conn, domain=domain, worker_type=login.mode)
                            conn.sendall(models.LoginReplyStruct().serialize())
                            logging.info("Accepted client on remote port %d" % login.remote_port)
                            if domain != '':
                                logging.info("The client registered domain %s on remote_port %d." % (domain, login.remote_port))
                        else:
                            logging.debug('LoopServer client invalid token, reject')
                            conn.sendall(models.LoginReplyStruct(errno=models.ErrorNo.invalid_token))
                            conn.shutdown(socket.SHUT_RDWR)
                            conn.close()
                            self.peer_conns.remove(conn)
                            break
                    else:
                        conn_header = models.ConnHeaderStruct()
                        conn_header.fill(buf[:models.ConnHeaderStruct._length])
                        assert conn_header.magic == models.ConnHeaderStruct.magic
                        buf = buf[models.ConnHeaderStruct._length:]
                        worker_socket: socket.socket
                        worker_socket = self.user_info_map.get(uid, {}).get(conn_header.conn_id, models.ConnectionInfoMap()).get('worker_socket', None)
                        if worker_socket:
                            try:
                                while True:
                                    _, wl, _ = select.select([], [worker_socket], [], 0.5)
                                    if worker_socket in wl:
                                        logging.debug("LoopServer writing to worker_socket [%s]:%d" % (worker_socket.getpeername()))
                                        worker_socket.sendall(buf[:conn_header.chunksize])
                                        logging.debug("LoopServer finished writing to worker_socket [%s]:%d" % (worker_socket.getpeername()))
                                        break
                            except Exception as e:
                                logging.debug('LoopServer writing worker_socket failed: ' + str(e))
                        buf = buf[conn_header.chunksize:]
            except select.error:
                if uid != -1:
                    for worker in self.user_info_map.get(uid, {}).get('workers', []):
                        worker: WorkerServer
                        worker.stop()
                    del self.user_info_map[uid]
                    logging.debug('LoopServer: stopping worker for uid %d' % (uid))
                peername = conn.getpeername()
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
                self.peer_conns.remove(conn)
                logging.debug('LoopServer: closed connection %s' % (str(peername)))
                break
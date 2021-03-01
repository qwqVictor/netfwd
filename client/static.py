import http.server
import logging
import socket
import socketserver
import os

def static_http_server(path: str, port: int, host: str='127.0.0.1'):
    os.chdir(path)
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((host, port), Handler) as httpd:
        logging.debug("http server serving at port %d" % port)
        httpd.serve_forever()